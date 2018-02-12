from django.db import models
import os
from functools import reduce
import exercises.paths as paths
from exercises.parsing import ExerciseParseError, exercise_key_get_or_create
from exercises.parsing import is_exercise, ExerciseNotFound, exercise_xmltree
from exercises.parsing import question_validate_xmltree, get_translations
from exercises.parsing import exercise_check_thumbnail, exercise_key_get
from course.models import Course
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from exercises.util import nested_print
import json as JSON
import uuid
import logging

logger = logging.getLogger(__name__)


class ExerciseManager(models.Manager):
    def mend_answers_and_audits(self):
        '''
        Tries to match orphan answers with an exercise and question.
        '''
        answers = Answer.objects.filter(question__isnull=True)
        for answer in answers:
            try:
                question = Question.objects.get(
                    exercise__exercise_key=answer.exercise_key, question_key=answer.question_key
                )
                answer.question = question
                answer.save()
                logger.info("Found question for orphan answer")
            except ObjectDoesNotExist:
                pass
        imageanswers = ImageAnswer.objects.filter(exercise__isnull=True)
        for imageanswer in imageanswers:
            try:
                exercise = Exercise.objects.get(exercise_key=imageanswer.exercise_key)
                imageanswer.exercise = exercise
                imageanswer.save()
                logger.info("Found exercise for orphan imageanswer")
            except ObjectDoesNotExist:
                pass
        audits = AuditExercise.objects.filter(exercise__isnull=True)
        for audit in audits:
            try:
                exercise = Exercise.objects.get(exercise_key=audit.exercise_key)
                audit.exercise = exercise
                audit.save()
                logger.info("Found exercise for orphan audit")
            except ObjectDoesNotExist:
                pass

    def add_exercise(self, exercise_path, course):
        progress = []
        translation_name = {}
        fullpath = os.path.join(course.get_exercises_path(), exercise_path)
        if not exercise_path.startswith("/"):
            raise ExerciseParseError("Exercise path does not start with a /")
        if not is_exercise(course.get_exercises_path(), exercise_path):
            raise ExerciseNotFound(fullpath)
        exercisetree = exercise_xmltree(course.get_exercises_path(), exercise_path)
        exercisename_xml = exercisetree.xpath('/exercise/exercisename')
        if exercisename_xml:
            translation_name = get_translations(exercisename_xml[0])
        name = (exercisetree.xpath('/exercise/exercisename/text()') or ['No name'])[0]
        key = exercise_key_get_or_create(course.get_exercises_path(), exercise_path)
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

        for question in Question.objects.filter(exercise=dbexercise):
            bool_list = map(lambda q: q.get('key') == question.question_key, questions)
            exists = reduce(lambda a, b: a or b, bool_list, False)
            if not exists:
                question.delete()
        progress.extend(
            exercise_check_thumbnail(course.get_exercises_path(), exercisetree, exercise_path)
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
        exercises_path = course.get_exercises_path()
        for root, directories, filenames in os.walk(course.get_exercises_path(), followlinks=True):
            for filename in filenames:
                if filename == 'exercise.xml':
                    name = os.path.basename(os.path.normpath(root))
                    relpath = root[len(exercises_path) :]
                    exerciselist.append((name, relpath))

        for name, path in exerciselist:
            try:
                key = exercise_key_get(exercises_path, path)
                if key in keys:
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
            if not is_exercise(exercises_path, exercise.path):
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
                    key = exercise_key_get(exercises_path, path)
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
            if not is_exercise(exercises_path, exercise.path):
                exercise.delete()
                progress.append(
                    (
                        'warning',
                        _("Deleted ")
                        + exercise.path
                        + _(" since it is not present on disc anymore"),
                    )
                )
                print('Deleting non existing ' + fullpath + ' from database.')
            else:
                key = exercise_key_get_or_create(exercises_path, exercise.path)
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

        self.mend_answers_and_audits()
        progress.append(('success', _("Finished syncing exercises.")))
        yield progress


class Exercise(models.Model):
    exercise_key = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255, default="")
    translated_name = models.CharField(max_length=512, default="{}")
    path = models.TextField()
    folder = models.TextField(default="")
    course = models.ForeignKey(Course, related_name="exercises", null=True)
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

    def user_is_correct(self, user):
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

    def user_tried_all(self, user):
        tried_all = True
        questions = Question.objects.filter(exercise=self)
        if not questions:
            return False
        for question in questions:
            try:
                Answer.objects.filter(user=user, question=question).latest('date')
            except Answer.DoesNotExist:
                tried_all = False
        return tried_all


