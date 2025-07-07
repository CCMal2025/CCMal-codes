import collections
from typing import Union, List

from redis_cache import Redis

Message = collections.namedtuple("Message", ["lang", "context", "message_version"])


class SignalManager:
    # s Signals
    # |- s:malware         the malware channel
    # |- s:jobset          processing jobs, empty when all jobs finished
    # |- s:{step}:start    started job of the step
    # |- s:{step}:fin      finished job of the step
    def __init__(self, r: Redis):
        self.r = r

        self.update_max_script = self.r.register_script( """
        local current = redis.call('GET', KEYS[1])
        if not current then
            redis.call('SET', KEYS[1], ARGV[1])
            return ARGV[1]
        else
            local current_num = tonumber(current)
            local new_num = tonumber(ARGV[1])
            if new_num > current_num then
                redis.call('SET', KEYS[1], ARGV[1])
                return ARGV[1]
            else
                return current
            end
        end
        """)

    def publish(self, lang: str, context: dict):
        self.r.push_queue_pickle("s:malware_message2", Message(lang, context, "42"))

    def listen(self, timeout=1, cnt=100) -> Union[List[Message], None]:
        return self.r.pop_queue_pickles("s:malware_message2", timeout=timeout, cnt=cnt)

    def append_job(self, job_id: str):
        self.r.save_to_set("s:jobset", job_id)

    def pop_job(self, job_id: str):
        self.r.remove_from_set("s:jobset", job_id)

    def is_detect_finished(self):
        return self.r.item_cnt("s:jobset") == 0

    def is_message_queue_empty(self):
        return self.r.queue_item_cnt("s:malware_message2") == 0

    def clear_signal(self):
        delete_keys = list(self.r.load_all_prefix_key("s"))
        if len(delete_keys) != 0:
            self.r.con.delete(*delete_keys)

    def incr_start_job(self, step: str):
        self.r.incr_key(f"s:{step}:start")

    def package_status_set(self, package_uuid:str, step: str):
        self.r.save_to_set(f"s:{step}:packages", package_uuid)

    def file_status_set(self, package_uuid:str, step: str):
        self.r.save_to_set(f"s:{step}:files", package_uuid)

    def incr_fin_job(self, step: str):
        self.r.incr_key(f"s:{step}:fin")

    def get_steps_info(self, step: str):
        return self.r.load_int(f"s:{step}:fin"), self.r.load_int(f"s:{step}:start")

    def package_status_get(self, step: str):
        return self.r.item_cnt(f"s:{step}:packages")

    def file_status_get(self, step: str):
        return self.r.item_cnt(f"s:{step}:files")

    def save_total_time(self, step: str, time: float):
        us_time = int(time * 1000000)
        self.r.save_pickle(f"s:{step}:time", us_time)

    def load_time(self, step):
        total_time = self.r.load_pickle(f"s:{step}:time")
        return float(total_time) / 1000000

    def record_max_sim(self, package_uuid, sim):
        return self.update_max_script(keys=[f's:max_sim:{package_uuid}'], args=[sim])

    def load_all_max_sim(self):
        sim_list = []
        for key in self.r.load_all_prefix_key("s:max_sim"):
            sim = self.r.load_float(key)
            sim_list.append(sim)
        return sim_list
