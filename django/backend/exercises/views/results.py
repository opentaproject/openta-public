from rest_framework.decorators import api_view
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from rest_framework import status
from exercises.models import Exercise, Question, Answer
from exercises.serializers import AnswerSerializer
from exercises.question import question_check
from exercises.aggregation import calculate_user_results, calculate_user_exercise_results
from django.contrib.auth.models import User
from itertools import groupby
from django.http import HttpResponse
import json
import uuid
import pickle


def _get_recent_results( exercise):
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
            if question.type == 'textbased' :
                sanswers = AnswerSerializer(answers[:1], many=True)
            else :
                sanswers = AnswerSerializer(answers[:10], many=True)
            unique = [next(x, None) for k, x in groupby(sanswers.data, lambda item: item['answer'])]
            results[question.question_key].append(
                dict(pk=user, username=dbuser.username, answers=unique[:5], n_answers=n_answers)
            )

    return results


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_recent_results(request, exercise):
    results = _get_recent_results(exercise)
    return Response( results )







@api_view(['GET','POST'])
def get_user_results(request, user_pk, course_pk):
    user = User.objects.get(pk=user_pk)
    if not request.user == user and not request.user.is_staff:
        return Response({'error': 'Permission denied'})
    return Response(calculate_user_results(user_pk, course_pk=course_pk))

@api_view(['GET','POST'])
def get_user_exercise_results(request, user_pk, course_pk,exercise):
    user = User.objects.get(pk=user_pk)
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    if not request.user == user and not request.user.is_staff:
        return Response({'error': 'Permission denied'})
    return Response(calculate_user_exercise_results(user_pk, course_pk=course_pk,exercise=dbexercise))