class Question(models.Model):
    class Meta:
        unique_together = ('question_key', 'exercise')
        permissions = (("log_question", "Answers are logged"),)

    question_key = models.CharField(max_length=255)
    exercise = models.ForeignKey(Exercise, related_name='question', on_delete=models.CASCADE)
    type = models.CharField(max_length=255, default='none')

    def __str__(self):
        return self.exercise.name + ": " + self.question_key


class Answer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(
        Question, on_delete=models.SET_NULL, null=True, related_name='answer'
    )
    question_key = models.CharField(max_length=255, default='')
    exercise_key = models.CharField(max_length=255, default='')
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
    exercise_key = models.CharField(max_length=255, default='')
    date = models.DateTimeField(default=now)
    filetype = models.CharField(max_length=3, choices=FILETYPE_CHOICES, default=IMAGE)
    image = models.ImageField(default=None, blank=True, null=True, upload_to=answer_image_filename)
    pdf = models.FileField(default=None, blank=True, null=True, upload_to=answer_image_filename)
    image_thumb = ImageSpecField(
        source='image', processors=[ResizeToFill(100, 50)], format='JPEG', options={'quality': 60}
    )

    def __str__(self):
        try:
            return self.user.username + " image for " + self.exercise.name
        except AttributeError:
            return "__Orphan__"


class ExerciseMeta(models.Model):
    DIFFICULTIES = ((1, 'Easy'), (2, 'Medium'), (3, 'Hard'))
    exercise = models.OneToOneField(Exercise, related_name='meta', on_delete=models.CASCADE)
    exercise_key = models.CharField(max_length=255, default='')
    deadline_date = models.DateField(default=None, null=True, blank=True)
    solution = models.BooleanField(default=False, verbose_name='Publish solution')
    difficulty = models.IntegerField(null=True, blank=True, choices=DIFFICULTIES, default=None)
    required = models.BooleanField(default=False, verbose_name='Obligatory')
    image = models.BooleanField(default=False, verbose_name='Image upload')
    allow_pdf = models.BooleanField(default=False, verbose_name='Allow pdf as image upload')
    bonus = models.BooleanField(default=False)
    server_reply_time = models.DurationField(default=None, null=True, blank=True)
    published = models.BooleanField(default=False)
    sort_key = models.CharField(max_length=255, default='', verbose_name='Sort order key')
    feedback = models.BooleanField(default=True, verbose_name='Feedback to student')

    def __str__(self):
        return self.exercise.name


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
    exercise_key = models.CharField(max_length=255, default='')
    subject = models.CharField(max_length=255, default='', blank=True)
    message = models.TextField(default="", blank=True)
    published = models.BooleanField(default=False)  # Audit shown to student
    force_passed = models.BooleanField(default=False)
    date = models.DateTimeField(default=now)
    sent = models.BooleanField(default=False)
    revision_needed = models.NullBooleanField(blank=True, default=None)
    updated = models.BooleanField(default=False)
    updated_date = models.DateTimeField(null=True, blank=True, default=None)

    objects = AuditManager()

    class Meta:
        unique_together = (("student", "exercise"),)  # Only one audit per student and exercise


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
    pdf = models.FileField(default=None, blank=True, null=True, upload_to=audit_response_filename)
    image_thumb = ImageSpecField(
        source='image', processors=[ResizeToFill(100, 50)], format='JPEG', options={'quality': 60}
    )
