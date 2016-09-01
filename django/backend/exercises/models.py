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
)
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from exercises.util import deep_get, nested_print
from functools import partial
import json as JSON


class ExerciseManager(models.Manager):
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
        try:
            json = exercise_validate_and_json(path)
        except ExerciseParseError as e:
            result['error'] = str(e)
        name = deep_get(json, 'exercise', 'exercisename', '$', default="No name")
        key = exercise_key_get_or_create(path)
        dbexercise, created = self.update_or_create(
            exercise_key=key, defaults={'name': name, 'path': path, 'folder': os.path.dirname(path)}
        )
        if created:
            print('Adding ' + path + '/' + name + ' to database.')
        else:
            print('Updated ' + path + '/' + name)
        questions = deep_get(json, 'exercise', 'question', default=[])
        # def merge_attrs(question):
        #    if '@attr' in question:
        #        for attr, value in question['@attr'].items():
        #            question['@' + attr] = value
        #    return question
        # questions = list(map(merge_attrs, questions))
        keys = [q['@attr']['key'] for q in questions if '@attr' in q and 'key' in q['@attr']]
        if len(keys) > len(set(keys)):
            raise ExerciseParseError("Duplicate question keys!")
        for question in questions:
            if not question_validate(question):
                print(path + " contains invalid question: ")
                nested_print(question)
                raise ExerciseParseError("Invalid question in " + name)
            dbquestion, created = Question.objects.update_or_create(
                exercise=dbexercise,
                question_key=question['@attr']['key'],
                defaults={'type': question['@attr']['type']},
            )
            if created:
                print(
                    name
                    + ': Adding question '
                    + question['@attr']['key']
                    + ' of type '
                    + question['@attr']['type']
                )
            else:
                print(
                    name
                    + ': Updating question '
                    + question['@attr']['key']
                    + ' of type '
                    + question['@attr']['type']
                )

        for question in Question.objects.filter(exercise=dbexercise):
            bool_list = map(
                lambda jsonitem: jsonitem['@attr']['key'] == question.question_key, questions
            )
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
        self.mend_answers()

    def folder_structure(self, user):
        folders = {}
        exercises = self.all()
        paths = map(lambda x: os.path.dirname(x.path), exercises)
        unique_paths = filter(lambda x: x != '/', set(paths))
        for path in list(map(lambda x: x.split('/')[1:], unique_paths)):
            traverse = folders
            for folder in path:
                if not ('folders' in traverse):
                    traverse['folders'] = {}
                if folder in traverse['folders']:
                    traverse = traverse['folders'][folder]['content']
                else:
                    traverse['folders'][folder] = {'content': {}}
        for exercise in exercises:
            # If this becomes a speed issue this should be done by getting all the answers and then populating the tree
            allcorrect = True
            questions = Question.objects.filter(exercise=exercise)
            print("Exercise: " + str(exercise) + " " + str(questions.count()))
            for question in questions:
                try:
                    answer = Answer.objects.filter(user=user, question=question).latest('date')
                    print("dbcorrect: " + str(answer.correct))
                    if not answer.correct:
                        allcorrect = False
                except ObjectDoesNotExist:
                    allcorrect = False
                print(allcorrect)
            paths = list(filter(lambda x: x != '', exercise.path.split('/')[1:-1]))
            root = reduce(lambda a, b: a['folders'].get(b)['content'], paths, folders)
            if 'exercises' not in root:
                root['exercises'] = {}
            root['exercises'].update(
                {exercise.exercise_key: {'name': exercise.name, 'correct': allcorrect}}
            )
        return folders


class Exercise(models.Model):
    exercise_key = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255, default="")
    path = models.TextField()
    folder = models.TextField(default="")
    objects = ExerciseManager()

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


class Question(models.Model):
    class Meta:
        unique_together = ('question_key', 'exercise')

    question_key = models.CharField(max_length=255)
    exercise = models.ForeignKey(Exercise)
    type = models.CharField(max_length=255, default='none')

    def __str__(self):
        return self.exercise.name + ": " + self.question_key


class Answer(models.Model):
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
        )
