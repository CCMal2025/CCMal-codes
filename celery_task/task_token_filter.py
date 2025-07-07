import os.path
import pickle
from collections import Counter

from celery import Task

from redis_cache import Redis, SignalManager
from .celery import app
from .task_syntax_filter import syntax_filter_task
from .utils import set_package_status, set_file_status


class TokenFilterTask(Task):
    langs = ["js", "py", "sh"]

    _redis = None
    _token_filters = {}

    ignore_result = True
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "token")

    @property
    def redis(self):
        if self._redis is None:
            self._redis = Redis()
        return self._redis

    @property
    def token_filters(self):
        if len(self._token_filters.keys()) == 0:
            for lang in self.langs:
                with open(os.path.join(self.cache_dir, f"{lang}.pickle"), "rb") as f:
                    self._token_filters[lang] = pickle.load(f)
        return self._token_filters


@app.task(base=TokenFilterTask, bind=True)
def token_filter_task(self, lang: str, context: dict, threshold_list: dict):

    set_package_status(self.redis, "token", lang, context["package_path"])
    set_file_status(self.redis, "token", lang, context["package_path"], context["path"])

    tf = self.token_filters[lang]
    target_token = Counter(context["token"])
    del context["token"]
    sim_mal_funcs, max_sim = tf.query(target_token, threshold_list["token"])

    signal = SignalManager(self.redis)
    signal.record_max_sim(context["package_path"], max_sim)

    if len(sim_mal_funcs) == 0:
        return

    sim_mal_funcs.sort(key=lambda pair: pair[1], reverse=True)
    sim_mal_funcs = sim_mal_funcs[:10]  # only first 10 mal pair is keep to reduce syntax filter load

    # Only goes token filter and determine if is mal
    if lang == "sh":
        set_package_status(self.redis, "total", lang, context["package_path"])
        set_file_status(self.redis, "total", lang, context["package_path"], context["path"])
        for mal_file_id, sim in sim_mal_funcs:
            context["mal_file_id"] = mal_file_id
            context["token_sim"] = sim
            signal.publish(lang, context)
            set_package_status(self.redis, "mal", lang, context["package_path"])
            set_file_status(self.redis, "mal", lang, context["package_path"], context["path"])
    else:
        syntax_filter_task.delay(lang, context, sim_mal_funcs, threshold_list)