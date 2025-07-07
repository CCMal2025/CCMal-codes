from typing import List, Tuple

from celery import Task

import components.syntaxFilter
from celery_task.celery import app
from celery_task.utils import set_package_status, set_file_status
from redis_cache import MalwareCache, Redis, SignalManager


class SyntaxFilterTask(Task):
    _redis = None

    @property
    def redis(self):
        if self._redis is None:
            self._redis = Redis()
        return self._redis


@app.task(base=SyntaxFilterTask, bind=True)
def syntax_filter_task(self, lang, context, sim_mal_files_and_sims: List[Tuple[str, float]], threshold_list: dict):
    sf = components.syntaxFilter.SyntaxFilter2(threshold=threshold_list["syntax"])
    cache = MalwareCache(self.redis)

    set_package_status(self.redis, "syntax", lang, context["package_path"])
    set_file_status(self.redis, "syntax", lang, context["package_path"], context["path"])

    target_seq = context["syntax_seq"]
    del context["syntax_seq"]

    for sim_mal_file, sim in sim_mal_files_and_sims:
        malware_seq = cache.load_malware_syntax_seq(lang, sim_mal_file)

        if len(target_seq) < 200000 and len(malware_seq) < 200000:
            is_mal, syntax_sim = sf.query(malware_seq, target_seq, threshold_list["syntax"])
        else:
            is_mal, syntax_sim = True, 1.0   # bypass too long sequence
            print(f"Detected TOO long sequence: T-{len(target_seq)}/M-{len(malware_seq)}")

        if is_mal:
            context["token_sim"] = sim
            context["mal_file_id"] = sim_mal_file
            context["syntax_sim"] = syntax_sim
            signal = SignalManager(self.redis)
            signal.publish(lang, context)
            set_package_status(self.redis, "mal", lang, context["package_path"])
            set_file_status(self.redis, "mal", lang, context["package_path"], context["path"])