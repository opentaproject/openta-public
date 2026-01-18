# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import hashlib
import os, glob
from datetime import timedelta
import datetime
import traceback
from backend.middleware import verify_or_create_database_connection, connection_number



import time
import subprocess

import exercises
from course.models import Course
from exercises.models import Exercise
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
import logging

logger = logging.getLogger(__name__)


from exercises.models import answer_received, exercise_saved, exercise_options_saved
from exercises.parsing import exercise_xml
from translations.models import TranslationThread
from utils import touch_


def hshkey(txt):
    txt = (" ".join(txt.split())).strip()
    return (hashlib.md5(txt.encode()).hexdigest())[0:7]


def t_cache_and_key(course, exercise):
    txt = "%s%s" % (course.course_key, exercise.exercise_key)
    cache = caches["translations"]
    cachekey = (hashlib.md5(txt.encode()).hexdigest())[0:7]
    return (cache, cachekey)


def handle_new_answer_available(sender, **kwargs):
    kw = f"{kwargs}".replace('\n',' ')
    logger.error(f"HANDLE_NEW_ANSWER AVAILABLE {settings.GIT_HASH} {kw} ")
    tb = ''
    try :
        course = kwargs['course']
        exercise = kwargs['exercise']
        db = kwargs['db']
        if isinstance(db, tuple):
            db = db[0];
        user = kwargs['user']
        username  = kwargs['username']
        userpk = None if user == None else user.pk
        logger.info(f"HANDLE {course.pk} {userpk} {exercise}")
        src = kwargs['src']
        subdomain = kwargs['subdomain']
        verify_or_create_database_connection(subdomain)
        if not settings.RUNTESTS :
            cn = connection_number( subdomain)
            logger.info(f" HANDLE TOTAL_CONNECTIONS  = {cn}")
        if not username == None :
            username_ = username.encode('ascii','ignore').decode('ascii')
        else :
            username_ = None
        key = f"temp-{username_}";
        caches['default'].set(username_,subdomain,300)
        date = kwargs['date']
        exercise_key = exercise.exercise_key

        path = "/subdomain-data/aggregations/"
        if not settings.RUNTESTS :
            host = settings.OPENTA_SERVER
            pathbak = os.path.join(path, f"bak/{host}")
            os.makedirs(path, exist_ok=True)
            os.makedirs(pathbak, exist_ok=True)
            filepath =  os.path.join(path,       f"{subdomain}:{userpk}:{str(exercise_key)}")
            filepathbak =  os.path.join(pathbak, f"{subdomain}:{userpk}:{str(exercise_key)}")
            with open(filepath,"w") as fp : 
                fp.write(f"{subdomain} {userpk} {str(exercise_key)} {src} {username} \n")
        course_key = course.course_key
        touch_(db)
        if not user  == None :
            if user.is_staff or user.is_superuser:
                touchfile = "last_admin_activity"
            else:
                touchfile = "last_student_activity"
        else :
            touchfile = "last_student_activity"
        fname = os.path.join(settings.VOLUME, subdomain, touchfile)
        if not settings.RUNTESTS :
            os.utime( os.path.join( settings.VOLUME, subdomain),None)
            if os.path.exists(fname):
                os.utime(fname, None)
            else:
                dname = os.path.join(settings.VOLUME, subdomain)
                if os.path.exists(dname):
                    open(fname, "a").close()
    
    

    
        if settings.RUNTESTS:
            subdomain = settings.SUBDOMAIN
            db = settings.DB_NAME
        (cache, cachekey) = get_cache_and_key(
            "exercise_data_for_course:", coursePk=course_key, exercise_key=exercise_key, subdomain=subdomain
        )
        if cache:
            cache.delete(cachekey)
        if user == None and not exercise == None :
            aggregationentries = Aggregation.objects.using(db).filter(exercise=exercise)
            for ag in aggregationentries:
                ag.save(using=db)
                studentuser = ag.user
                for prefix in [
                    "safe_user_cache:",
                    "unsafe_user_cache:",
                    "calculate_unsafe_user_summary:",
                    "get_unsafe_exercise_summary:",
                ]:
                    (cache, cachekey) = get_cache_and_key(
                        prefix, userPk=str(studentuser.pk), coursePk=course_key, subdomain=subdomain
                    )
                    cache.delete(cachekey)
        else:
            for prefix in [
                "user_exercise_json:",
                "safe_user_cache:",
                "unsafe_user_cache:",
                "calculate_unsafe_user_summary:",
                "get_unsafe_exercise_summary:",
            ]:
                (cache, cachekey) = get_cache_and_key(
                    prefix, userPk=userpk, coursePk=course_key, subdomain=subdomain
                )
                cache.delete(cachekey)
            for prefix in ["serialized_exercise_with_question_data:"]:
                (cache, cachekey) = get_cache_and_key(
                    prefix,
                    exercise_key=exercise_key,
                    userPk=userpk,
                    coursePk=course_key,
                    subdomain=subdomain,
                )
                cache.delete(cachekey)
            userPk = userpk
            coursePk = course_key
            #subdomain = course.opentasite
    
            kwargs["date"]
            if not user == None and not  exercise_key == None :
                try :
                    logger.info(f" UPDATE AGGREGATION UPDATE_OR_CREATE USERNAME={username} EXERCISE_KEY={exercise_key} DB={db}")
                    ss = 'a'
                    dbuser = User.objects.using(db).get(pk=userpk)
                    ss = ss + 'b'
                    dbexercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
                    ss = ss + 'c'
                    gbs  =  Aggregation.objects.using(db).filter(course=course, user=dbuser, exercise=dbexercise)
                    gbsv = gbs.values()
                    extra = {"userpk" : userpk, "exercise_key" : exercise_key}
                    if len(gbs) == 0 :
                        logger.info(f"CREATE NEW AGGREGATION {course} {dbuser} {dbexercise}")
                        logger.info(f"CREATE NEW AGGREGATION {course.pk} {dbuser.pk} {dbexercise.pk}")
                        gb =  Aggregation.objects.create(course=course, user=dbuser, exercise=dbexercise)
                        gb.save(using=db,extra=extra)
                    else :
                        gb = gbs[0]
                        gb.save(using=db,extra=extra)
                except Exception as e :
                    logger.error(f"XXX SS={ss} {type(e).__name__} {str(e)} AGGREGATION ERROR CANNOT UPDATE_OR_CREATE COURSE={course} USER={user} USERNAME={username} EXERCISE={exercise} DB={db} src={src} ")
                    tb = traceback.format_exc()
                    raise e
            for prefix in ["user_exercise_tree:"]:
                cachekey_pat = prefix + str(userPk) + ":" + str(coursePk) + ":" + subdomain + "*"
                cache = caches["aggregation"]
                for key in cache.keys(cachekey_pat):
                    cache.delete(key)
            logger.info(f"HANDLE_NEW_ANSWER OK {settings.GIT_HASH} ")
        if not settings.RUNTESTS :
            os.rename(filepath,filepathbak)
    except Exception as e :
        logger.error(tb)
        logger.error(f"XXX SIGNAL_ERROR sender={sender} KWARGS = {kwargs}")
        logger.error(f"XXX SIGNAL_ERROR {str(e)}")



