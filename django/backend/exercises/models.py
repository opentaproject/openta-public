import json as JSON
import logging
from lxml import etree
import backend.settings as settings
import os
import uuid
from PIL import Image, ImageDraw, ImageFont
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.forms import ValidationError
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
import aggregation
import datetime
import pytz
from model_utils import FieldTracker

import exercises.paths as paths
from course.models import Course
from exercises.parsing import (
    ExerciseNotFound,
    ExerciseParseError,
    exercise_check_thumbnail,
    exercise_key_get,
    exercise_key_get_or_create,
    exercise_xmltree,
    get_translations,
    is_exercise,
    question_validate_xmltree,
)
from exercises.util import nested_print
import datetime

# from aggregation.models import answer_received

BIN_LENGTH = settings.BIN_LENGTH

logger = logging.getLogger(__name__)

# https://coderwall.com/p/ktdb3g/django-signals-an-extremely-simplified-explanation-for-beginners
#
# LISTEN TO ALL RELEVANT SIGNALS
#
@receiver([post_save, post_delete])
def signal_handler(sender, *args, **kwargs):
    for signal in ['post_save', 'post_delete']:
        if hasattr(sender, signal):
            getattr(sender, signal)(sender, *args, **kwargs)


answer_received = Signal(providing_args=["course", "user", "exercise"])


