# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from django.core.exceptions import ObjectDoesNotExist
import base64
from exercises.question import (
    get_combined_usermacros,
    get_usermacros,
)
from django.core.exceptions import ObjectDoesNotExist
import os
import logging
from course.models import Course, pytztimezone
from exercises.parsing import exercise_xmltree, question_xmltree_get
from exercises.question import question_check
from django.contrib.auth.models import User
from exercises.serializers import ExerciseSerializer, AnswerSerializer
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
from aggregation.models import Aggregation, get_cache_and_key
from dateutil.relativedelta import relativedelta, MO
from statistics import median, mean
from django.core.cache import caches
from random import randrange
from django.db.models import Count, DateTimeField
from django.db.models.functions import Trunc


logger = logging.getLogger(__name__)


bonafide_students = (
    User.objects.filter(groups__name="Student", is_active=True)
    .exclude(groups__name="View")
    .exclude(groups__name="Admin")
    .exclude(groups__name="Author")
    .exclude(username="student")
)

def set_selectedExercisesKeys( user,db, selectedExercisesKeys ) :
    print(f"get_selectedExerciseKeys")
    cachekey = user.username + db + 'selectedExercises'
    caches['default'].set( cachekey ,selectedExercisesKeys )
    return selectedExercisesKeys

def get_selectedExercisesKeys( user,db ) :
    print(f"get_selectedExerciseKeys")
    cachekey = user.username + db + 'selectedExercises'
    selectedExercisesKeys = caches['default'].get( cachekey ,[])
    print(f"get_selectedExercisesKeys {selectedExercisesKeys}")
    return selectedExercisesKeys



def e_name(exercise):
    return {"name": exercise.name}


def e_path(exercise):
    return {"path": exercise.path}


def e_student_attempt_count(exercise):
    db = exercise.db()
    attempt_list = list(
        Aggregation.objects.using(db).filter(exercise=exercise, user__in=bonafide_students).values_list(
            "attempt_count", flat=True
        )
    )
    attempts = sum(attempt_list)
    return {"attempts": attempts}


def e_student_activity(exercise):
    # return {
    #    'activity': {'1h': 0 , '24h': 0, '1w': 0 , 'all': 0}
    # }
    course = exercise.course
    coursePk = course.course_key
    subdomain = course.opentasite
    db = exercise.db();
    (cache, cachekey) = get_cache_and_key(
        "e_student_activity:", coursePk=coursePk, exercise_key=exercise.exercise_key, subdomain=subdomain
    )
    if settings.DO_CACHE and settings.USE_RESULTS_CACHE:
        if cache.has_key(cachekey):
            return cache.get(cachekey)
    t1h = timezone.now() - datetime.timedelta(hours=1)
    t24h = timezone.now() - datetime.timedelta(hours=24)
    t1w = timezone.now() - datetime.timedelta(days=7)
    n_questions = exercise.question.all().count()
    if n_questions == 0:
        return {"activity": {"1h": 0, "24h": 0, "1w": 0, "all": 0}}
    answers = Answer.objects.using(db).filter(question__exercise=exercise, user__groups__name="Student")
    # binfo = answers.annotate(trunctime=Trunc('date','min',output_field=DateTimeField() ) ) \
    ##    .values('trunctime') \
    #    .annotate(bins=Count('id') ) \
    #    .order_by('-trunctime') \
    #    .values('trunctime','bins')
    # fmt = '%Y-%m-%d:%H'
    # minnow = datetime.datetime.now().timestamp()
    # binny = [ { int( (  minnow -  item['trunctime'].timestamp()  )/60)  : item['bins'] }  for item in binfo]
    # print(f"EXERCISE = {exercise}")
    # print(f"binny={binny}")
    # print(f"binfo = {binfo}")

    activity_all = round(answers.count() / n_questions)
    answers = answers.filter(date__gt=t1w)
    activity_1w = round(answers.count() / n_questions)
    answers = answers.filter(date__gt=t24h)
    activity_24h = round(answers.count() / n_questions)
    answers = answers.filter(date__gt=t1h)
    activity_1h = round(answers.count() / n_questions)
    activity = {"activity": {"1h": activity_1h, "24h": activity_24h, "1w": activity_1w, "all": activity_all}}
    dt = float(settings.STATISTICS_CACHE_TIMEOUT)
    tc = dt / 2.0 + randrange(round(dt / 2.0))
    cache.set(cachekey, activity, tc)
    return activity


