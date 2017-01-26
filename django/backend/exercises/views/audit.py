from rest_framework.decorators import api_view, parser_classes
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from rest_framework import status
from exercises.modelhelpers import (
    serialize_exercise_with_question_data,
    exercise_folder_structure,
    student_attempts_exercises,
    exercise_test,
    get_passed_students,
)
from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from exercises.serializers import AuditExerciseSerializer, ImageAnswerSerializer
from course.models import Course
from django.contrib.auth.models import User
from django.db.models import Prefetch, Max, F, Count, Sum, Value, Q
import datetime
from django.utils import timezone
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser
import pytz
from random import choice


@permission_required('exercises.administer_exercise')
@api_view(['GET'])
def get_current_unsent_audits(request):
    audits = AuditExercise.objects.filter(auditor=request.user, sent=False)
    saudits = AuditExerciseSerializer(audits, many=True)
    return Response(saudits.data)


@permission_required('exercises.administer_exercise')
@api_view(['GET'])
def get_current_audits_exercise(request, exercise):
    audits = AuditExercise.objects.filter(auditor=request.user, exercise__pk=exercise)
    saudits = AuditExerciseSerializer(audits, many=True)
    return Response(saudits.data)


@permission_required('exercises.administer_exercise')
@api_view(['POST', 'GET'])
def get_new_audit(request, exercise):
    dbexercise = Exercise.objects.get(pk=exercise)
    students_audits = get_passed_students(dbexercise).annotate(n_audits=Count('audits'))
    # User.objects.filter(groups__name='Student').annotate(n_audits=Count('audits'))
    naudits_sorted = students_audits.order_by('n_audits').values_list('n_audits', flat=True)
    try:
        minimum = naudits_sorted[0]
    except IndexError:
        return Response({'error': 'No completed students available for audit.'})
    targets = students_audits.filter(n_audits=minimum).values_list('pk', 'n_audits')
    auditee = User.objects.get(pk=choice(targets)[0])
    audit = AuditExercise(auditor=request.user, student=auditee, exercise=dbexercise)
    audit.save()
    saudit = AuditExerciseSerializer(audit)
    return Response(saudit.data)


@permission_required('exercises.administer_exercise')
@api_view(['POST'])
def update_audit(request, pk):
    try:
        audit = AuditExercise.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return Response({'error': 'Invalid audit id'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    saudit = AuditExerciseSerializer(audit, data=request.data['audit'])
    if not saudit.is_valid():
        return Response(
            {'error': 'Not valid audit data'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    saudit.save()
    return Response({})
