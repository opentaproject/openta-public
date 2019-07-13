from rest_framework.decorators import api_view
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from rest_framework import status
from exercises.modelhelpers import (
    get_students_to_be_audited,
    get_students_not_to_be_audited,
    e_student_tried,
    get_all_who_tried,
    analyze_exercise_for_student,
    get_students_not_active,
)
from exercises.models import Exercise, AuditExercise
from exercises.serializers import AuditExerciseSerializer
from course.models import Course
from django.contrib.auth.models import User
from django.db.models import Count
from django.db import IntegrityError
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.utils.timezone import now
from random import choice, sample
from backend.user_utilities import send_email_object
import logging

logger = logging.getLogger(__name__)

FROM_READY = 'fromReady'
FROM_NOT_READY = 'fromNotReady'
FROM_NOT_ACTIVE = 'fromNotActive'


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
    """Get statistics on current audits for an exercise.

    Args:
        exercise (Exercise): Exercise instance for audit stats.

    Returns:
        Response: JSON response with data.

    """
    dbexercise = Exercise.objects.get(pk=exercise)
    audits = AuditExercise.objects.filter(exercise__pk=exercise).prefetch_related(
        'student__username'
    )
    passed_students = get_students_to_be_audited(dbexercise)
    students_not_active = get_students_not_active(dbexercise)
    students_not_to_be_audited = get_students_not_to_be_audited(dbexercise)
    student_audit_list = list(map(lambda student: student.username, passed_students))
    student_not_audit_list = list(map(lambda student: student.username, students_not_to_be_audited))
    student_not_active_list = list(map(lambda student: student.username, students_not_active))

    n_tried = e_student_tried(dbexercise)['ntried']
    n_not_to_be_audited = students_not_to_be_audited.count()
    n_complete = passed_students.count()
    passed_audited = passed_students.filter(audits__exercise=dbexercise)
    passed_audited_pks = passed_audited.values_list('pk', flat=True)
    n_passed_unaudited = passed_students.exclude(pk__in=passed_audited_pks).count()
    your_audits = AuditExercise.objects.filter(exercise__pk=exercise, auditor=request.user)
    n_auditees = audits.count()

    in_overview = set(audits.values_list('student__username', flat=True).distinct())
    in_heap_for_audit = set(student_audit_list) - in_overview
    not_ready_for_audit = (set(student_not_audit_list) - in_overview) - in_heap_for_audit
    not_active = list(set(student_not_active_list))
    in_overview = list(in_overview)
    in_heap_for_audit = list(in_heap_for_audit)
    not_ready_for_audit = list(not_ready_for_audit)

    n_your_audits = your_audits.count()
    n_total = User.objects.filter(groups__name='Student').exclude(username='student').count()
    data = {
        'n_auditees': n_auditees,
        'n_not_to_be_audited': n_not_to_be_audited,
        'n_complete': n_complete,
        'n_tried': n_tried,
        'n_unaudited': n_passed_unaudited,
        'n_your_audits': n_your_audits,
        'n_total': n_total,
        'in_overview': in_overview,
        'in_heap_for_audit': in_heap_for_audit,
        'not_ready_for_audit': not_ready_for_audit,
        'not_active': not_active,
    }
    return Response(data)


@permission_required('exercises.administer_exercise')
@api_view(['POST', 'GET'])
def get_new_audit(request, exercise, heap, n_audits):
    audits = AuditExercise.objects.filter(exercise__pk=exercise).prefetch_related('student__pk')
    in_overview_pk = list(set(audits.values_list('student__pk', flat=True).distinct()))

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

    if heap == FROM_READY:
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
        targets = list(students_audits.filter(n_audits=minimum).values_list('pk', flat=True))
    elif heap == FROM_NOT_READY:
        students_not_to_be_audited = get_students_not_to_be_audited(dbexercise)
        student_not_audit_list = set(
            students_not_to_be_audited.values_list('pk', flat=True).distinct()
        )
        diff = set(student_not_audit_list) - set(in_overview_pk)
        if len(diff) == 0:
            return Response({'error': 'The notReadyList has been emptied.'})
        targets = list(diff)
    elif heap == FROM_NOT_ACTIVE:
        students_not_active = get_students_not_active(dbexercise)
        student_not_active_list = set(students_not_active.values_list('pk', flat=True).distinct())
        diff = set(student_not_active_list) - set(in_overview_pk)
        if len(diff) == 0:
            return Response({'error': 'The notActiveList has been emptied.'})
        targets = list(diff)
    else:
        return Response({'error': 'Invalid audit heap.'}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Take n_audits or the left over, what ever is smallest
    student_pks = sample(targets, min(len(targets), int(n_audits)))
    audits = []
    for student_pk in student_pks:
        auditee = User.objects.get(pk=student_pk)
        course = dbexercise.course
        template = get_template('audit/subject.txt')
        data = {'course': course, 'exercise': dbexercise}
        subject = template.render(data).strip()
        audit = AuditExercise(
            auditor=request.user, student=auditee, exercise=dbexercise, subject=subject
        )
        pass_, message = analyze_exercise_for_student(dbexercise, student_pk)
        if not pass_:
            audit.revision_needed = True
        audit.message = message
        audit.subject = 'Your exercise ' + dbexercise.name
        try:
            audit.save()
            audits.append(audit)
        except IntegrityError:
            logger.error(
                "This would result in multiple audits for the same student "
                + auditee.username
                + "on this exercise."
            )
            return Response(
                {'error': 'Duplicate audit for this student ' + auditee.username + ' and exercise'}
            )
    saudit = AuditExerciseSerializer(audits, many=True)
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
    print("SEND_AUDIT")
    try:
        audit = AuditExercise.objects.get(pk=pk)
    except AuditExercise.DoesNotExist:
        return Response({'error': 'Invalid audit id'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    print("EMAIL ACTIVATED")
    if not audit.exercise.course.use_email:
        print("EMAIL NOT ACTIVATED")
        return Response({'warning': 'use_email is not activated'} ) 
    course_url = audit.exercise.course.url
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
        from_email=audit.exercise.course.email_reply_to.strip(),
        to=[audit.student.email],
        reply_to=[request.user.email],
    )
    # Send bcc to auditor (and current user if not auditor)
    bcc = request.data.get('bcc')
    bcclist = []
    if bcc and audit.auditor.email:
        bcclist = list(set([audit.auditor.email, request.user.email]))
        logger.info("Sending with bcc.")
        email.bcc = bcclist
    try:
        n_sent = send_email_object(email)
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
        course = exercise.course
        template = get_template('audit/subject.txt')
        data = {'course': course, 'exercise': exercise}
        subject = template.render(data).strip()
        audit = AuditExercise(auditor=auditor, exercise=exercise, subject=subject, student=student)
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