def handle_exercise_saved(sender, **kwargs):
    exercise = kwargs.get("exercise", None)
    course = exercise.course
    touch_(course.opentasite)
    (cache, cachekey) = t_cache_and_key(course, exercise)
    cache.delete(cachekey)

    cache = caches["aggregation"]
    prefix = "user_exercise_tree:"
    subdomain = course.opentasite
    coursePk = course.pk
    cachekey_pat = prefix + "*" + ":" + str(coursePk) + ":" + subdomain + "*"
    cache = caches["aggregation"]
    for key in cache.keys(cachekey_pat):
        if settings.SUBDOMAIN in key:
            cache.delete(key)
    cache = caches["aggregation"]
    exercisekey = exercise.exercise_key
    for prefix in ["serialized_exercise_with_question_data", "user_exercise_json"]:
        pat = f"*{prefix}*{exercisekey}*"
        for key in cache.keys(f"*{prefix}*{exercisekey}*"):
            cache.delete(key)

    assetpath = exercise.get_full_path()
    files = glob.glob(f"{assetpath}/*")
    for file in files:
        os.chmod(file, 0o755)  # Fix possible chmod issues when uploading and moving

    # DO NOT FORCE A TRANSLATION ON SAVE
    #if course.use_auto_translation and not caches["default"].get("temporarily_block_translations"):
    #    langs = exercise.course.get_languages()
    #    (cache, cachekey) = t_cache_and_key(course, exercise)
    #    xml = exercise_xml(exercise.get_full_path())
    #    TranslationThread(xml, langs, course, exercise).start()


