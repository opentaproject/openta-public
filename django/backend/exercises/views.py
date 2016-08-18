from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from exercises.models import Exercise, Question
from exercises.serializers import ExerciseSerializer
from exercises.parsing import exerciseJSON, exerciseXML, exerciseCheck, exerciseSave
from django.http import FileResponse
from exercises.paths import EXERCISES_PATH


@api_view(['GET'])
def exercise_list(request):
    """
    List all exercises
    """
    # Exercise.objects.sync_with_disc()
    # Exercise.objects.folder_structure()
    print('hoop')
    exercises = Exercise.objects.all()
    serializer = ExerciseSerializer(exercises, many=True)
    print(serializer.data)
    return Response(serializer.data)


@api_view(['GET'])
def exercise_json(request, exercise):
    dbexercise = Exercise.objects.get(exercise_name=exercise)
    return Response(exerciseJSON(dbexercise.path + '/' + exercise))


@api_view(['GET'])
def exercise_xml(request, exercise):
    dbexercise = Exercise.objects.get(exercise_name=exercise)
    return Response({'xml': exerciseXML(dbexercise.path + '/' + exercise)})


@api_view(['POST'])
def exercise_save(request, exercise):
    return exerciseSave(exercise, request.data)


@api_view(['GET'])
def exercise_check(request, exercise, question):
    print(request.data)
    return {}


@api_view(['GET'])
def exercise_asset(request, exercise, asset):
    dbexercise = Exercise.objects.get(exercise_name=exercise)
    return FileResponse(
        open(
            '{root}/{path}/{exercise}/{asset}'.format(
                root=EXERCISES_PATH, path=dbexercise.path, exercise=exercise, asset=asset
            ),
            'rb',
        )
    )
