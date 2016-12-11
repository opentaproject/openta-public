from rest_framework.decorators import api_view, parser_classes
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from exercises.modelhelpers import (
    serialize_exercise_with_question_data,
    exercise_folder_structure,
    student_attempts_exercises,
    exercise_test,
    student_statistics_exercises,
    get_passed_exercises_with_data,
    get_passed_students,
)
from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from exercises.serializers import AuditExerciseSerializer
from course.models import Course
from django.contrib.auth.models import User
from django.db.models import Prefetch, Max, F, Count, Sum, Value, Q
import datetime
from django.utils import timezone
import pytz
from random import choice


@permission_required('exercises.administer_exercise')
@api_view(['GET'])
def get_current_unsent_audits(request):
    audits = AuditExercise.objects.filter(auditor=request.user, sent=False)
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
@api_view(['GET'])
def get_audit_data(request, audit):
    dbaudit = AuditExercise.objects.get(pk=audit)
    image_answers = ImageAnswer.objects.filter(
        user=dbaudit.student, exercise=dbaudit.exercise
    ).values_list('pk', flat=True)
    questions = dbaudit.exercise.question.all()
    deadline_time = datetime.time(8, 0, 0, tzinfo=pytz.timezone('Europe/Stockholm'))
    course = Course.objects.first()
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    answers = {}
    for question in questions:
        answer = Answer.objects.filter(
            user=dbaudit.student,
            question=question,
            correct=True,
            date__lt=datetime.datetime.combine(dbaudit.exercise.meta.deadline_date, deadline_time),
        ).latest('date')
        answers[question.question_key] = answer.answer
    # question_list = questions.value_list(
    return Response({'image_answers': image_answers, 'answers': answers})