def handle_exercise_options_saved(sender, **kwargs):
    exercise = kwargs.get("exercise", None)
    course = exercise.course
    db = course.opentasite
    if settings.RUNTESTS :
        db = settings.DB_NAME
    touch_(course.opentasite)
    subdomain = course.opentasite
    (cache, cachekey) = t_cache_and_key(course, exercise)
    cache.delete(cachekey)
    cache = caches["aggregation"]
    for prefix in ["user_exercise_tree:"]:
        cachekey_pat = prefix + "*" + ":" + str(course.pk) + ":" + course.opentasite + "*"
        cache = caches["aggregation"]
        for key in cache.keys(cachekey_pat):
            cache.delete(key)

    for key in cache.keys("*"):
        if settings.SUBDOMAIN in key:
            cache.delete(key)
    cache = caches["aggregation"]
    exercisekey = exercise.exercise_key
    for prefix in ["serialized_exercise_with_question_data", "user_exercise_json"]:
        pat = f"*{prefix}*{exercisekey}*"
        for key in cache.keys(f"*{prefix}*{exercisekey}*"):
            cache.delete(key)

    if course.use_auto_translation and not caches["default"].get("temporarily_block_translations"):
        langs = exercise.course.get_languages()
        (cache, cachekey) = t_cache_and_key(course, exercise)
        xml = exercise_xml(exercise.get_full_path())
        TranslationThread(xml, langs, course, exercise).start()

    aggregationentries = Aggregation.objects.using(db).filter(exercise=exercise)
    for ag in aggregationentries:
        ag.save(using=db)
        user = ag.user
        for prefix in [
            "safe_user_cache:",
            "unsafe_user_cache:",
            "calculate_unsafe_user_summary:",
            "get_unsafe_exercise_summary:",
        ]:
            (cache, cachekey) = get_cache_and_key(
                prefix, userPk=str(user.pk), coursePk=course.course_key, subdomain=subdomain
            )
            cache.delete(cachekey)
        cache = caches["aggregation"]
        for prefix in ["user_exercise_tree:"]:
            cachekey_pat = prefix + "*" + settings.SUBDOMAIN + "*"
            for key in cache.keys(cachekey_pat):
                cache.delete(key)


answer_received.connect(handle_new_answer_available)
exercise_saved.connect(handle_exercise_saved)
exercise_options_saved.connect(handle_exercise_options_saved)

stypes = [
    "number_complete",
    "number_complete_by_deadline",
    "number_correct",
    "number_correct_by_deadline",
    "number_image_by_deadline",
    "failed_by_audit",
    "total_audits",
    "manually_passed",
    "manually_failed",
]
agkeys = [
    "all_complete",
    "complete_by_deadline",
    "user_is_correct",
    "correct_by_deadline",
    "image_by_deadline",
    "audit_needs_attention",
    "audit_published",
    "force_passed",
    "force_failed",
]


cache_prefixes = [
    "calculate_unsafe_user_summary:",
    "safe_user_cache:",
    "unsafe_user_cache:",
    "serialized_exercise_with_question_data:",
    "exercise_data_for_course:",
    "students_results:",
    "student_statistics_exercises:",
    "e_student_activity:",
    "get_unsafe_exercise_summary:",
    "user_exercise_tree:",
    "user_exercise_json:",
]

