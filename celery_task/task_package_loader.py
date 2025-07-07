from celery import Task

from celery_task.celery import app
from extractor import PackageExtractor
from .task_bloom_filter import bloom_filter_task


class PackageLoaderTask(Task):
    ignore_result = True


bypass_bloom_filter = False

@app.task(base=PackageLoaderTask)
def package_load_task(package_path, threshold_list):
    try:
        package_loader = PackageExtractor(package_path)
    except Exception as e:
        print(f"Package Load Failed: {package_path}, {str(e)}")
        return
    packages_list = package_loader.load_packages_to_dict()

    bypass = {"js": bypass_bloom_filter, "py": bypass_bloom_filter, "sh": True}
    # publish detect job for the package
    for lang in ["js", "py", "sh"]:
        if len(packages_list[lang]) > 0:
            bloom_filter_task.delay(lang, package_loader.package_path, packages_list[lang], bypass[lang], threshold_list)