class ExerciseManager(models.Manager):
    def add_exercise_full_path(self, path, course):
        """Add exercise from full path.

        Verifies that the folder structure corresponds to the specified course.

        Args:
            path (str): Full path to exercise.
            course (Course): Course model object.

        """
        course_path = course.get_exercises_path()
        if not path.startswith(course_path):
            raise ExerciseParseError('Exercise does not reside in the specified course')

        relative_path = path[len(course_path) :]
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
        return self.add_exercise(relative_path, course)

    def add_exercise(self, exercise_path, course):
        """Add exercise by relative path.

        Args:
            exercise_path (str): Path relative to course base.
            course (Course): Course model object.

        """
        progress = []
        translation_name = {}
        if exercise_path.startswith("/"):
            exercise_path = exercise_path[1:]
        full_path = os.path.join(course.get_exercises_path(), exercise_path)
        if not is_exercise(full_path):
            raise ExerciseNotFound(full_path)
        exercisetree = exercise_xmltree(os.path.join(course.get_exercises_path(), exercise_path))
        exercisename_xml = exercisetree.xpath('/exercise/exercisename')
        if exercisename_xml:
            translation_name = get_translations(exercisename_xml[0])
        name = (exercisetree.xpath('/exercise/exercisename/text()') or ['No name'])[0]
        key = exercise_key_get_or_create(os.path.join(course.get_exercises_path(), exercise_path))
        defaults = dict(
            name=name,
            translated_name=JSON.dumps(translation_name),
            path=exercise_path,
            folder=os.path.dirname(exercise_path),
        )
        dbexercise, created = self.update_or_create(
            exercise_key=key, course=course, defaults=defaults
        )
        defaults_meta = {'sort_key': os.path.basename(exercise_path)}
        dbmeta, created_meta = ExerciseMeta.objects.get_or_create(
            exercise=dbexercise, defaults=defaults_meta
        )
        if created:
            progress.append(('success', _("Added exercise ") + exercise_path))
            logger.info('Adding ' + exercise_path + '/' + name + ' to database.')
        else:
            progress.append(('info', _("Updated exercise ") + exercise_path))
            logger.info('Updated ' + exercise_path + '/' + name)
        questions = exercisetree.xpath('/exercise/question[@key and @type]')
        keys = [x.get('key') for x in questions]
        if len(keys) > len(set(keys)):
            raise ExerciseParseError("Duplicate question keys!")
        for question in questions:
            if not question_validate_xmltree(question):
                logger.info(exercise_path + " contains invalid question: ")
                nested_print(question)
                raise ExerciseParseError("Invalid question in " + name)
            dbquestion, created = Question.objects.update_or_create(
                exercise=dbexercise,
                question_key=question.get('key'),
                defaults={'type': question.get('type')},
            )
            if created:
                logger.info(
                    (
                        name
                        + ': Adding question '
                        + question.get('key')
                        + ' of type '
                        + question.get('type')
                    )
                )
            else:
                logger.info(
                    (
                        name
                        + ': Updating question '
                        + question.get('key')
                        + ' of type '
                        + question.get('type')
                    )
                )
        questions_with_key = exercisetree.xpath('/exercise/question[@key]')
        for question in Question.objects.filter(exercise=dbexercise):
            bool_list = map(lambda q: q.get('key') == question.question_key, questions_with_key)
            exists = reduce(lambda a, b: a or b, bool_list, False)
            if not exists:
                question.delete()
        progress.extend(
            exercise_check_thumbnail(
                exercisetree, os.path.join(course.get_exercises_path(), exercise_path)
            )
        )
        return progress

    def sync_with_disc(self, course, i_am_sure=False):
        need_to_be_sure = False
        prevent_reload = False
        logger.info("Starting sync with disc of exercises.")
        progress = [('success', _('Checking status of file tree...'))]
        exerciselist = []
        exercises_without_keys = []
        keys = {}
        other_courses_keys = self.exclude(course=course).values_list('exercise_key', flat=True)
        exercises_path = course.get_exercises_path()
        progress.append(('success', "Checking in" + exercises_path))
        for root, directories, filenames in os.walk(course.get_exercises_path(), followlinks=True):
            for filename in filenames:
                if filename == 'exercise.xml':
                    name = os.path.basename(os.path.normpath(root))
                    relpath = root[len(exercises_path) :]
                    # THE NEXT COMMAND CAUSED SYNC TO CRASH WHEN exercise.xml mistakenly is put in root dir
                    if (
                        not relpath == ''
                    ):  # GET RID OF EDGE CASE WHEN exercise.xml mistakenly is put in root dir
                        exerciselist.append((name, relpath))

        for name, path in exerciselist:
            try:
                key = exercise_key_get(os.path.join(exercises_path, path))
                if key in other_courses_keys:
                    duplicate_exercise = self.get(exercise_key=key)
                    progress.append(('error', _("Duplicate exercise keys!")))
                    progress.append(
                        (
                            'error',
                            _("Exercise at [")
                            + path
                            + _(
                                "] has the same key as exercise in other course:"
                                + str(duplicate_exercise)
                            ),
                        )
                    )
                    progress.append(
                        (
                            'warning',
                            _(
                                (
                                    "You will need to fix this before a reload is possible."
                                    "(Perhaps you copied an exercise? Then please remove the"
                                    " key file from the new exercise to generate a new one on reload)"
                                )
                            ),
                        )
                    )
                    prevent_reload = True
                elif key in keys:
                    progress.append(('error', _("Duplicate exercise keys!")))
                    progress.append(
                        (
                            'error',
                            _("Exercise at [")
                            + path
                            + _("] has the same key as exercise at [")
                            + keys[key]
                            + "]",
                        )
                    )
                    progress.append(
                        (
                            'warning',
                            _(
                                (
                                    "You will need to fix this before a reload is possible."
                                    "(Perhaps you copied an exercise? Then please remove the"
                                    " key file from the new exercise to generate a new one on reload)"
                                )
                            ),
                        )
                    )
                    keys.pop(key)
                    prevent_reload = True
                else:
                    keys[key] = path
            except IOError:
                exercises_without_keys.append(path)

        existing_exercises = set(self.filter(course=course).values_list('pk', flat=True))
        file_tree_exercises = set(keys.keys())
        new_exercises = file_tree_exercises - existing_exercises
        for new_exercise in new_exercises:
            progress.append(('success', 'A reload would add the exercise at ' + keys[new_exercise]))
        for exercise_path in exercises_without_keys:
            progress.append(('success', 'A reload would add the exercise at ' + exercise_path))

        for exercise in self.filter(course=course):
            if not is_exercise(exercise.get_full_path()):
                if exercise.exercise_key in keys:
                    progress.append(
                        (
                            'info',
                            _("The exercise with path ")
                            + exercise.path
                            + _(" seems to have been moved to ")
                            + keys[exercise.exercise_key],
                        )
                    )
                else:
                    progress.append(
                        (
                            'warning',
                            _("The exercise with path ")
                            + exercise.path
                            + _(
                                " does no longer contain an exercise.xml file and will be deleted."
                            ),
                        )
                    )

        for name, path in exerciselist:
            try:
                dbexercise = Exercise.objects.get(path=path)
                try:
                    key = exercise_key_get(os.path.join(exercises_path, path))
                except IOError:
                    key = None
                if dbexercise.exercise_key != key:
                    need_to_be_sure = True
                    progress.append(
                        (
                            'warning',
                            _("The exercise with path ")
                            + path
                            + _(
                                " changed exercise key, this will result in a new exercise "
                                "being added and the old one deleted."
                            ),
                        )
                    )
                    progress.append(('info', 'Old key:  ' + dbexercise.exercise_key))
                    if key is not None:
                        progress.append(('info', 'New key: ' + key))
                    else:
                        progress.append(('info', 'New key: Empty, a new one will be generated.'))
            except Exercise.DoesNotExist:
                pass

        if prevent_reload:
            progress.append(
                (
                    'error',
                    _(
                        "Something will prevent a reload from being carried out, "
                        "please review messages above."
                    ),
                )
            )
            yield progress
            return
        if need_to_be_sure and not i_am_sure:
            progress.append(('error', _("Are you sure you want to do these actions?")))
            yield progress
            return
        if not need_to_be_sure and not i_am_sure:
            progress.append(
                (
                    'info',
                    _(
                        "Do you want to do a reload? This will update all existing exercises and perform "
                        "any additional actions listed above."
                    ),
                )
            )
            yield progress
            return
        progress.append(('info', 'Ok, starting reload...'))
        for name, path in exerciselist:
            try:
                msgs = self.add_exercise(path, course)
                progress.extend(msgs)
                yield progress
                progress.clear()
            except (ExerciseParseError, IOError) as e:
                progress.append(('error', "Failed to add " + path + " because " + str(e)))
        for exercise in self.filter(course=course):
            fullpath = exercise.path + '/exercise.xml'
            if not is_exercise(exercise.get_full_path()):
                exercise.delete()
                progress.append(
                    (
                        'warning',
                        _("Deleted ")
                        + exercise.path
                        + _(" since it is not present on disc anymore"),
                    )
                )
            else:
                key = exercise_key_get_or_create(os.path.join(exercises_path, exercise.path))
                if key != exercise.exercise_key:
                    exercise.delete()
                    progress.append(
                        (
                            'warning',
                            _("Deleted an entry for ")
                            + exercise.path
                            + _(
                                " since the stored exercise key did not correspond to the "
                                "exercisekey in the folder."
                            ),
                        )
                    )

        progress.append(('success', _("Finished syncing exercises.")))
        yield progress


