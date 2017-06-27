from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
import os
import backend.settings as settings
from .models import QueueTask
from exercises.views.file_handling import serve_file
import json
import django_rq

from .util import task_result


@api_view(['GET'])
def get_task_result_file(request, task):
    dbtask = QueueTask.objects.get(pk=task)
    if dbtask.owner is not None and request.user is not dbtask.owner and not request.user.is_staff:
        return Response({'error': 'You do not own this task'})
    if not dbtask.done:
        return Response({'error': 'Not done'})
    if dbtask.result_file is None:
        return Response({'error': 'There is no result file for this task'})
    return serve_file(
        '/' + settings.SUBPATH + dbtask.result_file.name,
        os.path.basename(dbtask.result_file.name),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        dev_path=dbtask.result_file.path,
    )


@api_view(['GET'])
def get_task_result(request, task):
    dbtask = QueueTask.objects.get(pk=task)
    if dbtask.owner is not None and request.user is not dbtask.owner and not request.user.is_staff:
        return Response({'error': 'You do not own this task'})
    if not dbtask.done:
        return Response({'error': 'Not done'})
    if dbtask.result_file is None:
        return Response({'error': 'There is no result file for this task'})
    result = task_result(task)
    if result is None:
        return Response({})
    return Response(result)


@api_view(['GET'])
def task_progress(request, task):
    dbtask = QueueTask.objects.get(pk=task)
    if dbtask.owner is not None and request.user is not dbtask.owner and not request.user.is_staff:
        return Response({'error': 'You do not own this task'})
    return Response({'status': dbtask.status, 'progress': dbtask.progress, 'done': dbtask.done})
