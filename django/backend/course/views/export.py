from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import permission_required
from django.utils.translation import ugettext as _
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from rest_framework.response import Response
import backend.settings as settings
from django.core.files.base import File
from django.db import transaction
import time
import logging

LOGGER = logging.getLogger(__file__)
from course.models import Course
from course.export_import import import_course_exercises, export_course_exercises
from course.export_import import export_course
from course.export_import import import_server
import workqueue.util as workqueue
import tempfile


def export_course_exercises_pipeline(task, course):
    LOGGER.debug("EXPORT COURSE EXERCISES PIPELINE")
    task.status = "Working"
    task.save()
    dirpath = str(tempfile.mkdtemp())
    output_filename = None
    try:
        for filename, progress in export_course_exercises(course=course, output_path=dirpath):
            LOGGER.debug("FILENAME = %s PROGRESS = %s " % (filename, progress) )
            task.progress = progress * 100
            task.status = filename
            task.save()
            output_filename = filename
        if output_filename is None:
            task.result_file = None
            task.done = False
            task.status = "No exercises to export"
            task.progress = 100
            task.save()
        else:
            LOGGER.debug("OUTPUT FILENAME = %s PROGRESS = %s " % (output_filename, progress) )
            task.result_file = File(open(output_filename, 'rb'))
            task.done = True
            task.status = "Done"
            task.progress = 100
            task.save()
            LOGGER.debug("TASK SAVED OUTPUT FILENAME = %s PROGRESS = %s " % (output_filename, progress) )
            LOGGER.debug("TASK RESULT FILE %s " % task.result_file )
            LOGGER.debug("DB_NAME = %s " %  settings.DB_NAME )
    except Exception as e:
        task.status = str(e)
        task.save()


@permission_required('exercises.edit_exercises')
@api_view(['GET'])
def export_course_exercises_async(request, course_pk):
    LOGGER.debug("EXPORT COURSE EXERCISES ASYNC")
    dbcourse = Course.objects.get(pk=course_pk)
    LOGGER.debug("OPENTASITE = %s " %  dbcourse.opentasite)
    subdomain = str( dbcourse.opentasite )
    task_id = workqueue.enqueue_task(
        "course_exercises_export", export_course_exercises_pipeline, course=dbcourse, subdomain=subdomain
    )
    return Response({'task_id': task_id})


def export_course_pipeline(task, course):
    LOGGER.debug("EXPORT COURSE PIPELINE")
    task.status = "Working"
    task.save()
    dirpath = str(tempfile.mkdtemp())
    output_filename = None
    LOGGER.debug(" DIRPATH = " + str(dirpath))
    try:
        # for status, progress, filename in export_course(course=course, output_path=dirpath):
        for task_result in export_course(course=course, output_path=dirpath):
            task.progress = task_result.progress * 100
            task.status = task_result.status
            task.save()
            output_filename = task_result.result
        task.result_file = File(open(output_filename, 'rb'))
        task.done = True
        task.status = "Done"
        task.progress = 100
        task.save()
    except Exception as e:
        task.status = str(e)
        task.done = True
        task.save()


@permission_required('exercises.edit_exercises')
@api_view(['GET'])
def export_course_async(request, course_pk):
    LOGGER.debug("EXPORT COURSE ASYNC")
    dbcourse = Course.objects.get(pk=course_pk)
    task_id = workqueue.enqueue_task("course_export", export_course_pipeline, course=dbcourse, subdomain=settings.SUBDOMAIN)
    return Response({'task_id': task_id})


def import_server_pipeline(task, file_path):
    task.status = "Working"
    task.save()
    try:
        # TODO(hamlin): It would be really nice if this was done atomically so that
        # we could safely revert if there are any errors. However this prevents the
        # progress reporting since that is a database commit to the workqueue model.
        # with transaction.atomic():
        for status, progress in import_server(file_path, merge=True):
            task.progress = progress * 100
            task.status = "({percent}% of subtasks done) Importing {status}".format(
                percent=task.progress, status=status
            )
            task.save()

        task.done = True
        task.status = "Done"
        task.progress = 100
        task.save()

    except Exception as e:
        task.status = str(e)
        task.done = True
        task.save()


@api_view(['POST'])
@parser_classes((MultiPartParser,))
def import_server_view(request):
    if request.FILES['file'].size > 500e6:
        return Response("File larger than 500mb", status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        if not request.user.has_perm('exercises.edit_exercise'):
            return Response({}, status.HTTP_403_FORBIDDEN)
        _, tmp_filename = tempfile.mkstemp(suffix=".zip")
        with open(tmp_filename, 'wb') as destination:
            for chunk in request.FILES['file'].chunks():
                destination.write(chunk)
        task_id = workqueue.enqueue_task(
            "server_import", import_server_pipeline, file_path=tmp_filename,  subdomain=settings.SUBDOMAIN
        )
        return Response({'task_id': task_id})

    except Exception as e:
        return Response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
