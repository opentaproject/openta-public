from django.db import models

# Create your models here.
import json as JSON
import logging
import backend.settings as settings
import os
import uuid
from django.core.cache import caches
from PIL import Image, ImageDraw, ImageFont

# from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver, Signal
from django.template.defaultfilters import slugify
from functools import reduce

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from image_utils import compress_pil_image_timestamp
import datetime
import time
import pytz
import exercises.paths as paths
from course.models import Course
import exercises
from exercises.models import answer_received

STATISTICS_CACHE_TIMEOUT = 60 * 30  # RECOMPUTE RECENT ACTIVITY


# answer_received = Signal(providing_args=["course", "user", "exercise"])

# @receiver([answer_received])
# def signal_handler(sender, *args, **kwargs):
#    for signal in ['answer_received','post_save', 'post_delete']:
#        if hasattr(sender, signal):
#            print("SENDER ", signal, " RECEIVED IN AGGREGATION= ", sender)
#            getattr(sender, signal)(sender, *args, **kwargs)


def handle_new_answer_available(sender, **kwargs):
    exercise = kwargs['exercise']
    course = exercise.course
    user = kwargs.get('user', None)
    #
    # THIS STEP TAKES ABOUT 3 seconds for 250 students
    # WHEN ADMIN MAKES A META CHANGE
    # AN IRRITATING DELTA IN META SAVE
    # MOVE TO ASYNC HANDLING
    #
    # timebegin = time.time()
    if user == None:
        aggregationentries = Aggregation.objects.filter(exercise=exercise)
        for ag in aggregationentries:
            ag.save()
    else:
        date = kwargs['date']
        gb, _ = Aggregation.objects.update_or_create(course=course, user=user, exercise=exercise)
    # print("DELTAT HANDLE NEW ANSWSER", time.time() - timebegin)


answer_received.connect(handle_new_answer_available)

stypes = [
    'number_complete',
    'number_complete_by_deadline',
    'number_correct',
    'number_correct_by_deadline',
    'number_image_by_deadline',
    'failed_by_audit',
    'total_audits',
    'manually_passed',
    'manually_failed',
]
agkeys = [
    'all_complete',
    'complete_by_deadline',
    'user_is_correct',
    'correct_by_deadline',
    'image_by_deadline',
    'audit_needs_attention',
    'audit_published',
    'force_passed',
    'force_failed',
]


cache_prefixes = [
    'calculate_unsafe_user_summary:',
    'safe_user_cache:',
    'unsafe_user_cache:',
    'serialized_exercise_with_question_data:',
    'exercise_data_for_course:',
    #'calculate_user_results:',
    'students_results:',
    'student_statistics_exercises:',
    'e_student_activity:',
    'get_unsafe_exercise_summary:',
]


def get_cache_and_key(prefix, exercise_key=None, userPk=None, coursePk=None):
    # print("GET CACHEKEY " , exercise_key, userPk, coursePk)
    assert prefix in cache_prefixes, "ILLEGAL KEY >" + str(prefix) + "< GIVEN TO get_cachekey"
    cache = caches['aggregation']
    assert not (coursePk == None), 'COURSE WAS NONE IN ' + str(prefix)
    if prefix in [
        'safe_user_cache:',
        'unsafe_user_cache:',
        'calculate_unsafe_user_summary:',
        'get_unsafe_exercise_summary:',
    ]:
        cachekey = prefix + str(userPk) + ':' + str(coursePk)
    elif prefix in ['serialized_exercise_with_question_data:']:
        cache = caches['aggregation']
        cachekey = prefix + str(userPk) + ':' + str(coursePk) + ':' + exercise_key
    elif prefix in ['exercise_data_for_course:', 'e_student_activity:']:
        cachekey = prefix + str(coursePk) + ':' + exercise_key
    elif prefix in ['students_results:', 'student_statistics_exercises:']:
        cachekey = prefix + str(coursePk)
    else:
        assert False, 'NO PROPER CACHE DEFINED'
    # print("CACHEKEY = ", cachekey )
    return (cache, cachekey)