class Exercise(models.Model):
    exercise_key = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255, default="")
    translated_name = models.CharField(max_length=512, default="{}")
    path = models.TextField()
    folder = models.TextField(default="")
    course = models.ForeignKey(
        Course, related_name="exercises", null=True, on_delete=models.CASCADE
    )
    objects = ExerciseManager()

    class Meta:
        permissions = (
            ("reload_exercise", "Can reload exercises from disk"),
            ("edit_exercise", "Can edit exercises in frontend"),
            ("create_exercise", "Can create exercises in frontend"),
            ("administer_exercise", "Can administer exercise options"),
            ("view_solution", "Can view exercise solution (even if not published)"),
            ("view_statistics", "Can view student progress statistics"),
            ("view_student_id", "Can view student identity"),
            ("view_unpublished", "Can view unpublished exercises"),
            ("view_xml", "Can view exercise XML"),
        )

    def __str__(self):
        return self.name + ': ' + self.path

    def deadline(self):
        tz = pytz.timezone('Europe/Berlin')
        deadline_time = datetime.time(23, 59, 59)
        course = self.course
        if course is not None and course.deadline_time is not None:
            deadline_time = course.deadline_time
        try:
            deadline_date = self.meta.deadline_date
        except:
            deadline_date = None
        if deadline_date is not None:
            deadline_date_time = tz.localize(
                datetime.datetime.combine(deadline_date, deadline_time)
            )
        else:
            deadline_date_time = None
        return deadline_date_time

    def get_full_path(self):
        return os.path.join(self.course.get_exercises_path(), *self.path.split('/'))

    def old_user_is_correct(self, user):
        allcorrect = True
        questions = Question.objects.filter(exercise=self)
        for question in questions:
            try:
                answer = Answer.objects.filter(user=user, question=question).latest('date')
                if not answer.correct:
                    allcorrect = False
            except ObjectDoesNotExist:
                allcorrect = False
        return allcorrect

    def user_is_correct(self, user):
        try:
            user_is_correct = aggregation.models.Aggregation.objects.get(
                user=user, exercise=self
            ).user_is_correct
        except:
            user_is_correct = False
        return user_is_correct

    def user_tried_all(self, user):
        try:
            tried_all = aggregation.models.Aggregation.objects.get(
                user=user, exercise=self
            ).user_tried_all
        except:
            tried_all = False
        return tried_all