def p_student_activity(data):
    # print("P_STUDENT_ACTIVITY")
    try:
        max_1h = max(data.values(), key=lambda exercise: exercise["activity"]["1h"])
        max_24h = max(data.values(), key=lambda exercise: exercise["activity"]["24h"])
        max_1w = max(data.values(), key=lambda exercise: exercise["activity"]["1w"])
        max_all = max(data.values(), key=lambda exercise: exercise["activity"]["all"])
    except ValueError:
        return {"max_1h": 0, "max_24h": 0, "max_1w": 0, "max_all": 0}
    return {
        "max_1h": max_1h["activity"]["1h"],
        "max_24h": max_24h["activity"]["24h"],
        "max_1w": max_1w["activity"]["1w"],
        "max_all": max_all["activity"]["all"],
    }


def e_student_attempts_mean(exercise):
    db = exercise.db();
    users = bonafide_students
    users = bonafide_students.filter(opentauser__courses=exercise.course)
    n_questions = Question.objects.using(db).filter(exercise=exercise).count()

    attempt_list = list(
        Aggregation.objects.using(db).filter(exercise=exercise, user__in=users)
        .filter(Q(attempt_count__gt=0))
        .values_list("attempt_count", flat=True)
    )
    avg = 0 if len(attempt_list) == 0 else mean(attempt_list)
    avg = 0 if n_questions == 0 else avg / n_questions
    ret = {"attempts_mean": 1.0 * avg}

    return ret


def e_student_attempts_median(exercise):
    # users = User.objects.filter(groups__name='Student', is_active=True)
    # users = bonafide_students
    db = exercise.course.opentasite
    users = bonafide_students.filter(opentauser__courses=exercise.course)
    n_questions = Question.objects.using(db).filter(exercise=exercise).count()
    attempt_list = list(
        Aggregation.objects.using(db).filter(exercise=exercise, user__in=users).values_list("attempt_count", flat=True)
    )
    med = 0 if (sum(attempt_list) == 0 or n_questions == 0) else median(attempt_list) / n_questions
    ret = {"attempts_median": 1.0 * med}
    return ret


def get_all_who_tried(exercise):
    db = exercise.db();
    new = Aggregation.objects.using(db).filter(exercise=exercise)
    users = bonafide_students.filter(user_from_answers__in=new)
    return users

def get_all_who_passed(exercise):
    db = exercise.db()
    new = Aggregation.objects.using(db).filter(exercise=exercise, all_complete=True)
    users = bonafide_students.filter(user_from_answers__in=new)
    return users



def e_student_tried(exercise):
    n_students = bonafide_students.filter(opentauser__courses=exercise.course).count()
    n_tried = get_all_who_tried(exercise).count()
    ret = {"ntried": n_tried, "percent_tried": n_tried / n_students if n_students > 0 else 0}
    return ret


def has_audit_response_waiting(exercise):
    """Get number of audits that has updates."""
    db = exercise.db()
    return dict(response_awaits=AuditExercise.objects.using(db).filter(exercise=exercise, updated=True).count())


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

    db = exercise.db()
    users = bonafide_students.filter(opentauser__courses=exercise.course)
    n_students = users.count()
    answers = Aggregation.objects.using(db).filter(exercise=exercise, user__in=users)
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
        "percent_complete": allcomplete.count() / n_students if n_students > 0 else 0,
        "percent_correct": allcorrect_answer.count() / n_students if n_students > 0 else 0,
        "ncomplete": allcomplete.count(),
        "ncorrect": allcorrect_answer.count(),
        "nstudents": n_students,
        "deadline": deadline_date,
    }

    return ret


