import os
import pickle

import fastuuid
from tqdm import tqdm

import config
from components import NSFBF, TokenFilter
from dataset import PreciseDatasetLoaderV2
from extractor import keywords_len, extract_code, remove_setup_args, purify_bash_code
from redis_cache import Redis, MalwareCache

def initialization():
    # Create Connection to Redis
    redis = Redis()
    malware_cache = MalwareCache(redis)
    malware_cache.clear_cache()
    version = str(fastuuid.uuid4())

    for lang in ["js", "py", "sh"]:
        # Load All Mal Files
        loader = PreciseDatasetLoaderV2(config.config["resource"]["precise_dataset"], lang)

        # Components Init
        if lang != "sh":
            nsfbf = NSFBF(keywords_len(lang), tile_cnt=config.config["pfbf"]["tile_cnt"], seed=config.config["pfbf"]["seed"],version=version)

        nsfbf_vectors = []
        token_list = []
        for code, meta in tqdm(loader):
            if lang == "py" and meta["path"].find("setup.py") != -1:
                code = remove_setup_args(code)

            if lang == "sh":
                code = purify_bash_code(code).strip()

            extractor = extract_code(code, lang)
            func_id = malware_cache.insert_malware(lang, meta, extractor.syntax_seq())
            if lang != "sh":  # bypass sh nsfbf since there is very few
                nsfbf_vectors.append(extractor.keyword_vector())
            token = extractor.token()
            token_list.append((token, func_id, sum(token.values())))

        if lang != "sh":
            nsfbf.construct(nsfbf_vectors, config.config["threshold"]["pfbf"])
            os.makedirs("celery_task/cache/nsfbf", exist_ok=True)
            with open(f"celery_task/cache/nsfbf/{lang}.pickle", "wb") as f:
                pickle.dump(nsfbf, f)


        token_list.sort(key=lambda token_pair: token_pair[2])
        tf = TokenFilter(threshold=config.config["threshold"]["token"], version=version)

        for token in token_list:
            tf.insert(token[0], token[1], token[2])

        os.makedirs("celery_task/cache/token", exist_ok=True)
        with open(f"celery_task/cache/token/{lang}.pickle", "wb") as f:
            pickle.dump(tf, f)

    with open(f"celery_task/cache/version.txt", "w") as f:
        f.write(version)

    redis.dump_rdb()

if __name__ == "__main__":
   initialization()
