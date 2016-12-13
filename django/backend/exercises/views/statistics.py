from rest_framework.decorators import api_view, parser_classes
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from exercises.modelhelpers import (
    serialize_exercise_with_question_data,
    exercise_folder_structure,
    student_attempts_exercises,
    exercise_test,
    student_statistics_exercises,
    get_passed_exercises_with_data,
)
from exercises.models import Exercise, Question, Answer, ImageAnswer
from course.models import Course
from django.contrib.auth.models import User
from django.db.models import Prefetch, Max, F, Count, Sum, Value, Q
from django.views.decorators.cache import cache_page
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
@cache_page(2 * 60 * 60)
def get_results(request):
    required = Exercise.objects.filter(meta__required=True).select_related('meta')
    required_questions = Question.objects.filter(exercise__in=required)
    bonus = Exercise.objects.filter(meta__bonus=True).select_related('meta')
    students = (
        User.objects.filter(groups__name='Student')
        .exclude(username='student')
        .order_by('first_name')
    )
    deadline_time = Course.objects.deadline_time()
    results = []
    for student in students:
        print(student.username)
        passed_required_rendered = get_passed_exercises_with_data(required, student)
        passed_bonus_rendered = get_passed_exercises_with_data(bonus, student)
        results.append(
            {
                'username': student.username,
                'first_name': student.first_name,
                'last_name': student.last_name,
                #'failed': failed_exercises,
                #'passed': set(passed_questions.values_list('exercise__name', 'answers',))
                'n_passed_required': len(passed_required_rendered),
                'passed_required': passed_required_rendered,
                'n_passed_bonus': len(passed_bonus_rendered),
                'passed_bonus': passed_bonus_rendered,
                'n_passed_total': len(passed_required_rendered) + len(passed_bonus_rendered),
            }
        )
    return Response(results)


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_activity_exercise(request, exercise):
    answers = Answer.objects.filter(question__exercise__pk=exercise)
    # correct_answers = Answer.objects.filter(question__exercise__pk=exercise, correct=True)

    answer_list = answers.values_list('date', flat=True)
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
