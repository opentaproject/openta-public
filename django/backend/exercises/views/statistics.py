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
@cache_page(2 * 60 * 60)
def get_results(request):
    required = Exercise.objects.filter(meta__required=True).select_related('meta')
    required_questions = Question.objects.filter(exercise__in=required)
    bonus = Exercise.objects.filter(meta__bonus=True).select_related('meta')
    students = User.objects.filter(groups__name='Student').order_by('first_name')
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
            }
        )
    return Response(results)
