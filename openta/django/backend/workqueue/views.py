# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
import os
import urllib

from exercises.views.file_handling import serve_file
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.conf import settings

from .models import QueueTask
from .util import task_result

logger = logging.getLogger(__name__)


def content_type_dispatch(name):
    content_types = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "zip": "application/zip",
        "csv": "text/csv",
    }
    for ending, content_type in content_types.items():
        if name.endswith(ending):
            return content_type
    return None


@api_view(["GET"])
def get_task_result_file(request, task):
    dbtask = QueueTask.objects.get(pk=task)
    # logger.error("GET TASK RESULT FILE %s " % dbtask.pk)
    if dbtask.owner is not None and request.user is not dbtask.owner and not request.user.is_staff:
        return Response({"error": "You do not own this task"})
    if not dbtask.done:
        return Response({"error": "Not done"})
    if dbtask.result_file is None:
        return Response({"error": "There is no result file for this task"})

    # taskfile = os.path.join('/.' , 'ubdomain-data' ,  dbtask.result_file.name )
    # if settings.MULTICOURSE :
    #    taskfile = '/ubdomain-data/' + dbtask.result_file.name
    # else :
    #    taskfile =dbtask.result_file.name
    taskfile = dbtask.result_file.name
    # logger.error("GET TASK RESULT FILE AND SERVE %s " % dbtask.result_file.name )
    # logger.error("taskfile = %s " % taskfile )
    devpath = urllib.parse.unquote(settings.VOLUME + "/" + taskfile)
    accel_xpath = str(taskfile)
    accel_xpath = urllib.parse.quote(accel_xpath.encode("utf-8"))
    logger.error(
        f"GET_TASK_RESULT_FILE  {task}, file={taskfile} name={dbtask.name} user={request.user} subdomain={dbtask.subdomain}"
    )
    path = os.path.join(settings.VOLUME, dbtask.subdomain, "admin_activity", request.user.username)
    os.makedirs(path, exist_ok=True)
    logger.error(f"path = {path}")
    print(f"DEV_PATH = {devpath}")
    with open(os.path.join(path, str(dbtask.name)), "w") as fp:
        pass
    return serve_file(
        taskfile,
        os.path.basename(dbtask.result_file.name),
        content_type=content_type_dispatch(taskfile),
        dev_path=devpath,
        source="get_task_result_file",
        devpath=devpath,
        accel_xpath=accel_xpath,
    )


@api_view(["GET"])
def get_task_result(request, task):
    # logger.error("GET TASK RESULT %s " % str( task) )
    try:
        dbtask = QueueTask.objects.get(pk=task)
    except Exception as e:
        logger.error(f"GET TASK RESULT FAILED {type(e).__name__}")
        return Response({"error": "Task {task} does not exist"})
    if dbtask.owner is not None and request.user is not dbtask.owner and not request.user.is_staff:
        return Response({"error": "You do not own this task"})
    # logger.error("D")
    if not dbtask.done:
        return Response({"error": "Not done"})
    # logger.error("DBTASK = %s " % str(dbtask) )
    if dbtask.result_file is None:
        return Response({"error": "There is no result file for this task"})
    # logger.error("GET TASK RESULT: RESULT IS %s " % len( str( task_result(task) ) ))
    result = task_result(task)
    if result is None:
        return Response({})
    return Response(result)


@api_view(["GET"])
def task_progress(request, task):
    try:
        dbtask = QueueTask.objects.using("default").get(pk=task)
        if dbtask.owner is not None and request.user is not dbtask.owner and not request.user.is_staff:
            return Response({"error": "You do not own this task"})
        return Response({"status": dbtask.status, "progress": dbtask.progress, "done": dbtask.done})
    except:
        return Response({"status": "Cancelled", "progress": "100", "done": True})