def get_cache_and_key(prefix, exercise_key=None, userPk=None, coursePk=None, subdomain=None, exercise_filter=""):
    if not settings.RUNTESTS:
        assert not subdomain == "", "SUBDOMAIN IS NONE"
    assert prefix in cache_prefixes, "ILLEGAL KEY >" + str(prefix) + "< GIVEN TO get_cachekey"
    cache = caches["aggregation"]
    if prefix in [
        "safe_user_cache:",
        "unsafe_user_cache:",
        "calculate_unsafe_user_summary:",
        "get_unsafe_exercise_summary:",
    ]:
        cachekey = prefix + str(userPk) + ":" + str(coursePk) + ":" + subdomain
    elif prefix in ["user_exercise_tree:"]:
        cachekey = prefix + str(userPk) + ":" + str(coursePk) + ":" + subdomain + ":" + exercise_filter
    elif prefix in ["user_exercise_json:"]:
        cachekey = prefix + str(userPk) + ":" + str(coursePk) + ":" + subdomain + ":" + str(exercise_key)
    elif prefix in ["serialized_exercise_with_question_data:", "user_exercise_json:"]:
        cache = caches["aggregation"]
        cachekey = prefix + str(userPk) + ":" + str(coursePk) + ":" + subdomain + ":" + str(exercise_key)
    elif prefix in ["exercise_data_for_course:", "e_student_activity:"]:
        cachekey = prefix + str(coursePk) + ":" + subdomain + ":" + str( exercise_key )
    elif prefix in ["students_results:", "student_statistics_exercises:"]:
        cachekey = prefix + str(coursePk) + ":" + subdomain
    else:
        assert False, "NO PROPER CACHE DEFINED"
    return (cache, cachekey)


