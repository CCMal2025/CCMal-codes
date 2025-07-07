from celery import Celery

broker = 'redis://127.0.0.1:24779/1'
backend = 'redis://127.0.0.1:24779/2'
app = Celery(
    broker=broker,
    backend=backend,
    include=[
        'celery_task.task_package_loader',
        'celery_task.task_bloom_filter',
        'celery_task.task_token_filter',
        'celery_task.task_syntax_filter',
        'celery_task.signals'])
