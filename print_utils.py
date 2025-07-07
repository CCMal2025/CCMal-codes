from loguru import logger
from redis_cache import Message


def print_mal_message(malware_cache, mal_message: Message, writer, polling=True):
    context = mal_message.context
    mal_meta = malware_cache.load_malware_meta(mal_message.lang, context["mal_file_id"])
    if polling:
        logger.success(f"Find Malicious: Pacakge: {context['package_path']}, Path:{context['path']}")
        logger.success(f"Similar to Known Malicious: {mal_meta}")
    writer.write({"target": context['package_path'], "file": context['path'], "path": mal_meta})


def print_rates(title, cnt):
    logger.info(
        "{} Info: bloom: {} => token: {}({:.2f}%) => syntax {}({:.2f}%, {:.2f}%) => {}({:.2f}%, {:.2f}%)".format(
            title,
            cnt[0],
            cnt[1], cnt[1] / max(1, cnt[0]) * 100,
            cnt[2], cnt[2] / max(1, cnt[1]) * 100, cnt[2] / max(1, cnt[0]) * 100,
            cnt[3], cnt[3] / max(1, cnt[2]) * 100, cnt[3] / max(1, cnt[0]) * 100
        ))


def print_filter_rate(signal):
    print("Package\ttotal\tbloom\ttoken\tsyntax\tmal")
    # print("py\t\t123456\t123456\t123456\t123456")
    for lang in ["py", "js", "sh"]:
        print(lang, end="\t\t")
        for step in ["total", "bloom", "token", "syntax", "mal"]:
            print("%6d" % signal.package_status_get(f"{step}_{lang}"), end="\t")
        print("")
    print("total", end="\t")
    for step in ["total", "bloom", "token", "syntax", "mal"]:
        print("%6d" % signal.package_status_get(step), end="\t")

    print("\n")

    print("File\ttotal\tbloom\ttoken\tsyntax\tmal")
    for lang in ["py", "js", "sh"]:
        print(lang, end="\t\t")
        for step in ["total", "bloom", "token", "syntax", "mal"]:
            print("%6d" % signal.file_status_get(f"{step}_{lang}"), end="\t")
        print("")
    print("total", end="\t")
    for step in ["total", "bloom", "token", "syntax", "mal"]:
        print("%6d" % signal.file_status_get(step), end="\t")

    print("\n")


def print_progress(signal, mal_cnt):
    steps = ["bloom", "token", "syntax"]
    log_info = ""
    for step in steps:
        fin_cnt, start_cnt = signal.get_steps_info(step)
        try:
            average_time = signal.load_time(step)
        except:
            average_time = 0
        log_info += f"{step}:{fin_cnt}/{start_cnt}[{average_time:.2f} s], "
    log_info += f"mal_cnt: {mal_cnt}"
    print(log_info)
    print_filter_rate(signal)
