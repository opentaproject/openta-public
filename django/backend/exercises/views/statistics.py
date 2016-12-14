from rest_framework.decorators import api_view, parser_classes
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from django.http import FileResponse, HttpResponse
from exercises.modelhelpers import (
    serialize_exercise_with_question_data,
    exercise_folder_structure,
    student_attempts_exercises,
    exercise_test,
    student_statistics_exercises,
    get_passed_exercises_with_data,
)
from exercises.models import Exercise, Question, Answer, ImageAnswer
from exercises.aggregation import students_results
from course.models import Course
from django.contrib.auth.models import User
from django.db.models import Prefetch, Max, F, Count, Sum, Value, Q
from django.views.decorators.cache import cache_page
import xlsxwriter
from datetime import datetime
import numpy
import io


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
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()
    worksheet.write(0, 0, 'Username')
    worksheet.write(0, 1, 'First')
    worksheet.write(0, 2, 'Last')
    worksheet.write(0, 3, 'Obligatory')
    worksheet.write(0, 4, 'Bonus')
    worksheet.write(0, 5, 'Total')
    for index, student in enumerate(results):
        worksheet.write(index + 1, 0, student['username'])
        worksheet.write(index + 1, 1, student['first_name'])
        worksheet.write(index + 1, 2, student['last_name'])
        worksheet.write(index + 1, 3, student['n_passed_required'])
        worksheet.write(index + 1, 4, student['n_passed_bonus'])
        worksheet.write(index + 1, 5, student['n_passed_total'])
    workbook.close()
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
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
    nbins = int((numpy.max(answer_ts_array) - numpy.min(answer_ts_array)) / (2 * 60 * 60))
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
