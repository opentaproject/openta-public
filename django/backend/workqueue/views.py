from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
import os
from exercises.paths import _subpath
from .models import QueueTask
from exercises.views.file_handling import serve_file
import json
import django_rq
import logging
import re
LOGGER = logging.getLogger(__file__)


from .util import task_result


def content_type_dispatch(name):
    content_types = {
        'xlsx': "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        'zip': "application/zip",
        'csv': "text/csv",
    }
    for ending, content_type in content_types.items():
        if name.endswith(ending):
            return content_type
    return None


@api_view(['GET'])
def get_task_result_file(request, task):
    dbtask = QueueTask.objects.get(pk=task)
    LOGGER.info("GET TASK RESULT FILE %s " % task.pk)
    if dbtask.owner is not None and request.user is not dbtask.owner and not request.user.is_staff:
        return Response({'error': 'You do not own this task'})
    if not dbtask.done:
        return Response({'error': 'Not done'})
    if dbtask.result_file is None:
        return Response({'error': 'There is no result file for this task'})

    subpath = _subpath(uri=request.get_full_path() , session=request.session)
    LOGGER.info(" SUBPATH IN GET_TASK RESULT FILE = %s " % subpath)
    LOGGER.info("GET TASK RESULT FILE AND SERVE %s " % dbtask.result_file.name )
    taskfile = '/subdomain-data/' + dbtask.result_file.name;
    LOGGER.info("taskfile = %s " % taskfile )
    return serve_file(
        taskfile,
        os.path.basename(dbtask.result_file.name),
        content_type=content_type_dispatch(taskfile),
        dev_path=taskfile,
    )


@api_view(['GET'])
def get_task_result(request, task):
    LOGGER.info("GET TASK RESULT %s " % str( task) )
    LOGGER.info("A")
    dbtask = QueueTask.objects.get(pk=task)
    LOGGER.info("B")
    if (
        dbtask.owner is not None
        and request.user is not dbtask.owner
        and not request.user.is_staff
    ):
        return Response({'error': 'You do not own this task'})
    LOGGER.info("D")
    if not dbtask.done:
        return Response({'error': 'Not done'})
    LOGGER.info("E")
    LOGGER.info("DBTASK = %s " % str(dbtask) )
    if dbtask.result_file is None:
        return Response({'error': 'There is no result file for this task'})
    LOGGER.info("GET TASK RESULT: RESULT IS %s " % len( str( task_result(task) ) ))
    result = task_result(task)
    if result is None:
        return Response({})
    return Response(result)


@api_view(['GET'])
def task_progress(request, task):
    try:
        dbtask = QueueTask.objects.get(pk=task)
        if (
            dbtask.owner is not None
            and request.user is not dbtask.owner
            and not request.user.is_staff
        ):
            return Response({'error': 'You do not own this task'})
        return Response({'status': dbtask.status, 'progress': dbtask.progress, 'done': dbtask.done})
    except:
        return Response({'status': 'Cancelled', 'progress': '100', 'done': True})
