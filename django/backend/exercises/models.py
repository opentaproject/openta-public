from django.db import models
import os
from functools import reduce
from exercises.paths import EXERCISES_PATH
from exercises.parsing import deep_get, exerciseJSON

# /Dynamics/Week 1/problem1
# /Dynamics/Week 1/problem2
# /Dynamics/Week 2/problem1
# /Statics/Week 1/problem1
# /Statics/Week 1/problem2
# /Statics/Week 2/problem1

# Folders [ Name ]


class ExerciseManager(models.Manager):
    def sync_with_disc(self):
        exerciselist = []
        for root, directories, filenames in os.walk(EXERCISES_PATH):
            for filename in filenames:
                if filename == 'problem.xml':
                    name = os.path.basename(os.path.normpath(root))
                    relpath = os.path.dirname(root[len(EXERCISES_PATH) :])
                    exerciselist.append((name, relpath))
        for name, path in exerciselist:
            dbexercise, created = self.get_or_create(exercise_name=name, defaults={'path': path})
            if created:
                print('Adding ' + path + '/' + name + ' to database.')
            json = exerciseJSON(path + '/' + name)
            questions = deep_get(json, 'problem', 'thecorrectanswer')
            for index, question in enumerate(questions):
                question_id = index
                if '@id' in question and question['@id'] != 'ingress':
                    question_id = 'q' + str(question['@id'])
                dbquestion, created = Question.objects.get_or_create(
                    exercise_name=dbexercise, question_id=question_id
                )
        for exercise in self.all():
            fullpath = exercise.path + '/' + exercise.exercise_name + '/problem.xml'
            if not os.path.isfile(EXERCISES_PATH + fullpath):
                exercise.delete()
                print('Deleting non existing ' + fullpath + ' from database.')

    def folder_structure(self):
        folders = {}
        exercises = self.all()
        paths = map(lambda x: x.path, exercises)
        unique_paths = filter(lambda x: x != '/', set(paths))
        for path in list(map(lambda x: x.split('/')[1:], unique_paths)):
            traverse = folders
            for folder in path:
                if folder in traverse:
                    traverse = traverse[folder]
                else:
                    traverse[folder] = {}
        return folders


class Exercise(models.Model):
    exercise_name = models.CharField(primary_key=True, max_length=255)
    path = models.TextField()
    objects = ExerciseManager()


class Question(models.Model):
    class Meta:
        unique_together = ('question_id', 'exercise_name')

    question_id = models.CharField(max_length=255)
    exercise_name = models.ForeignKey(Exercise)
