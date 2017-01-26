from exercises.modelhelpers import (
    serialize_exercise_with_question_data,
    exercise_folder_structure,
    student_attempts_exercises,
    exercise_test,
    get_passed_exercises_with_image_data,
    get_passed_exercises,
)
from exercises.models import Exercise, Question, Answer, ImageAnswer
from course.models import Course
from django.contrib.auth.models import User
from django.db.models import Prefetch, Max, F, Count, Sum, Value, Q
from datetime import datetime
import numpy
from django.db import connection
from django.core.cache import cache
from exercises.modelhelpers import (
    exercise_list_data,
    e_name,
    e_path,
    e_student_tried,
    e_student_percent_complete,
    e_student_attempts_mean,
    e_student_attempts_median,
    e_student_activity,
    post_process_list,
    p_student_activity,
)


def students_results(cache_seconds=1 * 60 * 60, force=False):
    result = cache.get('exercises.aggregation.results')
    if result is not None and not force:
        return result
    result = calculate_students_results()
    cache.set('exercises.aggregation.results', result, cache_seconds)
    return result


def student_statistics_exercises(cache_seconds=1 * 60 * 60, force=False):
    result = cache.get('exercises.aggregation.statistics')
    if result is not None and not force:
        return result
    result = calculate_student_statistics_exercises()
    cache.set('exercises.aggregation.statistics', result, cache_seconds)
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
        passed_required = get_passed_exercises_with_image_data(
            required, student, deadline=False, image_deadline=False
        )
        passed_required_d = get_passed_exercises_with_image_data(
            required, student, deadline=True, image_deadline=False
        )
        passed_required_d_id = get_passed_exercises_with_image_data(
            required, student, deadline=True, image_deadline=True
        )
        passed_bonus = get_passed_exercises_with_image_data(
            bonus, student, deadline=False, image_deadline=False
        )
        passed_bonus_d = get_passed_exercises_with_image_data(
            bonus, student, deadline=True, image_deadline=False
        )
        passed_bonus_d_id = get_passed_exercises_with_image_data(
            bonus, student, deadline=True, image_deadline=True
        )
        total = get_passed_exercises(Exercise.objects.filter(meta__published=True), student)
        optional = get_passed_exercises(
            Exercise.objects.filter(meta__published=True, meta__required=False, meta__bonus=False),
            student,
        )
        # n2 = len(connection.queries)
        # print('N_queries: ' + str(n2-n1))
        # for query in connection.queries[-(n2-n1):]:
        #    print(query['time'])
        results.append(
            {
                'username': student.username,
                'pk': student.pk,
                'first_name': student.first_name,
                'last_name': student.last_name,
                #'failed': failed_exercises,
                #'passed': set(passed_questions.values_list('exercise__name', 'answers',))
                'required': {
                    'n_correct': len(passed_required),
                    'n_deadline': len(passed_required_d),
                    'n_image_deadline': len(passed_required_d_id),
                },
                'bonus': {
                    'n_correct': len(passed_bonus),
                    'n_deadline': len(passed_bonus_d),
                    'n_image_deadline': len(passed_bonus_d_id),
                },
                'optional': len(optional),
                'total': len(total),
            }
        )
    return results  # }}}


def calculate_student_statistics_exercises():  # {{{
    data = exercise_list_data(
        [
            e_name,
            e_path,
            e_student_tried,
            e_student_percent_complete,
            e_student_attempts_mean,
            e_student_attempts_median,
            e_student_activity,
        ]
    )
    aggregates = post_process_list(data, [p_student_activity])
    return {'exercises': data, 'aggregates': aggregates}
    # }}}
