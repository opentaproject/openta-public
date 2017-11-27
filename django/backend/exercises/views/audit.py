from rest_framework.decorators import api_view
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from rest_framework import status
from exercises.modelhelpers import get_students_to_be_audited
from exercises.models import Exercise, AuditExercise
from exercises.serializers import AuditExerciseSerializer
from course.models import Course
from django.contrib.auth.models import User
from django.db.models import Count
from django.db import IntegrityError
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.template import Context
from django.utils.timezone import now
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
    audits = AuditExercise.objects.filter(exercise__pk=exercise)
    saudits = AuditExerciseSerializer(audits, many=True)
    return Response(saudits.data)


@permission_required('exercises.administer_exercise')
@api_view(['GET'])
def get_current_audits_stats(request, exercise):
    dbexercise = Exercise.objects.get(pk=exercise)
    audits = AuditExercise.objects.filter(exercise__pk=exercise)
    passed_students = get_students_to_be_audited(dbexercise)
    passed_audited = passed_students.filter(audits__exercise=dbexercise)
    passed_audited_pks = passed_audited.values_list('pk', flat=True)
    n_passed_unaudited = passed_students.exclude(pk__in=passed_audited_pks).count()
    your_audits = AuditExercise.objects.filter(exercise__pk=exercise, auditor=request.user)
    n_auditees = audits.count()
    n_your_audits = your_audits.count()
    n_complete = passed_students.count()
    n_total = User.objects.filter(groups__name='Student').exclude(username='student').count()
    data = {
        'n_auditees': n_auditees,
        'n_complete': n_complete,
        'n_unaudited': n_passed_unaudited,
        'n_your_audits': n_your_audits,
        'n_total': n_total,
    }
    return Response(data)


@permission_required('exercises.administer_exercise')
@api_view(['POST', 'GET'])
def get_new_audit(request, exercise):
    try:
        dbexercise = Exercise.objects.get(pk=exercise)
    except Exercise.DoesNotExist:
        return Response(
            {'error': 'Invalid exercise or no image required.'},
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    students_audited_here = (
        User.objects.filter(groups__name='Student', audits__exercise=dbexercise)
        .values_list('pk', flat=True)
        .distinct()
    )
    students_audits = (
        get_students_to_be_audited(dbexercise)
        .exclude(pk__in=students_audited_here)
        .annotate(n_audits=Count('audits'))
    )
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
        auditor=request.user,
        student=auditee,
        exercise=dbexercise,
        subject=subject,
        exercise_key=dbexercise.exercise_key,
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
    except AuditExercise.DoesNotExist:
        return Response({'error': 'Invalid audit id'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if (audit.auditor != request.user) and not request.user.is_superuser:
        return Response(
            {'error': ('You are not the auditor of this ' 'audit and you are not a superuser.')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    n_deleted = audit.delete()
    return Response({'success': 'Deleted ' + str(n_deleted) + 'objects.'})


@permission_required('exercises.administer_exercise')
@api_view(['POST'])
def update_audit(request, pk):
    try:
        audit = AuditExercise.objects.get(pk=pk)
    except AuditExercise.DoesNotExist:
        return Response({'error': 'Invalid audit id'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    saudit = AuditExerciseSerializer(audit, data=request.data['audit'], partial=True)
    if not saudit.is_valid():
        return Response(
            {'error': 'Not valid audit data', 'details': saudit.errors},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    saudit.save()
    return Response({})


@permission_required('exercises.administer_exercise')
@api_view(['POST'])
def send_audit(request, pk):
    try:
        audit = AuditExercise.objects.get(pk=pk)
    except AuditExercise.DoesNotExist:
        return Response({'error': 'Invalid audit id'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    course_url = Course.objects.course_url()
    mail_message_template = (
        "{message}"
        "\n\n"
        "---------------------------------\n"
        "This message is sent from OpenTA."
        "\n"
        "{url}"
    )
    mail_message = mail_message_template.format(message=audit.message, url=course_url)

    email = EmailMessage(
        subject=audit.subject,
        body=mail_message,
        from_email=Course.objects.course_name().lower() + "@openta.se",
        to=[audit.student.email],
        reply_to=[request.user.email],
    )
    # Send bcc to auditor (and current user if not auditor)
    bcc = request.data.get('bcc')
    if bcc:
        logger.info("Sending with bcc.")
        email.bcc = list(set([audit.auditor.email, request.user.email]))
    try:
        n_sent = email.send()
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        course = Course.objects.first()
        template = get_template('audit/subject.txt')
        data = {'course': course, 'exercise': exercise}
        context = Context(data)
        subject = template.render(context).strip()
        audit = AuditExercise(
            auditor=auditor,
            exercise=exercise,
            subject=subject,
            student=student,
            exercise_key=exercise.exercise_key,
        )
        audit.save()
        return Response({'pk': audit.pk, 'created': True})


@api_view(['POST'])
def student_audit_update(request, pk):
    try:
        audit = AuditExercise.objects.get(pk=pk)
    except AuditExercise.DoesNotExist:
        return Response({'error': 'Invalid audit id'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if (audit.student != request.user) and not request.user.is_superuser:
        return Response(
            {'error': ('You are not the student of this' ' audit and you are not a superuser.')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    updated = request.data.get('updated')
    if updated is None:
        return Response(
            {'error': 'No update status in request'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    audit.updated = updated
    audit.updated_date = now()
    audit.save()
    return Response({'success': "Update status: " + str(updated)})
