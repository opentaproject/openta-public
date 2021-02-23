from rest_framework.decorators import api_view, parser_classes
import requests
import json
from rest_framework import status
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
import backend.settings as settings

from course.models import Course
from course.duplicate import duplicate_course
import workqueue.util as workqueue
import logging
logger = logging.getLogger(__name__)



def course_duplicate_pipeline(task, course,  data):
    logger.info("COURSE_DUPLICATE_PIPELINE" )
    task.status = "Working"
    task.save()
    
    try:
        for phase, progress in duplicate_course(course=course,  data=data):
            task.progress = progress * 100
            task.status = phase
            task.save()
    except Exception as e:
        task.status = str(e)
        task.done = True
        task.save()
        return

    task.done = True
    task.status = "Done"
    task.progress = 100
    task.save()


@permission_required('exercises.edit_exercises')
@api_view(['GET', 'POST'])
def course_duplicate_async(request, course_pk):
    data = request.data
    newname = data.get('newname', "NEWNAME")
    days = data.get('days', "0")
    checked1 = data.get('checked1', False)
    checked2 = data.get('checked2', False)
    dbcourse = Course.objects.get(pk=course_pk)
    subdomain =  str( dbcourse.opentasite )
    data['subdomain'] = subdomain
    logger.info("COURSE_DUPLICATE ASYNC subdomain = %s " % subdomain)
    task_id = workqueue.enqueue_task(
        "course_duplicate", course_duplicate_pipeline,  course=dbcourse, subdomain=subdomain,  data=data, 
    )
    return Response({'task_id': task_id})
