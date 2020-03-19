from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from course.models import Course
from exercises.parsing import exercise_xmltree, question_xmltree_get
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
from statistics import median, mean
from exercises.modelhelpers import e_student_tried, get_all_who_tried, bonafide_students


def folder_structure(exercise_data_func_list):
    folders = {}
    exercises = Exercise.objects.all()
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
    ordered_folders = OrderedDict(sorted(folders.items(), key=lambda t: t[0]))
    for exercise in exercises:

        def reduce_data_func(prev, next):
            prev.update(next(exercise))
            return prev

        data = reduce(reduce_data_func, exercise_data_func_list, {})
        paths = list(filter(lambda x: x != '', exercise.path.split('/')[1:-1]))
        root = reduce(lambda a, b: a['folders'].get(b)['content'], paths, ordered_folders)
        if 'exercises' not in root:
            root['exercises'] = {}
        root['exercises'].update({exercise.exercise_key: data})
    return ordered_folders


def exercise_folder_structure(manager, user, course, exercisefilter):
    def recursive_dict():
        return defaultdict(recursive_dict)

    folders = recursive_dict()
    exercises = []
    groups = User.objects.get(username=user).groups.all()
    can_see_unpublished = (
        groups.filter(name='Admin').exists()
        or groups.filter(name='Author').exists()
        or user.has_perm('exercises.view_unpublished')
    )
    # print("can_see_unpublished initially = ", can_see_unpublished )
    if can_see_unpublished:
        exercises = manager.filter(course=course).prefetch_related(
            Prefetch(
                'question__answer',
                queryset=Answer.objects.filter(user=user).order_by('-date'),
                to_attr="useranswers",
            ),
            'meta',
        )
    else:
        exercises = manager.filter(meta__published=True, course=course).select_related('meta')

    if not exercisefilter.get('unpublished_exercises',False):
        exercises = exercises.filter(meta__published=True)
    if not exercisefilter.get('required_exercises',False):
        exercises = exercises.filter(meta__required=False)
    if not exercisefilter.get('bonus_exercises',False):
        exercises = exercises.filter(meta__bonus=False)
    if not exercisefilter.get('optional_exercises',False):
        optional = exercises.filter(meta__required=False, meta__bonus=False)
        exercises = exercises.difference(optional)

    paths = map(lambda x: os.path.dirname(x.path), exercises)
    unique_paths = filter(lambda x: x != '', set(paths))
    folders['path'] = ['']
    for path in list(map(lambda x: x.split('/'), unique_paths)):
        root = folders
        fullpath = []
        for item in path:
            fullpath.append(item)
            root = root['folders'][item]['content']
            if 'path' not in root:
                root['path'] = list(fullpath)

    for exercise in exercises:
        allcorrect = True
        for question in exercise.question.all():
            try:
                if hasattr(question, 'useranswers') and question.useranswers:
                    if not question.useranswers[0].correct:
                        allcorrect = False
            except ObjectDoesNotExist:
                allcorrect = False
        paths = list(filter(lambda x: x != '', exercise.path.split('/')[:-1]))
        root = reduce(lambda a, b: a['folders'].get(b)['content'], paths, folders)

        if 'exercises' not in root:
            root['exercises'] = {}
            root['order'] = []
        exercise_meta = (
            ExerciseMetaSerializer(exercise.meta).data if hasattr(exercise, 'meta') else {}
        )
        root['exercises'].update(
            {
                exercise.exercise_key: {
                    'name': exercise.name,
                    'translated_name': json.loads(exercise.translated_name),
                    'correct': allcorrect,
                    'meta': exercise_meta,
                }
            }
        )

    def add_sort_order(node):
        key_func = [('published', lambda x: str(not x)), ('sort_key', str)]

        def sort_key_func(exercisekey):
            return "".join(
                [func(node['exercises'][exercisekey]['meta'][key]) for (key, func) in key_func]
            )

        if 'exercises' in node:
            node['order'] = list(node['exercises'].keys())
            node['order'].sort(key=sort_key_func)
        if 'folders' in node:
            for key, value in node['folders'].items():
                add_sort_order(value['content'])

    add_sort_order(folders)
    return folders
