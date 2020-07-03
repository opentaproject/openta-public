from .models import QueueTask
import django_rq
from redis.exceptions import ResponseError
from workqueue.exceptions import WorkQueueError
from collections import namedtuple


def enqueue_task(name, func, *args, owner=None, **kwargs):
    task = QueueTask.objects.create(name=name, owner=owner)
    try:
        job = django_rq.enqueue(func, *args, task=task, job_id=str(task.pk), **kwargs)
        job.meta['meta_info'] = 'meta_info'
        job.save_meta()
        
    except ResponseError as e:
        raise WorkQueueError(
            'Could not connect to Redis server. (Please check that the authentication '
            'configuration matches between redis.conf (system) and your OpenTA backend settings.'
            '# ' + str(e)
        )
    return task.pk


def task_result(task_pk):
    try:
        queue = django_rq.get_queue()
        return queue.fetch_job(str(task_pk)).result
    except:
        return None


TaskResult = namedtuple("TaskResult", ['status', 'progress', 'result'])


