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
import time

from course.models import Course
from course.export_import import import_course_exercises, export_course_exercises
import workqueue.util as workqueue
import tempfile


def export_course_exercises_pipeline(task, course):
    task.status = "Working"
    task.save()
    dirpath = str(tempfile.mkdtemp())
    output_filename = None
    for filename, progress in export_course_exercises(course=course, output_path=dirpath):
        task.progress = progress * 100
        task.save()
        output_filename = filename

    task.result_file = File(open(output_filename, 'rb'))
    task.done = True
    task.status = "Working"
    task.progress = 100
    task.save()


@permission_required('exercises.edit_exercises')
@api_view(['GET'])
def export_course_exercises_async(request, course_pk):
    dbcourse = Course.objects.get(pk=course_pk)
    task_id = workqueue.enqueue_task(
        "course_exercises_export", export_course_exercises_pipeline, course=dbcourse
    )
    return Response({'task_id': task_id})
