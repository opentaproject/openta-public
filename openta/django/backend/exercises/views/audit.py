# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from rest_framework.decorators import api_view
from django.db.utils import OperationalError
from django.utils import timezone
import time
import json
import sys, traceback
from rest_framework import status
from django.contrib.auth.decorators import permission_required
from django.conf import settings
import datetime, time
from rest_framework.response import Response
from rest_framework import status
from exercises.modelhelpers import e_student_tried, get_all_who_tried
from exercises.aggregation import Aggregation
from django.contrib import messages
from utils import response_from_messages
from django.http import HttpResponse, JsonResponse
from utils import get_subdomain_and_db


from exercises.audits.modelhelpers import (
    get_students_to_be_audited,
    get_students_not_to_be_audited,
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
from utils import send_email_objects
import logging
import re

logger = logging.getLogger(__name__)

FROM_READY = "fromReady"
FROM_NOT_READY = "fromNotReady"
FROM_NOT_ACTIVE = "fromNotActive"


@permission_required("exercises.administer_exercise")
@api_view(["GET"])
def get_current_unsent_audits(request):
    subdomain, db = get_subdomain_and_db(request)
    audits = AuditExercise.objects.using(db).filter(auditor=request.user, sent=False, published=True)
    saudits = AuditExerciseSerializer(audits, many=True)
    return Response(saudits.data)


@permission_required("exercises.administer_exercise")
@api_view(["GET"])
def get_current_audits_exercise(request, exercise):
    subdomain, db = get_subdomain_and_db(request)
    audits = AuditExercise.objects.using(db).filter(exercise__pk=exercise)
    saudits = AuditExerciseSerializer(audits, many=True)
    return Response(saudits.data)


def dosort(students, dates):
    pairs = []
    for student in students:
        t = dates[student]
        ist = isinstance(t, datetime.datetime)
        if ist:
            t = t.timestamp()
        pairs = pairs + [{t: student}]
    pairss = sorted(pairs, key=lambda d: list(d.keys()))
    students = [list(item.values())[0] for item in pairss]
    return students


@permission_required("exercises.administer_exercise")
@api_view(["GET"])
def get_current_audits_stats(request, exercise):
    """Get statistics on current audits for an exercise.

    Args:
        exercise (Exercise): Exercise instance for audit stats.

    Returns:
        Response: JSON response with data.

    """
    subdomain, db = get_subdomain_and_db(request)
    dbexercise = Exercise.objects.using(db).select_related("meta").get(pk=exercise)
    ags = Aggregation.objects.using(db).select_related("user").filter(exercise=dbexercise)
    dates = {}
    for ag in ags:
        if ag.all_complete:
            dat = ag.date_complete
        elif ag.image_date:
            dat = ag.image_date
        elif ag.answer_date:
            dat = ag.answer_date
        else:
            dat = now()
        if hasattr(dat, "timetuple"):
            dates[ag.user.username] = time.mktime(dat.timetuple())
        else:
            dates[ag.user.username] = now()
    audits = AuditExercise.objects.using(db).filter(exercise__pk=exercise).prefetch_related("student__username")
    passed_students = get_students_to_be_audited(dbexercise)  ## fails
    students_not_active = get_students_not_active(dbexercise)
    students_not_to_be_audited = get_students_not_to_be_audited(dbexercise)
    student_audit_list = list(map(lambda student: student.username, passed_students))
    student_not_audit_list = list(map(lambda student: student.username, students_not_to_be_audited))
    student_not_active_list = list(map(lambda student: student.username, students_not_active))

    n_tried = e_student_tried(dbexercise)["ntried"]
    n_not_to_be_audited = students_not_to_be_audited.count()
    n_complete = passed_students.count()
    passed_audited = passed_students.filter(audits__exercise=dbexercise)
    passed_audited_pks = passed_audited.values_list("pk", flat=True)
    n_passed_unaudited = passed_students.exclude(pk__in=passed_audited_pks).count()
    your_audits = AuditExercise.objects.using(db).filter(exercise__pk=exercise, auditor=request.user)
    n_auditees = audits.count()
    # your_auditss = sorted( zip(dates, your_audits) )
    # your_audits = [ item[1] for item in your_auditss]
    in_overview = set(audits.values_list("student__username", flat=True).distinct())
    in_heap_for_audit = set(student_audit_list) - in_overview
    not_ready_for_audit = (set(student_not_audit_list) - in_overview) - in_heap_for_audit
    not_active = list(set(student_not_active_list))
    # TODO list in some sort of rational order
    in_overview = dosort(list(in_overview), dates)
    in_heap_for_audit = dosort(list(in_heap_for_audit), dates)
    not_ready_for_audit = dosort(list(not_ready_for_audit), dates)
    n_your_audits = len(your_audits)
    n_total = User.objects.using(db).filter(groups__name="Student").exclude(username="student").count()
    data = {
        "n_auditees": n_auditees,
        "n_not_to_be_audited": n_not_to_be_audited,
        "n_complete": n_complete,
        "n_tried": n_tried,
        "n_unaudited": n_passed_unaudited,
        "n_your_audits": n_your_audits,
        "n_total": n_total,
        "in_overview": in_overview,
        "in_heap_for_audit": in_heap_for_audit,
        "not_ready_for_audit": not_ready_for_audit,
        "not_active": not_active,
    }
    return Response(data)


@api_view(["POST", "GET"])
def get_new_audit_by_user(request, username, exercise):
    #print(f"GET_NEW_AUDIT_BY_USER")
    subdomain, db = get_subdomain_and_db(request)
    user = User.objects.using(db).get(username=username)
    student_pk = user.pk
    audits = (
        AuditExercise.objects.using(db)
        .select_related("student", "auditor", "exercise", "exercise__meta")
        .filter(exercise__pk=exercise, student__pk=student_pk)
    )
    dbexercise = Exercise.objects.using(db).select_related("meta").get(pk=exercise)
    auditee = User.objects.using(db).get(pk=student_pk)
    course = dbexercise.course
    template = get_template("audit/subject.txt")
    data = {"course": course, "exercise": dbexercise}
    subject = template.render(data).strip()
    audit = AuditExercise(auditor=request.user, student=auditee, exercise=dbexercise, subject=subject)
    pass_, message, did_something, revision_needed = analyze_exercise_for_student(dbexercise, student_pk)
    audit.revision_needed = revision_needed
    audit.message = message
    if not did_something:
        audit.message = "No data"
    audit.subject = "Your exercise " + dbexercise.name
    try:
        t = datetime.datetime.now().strftime("%F %T.%f")[:-3]
        # print(f"AUDIT-A {t}")
        audit.save(using=db)
    except IntegrityError:
        logger.error(
            f"This would result in multiple audits on {db} for the same student "
            + auditee.username
            + f"on this exercise {exercise}."
        )
        return Response({"error": "Duplicate audit for this student " + auditee.username + " and exercise"})
    saudit = AuditExerciseSerializer([audit], many=True)
    # print(f"SAUDIT.DATA {saudit.data}")
    return Response(saudit.data)


@permission_required("exercises.administer_exercise")
@api_view(["POST", "GET"])
def get_new_audit(request, exercise, heap, n_audits):
    logger.info("GET NEW AUDIT NAUDITS = %s", n_audits)
    subdomain, db = get_subdomain_and_db(request)
    audits = AuditExercise.objects.using(db).filter(exercise__pk=exercise).prefetch_related("student__pk")
    in_overview_pk = list(set(audits.values_list("student__pk", flat=True).distinct()))

    try:
        dbexercise = Exercise.objects.using(db).select_related("meta").get(pk=exercise)
    except Exercise.DoesNotExist:
        return Response(
            {"error": "Invalid exercise or no image required."},
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    students_audited_here = (
        User.objects.using(db)
        .filter(groups__name="Student", audits__exercise=dbexercise)
        .values_list("pk", flat=True)
        .distinct()
    )

    if heap == FROM_READY:
        students_audits = (
            get_students_to_be_audited(dbexercise)
            .exclude(pk__in=students_audited_here)
            .annotate(n_audits=Count("audits"))
        )
        naudits_sorted = students_audits.order_by("n_audits").values_list("n_audits", flat=True)
        try:
            minimum = naudits_sorted[0]
        except IndexError:
            return Response({"error": "No completed students available for audit."})
        targets = list(students_audits.order_by("n_audits").values_list("pk", flat=True))
    elif heap == FROM_NOT_READY:
        students_not_to_be_audited = get_students_not_to_be_audited(dbexercise)
        student_not_audit_list = set(students_not_to_be_audited.values_list("pk", flat=True).distinct())
        diff = set(student_not_audit_list) - set(in_overview_pk)
        if len(diff) == 0:
            return Response({"error": "The notReadyList has been emptied."})
        targets = list(diff)
    elif heap == FROM_NOT_ACTIVE:
        students_not_active = get_students_not_active(dbexercise)
        # logger.debug("STUDENTS NOT ACTIVE = %s", students_not_active)
        # logger.debug("STUDENTS IN OVERVIEW PK = %s", in_overview_pk)
        if len(students_not_active) > 0:
            student_not_active_list = set(students_not_active.values_list("pk", flat=True).distinct())
            # student_not_active_list = students_not_active
        else:
            student_not_active_list = []
        diff = set(student_not_active_list) - set(in_overview_pk)
        if len(diff) == 0:
            return Response({"error": "The notActiveList has been emptied."})
        targets = list(diff)
    else:
        return Response({"error": "Invalid audit heap."}, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Take n_audits or the left over, what ever is smallest
    # logger.debug("LEN TARGETS = %d, N_AUDTS = %d", len(targets), int(n_audits))
    student_pks = sample(targets, min(len(targets), int(n_audits)))
    audits = []
    dates = []
    # logger.debug("STUDENT_PKS = %s", student_pks)
    for student_pk in student_pks:
        auditee = User.objects.using(db).get(pk=student_pk)
        course = dbexercise.course
        template = get_template("audit/subject.txt")
        data = {"course": course, "exercise": dbexercise}
        subject = template.render(data).strip()
        audit = AuditExercise(auditor=request.user, student=auditee, exercise=dbexercise, subject=subject)
        pass_, message, did_something, revision_needed = analyze_exercise_for_student(dbexercise, student_pk)
        # logger.debug("AUDIT = %s " % audit )
        audit.revision_needed = revision_needed
        audit.message = message
        # logger.debug("DID SOMETHING = %s", did_something)
        if not did_something:
            audit.message = "No data"
        audit.subject = "Your exercise " + dbexercise.name
        try:
            t = datetime.datetime.now().strftime("%F %T.%f")[:-3]
            # print(f"AUDIT-B {t}")
            audit.save(using=db)
            audits.append(audit)
            dates = dates + [audit.answer_date()]
        except IntegrityError:
            logger.error(
                "This would result in multiple audits for the same student " + auditee.username + "on this exercise."
            )
            return Response({"error": "Duplicate audit for this student " + auditee.username + " and exercise"})
    try :
        sorts = sorted(zip(dates, audits))
        newaudits = [item[1] for item in sorts]
        audits = newaudits
    except Exception as e :
        logger.error(f"SORT ERRORS IN AUDITS; TRY WITHOUGH SORTS")
        logger.error(f"DATES = {dates} AUDITS={audits}")
    saudit = AuditExerciseSerializer(audits, many=True)
    # logger.debug("SAUDIT DATA = %s", saudit.data)
    return Response(saudit.data)


@permission_required("exercises.administer_exercise")
@api_view(["POST"])
def delete_audit(request, pk):
    subdomain, db = get_subdomain_and_db(request)
    try:
        audit = AuditExercise.objects.using(db).get(pk=pk)
    except AuditExercise.DoesNotExist:
        return Response({"error": "Invalid audit id"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if (audit.auditor != request.user) and not request.user.is_superuser:
        return Response(
            {"error": ("You are not the auditor of this " "audit and you are not a superuser.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    n_deleted = audit.delete()
    return Response({"success": "Deleted " + str(n_deleted) + "objects."})


@permission_required("exercises.administer_exercise")
@api_view(["POST"])
def update_audit(request, pk):
    logger.info(f"UPDATE_AUDIT {pk}")
    er = f"UPDATE AUDIT {pk}"
    subdomain, db = get_subdomain_and_db(request)
    try:
        audit = AuditExercise.objects.using(db).select_related("student", "auditor", "exercise").get(pk=pk)
    except AuditExercise.DoesNotExist:
        logger.error(f"UPDATE_AUDIT {pk} DOES NOT EXIST")
        return Response({"error": "Invalid audit id"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    data = request.data["audit"]
    er = er + "A"
    saudit = AuditExerciseSerializer(audit, data, partial=True)
    for attr, value in data.items():
            if attr == 'auditor' :
                value = User.objects.using(db).get(pk=value)
            setattr(audit, attr, value)
    er = er + "B"
    #if not saudit.is_valid():
    #    logger.error(f"AUDIT {pk} INVALID")
    #    return Response(
    #        {"error": "Not valid audit data", "details": saudit.erro / rs},
    #        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #    )
    audit.save(using=db)
    try:
        er = er + "C"
        t = datetime.datetime.now().strftime("%F %T.%f")[:-3]
        #print(f"\n\nUPDATE_AUDIT db={db} AUDIT-C {t} \n\n")
        audit.save(using=db)
    except OperationalError as e:
        msg = f"ERROR E7712: {er} UPDATE_AUDIT ERROR  data={data}"
        logger.error(msg)
        return Response({"error": "Error when saving; please try again"}, status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        msg = f"ERROR E7711: {er} UPDATE_AUDIT ERROR {type(e).__name__} data={data} traceback={traceback.format_exc()} saudit={saudit}"
        logger.error(msg)
        return Response({"error": "Unknown error when saving; try again"}, status.HTTP_403_FORBIDDEN)
    # print(f"AUDIT_OK {saudit.data}")
    return Response({})


@permission_required("exercises.administer_exercise")
@api_view(["POST", "GET"])
def send_audit(request, pk):
    ntries = 0;
    while ntries < 3 :
        try :
            subdomain, db = get_subdomain_and_db(request)
            break;
        except  Exception as err :
            r = request.get_full_path();
            logger.error(f" COULD NOT GET REQUEST DB CANNOT ATTACH PK={pk} {r} {request.POST} ")
            time.sleep(1);
        ntries = ntries + 1 ;

    user = request.user
    data = request.data
    response = send_audit_(pk,db,user,data)
    email = construct_audit_email( pk ,db,user,data)
    return response

@permission_required("exercises.administer_exercise")
@api_view(["GET"])
def send_my_audits(request,exercise):
    subdomain, db = get_subdomain_and_db(request)
    audits = AuditExercise.objects.using(db).filter(auditor=request.user, exercise__pk=exercise, sent=False, published=True)
    emails = []
    user = request.user
    data = {};
    data['bcc'] = True
    n_sent = 0;
    emails = [];
    for audit in audits:
        pk = audit.pk;
        db = db;
        user = request.user;
        data = data 
        email = construct_audit_email( pk, db, user,  data )
        n_sent = n_sent + 1
        emails.append( email)
        print(f"AUDIT_EMAIL_TO_BE_SENT = {email}")
    n_sent = send_email_objects( emails )
    logger.error(f"SENT_EMAIL_AUDITS (JOB,N) = {n_sent}")
    for audit in audits:
        audit.sent = True
        audit.save(using=db)
        logger.error(f"SAVING AUDIT {audit}")
    return Response({"success": "Email backend reported " + str(n_sent) + " email sent."})


def construct_audit_email( pk ,db,user,data) :
    er = "a"
    try:
        audit = AuditExercise.objects.using(db).select_related("exercise", "exercise__course").get(pk=pk)
        course_url = audit.exercise.course.url
        er = er + "b"
        logger.info(f"audit = {audit}")
        er = er + "c"
        course_url = audit.exercise.course.url
        er = er + "d"
        logger.info(f"COURSE_URL={course_url}")
        er = er + "e"
    except AuditExercise.DoesNotExist:
        logger.error(f"AUDIT FETCH FAILED {er}")
        return Response({"error": "Invalid audit id"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        # logger.debug("EXCEPTION = %s", e)
        return Response({"error": "Invalid audit id"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    mail_message_template = (
        "{message}" "\n\n" "---------------------------------\n" "This message is sent from OpenTA." "\n" "{url}"
    )
    mail_message = mail_message_template.format(message=audit.message, url=course_url)
    max_subject_length = 16
    subject = re.sub("\s+", " ", audit.subject)
    if len(subject) > max_subject_length:
        subject = subject[0:max_subject_length] + " ..."
    try :
        student = audit.student.email
        email = EmailMessage(
            subject=subject,
            body=mail_message,
            from_email=audit.exercise.course.email_reply_to.strip(),
            to=[student],
            reply_to=[user.email],
        )
        # Send bcc to auditor (and current user if not auditor)
        bcc = data.get("bcc",None)
        bcclist = []
        if bcc and audit.auditor.email:
            bcclist = list(set([audit.auditor.email, user.email]))
            logger.info("Sending with bcc.")
            email.bcc = bcclist
        return  email
    except Exception as e  :
        logger.error(f"EMAIL SEND ERROR FOR {type(e).__name__} {str(e)} {pk} {db} {user} {data} {audit} ")
        return None



def send_audit_(pk,db,user,data):

    er = "a"
    try:
        audit = AuditExercise.objects.using(db).select_related("exercise", "exercise__course").get(pk=pk)
    #    course_url = audit.exercise.course.url
    #    er = er + "b"
    #    logger.info(f"audit = {audit}")
    #    er = er + "c"
    #    course_url = audit.exercise.course.url
    #    er = er + "d"
    #    logger.info(f"COURSE_URL={course_url}")
    #    er = er + "e"
    except AuditExercise.DoesNotExist:
        logger.error(f"AUDIT FETCH FAILED {er}")
        return Response({"error": "Invalid audit id"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        # logger.debug("EXCEPTION = %s", e)
        return Response({"error": "Invalid audit id"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    #mail_message_template = (
    #    "{message}" "\n\n" "---------------------------------\n" "This message is sent from OpenTA." "\n" "{url}"
    #)
    #mail_message = mail_message_template.format(message=audit.message, url=course_url)
    #max_subject_length = 16
    #subject = re.sub("\s+", " ", audit.subject)
    #if len(subject) > max_subject_length:
    #    subject = subject[0:max_subject_length] + " ..."
    #student = audit.student.email
    #email = EmailMessage(
    #    subject=subject,
    #    body=mail_message,
    #    from_email=audit.exercise.course.email_reply_to.strip(),
    #    to=[student],
    #    reply_to=[user.email],
    #)
    ## Send bcc to auditor (and current user if not auditor)
    #logger.error(f"EMAIL = {email}")
    #bcc = data.get("bcc")
    #bcclist = []
    #if bcc and audit.auditor.email:
    #    bcclist = list(set([audit.auditor.email, request.user.email]))
    #    logger.info("Sending with bcc.")
    #    email.bcc = bcclist
    email = construct_audit_email( pk ,db,user,data)
    if settings.BLOCK_EMAIL_AUDITS:  # not audit.exercise.course.use_email:
        audit.sent = False
        t = datetime.datetime.now().strftime("%F %T.%f")[:-3]
        # print(f"AUDIT-D {t}")
        audit.save(using=db)
        logger.error(f"AUDIT {pk} NOT SENT No email sent BLOCK={settings.BLOCK_EMAIL_AUDITS} ")
        return Response({"warning": "No email sent due to BLOCK_EMAIL_AUDIT=True "})
    else:
        try:
            n_sent = send_email_object(email)
            audit.sent = True
            t = datetime.datetime.now().strftime("%F %T.%f")[:-3]
            # print(f"AUDIT-E {t}")
            audit.save(using=db)
            logger.error(f"AUDIT {pk} OK SENT {audit.student.email} {audit.subject} {audit.exercise} ")
        except Exception as e:
            logger.error(f"AUDIT {pk} NOT SENT {str( type(e).__name__)} {str(e)}")
            logger.error(f"AUDIT {pk} NOT SENT {audit.student.email} {audit.subject} {audit.exercise} ")
            return Response({"error": "error in sending email"})
        # old = []
        # now = datetime.datetime.now()
        # earlier = timezone.now()-timezone.timedelta(hours=settings.EMAIL_BACKLOG)
        # unsent = []
        # if not settings.BLOCK_EMAIL_AUDITS  :
        #    unsent= AuditExercise.objects.using(db).select_related('exercise','exercise__course').filter(sent=False,exercise=audit.exercise,date__gt=earlier)
        #    print(f"UNSENT = {unsent}")
        # for a in unsent :
        #    mail_message = mail_message_template.format(message=a.message, url=course_url)
        #    student = a.student.email
        #    email = EmailMessage(
        #        subject=a.subject,
        #        body=mail_message,
        #        bcc=bcclist,
        #        from_email=a.exercise.course.email_reply_to.strip(),
        #        to=[student],
        #        reply_to=[request.user.email],
        #        )
        #    old.append(email)
        # try :
        #    n_sent = send_email_objects(old)
        #    for a in unsent:
        #        logger.error(f"SENT AUDIT MESSAGE TO {n_sent} {subdomain}  {a.student.email}")
        #        a.sent = True # TODO
        #        a.save()
        # except Exception as e :
        #    logger.error(f"AUDIT_SEND_ERROR {type(e).__name__} {str(e)} ")
        #    return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"success": "Email backend reported " + str(n_sent) + " email sent."})


@permission_required("exercises.administer_exercise")
@api_view(["POST"])
def add_audit(request):
    #print(f"ADD_AUDIT")
    auditor = request.user
    subdomain, db = get_subdomain_and_db(request)
    try:
        exercise_pk = request.data["audit"]["exercise"]
        student_pk = request.data["audit"]["student"]
    except KeyError:
        return Response({"error": "Not valid audit data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    try:
        current = AuditExercise.objects.using(db).get(exercise__pk=exercise_pk, student__pk=student_pk)
        return Response({"pk": current.pk, "created": False})
    except AuditExercise.DoesNotExist:
        exercise = Exercise.objects.using(db).get(pk=exercise_pk)
        student = User.objects.using(db).get(pk=student_pk)
        course = exercise.course
        template = get_template("audit/subject.txt")
        data = {"course": course, "exercise": exercise}
        subject = template.render(data).strip()
        audit = AuditExercise(auditor=auditor, exercise=exercise, subject=subject, student=student)
        t = datetime.datetime.now().strftime("%F %T.%f")[:-3]
        # print(f"AUDIT-F {t}")
        audit.save(using=db)
        return Response({"pk": audit.pk, "created": True})


@api_view(["POST"])
def student_audit_update(request, pk):
    subdomain, db = get_subdomain_and_db(request)
    try:
        audit = AuditExercise.objects.using(db).get(pk=pk)
    except AuditExercise.DoesNotExist:
        return Response({"error": "Invalid audit id"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if (audit.student != request.user) and not request.user.is_superuser:
        return Response(
            {"error": ("You are not the student of this" " audit and you are not a superuser.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    updated = request.data.get("updated")
    if updated is None:
        return Response({"error": "No update status in request"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    audit.updated = updated
    audit.updated_date = now()
    t = datetime.datetime.now().strftime("%F %T.%f")[:-3]
    # print(f"AUDIT-G {t}")
    audit.save(using=db)
    return Response({"success": "Update status: " + str(updated)})