class Question(models.Model):
    class Meta:
        unique_together = ('question_key', 'exercise')
        permissions = (("log_question", "Answers are logged"),)

    question_key = models.CharField(max_length=255)
    exercise = models.ForeignKey(Exercise, related_name='question', on_delete=models.CASCADE)
    type = models.CharField(max_length=255, default='none')
    tracker = FieldTracker()

    def __str__(self):
        return self.exercise.name + ": " + self.question_key

    def points(self ,*args, **kwargs):
        xmltree = exercise_xmltree(self.exercise.get_full_path(), {} )
        question_xmltree = xmltree.xpath('/exercise/question[@key="{key}"]'.format(key=self.question_key))[0]
        return  question_xmltree.get('points',None)
        


    def post_save(self, *args, **kwargs):
        #print("QUESTION POST_SAV ARGS", args)
        #print("QUESTION POST_SAV KWARGS", kwargs)
        instance = kwargs['instance']
        question_key_has_changed = instance.tracker.has_changed('question_key')
        if question_key_has_changed:
            exercise = kwargs['instance'].exercise
            course = exercise.course
            answer_received.send(
                sender=self.__class__, user=None, exercise=exercise, course=course, date=None
            )

    def post_delete(self, *args, **kwargs):
        instance = kwargs['instance']
        question_key_has_changed = instance.tracker.has_changed('question_key')
        exercise = kwargs['instance'].exercise
        course = exercise.course
        if question_key_has_changed:
            answer_received.send(
                sender=self.__class__, user=None, exercise=exercise, course=course, date=None
            )


class Answer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(
        Question, on_delete=models.SET_NULL, null=True, related_name='answer'
    )

    answer = models.TextField()
    grader_response = models.TextField(default='')
    correct = models.BooleanField()
    date = models.DateTimeField(default=now)
    user_agent = models.TextField(default='')

    def __str__(self):
        return (
            self.user.username
            + " answered {"
            + self.answer
            + "} which is "
            + ("correct" if self.correct else "incorrect")
        )

    def post_save(self, *args, **kwargs):
        #print("ANSWER POST_SAVE ARGS = ", args )
        #print("ANSWER POST_SAVE KWARGS = ", kwargs)
        instance = kwargs['instance']
        user = instance.user
        date = instance.date
        grader_response = instance.grader_response
        if instance.question:
            exercise = instance.question.exercise
            course = exercise.course
            answer_received.send(
                sender=self.__class__, user=user, exercise=exercise, course=course, date=date
            )

    def save(self, *args, **kwargs):
        #print("ANSSWER SAVE args = ", args )
        #print("ANSWSER KWARGS = ", kwargs)
        if self.pk == None:
             answers = Answer.objects.filter(user=self.user, question=self.question)
             nattempt = 1 if answers == None else answers.count()
             self.nattempt = nattempt
        super().save(*args, **kwargs)

    

def answer_image_filename(instance, filename):
    return '/'.join(
        [
            'answerimages',
            instance.user.username,
            instance.exercise.exercise_key,
            str(uuid.uuid4()) + os.path.splitext(filename)[1],
        ]
    )


class ImageAnswer(models.Model):
    IMAGE = 'IMG'
    PDF = 'PDF'
    FILETYPE_CHOICES = ((IMAGE, 'Image'), (PDF, 'Pdf'))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(
        Exercise, on_delete=models.SET_NULL, null=True, related_name="imageanswer"
    )
    date = models.DateTimeField(default=now)
    filetype = models.CharField(max_length=3, choices=FILETYPE_CHOICES, default=IMAGE)
    image = models.ImageField(
        default=None, blank=True, null=True, upload_to=answer_image_filename, max_length=512
    )
    pdf = models.FileField(
        default=None, blank=True, null=True, upload_to=answer_image_filename, max_length=512
    )
    image_thumb = ImageSpecField(
        source='image', processors=[ResizeToFill(100, 50)], format='JPEG', options={'quality': 60}
    )

    def __str__(self):
        try:
            return self.user.username + " image for " + self.exercise.name
        except AttributeError:
            return "__Orphan__"

    def compress(self):
        compress_pil_image_timestamp(self.image.path)

    def remove_file(self):
        if self.image:
            os.remove(self.image.path)
        elif self.pdf:
            os.remove(self.pdf.path)

    def post_save(self, *args, **kwargs):
        instance = kwargs['instance']
        user = instance.user
        date = instance.date
        exercise = instance.exercise
        course = exercise.course
        answer_received.send(
            sender=self.__class__, user=user, exercise=exercise, course=course, date=date
        )

    def post_delete(self, *args, **kwargs):
        instance = kwargs['instance']
        user = instance.user
        date = instance.date
        exercise = instance.exercise
        course = exercise.course
        answer_received.send(
            sender=self.__class__, user=user, exercise=exercise, course=course, date=date
        )