def exercise_list_data(exercise_data_func_list, course):
    db = course.opentasite
    exercises = Exercise.objects.using(db).filter(course=course)
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


def get_exercise_render(user, course_pk, exercise, db=None):
    # print("GET_EXERCISE_RENDER")
    #assert db != None, "GET_EXERCISE_RENDER DB=None"
    # print(f"GET_EXERCISE_RENDER DB = {db}, user={user} type={type(exercise)} exercise={exercise} ")
    try:
        course = exercise.course
        if db == None :
            db = course.opentasite
    except ObjectDoesNotExist as e:
        logger.error(f"ERROR 92831 {type(e).__name__} in get_exercise_render  exercise={exercise} DOES NOT EXIST")
        return {}
    # course = Course.objects.using(db).get(pk=course_pk)
    tz = pytztimezone(settings.TIME_ZONE)
    deadline_time = datetime.time(23, 59, 59)
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    sexercise = ExerciseSerializer(exercise)
    render = sexercise.data
    questionlist_is_empty = exercise.questionlist_is_empty()
    ags = Aggregation.objects.using(db).filter(user=user, exercise=exercise)
    if len(ags) == 0:
        # CODE FOR AN EXERCISE THAT HAS NOT BEEN ATTEMPTED
        # print(f"GET_EXERCISE_RENDER AG NOT FOUND db={db} user={user} exercise={exercise} ")
        render["questions"] = {}
        render["force_passed"] = False
        render["correct"] = False
        render["correct_by_deadline"] = False
        render["image_deadline"] = False
        render["image"] = False
        render["force_passed"] = False
        render["revision_needed"] = False
        render["points"] = ""
        return render
    else:
        ag = ags[0]
    student_audits = AuditExercise.objects.using(db).filter(student=user, exercise=exercise)
    questions = Question.objects.using(db).filter(exercise=exercise)
    render["questions"] = {}
    render["force_passed"] = ag.force_passed
    render["revision_needed"] = ag.audit_needs_attention
    render["audited"] = ag.audit_published
    render["deadline"] = exercise.deadline()
    render["correct_by_deadline"] = ag.correct_by_deadline
    render["image_deadline"] = ag.image_by_deadline
    render["image"] = ag.image_exists
    render['questionlist_is_empty'] = questionlist_is_empty
    logger.info(f"Q1 {questionlist_is_empty}")
    imageanswers = ImageAnswer.objects.using(db).filter(user=user, exercise=exercise).order_by("-date")
    image_answers_serialized = ImageAnswerSerializer(imageanswers, many=True)
    render["imageanswers"] = image_answers_serialized.data

    for question in questions:
        answers_ = Answer.objects.using(db).filter(user=user, question=question)
        render["questions"][question.question_key] = {}
        answers = AnswerSerializer(answers_, many=True)
        render["questions"][question.question_key]["answers"] = answers.data
    render["correct"] = ag.user_is_correct
    render["tries"] = ag.attempt_count
    render["points"] = ag.points or ag.correct_by_deadline
    render["questionlist_is_empty"] = questionlist_is_empty
    logger.info(f'Q2 {render["questionlist_is_empty"]}')
    return render


