import time

from celery.signals import before_task_publish, task_postrun, task_prerun

from redis_cache import SignalManager, Redis

signal = SignalManager(Redis())

convert_dict = {
    "celery_task.task_token_filter.token_filter_task": "token",
    "celery_task.task_syntax_filter.syntax_filter_task": "syntax",
    "celery_task.task_bloom_filter.bloom_filter_task": "bloom",
    "celery_task.task_package_loader.package_load_task": "package_load",
}

task_start_at = {}


@before_task_publish.connect
def before_task_publish(headers=None, body=None, **kwargs):
    global signal
    info = headers if 'task' in headers else body
    task_id = info['id']
    task = info["task"]
    if task in convert_dict:
        task = convert_dict[task]
        signal.append_job(task_id)
        signal.incr_start_job(task)
    else:
        # print(f"Task {task} not found")
        pass


@task_prerun.connect
def task_prerun(task_id=None, task=None, **kwargs):
    global signal
    if task.name in convert_dict and task.name not in task_start_at:
        task_start_at[task.name] = time.time()


@task_postrun.connect()
def task_postrun(task_id=None, task=None, **kwargs):
    global signal
    if task.name in convert_dict:
        task_name = convert_dict[task.name]
        signal.pop_job(task_id)
        signal.incr_fin_job(task_name)
        signal.save_total_time(task_name, time.time() - task_start_at[task.name])

