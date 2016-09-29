from django.db import models
import os
from functools import reduce
from exercises.paths import EXERCISES_PATH
from exercises.parsing import (
    exercise_validate_and_json,
    question_validate,
    ExerciseParseError,
    exercise_key_get_or_create,
    is_exercise,
    ExerciseNotFound,
    exercise_xmltree,
    question_validate_xmltree,
)
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from exercises.util import deep_get, nested_print
from functools import partial
from datetime import timedelta
import json as JSON
import uuid


class ExerciseManager(models.Manager):  # {{{
    def mend_answers(self):
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
                print("Found question for orphan answer")
            except ObjectDoesNotExist:
                pass

    def add_exercise(self, path):
        result = {}
        json = {}
        if not is_exercise(path):
            raise ExerciseNotFound(path)
        exercisetree = exercise_xmltree(path)
        # except ExerciseParseError as e:
        #    result['error'] = str(e)
        name = (exercisetree.xpath('/exercise/exercisename/text()') or ['No name'])[0]
        key = exercise_key_get_or_create(path)
        dbexercise, created = self.update_or_create(
            exercise_key=key, defaults={'name': name, 'path': path, 'folder': os.path.dirname(path)}
        )
        if created:
            print('Adding ' + path + '/' + name + ' to database.')
        else:
            print('Updated ' + path + '/' + name)
        questions = exercisetree.xpath('/exercise/question[@key and @type]')
        keys = [x.get('key') for x in questions]
        if len(keys) > len(set(keys)):
            raise ExerciseParseError("Duplicate question keys!")
        for question in questions:
            if not question_validate_xmltree(question):
                print(path + " contains invalid question: ")
                nested_print(question)
                raise ExerciseParseError("Invalid question in " + name)
            dbquestion, created = Question.objects.update_or_create(
                exercise=dbexercise,
                question_key=question.get('key'),
                defaults={'type': question.get('type')},
            )
            if created:
                print(
                    name
                    + ': Adding question '
                    + question.get('key')
                    + ' of type '
                    + question.get('type')
                )
            else:
                print(
                    name
                    + ': Updating question '
                    + question.get('key')
                    + ' of type '
                    + question.get('type')
                )

        for question in Question.objects.filter(exercise=dbexercise):
            bool_list = map(lambda q: q.get('key') == question.question_key, questions)
            exists = reduce(lambda a, b: a or b, bool_list, False)
            if not exists:
                question.delete()

    def sync_with_disc(self):
        print("Syncing with disc...")
        exerciselist = []
        for root, directories, filenames in os.walk(EXERCISES_PATH):
            for filename in filenames:
                if filename == 'exercise.xml':
                    name = os.path.basename(os.path.normpath(root))
                    relpath = root[len(EXERCISES_PATH) :]
                    exerciselist.append((name, relpath))
        for name, path in exerciselist:
            try:
                self.add_exercise(path)
            except (ExerciseParseError, IOError) as e:
                print("Failed to add " + name + " because " + str(e))
        for exercise in self.all():
            fullpath = exercise.path + '/exercise.xml'
            if not is_exercise(exercise.path):
                exercise.delete()
                print('Deleting non existing ' + fullpath + ' from database.')
        self.mend_answers()  # }}}


class Exercise(models.Model):
    exercise_key = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255, default="")
    path = models.TextField()
    folder = models.TextField(default="")
    objects = ExerciseManager()

    class Meta:
        permissions = (
            ("reload_exercise", "Can reload exercises from disk"),
            ("edit_exercise", "Can edit exercises in frontend"),
            ("create_exercise", "Can create exercises in frontend"),
            ("administer_exercise", "Can administer exercise options"),
        )

    def __str__(self):
        return self.name + ': ' + self.path

    def user_is_correct(self, user):  # {{{
        allcorrect = True
        questions = Question.objects.filter(exercise=self)
        for question in questions:
            try:
                answer = Answer.objects.filter(user=user, question=question).latest('date')
                if not answer.correct:
                    allcorrect = False
            except ObjectDoesNotExist:
                allcorrect = False
        return allcorrect  # }}}


class Question(models.Model):  # {{{
    class Meta:
        unique_together = ('question_key', 'exercise')
        permissions = (("log_question", "Answers are logged"),)

    question_key = models.CharField(max_length=255)
    exercise = models.ForeignKey(Exercise)
    type = models.CharField(max_length=255, default='none')

    def __str__(self):
        return self.exercise.name + ": " + self.question_key  # }}}


class Answer(models.Model):  # {{{
    user = models.ForeignKey(User)
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True)
    question_key = models.CharField(max_length=255, default='')
    exercise_key = models.CharField(max_length=255, default='')
    answer = models.TextField()
    grader_response = models.TextField(default='')
    correct = models.BooleanField()
    date = models.DateTimeField(default=now)

    def __str__(self):
        return (
            self.user.username
            + " answered {"
            + self.answer
            + "} which is "
            + ("correct" if self.correct else "incorrect")
        )  # }}}


def answer_image_filename(instance, filename):  # {{{
    return '/'.join(
        [
            'answerimages',
            instance.user.username,
            instance.exercise.exercise_key,
            str(uuid.uuid4()) + os.path.splitext(filename)[1],
        ]
    )  # }}}


class ImageAnswer(models.Model):  # {{{
    user = models.ForeignKey(User)
    exercise = models.ForeignKey(Exercise)
    exercise_key = models.CharField(max_length=255, default='')
    date = models.DateTimeField(default=now)
    image = models.ImageField(upload_to=answer_image_filename)
    image_thumb = ImageSpecField(
        source='image', processors=[ResizeToFill(100, 50)], format='JPEG', options={'quality': 60}
    )

    def __str__(self):
        return self.user.username + " image for " + self.exercise.name  # }}}


class ExerciseMeta(models.Model):  # {{{
    DIFFICULTIES = ((1, 'Easy'), (2, 'Medium'), (3, 'Hard'))
    exercise = models.OneToOneField(Exercise, related_name='meta')
    exercise_key = models.CharField(max_length=255, default='')
    deadline_date = models.DateField(default=None, null=True, blank=True)
    pdf_solution = models.BooleanField(default=False)
    difficulty = models.IntegerField(null=True, blank=True, choices=DIFFICULTIES, default=None)
    required = models.BooleanField(default=False)
    image = models.BooleanField(default=False)
    bonus = models.BooleanField(default=False)
    server_reply_time = models.DurationField(default=None, null=True, blank=True)

    def __str__(self):
        return self.exercise.name

    # }}}
