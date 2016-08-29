from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from exercises.models import Exercise, Question, Answer
from exercises.serializers import ExerciseSerializer
from exercises import parsing
from exercises.question import question_check
from django.http import FileResponse
from exercises.paths import EXERCISES_PATH

import sys
import os

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__) + '/../../../questiontypes'))
import question_types


@api_view(['POST', 'GET'])
def exercises_reload(request):
    Exercise.objects.sync_with_disc()
    return Response("Reloaded")


@api_view(['GET'])
def exercise(request, exercise):
    exercise = Exercise.objects.get(exercise_key=exercise)
    correct = exercise.user_is_correct(request.user)
    serializer = ExerciseSerializer(exercise)
    data = serializer.data
    data['correct'] = correct
    return Response(data)


@api_view(['GET'])
def exercise_list(request):
    """
    List all exercises
    """
    # Exercise.objects.sync_with_disc()
    # Exercise.objects.folder_structure()
    response = []
    exercises = Exercise.objects.all()
    for exercise in exercises:
        correct = exercise.user_is_correct(request.user)
        serializer = ExerciseSerializer(exercise)
        data = serializer.data
        data['correct'] = correct
        response.append(data)
    return Response(response)


@api_view(['GET'])
def exercise_tree(request):
    """
    Get exercise tree
    """
    return Response(Exercise.objects.folder_structure(request.user))


@api_view(['GET'])
def other_exercises_from_folder(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    other = Exercise.objects.filter(folder=dbexercise.folder)
    serializer = ExerciseSerializer(other, many=True)
    print(serializer.data)
    return Response(serializer.data)


@api_view(['GET'])
def exercise_json(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    return Response(parsing.exercise_json(dbexercise.path))


@api_view(['GET'])
def exercise_xml(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    return Response({'xml': parsing.exercise_xml(dbexercise.path)})


@api_view(['POST'])
def exercise_save(request, exercise):
    result = {}
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    try:
        result = parsing.exercise_save(dbexercise.path, request.data['xml'])
    except IOError:
        result = {'success': False}
    return Response(result)


@api_view(['POST'])
def exercise_check(request, exercise, question):
    print(question)
    answer_data = request.data['answerData']
    # dbexercise = Exercise.objects.get(exercise_key=exercise)
    # dbquestion = Question.objects.get(exercise=dbexercise, question_id=question)
    # result = question_check(dbexercise.path, question, answer)
    # if 'correct' in result:
    #    dbanswer = Answer.objects.create(user=request.user, question=dbquestion, answer=answer, correct=result['correct'])
    result = question_check(request.user, exercise, question, answer_data)
    return Response(result)


@api_view(['GET'])
def exercise_asset(request, exercise, asset):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    return FileResponse(
        open(
            '{root}/{path}/{asset}'.format(
                root=EXERCISES_PATH, path=dbexercise.path, exercise=exercise, asset=asset
            ),
            'rb',
        )
    )
