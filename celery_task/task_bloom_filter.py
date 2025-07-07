import os
import pickle

from celery import Task

import extractor
from redis_cache import Redis
from .celery import app
from .task_token_filter import token_filter_task
from .utils import set_file_status, set_package_status


class BloomFilterTask(Task):
    langs = ["js", "py"]

    _nsfbf = {}
    _redis = None
    _token_filter_meta = None
    ignore_result = True

    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "nsfbf")

    @property
    def nsfbf(self):
        if len(self._nsfbf.keys()) == 0:
            for lang in self.langs:
                with open(os.path.join(self.cache_dir, f"{lang}.pickle"), "rb") as f:
                    self._nsfbf[lang] = pickle.load(f)
        return self._nsfbf

    @property
    def redis(self):
        if self._redis is None:
            self._redis = Redis()
        return self._redis


@app.task(base=BloomFilterTask, bind=True)
def bloom_filter_task(self, lang: str, package_path: str, target_funcs_list: dict, bypass: bool, threshold_list: dict):
    set_package_status(self.redis, "bloom", lang, package_path)
    set_package_status(self.redis, "total", lang, package_path)

    for context in target_funcs_list:
        target_func_path = context["path"]
        set_file_status(self.redis, "bloom", lang, package_path, target_func_path)
        set_file_status(self.redis, "total", lang, package_path, target_func_path)

        code = context["code"]
        e = extractor.extract_code(code, lang)

        if not bypass:
            vector = e.keyword_vector()
            self.nsfbf[lang].threshold = threshold_list["bloom"]
            result = self.nsfbf[lang].detect(vector)
        else:
            result = True

        if result:
            # Maybe vul
            token = e.token()

            context["package_path"] = package_path
            context["token"] = token
            context["syntax_seq"] = e.syntax_seq()

            # del context["code"]

            token_filter_task.delay(lang, context, threshold_list)