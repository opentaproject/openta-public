# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from .models import QueueTask
from django.conf import settings
from django.contrib.auth.models import User
import django_rq
from redis.exceptions import ResponseError
from workqueue.exceptions import WorkQueueError
from collections import namedtuple
import logging
from django.core.cache import caches


logger = logging.getLogger(__name__)


def enqueue_task(name, func, *args, owner=None, subdomain=None, **kwargs):
    logger.error("ENQUEUE subdomain = %s " % subdomain )
    logger.error(f"ENQUEUE kwargs = {kwargs}")
    if subdomain == None:
        subdomain = settings.DB_NAME
        logger.error("ENQUEUE subdomain changed to = %s " % subdomain )
    username = kwargs.get("username", None)
    has_perm = kwargs.get("has_perm", None)
    logger.error(f"KWARGS IN ENQUE = {kwargs}")
    task = QueueTask.objects.create(name=name, owner=owner, subdomain=subdomain)
    logger.error(f"IN ENQUED TASK ID {task.pk}")
    # Legacy compatibility: keep cache for older workers that still read it
    cachekey = f"queutask-has-perm-{task.pk}"
    caches["default"].set(cachekey, has_perm, settings.STATISTICS_CACHE_TIMEOUT)
    try:
        job = django_rq.enqueue(func, *args, task=task, job_id=str(task.pk), **kwargs)
        # Persist has_perm in job meta so workers can reliably read it
        job.meta["meta_info"] = "meta_info"
        if has_perm is not None:
            job.meta["has_perm"] = has_perm
        job.save_meta()

    except ResponseError as e:
        raise WorkQueueError(
            "Could not connect to Redis server. (Please check that the authentication "
            "configuration matches between redis.conf (system) and your OpenTA backend settings."
            "# " + str(e)
        )
    return task.pk


def task_result(task_pk):
    try:
        logger.error("TASK RESULT PK = %s " % str( task_pk) )
        queue = django_rq.get_queue()
        logger.error("TASK RESULT QUEUE = %s " % queue )
        job = queue.fetch_job(str(task_pk))
        logger.error("TASK RESULT JOB = %s " % str(job) )
        res = job.result
        logger.error("WORKQUEUE TASK_RESULELEN RES = %s " % len( str(res) ) )
        return res
    except Exception as e:
        logger.error("TASK_RESULT_ERROR = %s " % type(e).__name__)
        return None


TaskResult = namedtuple("TaskResult", ["status", "progress", "result"])
