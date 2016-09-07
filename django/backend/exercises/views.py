from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from exercises.models import Exercise, Question, Answer, ImageAnswer
from exercises.serializers import ExerciseSerializer, AnswerSerializer
from exercises import parsing
from exercises.question import question_check
from exercises.modelhelpers import serialize_exercise_with_question_data
from exercises.paths import EXERCISES_PATH
from exercises.util import nested_print
from django.http import FileResponse, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
import backend.settings as settings
import json
import time
import random

import sys
import os

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__) + '/../../../questiontypes'))
import question_types


@api_view(['POST', 'GET'])
def exercises_reload(request):  # {{{
    Exercise.objects.sync_with_disc()
    return Response("Reloaded")  # }}}


@api_view(['GET'])
def exercise(request, exercise):  # {{{
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    data = serialize_exercise_with_question_data(dbexercise, request.user)
    return Response(data)  # }}}


@api_view(['GET'])
def exercise_list(request):  # {{{
    """
    List all exercises
    """
    response = []
    exercises = Exercise.objects.all()
    for exercise in exercises:
        data = serialize_exercise_with_question_data(exercise, request.user)
        response.append(data)
    return Response(response)  # }}}


@api_view(['GET'])
def exercise_tree(request):  # {{{
    """
    Get exercise tree
    """
    return Response(Exercise.objects.folder_structure(request.user))  # }}}


@api_view(['GET'])
def other_exercises_from_folder(request, exercise):  # {{{
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    other = Exercise.objects.filter(folder=dbexercise.folder)
    serializer = ExerciseSerializer(other, many=True)
    return Response(serializer.data)  # }}}


@api_view(['GET'])
def exercise_json(request, exercise):  # {{{
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    try:
        exercisejson = parsing.exercise_json(dbexercise.path)
        return Response(exercisejson)
    except parsing.ExerciseParseError as e:
        return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)  # }}}


@api_view(['GET'])
def exercise_xml(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    return Response({'xml': parsing.exercise_xml(dbexercise.path)})


@api_view(['POST'])
def exercise_save(request, exercise):  # {{{
    result = {}
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    try:
        result = parsing.exercise_save(dbexercise.path, request.data['xml'])
        Exercise.objects.add_exercise(dbexercise.path)
        return Response(result)
    except parsing.ExerciseParseError as e:
        result = {'success': True, 'error': str(e)}
        return Response(result)
    except IOError as e:
        result = {'success': False, 'error': str(e)}
        return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  # }}}


@api_view(['POST'])
def exercise_check(request, exercise, question):  # {{{
    answer_data = request.data['answerData']
    result = question_check(request.user, exercise, question, answer_data)
    return Response(result)  # }}}


def serve_file(path, filename, **kwargs):
    content_type = kwargs['content_type'] if 'content_type' in kwargs else None
    dev_path = kwargs['dev_path'] if 'dev_path' in kwargs else path

    if settings.RUNNING_DEVSERVER:
        if content_type:
            return FileResponse(open(dev_path, 'rb'), content_type)
        else:
            return FileResponse(open(dev_path, 'rb'))
    else:
        response = HttpResponse()
        response["Content-Type"] = content_type if content_type else ""
        response["Content-Disposition"] = "attachment; filename={0}".format(filename)
        response["X-Accel-Redirect"] = path
        return response


@api_view(['GET'])
def exercise_asset(request, exercise, asset):  # {{{
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    return serve_file(
        "/exerciseasset/{path}/{asset}".format(path=dbexercise.path, asset=asset),
        asset,
        dev_path='{root}/{path}/{asset}'.format(
            root=EXERCISES_PATH, path=dbexercise.path, asset=asset
        ),
    )
    # }}}


@api_view(['GET'])
def question_last_answer(request, exercise, question):  # {{{
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    dbquestion = Question.objects.get(exercise=dbexercise, question_key=question)
    dbanswer = Answer.objects.filter(user=request.user, question=dbquestion).latest('date')
    serializer = AnswerSerializer(dbanswer)
    return Response(serializer.data)  # }}}


@api_view(['POST'])
@parser_classes((MultiPartParser,))
def upload_answer_image(request, exercise):
    print(request.FILES['file'])
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    if request.FILES['file'].size > 10e6:
        return Response("Image larger than 10mb", status.HTTP_500_INTERNAL_SERVER_ERROR)

    image_answer = ImageAnswer(
        user=request.user, exercise=dbexercise, exercise_key=exercise, image=request.FILES['file']
    )
    image_answer.save()
    # nested_print(request.data)
    return Response({})


@api_view(['GET'])
def answer_image_view(request, image_id):
    try:
        image_answer = ImageAnswer.objects.get(pk=image_id)
        print(image_answer.image.name)
        if image_answer.user == request.user or request.user.is_staff:
            return serve_file(
                '/' + image_answer.image.name,
                os.path.basename(image_answer.image.name),
                content_type="image/jpeg",
                dev_path=image_answer.image.path,
            )
        else:
            return Response("Not authorized", status.HTTP_500_INTERNAL_SERVER_ERROR)
    except ObjectDoesNotExist:
        return Response("invalid answer image id", status.HTTP_500_INTERNAL_SERVER_ERROR)
