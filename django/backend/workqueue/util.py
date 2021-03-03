from .models import QueueTask
from django.conf import settings
import django_rq
from redis.exceptions import ResponseError
from workqueue.exceptions import WorkQueueError
from collections import namedtuple
import logging
LOGGER = logging.getLogger(__file__)



def enqueue_task(name, func, *args, owner=None, subdomain=None , **kwargs):
    LOGGER.info("ENQUEUE subdomain = %s " % subdomain )
    if subdomain == None:
        subdomain = settings.DB_NAME
        LOGGER.info("ENQUEUE subdomain changed to = %s " % subdomain )
    task = QueueTask.objects.create(name=name, owner=owner,subdomain=subdomain)
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
        LOGGER.info("TASK RESULT PK = %s " % str( task_pk) )
        queue = django_rq.get_queue()
        LOGGER.info("TASK RESULT QUEUE = %s " % queue )
        job = queue.fetch_job(str(task_pk))
        LOGGER.info("TASK RESULT JOB = %s " % str(job) )
        res = job.result
        LOGGER.info("WORKQUEUE TASK_RESULELEN RES = %s " % len( str(res) ) )
        return res
    except Exception as e:
        LOGGER.info("ERROR = %s " % str(e) )
        return None


TaskResult = namedtuple("TaskResult", ['status', 'progress', 'result'])


