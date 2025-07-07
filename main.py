import json
import os
import time
from typing import List

from jsonlines import jsonlines
from loguru import logger

from celery_task.celery import app
from celery_task.task_package_loader import package_load_task
from config import config
from dataset import MalwareBenchV2
from print_utils import print_mal_message, print_progress
from redis_cache import Redis, MalwareCache, SignalManager

remove_mal_log = config["remove_mal_log"]


def calculate_final_result_and_dump_fns(all_package_list, run_time=None):
    targets = set(all_package_list)
    tps = set()
    malicious_dict = {}
    with jsonlines.open(config["mal_file_logs"], "r") as reader:
        for obj in reader:
            tps.add(obj["target"])
            if obj["target"] not in malicious_dict:
                malicious_dict[obj["target"]] = {}
            if obj["file"] not in malicious_dict[obj["target"]]:
                malicious_dict[obj["target"]][obj["file"]] = []
            malicious_dict[obj["target"]][obj["file"]].append(obj["path"])

    positive_cnt = len(tps)
    negative_cnt = len(targets) - positive_cnt

    if config["experiment"]["dump_fn"]:
        with open("fn.json", "w") as f:
            json.dump(list(targets - tps), f)
    print(f"Positive: {positive_cnt}, Negative: {negative_cnt}")

    if config["experiment"]["dump_pn_result"]:
        signal = SignalManager(Redis())
        sh_file_cnt = signal.file_status_get('bloom_sh')
        mal_sh_file_cnt = signal.file_status_get('mal_sh')
        bloom_cnt = signal.file_status_get('bloom')
        token_cnt = signal.file_status_get('token')
        syntax_cnt = signal.file_status_get('syntax')
        mal_cnt = signal.file_status_get('mal')
        with open("pn_result.txt", "a") as f:
            f.write(f"Positive: {positive_cnt}, Negative: {negative_cnt}, Total: {positive_cnt + negative_cnt}, RunTime: {run_time}, sh_file:{sh_file_cnt}, total_file: {bloom_cnt}, bloom passed: {token_cnt}/{bloom_cnt - sh_file_cnt} = {token_cnt/(bloom_cnt - sh_file_cnt + 1): .3f}, token passed: {syntax_cnt + mal_sh_file_cnt}/{token_cnt} = {(syntax_cnt + mal_sh_file_cnt)/(token_cnt + 1): .3f}, syntax passed: {mal_cnt - mal_sh_file_cnt}/{syntax_cnt} = {(mal_cnt- mal_sh_file_cnt)/(syntax_cnt + 1):.3f}\n")

    return malicious_dict

def all_tasks_finished(signal):
    if signal.is_detect_finished() and signal.is_message_queue_empty():
        inspect = app.control.inspect()
        active = inspect.active() or {}
        reserved = inspect.reserved() or {}

        return not any(active.values()) and not any(reserved.values())
    else:
        return False

# setting threshold here can overwrite threshold in config.yaml
def detect(target_package_list: List, token_threshold=None, syntax_threshold=None, bloom_threshold=None):
    mal_cnt = 0
    redis = Redis()
    signal = SignalManager(redis)

    start = time.time()
    malware_cache = MalwareCache(redis)

    signal.clear_signal()
    if token_threshold is None:
        token_threshold = config["threshold"]["token"]
    if syntax_threshold is None:
        syntax_threshold = config["threshold"]["syntax"]
    if bloom_threshold is None:
        bloom_threshold = config["threshold"]["pfbf"]

    logger.info(f"Using Thresholds: PFBF: {bloom_threshold}, Token: {token_threshold}, Syntax: {syntax_threshold}")
    logger.info("Initialization Finished")

    # Detection
    # Step1: load target into redis

    i = 0
    for package_path in target_package_list:
        i += 1
        package_load_task.s(package_path, {
            "bloom": bloom_threshold,
            "token": token_threshold,
            "syntax": syntax_threshold,
        }).delay()

    logger.info(f"Total Packages: {i}")

    # time.sleep(1)   # make sure at least 1 job is published
    # Waiting
    if remove_mal_log and os.path.exists(config["mal_file_logs"]):
        os.remove(config["mal_file_logs"])
    writer = jsonlines.open(config["mal_file_logs"], "a")

    time.sleep(5)

    while not all_tasks_finished(signal):
        print_progress(signal, mal_cnt)
        mal_messages = signal.listen(cnt=10000)
        if mal_messages is None:
            continue
        for mal_message in mal_messages:
            print_mal_message(malware_cache, mal_message, writer, False)
            mal_cnt += 1

    writer.close()
    logger.info("Detect Finished")
    end = time.time()
    malicious_dict = calculate_final_result_and_dump_fns(target_package_list, run_time=end-start)

    logger.info("Time elasped: %.2f sec" % (end - start))
    return malicious_dict

if __name__ == '__main__':
    target_loader = MalwareBenchV2("./resource/malwareBench",
                                   "npm",
                                   load_mal=True,
                                   load_no_mal=False)

    detect(list(target_loader))