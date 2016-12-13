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
from datetime import datetime
import numpy
from django.db import connection
from django.core.cache import cache


def students_results():
    result = cache.get('exercises.aggregation.results')
    if result is not None:
        return result
    result = calculate_students_results()
    cache.set('exercises.aggregation.results', 1 * 60 * 60)
    return result


def calculate_students_results():  # {{{
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
        # n1 = len(connection.queries)
        passed_required_rendered = get_passed_exercises_with_data(required, student)
        passed_bonus_rendered = get_passed_exercises_with_data(bonus, student)
        # n2 = len(connection.queries)
        # print('N_queries: ' + str(n2-n1))
        # for query in connection.queries[-(n2-n1):]:
        #    print(query['time'])
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
    return results  # }}}
