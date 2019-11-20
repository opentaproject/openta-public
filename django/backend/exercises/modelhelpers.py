from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
import logging
from course.models import Course
from exercises.parsing import exercise_xmltree, question_xmltree_get
from exercises.question import question_check
from django.contrib.auth.models import User
from exercises.serializers import ExerciseSerializer, ExerciseMetaSerializer, AnswerSerializer
from exercises.serializers import ImageAnswerSerializer, AuditExerciseSerializer
import json
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch, Count, Avg, Q, F
from django.test import RequestFactory
import os
from functools import reduce
from collections import OrderedDict, defaultdict, namedtuple
import datetime
from django.utils import timezone
from django.conf import settings
import pytz
from aggregation.models import Aggregation, get_cache_and_key, STATISTICS_CACHE_TIMEOUT
from dateutil.relativedelta import relativedelta, MO
from statistics import median, mean
from django.core.cache import caches

logger = logging.getLogger(__name__)


bonafide_students = (
    User.objects.filter(groups__name='Student', is_active=True)
    .exclude(groups__name='View')
    .exclude(groups__name='Admin')
    .exclude(groups__name='Author')
    .exclude(username='student')
)


def e_name(exercise):
    return {'name': exercise.name}


def e_path(exercise):
    return {'path': exercise.path}


def e_student_attempt_count(exercise):
    attempt_list = list(
        Aggregation.objects.filter(exercise=exercise, user__in=bonafide_students).values_list(
            'attempt_count', flat=True
        )
    )
    attempts = sum(attempt_list)
    return {'attempts': attempts}


def e_student_activity(exercise):
    # return {
    #    'activity': {'1h': 0 , '24h': 0, '1w': 0 , 'all': 0}
    # }
    coursePk = exercise.course.pk
    (cache, cachekey) = get_cache_and_key(
        'e_student_activity:', coursePk=coursePk, exercise_key=exercise.exercise_key
    )
    print("E_STUDENT_ACTIVITY ", exercise.pk)
    if cache.has_key(cachekey):
        return cache.get(cachekey)
    t1h = timezone.now() - datetime.timedelta(hours=1)
    t24h = timezone.now() - datetime.timedelta(hours=24)
    t1w = timezone.now() - datetime.timedelta(days=7)
    n_questions = exercise.question.all().count()
    if n_questions == 0:
        return {'activity': {'1h': 0, '24h': 0, '1w': 0, 'all': 0}}

    activity_1h = round(
        Answer.objects.filter(
            date__gt=t1h, question__exercise=exercise, user__groups__name="Student"
        ).count()
        / n_questions
    )
    activity_24h = round(
        Answer.objects.filter(
            date__gt=t24h, question__exercise=exercise, user__groups__name="Student"
        ).count()
        / n_questions
    )
    activity_1w = round(
        Answer.objects.filter(
            date__gt=t1w, question__exercise=exercise, user__groups__name="Student"
        ).count()
        / n_questions
    )
    activity_all = round(
        Answer.objects.filter(question__exercise=exercise, user__groups__name="Student").count()
        / n_questions
    )
    activity = {
        'activity': {'1h': activity_1h, '24h': activity_24h, '1w': activity_1w, 'all': activity_all}
    }
    cache.set(cachekey, activity, STATISTICS_CACHE_TIMEOUT)
    return activity


def p_student_activity(data):
    print("P_STUDENT_ACTIVITY")
    try:
        max_1h = max(data.values(), key=lambda exercise: exercise['activity']['1h'])
        max_24h = max(data.values(), key=lambda exercise: exercise['activity']['24h'])
        max_1w = max(data.values(), key=lambda exercise: exercise['activity']['1w'])
        max_all = max(data.values(), key=lambda exercise: exercise['activity']['all'])
    except ValueError:
        return {'max_1h': 0, 'max_24h': 0, 'max_1w': 0, 'max_all': 0}
    return {
        'max_1h': max_1h['activity']['1h'],
        'max_24h': max_24h['activity']['24h'],
        'max_1w': max_1w['activity']['1w'],
        'max_all': max_all['activity']['all'],
    }


