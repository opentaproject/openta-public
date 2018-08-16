from rest_framework.decorators import api_view, parser_classes
from rest_framework import status
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
import backend.settings as settings
import time

from course.models import Course
from course.duplicate import duplicate_course
import workqueue.util as workqueue


def course_duplicate_pipeline(task, course):
    task.status = "Working"
    task.save()
    for progress in duplicate_course(course=course):
        task.progress = progress * 100
        task.save()

    task.done = True
    task.status = "Working"
    task.progress = 100
    task.save()


@permission_required('exercises.edit_exercises')
@api_view(['GET'])
def course_duplicate_async(request, course_pk):
    dbcourse = Course.objects.get(pk=course_pk)
    task_id = workqueue.enqueue_task("course_duplicate", course_duplicate_pipeline, course=dbcourse)
    return Response({'task_id': task_id})