def serialize_exercise_with_question_data(exercise, user, hijacked, db=None):
    #print("SERIALIZE_EXERCISE_WITH_QUESTION_DATA")
    #assert db != None, "SERIALIZE_EXERCISE... DB=None"
    """
    Serialize an exercise together with question and image answer data for the specified user.

    Args:
        exercise: Exercise instance (Django ORM)
        user: User instance (Django ORM)

    Returns:
        Dictionary corresponding to a JSON representation of the exercise together with user data.

    """
    # assert exercise.meta.published, "EXERCISE IS NOT PUBLISHED"
    course = exercise.course
    subdomain = db
    subdomain = course.opentasite
    if db == None :
        subdomain = course.opentasite
        db = subdomain 
    if False and settings.DO_CACHE and settings.USE_RESULTS_CACHE:
        (cache, cachekey) = settings.USE_RESULTS_CACHE and get_cache_and_key(
            "serialized_exercise_with_question_data:",
            exercise.exercise_key,
            user.pk,
            course.course_key,
            subdomain=subdomain,
        )
        if cache.has_key(cachekey):
            return cache.get(cachekey)
    #print(f"AA")
    exercise_render = get_exercise_render(user, course.id, exercise, db=db)
    if not exercise_render:
        return {}
    questions = Question.objects.using(db).filter(exercise=exercise)
    questionlist_is_empty = exercise.questionlist_is_empty();
    try:
        ag = Aggregation.objects.using(db).get(user=user, exercise=exercise)
        logger.info(f"AGGREAGATION_LIST_IS_EMPTY   {ag.questionlist_is_empty}")
        tried_all = ag.user_tried_all
        audit_published = ag.audit_published
        audit_needs_attention = ag.audit_needs_attention
        correct = ag.user_is_correct
        points = ag.points
        #questionlist_is_empty = ag.questionlist_is_empty
    except Aggregation.DoesNotExist:
        logger.info("AG DOES NOT EXIST")
        tried_all = False
        audit_published = False
        audit_needs_attention = False
        correct = False
    #print(f"BB")
    serializer = ExerciseSerializer(exercise)
    data = serializer.data
    data["exercise_render"] = exercise_render
    duedate = exercise.deadline()
    if duedate:
        data["due_datetime"] = (duedate).strftime("%Y-%m-%d at %H:%M:%S")
    else:
        data["due_datetime"] = "no duedate"
    data["correct"] = correct
    data["question"] = {}
    data["tried_all"] = tried_all
    data["audit_published"] = audit_published
    data["questionlist_is_empty"] = questionlist_is_empty
    logger.info(f"Q4 {questionlist_is_empty}")
    try:
        data["response_awaits"] = audit_needs_attention
    except:
        data["response_awaits"] = False
    try:
        data["failed_audit"] = audit_needs_attention and audit_published
    except:
        data["failed_audit"] = False
    try:
        if not exercise.meta.feedback and (not settings.IGNORE_NO_FEEDBACK) and hijacked:
            data["correct"] = None
    except ObjectDoesNotExist:  # error on openta legacy database
        pass
    #print(f"CC")
    student_audits = AuditExercise.objects.using(db).filter(student=user, exercise=exercise)
    force_passed = student_audits[0].force_passed if student_audits else False
    image_answers = ImageAnswer.objects.using(db).filter(user=user, exercise=exercise)
    image_answers_serialized = ImageAnswerSerializer(image_answers, many=True)
    image_answers_ids = [image_answer.pk for image_answer in image_answers]
    data["image_answers"] = image_answers_ids
    data["image_answers_data"] = image_answers_serialized.data
    try:
        audit = AuditExercise.objects.using(db).get(student=user, exercise=exercise)
        saudit = AuditExerciseSerializer(audit)
        data["audit"] = saudit.data
    except AuditExercise.DoesNotExist:
        pass
    #print(f"DD")
    usermacros = get_usermacros(user, exercise.exercise_key, db=db)
    #print( f"USERMACROS = {usermacros}")
    full_asset_path = usermacros["@exerciseassetpath"];
    studentAssetPath = usermacros["@studentassetpath"];
    #print( f"STUDENTASSETPATH = {studentAssetPath}");
    #print( f"FULL_ASSET_PATH = {full_asset_path}")
    exercise_seed = usermacros["@exerciseseed"];
    #print( f"SEED = {exercise_seed}")
    #print( f"is_admin= {user.is_staff}")
    try :
        index_exists = os.path.exists(os.path.join(studentAssetPath, "index.html"))
    except :
        index_exists = False
    #print( f"INEXE EXISTS = {index_exists}")
    http_protocol = settings.HTTP_PROTOCOL ; #  'http' ; # settings.HTTP_PROTCOL;
    server = settings.OPENTA_SERVER;
    port =  settings.HTTP_SERVER_PORT;
    outputFormat = 'single'
    try :
        if user.is_staff :
            outputFormat = 'simple'
        if exercise.meta.solution:
            outputFormat = 'simple'
    except ObjectDoesNotExist as e :
        outputFormat = 'simple'
    for question in questions:
        data["question"][question.question_key]  = {}
        decoded_identifier = f"{subdomain}:{course.course_key}:{user.pk}:{exercise.exercise_key}:{question.question_key}:{exercise_seed}" 
        decoded_identifier = f"{http_protocol}:{subdomain}:{server}:{port}:{course.course_key}:{user.pk}:{exercise.exercise_key}:{question.question_key}:{exercise_seed}:{outputFormat}" 
        encoded_identifier = base64.b64encode( decoded_identifier.encode()  );
        #print(f"MODELHELPER IDENTIFIER = {decoded_identifier}")
        identifier = encoded_identifier.decode() 
        if settings.DO_CACHE :
            icache = caches['default']
            icache.set(identifier, decoded_identifier);
            #print(f"CHECK {icache.get(identifier)}={decoded_identifier} ")
        else :
            pass
            #print(f" DO NOT CACHE ");
        try:
            #print("D1")
            dbanswer = Answer.objects.using(db).filter(user=user, question=question).latest("date")
            #print("D2");
            serializer = AnswerSerializer(dbanswer)
            #print("D3")
            try :
                response = json.loads(dbanswer.grader_response)
            except Exception as e :
                response = {"correct": True }
            #print("D4")
            #print(f"SERIALIAZXER = {serializer.data}")
            data["question"][question.question_key] = serializer.data
            data["question"][question.question_key]["response"] = response
            data["question"][question.question_key]["assetpath"] = full_asset_path
            data["question"][question.question_key]["studentAssetPath"] = studentAssetPath
            data["question"][question.question_key]["seed"] = exercise_seed
            data["question"][question.question_key]["identifier"] = identifier
            data["question"][question.question_key]["indexExists"] = index_exists
            data["question"][question.question_key]["outputFormat"] = outputFormat
            #if not exercise.meta.feedback:
            #    data["question"][question.question_key]["correct"] = None
            #    data["question"][question.question_key]["response"]["correct"] = None
        except ObjectDoesNotExist as e:
            data["question"][question.question_key]["studentAssetPath"] = studentAssetPath
            data["question"][question.question_key]["assetpath"] = full_asset_path
            data["question"][question.question_key]["seed"] = exercise_seed
            data["question"][question.question_key]["identifier"] = identifier
            data["question"][question.question_key]["indexExists"] = index_exists
            data["question"][question.question_key]["outputFormat"] = outputFormat
            pass

        except json.decoder.JSONDecodeError:
            pass
        except Exception as e:
            logger.error("EXCEPTION DBANSWER IN MODELHELPERS = ", e.__class__.__name__, str(e))
            pass
    try:
        tz = pytztimezone(settings.TIME_ZONE)
        data["manually_passed"] = force_passed
        data["correct"] = correct
        data["all_complete"] = ag.all_complete or force_passed
        data["complete_by_deadline"] = ag.complete_by_deadline
        data["image_by_deadline"] = ag.image_by_deadline  ###### TODO
        data["image_deadline"] = data["image_by_deadline"]  ###### TODO
        data["image"] = ag.image_exists  ###### TODO LEGACY KEY
        # FOR COMPATIBILITY MAKE image_deadline and correct_deadline
        # identity with ..._by_deadline
        data["correct_by_deadline"] = ag.correct_by_deadline or force_passed  #### TODO
        data["correct_deadline"] = ag.correct_by_deadline or force_passed  #### TODO  LEGACY KEY
        data["tried_all"] = ag.user_tried_all
        data["show_check"] = not questionlist_is_empty
        data["answer_deltat"] = getdatestring(duedate, ag.answer_date)
        data["image_deltat"] = getdatestring(duedate, ag.image_date)
        corrected = (ag.date_complete).astimezone(tz)
        data["date_complete"] = corrected.strftime("%Y-%m-%d at %H:%M")
        data["questions_exist"] = not questionlist_is_empty
        data["questionlist_is_empty"] = questionlist_is_empty
        data["passed"] = data["complete_by_deadline"] or force_passed
        data["points"] = ag.points or data["passed"]
    except:
        data["correct"] = False
        data["passed"] = False
        data["all_complete"] = False
        data["complete_by_deadline"] = False
        data["image_by_deadline"] = False
        data["correct_by_deadline"] = False
        data["tried_all"] = False
        data["show_check"] = False
        data["questions_exist"] = True
        data["questionlist_is_empty"] = questionlist_is_empty
        data["points"] = ""
    q = data.keys()
    name = data['name']
    data['questionlist_is_empty'] =  questionlist_is_empty
    empty = data['questionlist_is_empty']
    logger.info(f"SERIALIZWE_EXERCISE_WITH_QUESTION_DATA {name} QUESTIONLIST_IS_EMPTY {empty}")
    if False and settings.DO_CACHE and settings.USE_RESULTS_CACHE:
        cache.set(cachekey, data, settings.SERIALIZE_EXERCISE_DATA_FOR_COURSE_TIMEOUT)
    return data


