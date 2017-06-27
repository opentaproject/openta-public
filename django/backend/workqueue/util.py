from .models import QueueTask
import django_rq


def enqueue_task(name, func, *args, owner=None, **kwargs):
    task = QueueTask.objects.create(name=name, owner=owner)
    result = django_rq.enqueue(func, *args, task=task, job_id=str(task.pk), **kwargs)
    return task.pk


def task_result(task_pk):
    queue = django_rq.get_queue()
    return queue.fetch_job(str(task_pk)).result