class ExerciseMeta(models.Model):
    exercise = models.OneToOneField(Exercise, related_name='meta', on_delete=models.CASCADE)
    deadline_date = models.DateField(default=None, null=True, blank=True)
    solution = models.BooleanField(default=False, verbose_name='Publish solution')
    difficulty = models.CharField(max_length=64, null=True, blank=True, default=None)
    required = models.BooleanField(default=False, verbose_name='Obligatory')
    student_assets = models.BooleanField(default=False, verbose_name='Student assets')
    image = models.BooleanField(default=False, verbose_name='Image upload')
    allow_pdf = models.BooleanField(default=False, verbose_name='Allow pdf as image upload')
    bonus = models.BooleanField(default=False)
    server_reply_time = models.DurationField(default=None, null=True, blank=True)
    published = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)
    sort_key = models.CharField(max_length=255, default='', verbose_name='Sort order key')
    feedback = models.BooleanField(default=True, verbose_name='Feedback to student')

    def clean(self):
        if self.required and self.bonus:
            raise ValidationError('BONUS AND REQUIRED CANNOT BOTH BE TRUE')

    def __str__(self):
        return self.exercise.name

    def post_save(self, *args, **kwargs):
        instance = kwargs['instance']
        exercise = instance.exercise
        course = exercise.course
        answer_received.send(
            sender=self.__class__, user=None, exercise=exercise, course=course, date=None
        )

    def get_languages(self):
        return "ABCDEFG"


class AuditManager(models.Manager):
    def get_force_passed_exercises_pk(self, user):
        exercises = self.filter(student=user, force_passed=True).values_list(
            'exercise__pk', flat=True
        )
        return exercises


def audit_fileresponse_filename(instance, filename):
    return '/'.join(
        [
            'audit_fileresponses',
            instance.student.username,
            instance.exercise.exercise_key,
            str(uuid.uuid4()) + os.path.splitext(filename)[1],
        ]
    )


class AuditExercise(models.Model):
    student = models.ForeignKey(User, related_name='audits', on_delete=models.CASCADE)
    auditor = models.ForeignKey(User, related_name='studentaudits', on_delete=models.CASCADE)
    exercise = models.ForeignKey(
        Exercise, on_delete=models.SET_NULL, null=True, related_name='audits'
    )
    subject = models.CharField(max_length=255, default='', blank=True)
    message = models.TextField(default="", blank=True)
    published = models.BooleanField(default=False)  # Audit shown to student
    force_passed = models.BooleanField(default=False)
    date = models.DateTimeField(default=now)
    sent = models.BooleanField(default=False)
    revision_needed = models.NullBooleanField(blank=True, default=None)
    updated = models.BooleanField(default=False)
    updated_date = models.DateTimeField(null=True, blank=True, default=None)
    modified = models.DateTimeField(auto_now=True)
    points = models.TextField(default='',blank=True)

    objects = AuditManager()

    class Meta:
        unique_together = (("student", "exercise"),)  # Only one audit per student and exercise

    def post_save(self, *args, **kwargs):
        instance = kwargs['instance']
        user = instance.student
        date = instance.date
        points = instance.points
        #print("AUDIT EXERCISE POINTS = ", points)
        exercise = instance.exercise
        course = exercise.course
        answer_received.send(
            sender=self.__class__, user=user, exercise=exercise, course=course, date=date
        )


def audit_response_filename(instance, filename):
    return '/'.join(
        [
            'auditresponses',
            instance.audit.student.username,
            instance.audit.exercise.exercise_key,
            str(uuid.uuid4()) + os.path.splitext(filename)[1],
        ]
    )


class AuditResponseFile(models.Model):
    IMAGE = 'IMG'
    PDF = 'PDF'
    FILETYPE_CHOICES = ((IMAGE, 'Image'), (PDF, 'Pdf'))
    audit = models.ForeignKey(AuditExercise, related_name='responsefiles', on_delete=models.CASCADE)
    auditor = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(default=now)
    filetype = models.CharField(max_length=3, choices=FILETYPE_CHOICES, default=IMAGE)
    image = models.ImageField(
        default=None, blank=True, null=True, upload_to=audit_response_filename
    )
    pdf = models.FileField(
        default=None, blank=True, null=True, upload_to=audit_response_filename, max_length=512
    )
    image_thumb = ImageSpecField(
        source='image', processors=[ResizeToFill(100, 50)], format='JPEG', options={'quality': 60}
    )