class Aggregation(models.Model):
    course = models.ForeignKey(
        Course, default=None, related_name="course_from_answers", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, null=True, blank=True, related_name="user_from_answers", on_delete=models.CASCADE
    )
    exercise = models.ForeignKey(
        'exercises.Exercise',
        null=True,
        blank=True,
        default=None,
        related_name="exercise_from_answers",
        on_delete=models.CASCADE,
    )
    #
    # AUTOCORRECTED QUESTIONS
    #
    # ANSWER DATE FOR A QUESTION IS LAST DATE FOR AN INCORRECTED ANSWER
    # OR FIRST DATE OF A CORRECT ANSWERS  WHICHEVER IS EARLIER
    # THE ANSWER DATE IS THEN THE LAST OF ALL OF THESE
    #
    user_tried_all = models.BooleanField(
        default=False
    )  # USER TRIED ALL QUESTIONS ; FALSE IF NO QUESTION
    user_is_correct = models.BooleanField(
        default=False
    )  # CORRECT AUTOCORRECTED ANSWSERS ; TRUE IF NO QUESITION
    correct_by_deadline = models.BooleanField(default=False)  #  Dealine time
    answer_date = models.DateTimeField(null=True, blank=True)  # DATE ATTRIBUTED TO ANSWERS
    attempt_count = models.IntegerField(default=0)  # NUMBER OF ATTEMPTS FOR AUTOCORRECTED ANSWERS
    questionlist_is_empty = models.BooleanField(default=False)  #  Dealine time
    #
    #
    # ALL COMPLETE IS TRUE IF THERE ARE NO TASKS LEFT FOR THE STUDENT
    # THIS CAN CHANGE TO FALSE IF A AN AUDIT FAILS
    #
    all_complete = models.BooleanField(default=False)  # NO TASKS LEFT FOR THE STUDENT NOW.
    date_complete = models.DateTimeField(
        null=True, blank=True
    )  # DATE OF STUDENT COMPLETION OF REQUIREMENTS
    complete_by_deadline = models.BooleanField(default=False)  #  Dealine time
    #
    # AUDITS
    #
    audit_published = models.BooleanField(default=False)
    audit_needs_attention = models.BooleanField(default=False)  # UNRESOLVED AUDIT
    # IMAGES
    image_exists = models.BooleanField(default=False)  # STUDENT IMAGE EXISTS
    image_date = models.DateTimeField(null=True, blank=True)  # LAST DATE OF IMAGE UPLOAD
    image_by_deadline = models.BooleanField(default=False)  #  Dealine time
    # PASS FLAGS
    force_passed = models.BooleanField(default=False)  # FORCE PASSED
    force_failed = models.BooleanField(default=False)  # FORCE FAIL

    # def delete_caches( prefix, exercise_key=None, userPk=None, coursePk=None):
    #     for prefix in cache_prefixes:
    #        (cache, cachekey) = get_cache_and_key(prefix, exercise_key=exercise.exercise_key, userPk=userPk, coursePk=coursePk )
    #        #print("DELETE ", cachekey )
    #        cache.delete(cachekey)

    class Meta:
        unique_together = ('course', 'user', 'exercise')

    def __str__(self):
        return (
            self.user.username
            + ' X '
            + self.exercise.name
            + " = "
            + str(self.user_tried_all)
            + " , "
            + str(self.user_is_correct)
            + " , "
            + str(self.attempt_count)
            + " , "
        )

    def save(self, *args, **kwargs):
        # print("AGGREGATION_ANSWERS SAVE FIRED", args, kwargs,self)
        exercise = self.exercise
        if not exercise:
            return

        user_is_correct = True
        user_tried_all = True
        datelist = []
        attempt_count = 0
        user = self.user
        # print("AGGREGATION UPDATED FOR USER = ", user)
        # print("AGGREGATION UPDATED FOR course_id = ", exercise.course_id)
        userPk = str(user.pk)
        coursePk = str(exercise.course_id)
        timebegin = time.time()
        for prefix in cache_prefixes:
            (cache, cachekey) = get_cache_and_key(
                prefix, exercise_key=exercise.exercise_key, userPk=userPk, coursePk=coursePk
            )
            # print("DELETE ", cachekey )
            cache.delete(cachekey)
        deltat = time.time() - timebegin
        questions = exercises.models.Question.objects.filter(exercise=exercise)
        course = self.course
        dosave = False
        self.all_complete = True
        show = False
        # if user.username == 'devcha@student.chalmers.se' :
        #    print("SAVING DEVCHA EXERCISE ", exercise )
        #    show = True
        #
        # THE PRESENT VERSION ALLOWS A STUDENT TO BE COMPLETED
        # IF AN ANSWER WAS CORRECT AT SOME POINT
        # THIS COLLIDES WITH DEFINITION OF
        # COMPLETE IN E_STUDENT_PERCENT_COMPLETE
        # IT IS FIXED BY HAND THERE TO BE COMPLIANT
        #
        self.questionlist_is_empty = True
        nquestions = 0
        for question in questions:
            # print("KEY = ", question.question_key)
            nquestions += 1
            self.questionlist_is_empty = False
            answers = exercises.models.Answer.objects.filter(user=user, question=question).order_by(
                'date'
            )
            if answers.count() > 0:
                dosave = True
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
        if show:
            print("DID QUEWSIONTS")
        if len(datelist) > 0:
            self.answer_date = max(datelist)
        # print("TOTAL NUMBER OF QUESTIONS = ", nquestions)
        #
        # THIS SECTION SHOULD BE REMOVED TO ALLOW INCORRECT ANSWERS AFER A CORRECT ONE
        #
        # allcorrect = True
        # questions = exercises.models.Question.objects.filter(exercise=exercise)
        # for question in questions:
        #    try:
        #        #print("GET LAST ANSWER")
        #        answer = exercises.models.Answer.objects.filter(
        #            user=user, question=question
        #        ).latest('date')
        #        #print("LATEST ANSER = ", answer)
        ##        if not answer.correct:
        #            allcorrect = False
        #    except ObjectDoesNotExist:
        #        allcorrect = False
        # user_is_correct = allcorrect

        # tried_all = True
        # for question in questions:
        #    try:
        #        exercises.models.Answer.objects.filter(user=user, question=question).latest('date')
        #    except exercises.models.Answer.DoesNotExist:
        #        tried_all = False
        # if not user_tried_all == tried_all:
        #    print("TRIED_ALL IN AGGREGATION MODEL SAVE GIVES INCONSISTENT RESULTS")
        # else:
        #    pass
        #    #print("TRIED ALL OK", user, exercise)
        # if show:
        #    print(" BBB ")

        self.user_is_correct = self.questionlist_is_empty or (user_is_correct and user_tried_all)
        self.user_tried_all = self.questionlist_is_empty or user_tried_all
        self.attempt_count = attempt_count

        # PROCESS IMAGES
        last_image = (
            exercises.models.ImageAnswer.objects.filter(user=user, exercise=exercise)
            .order_by('date')
            .last()
        )
        # if show:
        #    print("CCC")
        if last_image:
            dosave = True
            self.image_exists = True
            self.image_date = last_image.date
            datelist = datelist + [self.image_date]
        else:
            self.image_exists = False
            self.image_date = None
        if len(datelist) > 0:
            self.date_complete = max(datelist)
            dosave = True
        deadline_ = exercise.deadline()
        try:
            image_required = self.exercise.meta.image
        except ObjectDoesNotExist:
            image_required = False
        image_ok = True if not (image_required) else self.image_exists
        self.all_complete = (
            self.all_complete and image_ok and self.user_is_correct and user_tried_all
        )
        if not image_required and self.questionlist_is_empty:
            self.all_complete = True
        self.complete_by_deadline = self.all_complete and (
            deadline_ == None or self.date_complete < deadline_
        )
        if self.answer_date:
            self.correct_by_deadline = self.user_is_correct and (
                True if deadline_ == None else self.answer_date < deadline_
            )
        else:
            self.correct_by_deadline = False
        self.correct_by_deadline = self.correct_by_deadline and user_tried_all
        self.image_by_deadline = (
            False
            if self.image_date == None
            else (image_ok and (True if deadline_ == None else self.image_date < deadline_))
        )
        # PROCESS AUDITS
        audit_exists = False
        try:
            audit = exercises.models.AuditExercise.objects.get(student=user, exercise=exercise)
            if audit.force_passed:
                self.force_passed = True
            if audit.published:
                audit_exists = True
                self.audit_published = True
                self.audit_needs_attention = audit.revision_needed
                if audit.revision_needed:
                    self.all_complete = False
                    self.complete_by_deadline = False
                if audit.force_passed or not audit.revision_needed:
                    self.all_complete = True
                    self.complete_by_deadline = True
                    self.audit_needs_attention = False
            # if user.username == 'devcha@student.chalmers.se':
            #    print("AUDIT ADDED FOR USER = ", user, " AND EXERCISE ", exercise)
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
        # if user.username == 'devcha@student.chalmers.se':
        #    print(
        #        "FINALLY SAVED ANSWSERS FOR ",
        #        user,
        #        " AND EXERCISE ",
        #        exercise,
        #        exercise.exercise_key,
        #    )
        #    print("SELF = ", self)
        super(Aggregation, self).save(*args, **kwargs)