def getdatestring(duedate, submitdate):
    tz = pytztimezone(settings.TIME_ZONE)
    if duedate and submitdate:
        tz_corrected_submitdate = submitdate.astimezone(tz)
        submitdate = tz_corrected_submitdate
        diff = int(duedate.strftime("%s")) - int(submitdate.strftime("%s"))
        suff = " early" if diff > 0 else " late"
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
    request = requests.get("/test")
    dbexercise = Exercise.objects.get(exercise_key=exercise_key)
    dbquestions = Question.objects.filter(exercise=dbexercise)
    xmltree = exercise_xmltree(dbexercise.get_full_path())
    user = User.objects.get(username="tester")
    results = []
    for dbquestion in dbquestions:
        if dbquestion.type in ["compareNumeric", "linearAlgebra"]:
            question_key = dbquestion.question_key
            question_xml = question_xmltree_get(xmltree, question_key)
            answer_element = question_xml.find("expression")
            if answer_element is not None:
                answer = answer_element.text.split(";")[0]
                result = {}
                try:
                    result = question_check(request, user, "tester", exercise_key, question_key, answer)
                except Exception as e:
                    result["exception"] = str(e)
                result.update({"answer": answer})
                results.append(result)
    return results


def get_passed_exercises(exercise_queryset, user):
    """Get exercises with correct answer by user.

    Args:
        exercise_queryset (django queryset): Exercises to be checked
        user (django user): User to check for
    Returns:
    (list of dict): List with dictionaries containing the structure
        {
            'exercise_name': ...
            'exercise_key': ...
            'deadline': ...
        }
    """
    questions = Question.objects.filter(exercise__in=exercise_queryset)
    passed_questions_pk_list = questions.filter(answer__user=user, answer__correct=True).values_list("pk", flat=True)

    failed_questions = questions.exclude(pk__in=passed_questions_pk_list)
    failed_exercises_pk_list = failed_questions.values_list("exercise__pk", flat=True)
    passed_exercises = exercise_queryset.exclude(pk__in=failed_exercises_pk_list).select_related("meta")
    passed_rendered = []
    for passed in passed_exercises:
        passed_rendered.append(
            {
                "exercise_name": passed.name,
                "exercise_key": passed.exercise_key,
                "deadline": passed.meta.deadline_date,
            }
        )
    return passed_rendered


