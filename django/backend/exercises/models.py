from django.db import models
import os
from functools import reduce
from exercises.paths import EXERCISES_PATH
from exercises.parsing import deep_get, legacy_process_questions, exerciseJSON, parseLegacyXMLtoJSON
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
import exercises.util as util
from functools import partial
import json as JSON

# /Dynamics/Week 1/problem1
# /Dynamics/Week 1/problem2
# /Dynamics/Week 2/problem1
# /Statics/Week 1/problem1
# /Statics/Week 1/problem2
# /Statics/Week 2/problem1

# Folders [ Name ]


class ExerciseManager(models.Manager):
    def add_legacy_exercise(self, path):
        (valid, json) = parseLegacyXMLtoJSON(path)
        if valid:
            name = deep_get(json, 'problem', 'name', '$')
            key = deep_get(json, 'problem', '@key')
            if not key:
                print('No key for ' + path)
            else:
                dbexercise, created = self.get_or_create(
                    exercise_key=key,
                    defaults={'name': name, 'path': path, 'folder': os.path.dirname(path)},
                )
                if created:
                    print('Adding ' + path + '/' + name + ' to database.')
                questions = deep_get(json, 'problem', 'thecorrectanswer')
                # util.nested_print(list(proper_questions))
                proper_questions = legacy_process_questions(questions)
                for question in proper_questions:
                    dbquestion, created = Question.objects.get_or_create(
                        exercise=dbexercise, question_id=question['@id']
                    )
                for question in Question.objects.filter(exercise=dbexercise):
                    bool_list = map(
                        lambda jsonitem: jsonitem['@id'] == question.question_id, proper_questions
                    )
                    exists = reduce(lambda a, b: a or b, bool_list, False)
                    if not exists:
                        question.delete()

    def sync_with_disc(self):
        print("Syncing with disc...")
        exerciselist = []
        for root, directories, filenames in os.walk(EXERCISES_PATH):
            for filename in filenames:
                if filename == 'problem.xml':
                    print(root)
                    name = os.path.basename(os.path.normpath(root))
                    relpath = root[len(EXERCISES_PATH) :]
                    exerciselist.append((name, relpath))
        for name, path in exerciselist:
            self.add_legacy_exercise(path)
        for exercise in self.all():
            fullpath = exercise.path + '/problem.xml'
            (valid, _) = parseLegacyXMLtoJSON(exercise.path)
            if not os.path.isfile(EXERCISES_PATH + fullpath) or not valid:
                exercise.delete()
                print('Deleting non existing ' + fullpath + ' from database.')

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
        unique_together = ('question_id', 'exercise')

    question_id = models.CharField(max_length=255)
    exercise = models.ForeignKey(Exercise)

    def __str__(self):
        return self.exercise.name + ": " + self.question_id


class Answer(models.Model):
    user = models.ForeignKey(User)
    question = models.ForeignKey(Question)
    answer = models.TextField()
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
