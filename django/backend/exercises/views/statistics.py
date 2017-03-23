from rest_framework.decorators import api_view, parser_classes
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from django.http import FileResponse, HttpResponse
from exercises.modelhelpers import (
    serialize_exercise_with_question_data,
    exercise_folder_structure,
    student_attempts_exercises,
    exercise_test,
)
from exercises.models import Exercise, Question, Answer, ImageAnswer
from exercises.aggregation import (
    student_statistics_exercises,
    students_results,
    create_xlsx_from_results_list,
)
from course.models import Course
from django.contrib.auth.models import User
from django.db.models import Prefetch, Max, F, Count, Sum, Value, Q
from django.views.decorators.cache import cache_page
from .results import get_user_results
from datetime import datetime
import numpy


@permission_required('exercises.administer_exercise')
@api_view(['GET'])
def get_student_attempts_per_exercise(request):
    return Response(student_attempts_exercises())


@permission_required('exercises.view_statistics')
@api_view(['GET'])
@cache_page(1 * 60 * 60)
def get_statistics_per_exercise(request):
    return Response(student_statistics_exercises())


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_results(request):
    results = students_results()
    return Response(results)


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_results_excel(request):
    results = students_results()
    xlsx_data = create_xlsx_from_results_list(results)
    response = HttpResponse(
        xlsx_data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=results.xlsx'
    return response


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_activity_exercise(request, exercise):
    answers = Answer.objects.filter(question__exercise__pk=exercise)
    # correct_answers = Answer.objects.filter(question__exercise__pk=exercise, correct=True)

    answer_list = answers.values_list('date', flat=True)
    if not answer_list:
        return Response({'answers_histogram': [], 'bins': []})
    # correct_answer_list = correct_answers.values_list('date', flat=True)
    dformat = '%Y-%m-%dT%H:%M:%S.%fZ'
    epoch = datetime(1970, 1, 1)

    to_timestamp = numpy.vectorize(lambda x: x.timestamp())
    # answer_ts_list = [time.timestamp() for time in answer_list]
    answer_ts_array = to_timestamp(answer_list)
    # correct_answer_ts_array = to_timestamp(correct_answer_list)
    nbins = int((numpy.max(answer_ts_array) - numpy.min(answer_ts_array)) / (2 * 60 * 60)) + 1
    bins = []
    histogram = []
    if nbins > 0:
        histogram, bins = numpy.histogram(answer_ts_array, bins=nbins)
    return Response(
        {
            'answers_histogram': histogram,
            'bins': bins,
            #'correct_answers': correct_answer_list,
        }
    )
