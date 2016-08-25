from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from exercises.models import Exercise, Question, Answer
from exercises.serializers import ExerciseSerializer
from exercises.parsing import exerciseJSON, exerciseXML, exerciseCheck, exerciseSave
from django.http import FileResponse
from exercises.paths import EXERCISES_PATH


@api_view(['POST', 'GET'])
def exercises_reload(request):
    Exercise.objects.sync_with_disc()
    return Response("Reloaded")


@api_view(['GET'])
def exercise_list(request):
    """
    List all exercises
    """
    # Exercise.objects.sync_with_disc()
    # Exercise.objects.folder_structure()
    exercises = Exercise.objects.all()
    serializer = ExerciseSerializer(exercises, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def exercise_tree(request):
    """
    Get exercise tree
    """
    return Response(Exercise.objects.folder_structure(request.user))


@api_view(['GET'])
def other_exercises_from_folder(request, exercise):
    dbexercise = Exercise.objects.get(exercise_name=exercise)
    other = Exercise.objects.filter(path=dbexercise.path)
    serializer = ExerciseSerializer(other, many=True)
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
    result = {}
    dbexercise = Exercise.objects.get(exercise_name=exercise)
    try:
        result = exerciseSave(dbexercise.path + '/' + exercise, request.data['xml'])
    except IOError:
        result = {'success': False}
    return Response(result)


@api_view(['POST'])
def exercise_check(request, exercise, question):
    print(question)
    answer = request.data['expression']
    dbexercise = Exercise.objects.get(exercise_name=exercise)
    dbquestion = Question.objects.get(exercise=dbexercise, question_id=question)
    result = exerciseCheck(dbexercise.path + '/' + exercise, question, answer)
    if 'correct' in result:
        dbanswer = Answer.objects.create(
            user=request.user, question=dbquestion, answer=answer, correct=result['correct']
        )
    return Response(result)


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