def e_student_attempts_mean(exercise):
    users = bonafide_students
    users = bonafide_students.filter(opentauser__courses=exercise.course)
    n_questions = Question.objects.filter(exercise=exercise).count()

    attempt_list = list(
        Aggregation.objects.filter(exercise=exercise, user__in=users)
        .filter(Q(attempt_count__gt=0))
        .values_list('attempt_count', flat=True)
    )
    avg = 0 if len(attempt_list) == 0 else mean(attempt_list)
    avg = 0 if n_questions == 0 else avg / n_questions
    ret = {'attempts_mean': 1.0 * avg}

    return ret


def e_student_attempts_median(exercise):
    # users = User.objects.filter(groups__name='Student', is_active=True)
    # users = bonafide_students
    users = bonafide_students.filter(opentauser__courses=exercise.course)
    n_questions = Question.objects.filter(exercise=exercise).count()
    attempt_list = list(
        Aggregation.objects.filter(exercise=exercise, user__in=users).values_list(
            'attempt_count', flat=True
        )
    )
    med = 0 if (sum(attempt_list) == 0 or n_questions == 0) else median(attempt_list) / n_questions
    ret = {'attempts_median': 1.0 * med}
    return ret


def get_all_who_tried(exercise):
    new = Aggregation.objects.filter(exercise=exercise)
    users = bonafide_students.filter(user_from_answers__in=new)
    return users


def e_student_tried(exercise):
    n_students = bonafide_students.filter(opentauser__courses=exercise.course).count()
    n_tried = get_all_who_tried(exercise).count()
    ret = {'ntried': n_tried, 'percent_tried': n_tried / n_students if n_students > 0 else 0}
    return ret


def has_audit_response_waiting(exercise):
    """Get number of audits that has updates."""
    return dict(
        response_awaits=AuditExercise.objects.filter(exercise=exercise, updated=True).count()
    )


def e_student_percent_complete(exercise):
    """Get statistics on completed status.

    Completed means that the student has performed all the required activities
    before the deadline (if there is one)

    Returns:
        dict: containing::

            {
                'percent_complete': Fraction of students that have completed the exercise
                'percent_correct': Fraction of students that have answered questions correctly
                'ncomplete': Number of completed students
                'ncorrect': Number of currect students
                'nstudents': Number of active students
            }

    """

    users = bonafide_students.filter(opentauser__courses=exercise.course)
    n_students = users.count()
    answers = Aggregation.objects.filter(exercise=exercise, user__in=users)
    # TODO FIX THIS TO NOT SCORE WRONG FOR EMPTY QUESITONLIST
    allcorrect_answer = answers.filter(user_is_correct=True, questionlist_is_empty=False)
    # THERE IS AN ISSUE IF STUDENT CAN LEAVE AN INCORRECT
    # ANSWSER IF A PREVIOUS ONE WAS CORRECT
    # NOT ACCORDING TO THIS CODE WHICH IS CONSISTENT WITH OLD
    # SEE AGGREGATION MODEL
    allcomplete = answers.filter(complete_by_deadline=True, questionlist_is_empty=False)
    deadline_date = exercise.deadline()
    deadline_date = exercise.meta.deadline_date  # TODO THIS SHOULD BE THE PREVI

    ret = {
        'percent_complete': allcomplete.count() / n_students if n_students > 0 else 0,
        'percent_correct': allcorrect_answer.count() / n_students if n_students > 0 else 0,
        'ncomplete': allcomplete.count(),
        'ncorrect': allcorrect_answer.count(),
        'nstudents': n_students,
        'deadline': deadline_date,
    }

    return ret


def exercise_list_data(exercise_data_func_list, course):
    exercises = Exercise.objects.filter(course=course)
    result = {}
    for exercise in exercises:

        def reduce_data_func(prev, next_func):
            prev.update(next_func(exercise))
            return prev

        data = reduce(reduce_data_func, exercise_data_func_list, {})
        result[exercise.exercise_key] = data
    return result


def post_process_list(data, data_func_list):
    def reduce_data_func(prev, next_func):
        prev.update(next_func(data))
        return prev

    result = reduce(reduce_data_func, data_func_list, {})
    return result