class Aggregation(models.Model):
    course = models.ForeignKey(
        Course,
        default=None,
        related_name="course_from_answers",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="user_from_answers",
        on_delete=models.CASCADE,
    )
    exercise = models.ForeignKey(
        "exercises.Exercise",
        null=True,
        blank=True,
        default=None,
        related_name="exercise_from_answers",
        on_delete=models.CASCADE,
    )
    user_tried_all = models.BooleanField(default=False)  # USER TRIED ALL QUESTIONS ; FALSE IF NO QUESTION
    user_is_correct = models.BooleanField(default=False)  # CORRECT AUTOCORRECTED ANSWSERS ; TRUE IF NO QUESITION
    correct_by_deadline = models.BooleanField(default=False)  #  Dealine time
    answer_date = models.DateTimeField(null=True, blank=True)  # DATE ATTRIBUTED TO ANSWERS
    attempt_count = models.IntegerField(default=0)  # NUMBER OF ATTEMPTS FOR AUTOCORRECTED ANSWERS
    questionlist_is_empty = models.BooleanField(default=False)  #  Dealine time
    all_complete = models.BooleanField(default=False)  # NO TASKS LEFT FOR THE STUDENT NOW.
    date_complete = models.DateTimeField(null=True, blank=True)  # DATE OF STUDENT COMPLETION OF REQUIREMENTS
    complete_by_deadline = models.BooleanField(default=False)  #  Dealine time
    audit_published = models.BooleanField(default=False)
    audit_needs_attention = models.BooleanField(default=False)  # UNRESOLVED AUDIT
    image_exists = models.BooleanField(default=False)  # STUDENT IMAGE EXISTS
    image_date = models.DateTimeField(null=True, blank=True)  # LAST DATE OF IMAGE UPLOAD
    image_by_deadline = models.BooleanField(default=False)  #  Dealine time
    force_passed = models.BooleanField(default=False)  # FORCE PASSED
    force_failed = models.BooleanField(default=False)  # FORCE FAIL
    points = models.TextField(default="", blank=True)

    class Meta:
        unique_together = ("course", "user", "exercise")

    def __str__(self):
        return (
            str( self.user )
            + ":X:"
            + self.exercise_id
            + " = "
            + str(self.user_tried_all)
            + " , "
            + str(self.user_is_correct)
            + " , "
            + str(self.attempt_count)
            + " , "
        )

    def bonus(self, *args, **kwargs):
        #print(f"AGGREGATION - BONUS")
        db = self.course.opentasite
        dbexercise = Exercise.objects.using(db).select_related("course", "meta").get(exercise_key=self.exercise_id)
        isbonus = dbexercise.isbonus()
        #print(f"BONUS - ISBONUS = {isbonus}")
        return isbonus

    def save(self, *args, **kwargs):
        db = kwargs.get('using', self.course.opentasite)
        verify_or_create_database_connection(db)
        logger.info(f"SAVE AGGREGATION  {args} {kwargs} ")
        success = True
        exercise_key = None
        username = None
        dbs = []
        try :
            extra = kwargs.get('extra',None)
            #
            # FOR SOME READON AGGREGATION ARGUMENTS ARE CORRUPTED IN THE SAVE
            # THE EXTRA kwarg WHEN IT EXISTS puts in the correct userpk and exercise_id
            #
            if extra  == None :
                user = self.user
                exercise = self.exercise
                course = self.course
                userpk = None if user == None else user.pk
                exercise_key = None if exercise == None else exercise.exercise_key
            else :
                userpk = extra['userpk']
                user = User.objects.using(db).get(pk=userpk)
                exercise_key = extra['exercise_key']
                exercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
                course = self.course
                logger.info(f"GOT EXERCISE AND USER {user} {exercise}")
            logger.info(f"SAVE AGGREGATION {course.pk} {user.pk} {exercise.pk}")
            cache = caches['default'] # THIS IS A HACK TO FIX BROKEN DATABASE ASSIGNMENT; CACHE GET SET IN question.py
            username = None if user == None else user.username
            if not username == None :
                username_ = username.encode('ascii','ignore').decode('ascii')
            else :
                username_ = None
            dbcheck = cache.get(username_,None)
            if not dbcheck == None :
                dbs.append(dbcheck)
            key = f"temp-{username_}"
            dbcheck2 = cache.get(key, None)
            if not dbcheck2 == None :
                dbs.append(dbcheck2)
            exercise_key = None if exercise == None else exercise.exercise_key
            logger.info(f"DBCHECK = {key} {db} {dbcheck} DBCHECK2={dbcheck2} ")
        except Exception as e :
            logger.error(f"XXX AGGREGATION EXCEPTION WILL TRY TO GET  FIXED DB={db}  {str(e)} {type(e).__name__} E12334177  SELF = {self} ARGS={args} KWARGS = {kwargs}")
            success = False
        #
        # NOW WILL CHECK THAT AGGREGATION AND EXERCISES
        # MATCHES DB
        # 
        #
        # SHOULD BE RDUNTANT CHECKS THAT user and exercise exist
        #
        if not success :
            logger.error(f"XXX NOSUCCESS: SUCCESS IS FALSE: TRY TO GET FIXED CHECK AGGREGATION WITH db={db} dbs = {dbs}")
            for db in dbs :
                try :
                    if not userpk == None :
                        user = User.objects.using(db).get(pk=userpk)
                    if not exercise_key == None :
                        exercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
                    success = True 
                    break;
                except  Exception as e :
                    er = e
                    pass
        if not success :
            logger.error(f"XXX AGGREGATION EXCEPTION STILL NOT FIXED DB={db}  EXERCISE_KEY={exercise_key} USERNAME={username}   E12334177  SELF = {self} ARGS={args} KWARGS = {kwargs}")
            return
        subdomain = db
        triggerfile = os.path.join(settings.VOLUME, db , "backuptrigger")
        if not settings.RUNTESTS :
            os.utime( os.path.join(settings.VOLUME, subdomain) )
        isold = False
        pathexists =  os.path.exists( triggerfile ) 
        questions = []

        try :
            if pathexists :
                now = datetime.datetime.now()
                filetime =  os.path.getmtime(triggerfile)
                filedate = datetime.datetime.fromtimestamp(filetime)
                dt = now -  filedate
                isold = dt > timedelta( minutes=40) # FORCE A TRIGGER IF TRIGGERFILE IS OLD
            if ( not pathexists  or isold  ) and ( not settings.RUNTESTS) :
                subprocess.run(["./db_trigger", settings.BASE_DIR,  db ] )
            user_is_correct = True
            user_tried_all = True
            datelist = []
            attempt_count = 0
            timebegin = time.time()
            questions = exercises.models.Question.objects.using(db).filter(exercise=exercise)
            #questions = questions.exclude(type='aibased')
            self.all_complete = True
            self.audit_needs_attention = False
        except Exception as e :
            logger.error(f"XXX EXCEPTION {type(e).__name__} {str(e)} ")


        qs = [];
        for question in questions:
            if str( question.points() ) != '0' :
                qs.append(question);
        questions = qs;
        self.questionlist_is_empty = True
        nquestions = 0
        for question in questions:
            nquestions += 1
            self.questionlist_is_empty = False
            answers = exercises.models.Answer.objects.using(db).filter(user=user, question=question).order_by("date")
            if answers.count() > 0:
                attempt_count = attempt_count + answers.count()
            correct_answers = answers.filter(correct=True)
            incorrect_answers = answers.filter(correct=False)
            correct = False if correct_answers.count() == 0 else True
            date = None
            if correct:
                date = correct_answers.first().date
            else:
                if incorrect_answers.count() > 0:
                    self.all_complete = False
                    date = incorrect_answers.last().date
            if not date is None:
                datelist = datelist + [date]
            user_tried_all = user_tried_all and (answers.count() > 0)  # RESTORE THIS
            user_is_correct = user_is_correct and correct
        if len(datelist) > 0:
            self.answer_date = max(datelist)

        self.user_is_correct = self.questionlist_is_empty or (user_is_correct and user_tried_all)
        self.user_tried_all = self.questionlist_is_empty or user_tried_all
        self.attempt_count = attempt_count

        deadline_ = exercise.deadline()
        last_image = exercises.models.ImageAnswer.objects.using(db).filter(user=user, exercise=exercise).order_by("date").last()
        images = exercises.models.ImageAnswer.objects.using(db).filter(user=user, exercise=exercise).order_by("date")
        if images  and deadline_ :
            images_on_time =  images.filter( date__lt=deadline_) 
            if  images_on_time : # len( images_on_time ) > 0 :
                last_image = images_on_time.last()
            else :
                last_image = images.last() 
        if last_image:
            self.image_exists = True
            self.image_date = last_image.date
            datelist = datelist + [self.image_date]
        else:
            self.image_exists = False
            self.image_date = None
        if len(datelist) > 0:
            self.date_complete = max(datelist)
        try:
            image_required = exercise.meta.image
        except ObjectDoesNotExist:
            image_required = False
        image_ok = True if not (image_required) else self.image_exists
        self.all_complete = self.all_complete and image_ok and self.user_is_correct and user_tried_all
        if not image_required and self.questionlist_is_empty:
            self.all_complete = True
            exercise_key = exercise.exercise_key
        try :
            self.complete_by_deadline = self.all_complete and (deadline_ == None or self.date_complete < deadline_)
        except :
            self.complete_by_deadline = self.all_complete and deadline_ == None
        # Guard against missing completion date to avoid None < datetime comparison
        #self.complete_by_deadline = self.all_complete and (
        #    deadline_ is None or (self.date_complete is not None and self.date_complete < deadline_)
        #)
        if self.answer_date:
            self.correct_by_deadline = self.user_is_correct and (
                True if deadline_ == None else self.answer_date < deadline_
            )
        else:
            self.correct_by_deadline = False
        self.correct_by_deadline = self.correct_by_deadline and user_tried_all
        if self.questionlist_is_empty:
            self.correct_by_deadline = True
        self.image_by_deadline = (
            False
            if self.image_date == None
            else (image_ok and (True if deadline_ == None else self.image_date < deadline_))
        )
        audit_exists = False
        try:
            audit = exercises.models.AuditExercise.objects.using(db).get(student=user, exercise=exercise)
            self.force_passed = audit.force_passed
            self.audit_published = audit.published
            self.audit_needs_attention = True if audit.revision_needed and audit.published else False
            if audit.revision_needed and audit.published :
                self.all_complete = False
                self.complete_by_deadline = False
            if audit.force_passed:
                self.all_complete = True
                self.complete_by_deadline = True
                self.image_by_deadline = True
            if not audit.revision_needed and audit.published:
                self.all_complete = True
            if (self.correct_by_deadline and self.image_by_deadline and self.all_complete) or self.force_passed:
                self.points = 1
            else:
                self.points = 0
            if audit.points and audit.published :
                self.points = audit.points
            if audit.revision_needed :
                self.points = 0
            audit_exists = True
        except ObjectDoesNotExist:
            pass
        if self.force_passed:
            self.complete_by_deadline = True
            self.audit_needs_attention = False
        if self.force_failed:
            self.audit_needs_attention = False
            self.all_complete = False

        if (not self.image_exists) and (attempt_count == 0) and (not audit_exists):
            return
        if 'update_fields' in kwargs : # MAKE SURE ALL FIELDS ARE SAVED
            del kwargs['update_fields']
        if 'extra' in kwargs :
            del kwargs['extra']
        super().save(*args, **kwargs)
        #print(f"AUDIT_PUBLISHED = {self.audit_published}")
        #super(Aggregation, self).save(*args, **kwargs)
