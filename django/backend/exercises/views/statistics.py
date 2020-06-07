from rest_framework.decorators import api_view
import openpyxl
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from exercises.models import Exercise, Answer
from exercises.aggregation import student_statistics_exercises, students_results
from exercises.aggregation import create_xlsx_from_results_list, calculate_students_results
from exercises.aggregation import excel_custom_results_pipeline, students_results_async_pipeline 
from course.models import Course
from workqueue.models import QueueTask
import workqueue.util as workqueue
from workqueue.exceptions import WorkQueueError
from datetime import datetime
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

import numpy
from messages import error, embed_messages


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_statistics_per_exercise(request, course_pk):
    dbcourse = Course.objects.get(pk=course_pk)
    return Response(student_statistics_exercises(course=dbcourse))


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_results_async(request, course_pk):
    dbcourse = Course.objects.get(pk=course_pk)
    try:
        task_id = workqueue.enqueue_task(
            "student_results", students_results_async_pipeline, course=dbcourse
        )
        return Response({'task_id': task_id})
    except WorkQueueError as e:
        messages = embed_messages([error(str(e))])
        return Response(messages)



@permission_required('exercises.view_statistics')
@api_view(['GET', 'POST'])
def get_results_excel(request, course_pk):
    dbcourse = Course.objects.get(pk=course_pk)
    dbexercises = Exercise.objects.filter(course_id=course_pk, meta__published=True)
    task_id = workqueue.enqueue_task(
        "Custom results", excel_custom_results_pipeline, dbexercises, course=dbcourse
    )
    return Response({'task_id': task_id})


@permission_required('exercises.view_statistics')
@api_view(['GET', 'POST'])
def enqueue_custom_result_excel(request, course_pk):
    exercises = None
    if request.method == 'GET':
        # print("GET", str( request.query_params ) )
        exercises = request.query_params.get('exercises').split(',')
    if request.method == 'POST':
        # print("POST", str( request.data ) )
        exercises = request.data.get('exercises')
    if exercises is None:
        return Response({})

    dbcourse = Course.objects.get(pk=course_pk)
    dbexercises = Exercise.objects.filter(exercise_key__in=exercises)
    # print("DBEXERCISES = ", list( dbexercises.values_list('exercise_key', flat=True) ) )
    task_id = workqueue.enqueue_task(
        "Custom results", excel_custom_results_pipeline, dbexercises, course=dbcourse
    )
    return Response({'task_id': task_id})


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def progress_custom_result_excel(request, task):
    dbtask = QueueTask.objects.get(pk=task)
    return Response({'status': dbtask.status, 'progress': dbtask.progress, 'done': dbtask.done})


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_activity_exercise(request, exercise):
    answers = Answer.objects.filter(question__exercise__pk=exercise)

    answer_list = answers.values_list('date', flat=True)
    if not answer_list:
        return Response({'answers_histogram': [], 'bins': []})

    to_timestamp = numpy.vectorize(lambda x: x.timestamp())
    answer_ts_array = to_timestamp(answer_list)
    nbins = int((numpy.max(answer_ts_array) - numpy.min(answer_ts_array)) / (2 * 60 * 60)) + 1
    bins = []
    histogram = []
    if nbins > 0:
        histogram, bins = numpy.histogram(answer_ts_array, bins=nbins)
    return Response({'answers_histogram': histogram, 'bins': bins})
