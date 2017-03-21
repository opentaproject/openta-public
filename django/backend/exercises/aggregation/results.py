from exercises.modelhelpers import (
    serialize_exercise_with_question_data,
    exercise_folder_structure,
    student_attempts_exercises,
    exercise_test,
    get_passed_exercises_with_image_data,
    get_passed_exercises,
)
from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from exercises.serializers import ExerciseSerializer, AnswerSerializer, ImageAnswerSerializer
from course.models import Course
from django.contrib.auth.models import User
from django.db.models import Prefetch, Max, F, Count, Sum, Value, Q

# from datetime import datetime
import datetime
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
import pytz


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
    bonus = Exercise.objects.filter(meta__bonus=True).select_related('meta')
    students = (
        User.objects.filter(groups__name='Student')
        .exclude(username='student')
        .order_by('first_name')
    )
    results = []
    for student in students:
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


def calculate_user_results(userpk):
    user = User.objects.get(pk=userpk)
    tz = pytz.timezone('Europe/Stockholm')
    deadline_time = datetime.time(23, 59, 59, tzinfo=pytz.timezone('Europe/Stockholm'))
    course = Course.objects.first()
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    exercises = Exercise.objects.filter(meta__published=True)
    exercises_with_answers = exercises.prefetch_related(  # {{{
        Prefetch(
            'question',
            queryset=Question.objects.all().prefetch_related(
                Prefetch(
                    'answer',
                    queryset=Answer.objects.filter(user=user, correct=True).order_by('-date'),
                    to_attr='correct',
                ),
                Prefetch(
                    'answer',
                    queryset=Answer.objects.filter(user=user).order_by('-date'),
                    to_attr='allanswers',
                ),
            ),
            to_attr='questions',
        ),
        Prefetch(
            'imageanswer',
            queryset=ImageAnswer.objects.filter(user=user).order_by('-date'),
            to_attr='imageanswers',
        ),
        Prefetch(
            'audits', queryset=AuditExercise.objects.filter(student=user), to_attr='student_audits'
        ),
    )  # }}}
    exercises_render = {}

    for exercise in exercises_with_answers:
        sexercise = ExerciseSerializer(exercise)  # {{{
        exercises_render[exercise.exercise_key] = sexercise.data
        exercises_render[exercise.exercise_key]['questions'] = {}
        # if exercise.student_audits:
        exercises_render[exercise.exercise_key]['force_passed'] = (
            exercise.student_audits[0].force_passed if exercise.student_audits else False
        )
        if exercise.meta.deadline_date:
            deadline_tz_date = tz.localize(
                datetime.datetime.combine(exercise.meta.deadline_date, deadline_time)
            )
            exercises_render[exercise.exercise_key]['deadline'] = deadline_tz_date
            n_correct_deadline = 0

            def before_deadline(item):
                return item.date < deadline_tz_date

            for question in exercise.questions:
                correct_before_deadline = next(
                    (x for x in question.correct if before_deadline(x)), None
                )
                if correct_before_deadline is not None:
                    n_correct_deadline += 1
            exercises_render[exercise.exercise_key]['correct_deadline'] = n_correct_deadline == len(
                exercise.questions
            )

            n_image_before_deadline = 0
            for imageanswer in exercise.imageanswers:
                if before_deadline(imageanswer):
                    n_image_before_deadline += 1
            exercises_render[exercise.exercise_key]['image_deadline'] = (
                n_image_before_deadline == len(exercise.imageanswers)
                and n_image_before_deadline > 0
            )
            exercises_render[exercise.exercise_key]['image'] = len(exercise.imageanswers) > 0
            imageanswers = ImageAnswerSerializer(exercise.imageanswers, many=True)
            exercises_render[exercise.exercise_key]['imageanswers'] = imageanswers.data

        n_correct = 0
        n_tries = 0
        for question in exercise.questions:
            if question.correct:
                n_correct += 1
            answers = AnswerSerializer(question.allanswers, many=True)
            exercises_render[exercise.exercise_key]['questions'][question.question_key] = {}
            exercises_render[exercise.exercise_key]['questions'][question.question_key][
                'answers'
            ] = answers.data
            n_tries += len(question.allanswers)
        exercises_render[exercise.exercise_key]['correct'] = n_correct == len(exercise.questions)
        exercises_render[exercise.exercise_key]['tries'] = n_tries  # }}}

    n_passed_required = 0
    n_passed_required_d = 0
    n_passed_required_d_id = 0
    n_passed_bonus = 0
    n_passed_bonus_d = 0
    n_passed_bonus_d_id = 0
    n_optional = 0
    n_total = 0

    for key, exercise in exercises_render.items():
        if exercise['correct'] or exercise['force_passed']:
            n_total += 1
        if exercise['meta']['required']:
            if exercise['correct'] or exercise['force_passed']:
                n_passed_required += 1
            if exercise['meta']['deadline_date']:
                if exercise['correct_deadline'] or exercise['force_passed']:
                    n_passed_required_d += 1
                    if (
                        exercise['image_deadline'] or exercise['force_passed']
                    ):  # Here d_id refers to both answer and image answer before deadline
                        n_passed_required_d_id += 1
        elif exercise['meta']['bonus']:
            if exercise['correct'] or exercise['force_passed']:
                n_passed_bonus += 1
            if exercise['meta']['deadline_date']:
                if exercise['correct_deadline'] or exercise['force_passed']:
                    n_passed_bonus_d += 1
                    if (
                        exercise['image_deadline'] or exercise['force_passed']
                    ):  # Here d_id refers to both answer and image answer before deadline
                        n_passed_bonus_d_id += 1
        else:
            if exercise['correct'] or exercise['force_passed']:
                n_optional += 1

    return {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'pk': user.pk,
        'exercises': exercises_render,
        'summary': {
            'required': {
                'n_correct': n_passed_required,
                'n_deadline': n_passed_required_d,
                'n_image_deadline': n_passed_required_d_id,
            },
            'bonus': {
                'n_correct': n_passed_bonus,
                'n_deadline': n_passed_bonus_d,
                'n_image_deadline': n_passed_bonus_d_id,
            },
            'optional': n_optional,
            'total': n_total,
        },
    }