def get_passed_exercises_with_image_data(
    exercise_queryset, user, deadline=True, image_deadline=True, require_image=True
):
    """
    Generate data containing which exercises from the queryset that user have
    passed and uploaded image for before the deadline.

    Args:
        user: Django User instance
        exercise_queryset: The exercises to be tested

    Returns:
        List
        [
            {
                'exercise_name':
                'answers': [
                    {
                        'answer':
                        'date':
                    }
                    ]
                'deadline':
            }
        ]

    """
    if not exercise_queryset:
        return []

    extra_question_filters = []
    courses = set()
    for exercise in exercise_queryset:
        courses.add(exercise.course.pk)

    if len(courses) > 1:
        raise Exception("Exercises must come from same course")

    deadline_hour = exercise_queryset.first().course.get_deadline_time().hour

    if deadline:
        extra_question_filters.append(
            Q(answer__date__date__lt=F("exercise__meta__deadline_date"))
            | (Q(answer__date__date=F("exercise__meta__deadline_date")) & Q(answer__date__hour__lte=deadline_hour))
        )
    if image_deadline:
        extra_question_filters.append(
            Q(exercise__imageanswer__date__date__lt=F("exercise__meta__deadline_date"))
            | (
                Q(exercise__imageanswer__date__date=F("exercise__meta__deadline_date"))
                & Q(exercise__imageanswer__date__hour__lte=deadline_hour)
            )
        )

    if require_image:
        extra_question_filters.append(Q(exercise__imageanswer__user=user))

    questions = Question.objects.filter(exercise__in=exercise_queryset)
    passed_questions_pk_list = questions.filter(
        answer__user=user, answer__correct=True, *extra_question_filters
    ).values_list("pk", flat=True)

    failed_questions = questions.exclude(pk__in=passed_questions_pk_list)
    failed_exercises_pk_list = failed_questions.values_list("exercise__pk", flat=True)
    failed_by_audit = exercise_queryset.filter(
        audits__student=user, audits__published=True, audits__revision_needed=True
    )
    failed_by_audit_pk_list = failed_by_audit.values_list("pk", flat=True)
    all_failed_pk_list = list(set(failed_by_audit_pk_list) | set(failed_exercises_pk_list))

    passed_exercises = exercise_queryset.exclude(pk__in=all_failed_pk_list).select_related("meta")
    force_passed_exercises = exercise_queryset.filter(
        pk__in=(AuditExercise.objects.get_force_passed_exercises_pk(user))
    )
    total_passed = passed_exercises | force_passed_exercises
    total_passed = total_passed.distinct()
    passed_rendered = []
    for passed in total_passed:
        passed_rendered.append(
            {
                "exercise_name": passed.name,
                "exercise_key": passed.exercise_key,
                "deadline": passed.meta.deadline_date,
            }
        )
    return passed_rendered


def duration_to_string(sec):
    days = int(sec / (3600 * 24.0))
    hours = int((sec - 3600.0 * 24.0 * days) / 3600.0)
    minutes = int((sec - 3600.0 * 24 * days - 3600.0 * hours) / 60.0)
    str_ = ""
    if days > 0:
        str_ = str_ + str(days) + " days"
    if hours > 0:
        str_ = str_ + " " + str(hours) + " hours"
    if minutes > 0:
        str_ = str_ + " " + str(minutes) + " minutes"
    return str_


def enrollment(user):
    try:
        courses = [sw.pk for sw in user.opentauser.courses.all()]
    except:
        courses = []
    return courses
