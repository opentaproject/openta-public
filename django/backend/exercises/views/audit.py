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
from django.db import IntegrityError
from django.core.mail import EmailMessage
import datetime
from django.utils import timezone
from django.utils.six import BytesIO
from django.template.loader import get_template
from django.template import Context
from rest_framework.parsers import JSONParser
import pytz
from random import choice
import logging

logger = logging.getLogger(__name__)


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
@api_view(['GET'])
def get_current_audits_stats(request, exercise):
    dbexercise = Exercise.objects.get(pk=exercise)
    audits = AuditExercise.objects.filter(exercise__pk=exercise)
    your_audits = AuditExercise.objects.filter(exercise__pk=exercise, auditor=request.user)
    n_auditees = audits.count()
    n_your_audits = your_audits.count()
    n_complete = get_passed_students(dbexercise).count()
    n_total = User.objects.filter(groups__name='Student').exclude(username='student').count()
    data = {
        'n_auditees': n_auditees,
        'n_complete': n_complete,
        'n_unaudited': (n_complete - n_auditees),
        'n_your_audits': n_your_audits,
        'n_total': n_total,
    }
    return Response(data)


@permission_required('exercises.administer_exercise')
@api_view(['POST', 'GET'])
def get_new_audit(request, exercise):
    try:
        dbexercise = Exercise.objects.get(pk=exercise, meta__image=True)
    except Exercise.DoesNotExist:
        return Response(
            {'error': 'Invalid exercise or no image required.'},
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    students_audits = get_passed_students(dbexercise).annotate(n_audits=Count('audits'))
    # User.objects.filter(groups__name='Student').annotate(n_audits=Count('audits'))
    naudits_sorted = students_audits.order_by('n_audits').values_list('n_audits', flat=True)
    try:
        minimum = naudits_sorted[0]
    except IndexError:
        return Response({'error': 'No completed students available for audit.'})
    targets = students_audits.filter(n_audits=minimum).values_list('pk', 'n_audits')
    auditee = User.objects.get(pk=choice(targets)[0])
    course = Course.objects.first()
    template = get_template('audit/subject.txt')
    data = {'course': course, 'exercise': dbexercise}
    context = Context(data)
    subject = template.render(context).strip()
    audit = AuditExercise(
        auditor=request.user, student=auditee, exercise=dbexercise, subject=subject
    )
    try:
        audit.save()
    except IntegrityError:
        logger.error("This would result in multiple audits for the same student on this exercise.")
        return Response({'error': 'Duplicate audit for this student and exercise'})
    saudit = AuditExerciseSerializer(audit)
    return Response(saudit.data)


@permission_required('exercises.administer_exercise')
@api_view(['POST'])
def delete_audit(request, pk):
    try:
        audit = AuditExercise.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return Response({'error': 'Invalid audit id'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if (audit.auditor != request.user) and not request.user.is_superuser:
        return Response(
            {'error': 'You are not the auditor of this audit and you are not a superuser.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    n_deleted = audit.delete()
    return Response({'success': 'Deleted ' + str(n_deleted) + 'objects.'})


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


@permission_required('exercises.administer_exercise')
@api_view(['POST'])
def send_audit(request, pk):
    try:
        audit = AuditExercise.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return Response({'error': 'Invalid audit id'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    email = EmailMessage(
        subject=audit.subject,
        body=audit.message,
        from_email=Course.objects.course_name().lower() + "@openta.se",
        to=[audit.student.email],
        reply_to=[request.user.email],
    )
    try:
        n_sent = email.send()
    except Exception as e:
        return Response({error: str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    audit.sent = True
    audit.save()
    return Response({'success': "Email backend reported " + str(n_sent) + " email sent."})


@permission_required('exercises.administer_exercise')
@api_view(['POST'])
def add_audit(request):
    auditor = request.user
    try:
        exercise_pk = request.data['audit']['exercise']
        student_pk = request.data['audit']['student']
    except KeyError:
        return Response(
            {'error': 'Not valid audit data'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    try:
        current = AuditExercise.objects.get(exercise__pk=exercise_pk, student__pk=student_pk)
        return Response({'pk': current.pk, 'created': False})
    except AuditExercise.DoesNotExist:
        exercise = Exercise.objects.get(pk=exercise_pk)
        student = User.objects.get(pk=student_pk)
        audit = AuditExercise(auditor=auditor, exercise=exercise, student=student)
        audit.save()
        return Response({'pk': audit.pk, 'created': True})
