from rest_framework.decorators import api_view, parser_classes
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from rest_framework import status
from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from exercises.modelhelpers import get_passed_exercises_with_image_data, get_passed_exercises
from exercises.serializers import ExerciseSerializer, AnswerSerializer, ImageAnswerSerializer
from exercises.aggregation import calculate_user_results

from course.models import Course
from django.contrib.auth.models import User
from django.db.models import Prefetch, Max, F, Count, Sum, Value, Q
from itertools import groupby
import datetime
import pytz


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_recent_results(request, exercise):
    """# {{{
    Retrieve list of recent answers from users.

    Args:
        request:
        exercise: Exercise key

    Returns:
        Error: Empty object
        Success: JSON of structure
            {
                question_key: {
                    user_pk: {
                        answers: [ answers ]
                        n_answers: Total number of answers
                        pk: User id
                        username: Username
                    }
                    ...
                }
                ...
            }
    """
    try:
        dbexercise = Exercise.objects.get(pk=exercise)
    except Exercise.DoesNotExist:
        return Response({}, status=status.HTTP_404_NOT_FOUND)
    questions = Question.objects.filter(exercise=dbexercise)
    results = {}

    def take_latest_unique_users(users, n):
        ret = []
        seen = set()
        for user in users:
            if user not in seen:
                seen.add(user)
                ret.append(user)
            if len(ret) >= n:
                return ret
        return ret

    for question in questions:
        users = (
            Answer.objects.filter(question=question)
            .order_by('-date')
            .values_list('user__pk', flat=True)[:100]
        )
        latest_users = take_latest_unique_users(users, 15)
        results[question.question_key] = []
        for user in latest_users:
            dbuser = User.objects.get(pk=user)
            answers = Answer.objects.filter(user__pk=user, question=question).order_by('-date')
            n_answers = answers.count()
            sanswers = AnswerSerializer(answers[:10], many=True)
            unique = [next(x, None) for k, x in groupby(sanswers.data, lambda item: item['answer'])]
            results[question.question_key].append(
                dict(pk=user, username=dbuser.username, answers=unique[:5], n_answers=n_answers)
            )

    return Response(results)  # }}}


@api_view(['GET'])
def get_user_results(request, userpk):
    user = User.objects.get(pk=userpk)
    if not request.user == user and not request.user.is_staff:
        return Response({'error': 'Permission denied'})
    return Response(calculate_user_results(userpk))


@api_view(['GET'])
def get_user_results_old(request, userpk):
    user = User.objects.get(pk=userpk)  # {{{
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
    )  # }}}
