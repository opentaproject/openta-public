from rest_framework.decorators import api_view, parser_classes
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from exercises.models import Exercise, Question, Answer, ImageAnswer
from exercises.modelhelpers import get_passed_exercises_with_image_data, get_passed_exercises
from exercises.serializers import ExerciseSerializer, AnswerSerializer, ImageAnswerSerializer

from course.models import Course
from django.contrib.auth.models import User
from django.db.models import Prefetch, Max, F, Count, Sum, Value, Q
import datetime
import pytz


@api_view(['GET'])
def get_user_results(request, userpk):
    user = User.objects.get(pk=userpk)
    if not request.user == user and not request.user.is_staff:
        return Response({'error': 'Permission denied'})
    tz = pytz.timezone('Europe/Stockholm')
    deadline_time = datetime.time(23, 59, 59, tzinfo=pytz.timezone('Europe/Stockholm'))
    course = Course.objects.first()
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    exercises = Exercise.objects.filter(meta__published=True)
    exercises_with_answers = exercises.prefetch_related(
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
    )
    exercises_render = {}

    for exercise in exercises_with_answers:
        sexercise = ExerciseSerializer(exercise)
        exercises_render[exercise.exercise_key] = sexercise.data
        exercises_render[exercise.exercise_key]['questions'] = {}
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
        exercises_render[exercise.exercise_key]['tries'] = n_tries

    return Response(
        {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'pk': user.pk,
            'exercises': exercises_render,
        }
    )


@api_view(['GET'])
def get_user_results_old(request, userpk):
    user = User.objects.get(pk=userpk)
    if not request.user == user and not request.user.is_staff:
        return Response({'error': 'Permission denied'})
    deadline = request.GET.get('deadline', 'true') == 'true'
    image_deadline = request.GET.get('imagedeadline', 'true') == 'true'
    exercises = Exercise.objects.filter(meta__published=True)
    passed = get_passed_exercises_with_image_data(exercises, user, deadline, image_deadline)
    correct = get_passed_exercises(exercises, user)
    exercises_with_answers = exercises.prefetch_related(
        Prefetch(
            'question__answer',
            queryset=Answer.objects.filter(user=user).order_by('-date'),
            # to_attr='answers'
        ),
        Prefetch(
            'imageanswer',
            queryset=ImageAnswer.objects.filter(user=user).order_by('-date'),
            # to_attr='imageanswers'
        ),
    )
    exercises_render = {}
    for exercise in exercises_with_answers:
        sexercise = ExerciseSerializer(exercise)
        exercises_render[exercise.exercise_key] = sexercise.data
        exercises_render[exercise.exercise_key]['questions'] = {}
        for question in exercise.question.all():
            answers = AnswerSerializer(question.answer.all(), many=True)
            exercises_render[exercise.exercise_key]['questions'][
                question.question_key
            ] = answers.data
        imageanswers = ImageAnswerSerializer(exercise.imageanswer, many=True)
        exercises_render[exercise.exercise_key]['imageanswers'] = imageanswers.data
        # else:
        #     exercises_render[exercise.exercise_key]['questions'][question.question_key] = []
    return Response(
        {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'exercises': exercises_render,
            'passed_exercises': passed,
            'correct_exercises': correct,
        }
    )
