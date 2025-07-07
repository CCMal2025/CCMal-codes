import pickle
import time
from typing import Any, Union, List

import redis


def get_function_id(redis_key) -> int:
    return int(redis_key.split(":")[-1])


def get_package_id(redis_key) -> int:
    return int(redis_key.split(":")[1])


class Redis:

    def __init__(self, host='127.0.0.1', port=24779, db=0):
        self.con = redis.StrictRedis(host=host, port=port, db=db)

    def __del__(self):
        self.con.close()

    def save_str(self, key, string: bytes) -> Any:
        self.con.set(key, string)

    def save_pickle(self, key, object: Any):
        self.con.set(key, pickle.dumps(object))

    def push_queue(self, key, uuid: str):
        self.con.lpush(key, uuid)

    def push_queue_pickle(self, key, obj):
        self.con.lpush(key, pickle.dumps(obj))

    def pop_queue(self, key, cnt=1) -> Union[List[bytes], None]:
        return self.con.rpop(key, cnt)

    def pop_queue_pickles(self, key, timeout=1, cnt=100):
        time.sleep(timeout)
        pickled_objs = self.con.rpop(key, count=cnt)
        if pickled_objs is not None:
            return [pickle.loads(pickled_obj) for pickled_obj in pickled_objs]
        return None

    def load_int(self, key) -> int:
        bytes = self.load_bytes(key)
        if bytes is None:
            return 0
        return int(bytes.decode())

    def load_float(self, key) -> float:
        bytes = self.load_bytes(key)
        if bytes is None:
            return 0.0
        return float(bytes.decode())

    def load_bytes(self, key) -> bytes:
        return self.con.get(key)

    def load_pickle(self, key) -> Any:
        value = self.con.get(key)
        if value is None:
            raise Exception(f"{key} is None!")
        return pickle.loads(value)

    def load_all_prefix_key(self, prefix: str):
        cursor = '0'
        while cursor != 0:
            cursor, keys = self.con.scan(cursor=cursor, match=f"{prefix}:*", count=1000)
            for key in keys:
                yield key

    def save_to_set(self, key, value: str):
        return self.con.sadd(key, value)

    def remove_from_set(self, key, value: str):
        return self.con.srem(key, value)

    def item_cnt(self, key):
        return int(self.con.scard(key))

    def queue_item_cnt(self, key):
        return int(self.con.llen(key))

    def incr_key(self, key, cnt=1):
        self.con.incr(key, amount=cnt)

    def register_script(self, script):
        return self.con.register_script(script)

    def dump_rdb(self):
        return self.con.save()