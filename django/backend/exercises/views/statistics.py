from rest_framework.decorators import api_view
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from django.http import HttpResponse
from exercises.modelhelpers import student_attempts_exercises
from exercises.models import Exercise, Answer
from exercises.aggregation import student_statistics_exercises, students_results
from exercises.aggregation import create_xlsx_from_results_list, calculate_students_results_subset
from exercises.aggregation import excel_custom_results_pipeline, students_results_async_pipeline
from workqueue.models import QueueTask
import workqueue.util as workqueue
from datetime import datetime
import numpy


@permission_required('exercises.administer_exercise')
@api_view(['GET'])
def get_student_attempts_per_exercise(request):
    return Response(student_attempts_exercises())


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_statistics_per_exercise(request):
    return Response(student_statistics_exercises())


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_results(request):
    results = students_results()
    return Response(results)


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_results_async(request):
    task_id = workqueue.enqueue_task("student_results", students_results_async_pipeline)
    return Response({'task_id': task_id})


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_results_excel(request):
    results = students_results()
    xlsx_data = create_xlsx_from_results_list(results)
    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response = HttpResponse(xlsx_data, content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename=results.xlsx'
    return response


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_custom_result_excel(request):
    exercises = request.query_params.get('exercises').split(',')
    dbexercises = Exercise.objects.filter(pk__in=exercises)
    results = calculate_students_results_subset(dbexercises)
    xlsx_data = create_xlsx_from_results_list(results)
    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response = HttpResponse(xlsx_data, content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename=results.xlsx'
    return response


@permission_required('exercises.view_statistics')
@api_view(['GET', 'POST'])
def enqueue_custom_result_excel(request):
    exercises = None
    if request.method == 'GET':
        exercises = request.query_params.get('exercises').split(',')
    if request.method == 'POST':
        exercises = request.data.get('exercises')
    if exercises is None:
        return Response({})

    dbexercises = Exercise.objects.filter(pk__in=exercises)
    task_id = workqueue.enqueue_task("Custom results", excel_custom_results_pipeline, dbexercises)
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
