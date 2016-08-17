from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from exercises.models import Exercise, Question
from exercises.serializers import ExerciseSerializer


@api_view(['GET'])
def exercise_list(request):
    """
    List all exercises
    """
    # Exercise.objects.sync_with_disc()
    Exercise.objects.folder_structure()
    exercises = Exercise.objects.all()
    serializer = ExerciseSerializer(exercises, many=True)
    return Response(serializer.data)
