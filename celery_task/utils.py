from redis_cache import SignalManager


def set_package_status(redis_con, step, lang, package_uuid):
    signal = SignalManager(redis_con)
    signal.package_status_set(package_uuid, f'{step}_{lang}')
    signal.package_status_set(package_uuid, step)


def set_file_status(redis_con, step, lang, package_path, target_func_id):
    signal = SignalManager(redis_con)
    signal.file_status_set(package_path + "@#@" + target_func_id, f'{step}_{lang}')
    signal.file_status_set(package_path + "@#@" + target_func_id, step)