def get_exercise_render(user, course_pk, exercise_key):
    course = Course.objects.get(pk=course_pk)
    exercise = Exercise.objects.get(exercise_key=exercise_key)
    tz = pytz.timezone('Europe/Stockholm')
    deadline_time = datetime.time(23, 59, 59)
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    sexercise = ExerciseSerializer(exercise)
    render = sexercise.data
    try:
        ag = Aggregation.objects.get(user=user, exercise=exercise)
    except Aggregation.DoesNotExist:
        render['questions'] = {}
        render['force_passed'] = False
        render['correct'] = False
        render['correct_by_deadline'] = False
        render['image_deadline'] = False
        render['image'] = False
        render['force_passed'] = False
        render['revision_needed'] = False
        return render

    student_audits = AuditExercise.objects.filter(student=user, exercise=exercise)
    questions = Question.objects.filter(exercise=exercise)
    render['questions'] = {}
    render['force_passed'] = ag.force_passed
    render['revision_needed'] = ag.audit_needs_attention
    render['audited'] = ag.audit_published
    render['deadline'] = exercise.deadline()
    render['correct_by_deadline'] = ag.correct_by_deadline
    render['image_deadline'] = ag.image_by_deadline
    render['image'] = ag.image_exists
    imageanswers = ImageAnswer.objects.filter(user=user, exercise=exercise).order_by('-date')
    image_answers_serialized = ImageAnswerSerializer(imageanswers, many=True)
    render['imageanswers'] = image_answers_serialized.data

    for question in questions:
        answers_ = Answer.objects.filter(user=user, question=question)
        render['questions'][question.question_key] = {}
        answers = AnswerSerializer(answers_, many=True)
        render['questions'][question.question_key]['answers'] = answers.data
    render['correct'] = ag.user_is_correct
    render['tries'] = ag.attempt_count
    return render


def serialize_exercise_with_question_data(exercise, user, hijacked):
    """
    Serialize an exercise together with question and image answer data for the specified user.

    Args:
        exercise: Exercise instance (Django ORM)
        user: User instance (Django ORM)

    Returns:
        Dictionary corresponding to a JSON representation of the exercise together with user data.

    """
    #assert exercise.meta.published, "EXERCISE IS NOT PUBLISHED"
    course = exercise.course
    (cache, cachekey) = get_cache_and_key(
        "serialized_exercise_with_question_data:", exercise.exercise_key, user.pk, course.id
    )
    if cache.has_key(cachekey):
        return cache.get(cachekey)
    exercise_render = get_exercise_render(user, course.id, exercise.exercise_key)
    questions = Question.objects.filter(exercise=exercise)
    try:
        ag = Aggregation.objects.get(user=user, exercise=exercise)
        tried_all = ag.user_tried_all
        audit_published = ag.audit_published
        audit_needs_attention = ag.audit_needs_attention
        correct = ag.user_is_correct
    except:
        tried_all = False
        audit_published = False
        audit_needs_attention = False
        correct = False
    serializer = ExerciseSerializer(exercise)
    data = serializer.data
    data['exercise_render'] = exercise_render
    duedate = exercise.deadline()
    if duedate:
        data['due_datetime'] = (duedate).strftime("%Y-%m-%d at %H:%M:%S")
    else:
        data['due_datetime'] = 'no duedate'
    data['correct'] = correct
    data['question'] = {}
    data['tried_all'] = tried_all
    data['audit_published'] = audit_published
    try:
        data['response_awaits'] = audit_needs_attention
    except:
        data['response_awaits'] = False
    try:
        data['failed_audit'] = audit_needs_attention and audit_published
    except:
        data['failed_audit'] = False
    if not exercise.meta.feedback and (not settings.IGNORE_NO_FEEDBACK) and hijacked:
        data['correct'] = None
    student_audits = AuditExercise.objects.filter(student=user, exercise=exercise)
    force_passed = student_audits[0].force_passed if student_audits else False
    image_answers = ImageAnswer.objects.filter(user=user, exercise=exercise)
    image_answers_serialized = ImageAnswerSerializer(image_answers, many=True)
    image_answers_ids = [image_answer.pk for image_answer in image_answers]
    data['image_answers'] = image_answers_ids
    data['image_answers_data'] = image_answers_serialized.data
    try:
        audit = AuditExercise.objects.get(student=user, exercise=exercise)
        saudit = AuditExerciseSerializer(audit)
        data['audit'] = saudit.data
    except AuditExercise.DoesNotExist:
        pass

    for question in questions:
        try:
            dbanswer = Answer.objects.filter(user=user, question=question).latest('date')
            serializer = AnswerSerializer(dbanswer)
            response = json.loads(dbanswer.grader_response)
            data['question'][question.question_key] = serializer.data
            data['question'][question.question_key]['response'] = response
            if not exercise.meta.feedback:
                data['question'][question.question_key]['correct'] = None
                data['question'][question.question_key]['response']['correct'] = None
        except ObjectDoesNotExist as e:
            pass

        except json.decoder.JSONDecodeError:
            pass
        except Exception as e:
            logger.error("EXCEPTION DBANSWER IN MODELHELPERS = ", e.__class__.__name__, str(e))
            pass
    try:
        data['manually_passed'] = force_passed
        data['correct'] = correct
        data['all_complete'] = ag.all_complete or force_passed
        data['complete_by_deadline'] = ag.complete_by_deadline
        data['image_by_deadline'] = ag.image_by_deadline  ###### TODO
        data['image_deadline'] = data['image_by_deadline']  ###### TODO
        data['image'] = ag.image_exists  ###### TODO LEGACY KEY
        # FOR COMPATIBILITY MAKE image_deadline and correct_deadline
        # identity with ..._by_deadline
        data['correct_by_deadline'] = ag.correct_by_deadline or force_passed  #### TODO
        data['correct_deadline'] = ag.correct_by_deadline or force_passed  #### TODO  LEGACY KEY
        data['tried_all'] = ag.user_tried_all
        data['show_check'] = not ag.questionlist_is_empty
        data['answer_deltat'] = getdatestring(duedate, ag.answer_date)
        data['image_deltat'] = getdatestring(duedate, ag.image_date)
        data['date_complete'] = (ag.date_complete).strftime("%Y-%m-%d at %H:%M")
        data['questions_exist'] = not ag.questionlist_is_empty
        data['passed'] = data['complete_by_deadline'] or force_passed
    except:
        data['correct'] = False
        data['passed'] = False
        data['all_complete'] = False
        data['complete_by_deadline'] = False
        data['image_by_deadline'] = False
        data['correct_by_deadline'] = False
        data['tried_all'] = False
        data['show_check'] = False
        data['questions_exist'] = True
    cache.set(cachekey, data, settings.CACHE_LIFETIME)
    return data


def getdatestring(duedate, submitdate):
    if duedate and submitdate:
        diff = int(duedate.strftime("%s")) - int(submitdate.strftime("%s"))
        suff = ' early' if diff > 0 else ' late'
        diff = diff if diff > 0 else -1 * diff
        if diff < 60:
            sdiff = "{} sec".format(diff)
        elif diff < 3600:
            sdiff = "{} min".format(int(diff / 60))
        elif diff < 2 * 86400:
            hours = int(diff / 3600)
            minutes = int((diff - 3600 * hours) / 60)
            sdiff = "{0} hours {1} min".format(hours, minutes)
        else:
            sdiff = "{} days ".format(int(diff / (86400)))
        return sdiff + suff
    elif duedate:
        return " missing"
    else:
        return " no deadline"


def exercise_test(exercise_key):
    requests = RequestFactory()
    request = requests.get('/test')
    dbexercise = Exercise.objects.get(exercise_key=exercise_key)
    dbquestions = Question.objects.filter(exercise=dbexercise)
    xmltree = exercise_xmltree(dbexercise.get_full_path())
    user = User.objects.get(username='tester')
    results = []
    for dbquestion in dbquestions:
        if dbquestion.type in ['compareNumeric', 'linearAlgebra']:
            question_key = dbquestion.question_key
            question_xml = question_xmltree_get(xmltree, question_key)
            answer_element = question_xml.find('expression')
            if answer_element is not None:
                answer = answer_element.text.split(';')[0]
                result = {}
                try:
                    result = question_check(
                        request, user, "tester", exercise_key, question_key, answer
                    )
                except Exception as e:
                    result['exception'] = str(e)
                result.update({'answer': answer})
                results.append(result)
    return results


def duration_to_string(sec):
    days = int(sec / (3600 * 24.0))
    hours = int((sec - 3600.0 * 24.0 * days) / 3600.0)
    minutes = int((sec - 3600.0 * 24 * days - 3600.0 * hours) / 60.0)
    str_ = ''
    if days > 0:
        str_ = str_ + str(days) + ' days'
    if hours > 0:
        str_ = str_ + ' ' + str(hours) + ' hours'
    if minutes > 0:
        str_ = str_ + ' ' + str(minutes) + ' minutes'
    return str_


def enrollment(user):
    try:
        courses = [sw.pk for sw in user.opentauser.courses.all()]
    except:
        courses = []
    return courses
