# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from django.http import Http404
from django.core.cache import caches
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
from statistics import median, mean
from exercises.modelhelpers import e_student_tried, get_all_who_tried, bonafide_students, get_selectedExercisesKeys
import logging

logger = logging.getLogger(__name__)



#def nofolder_structure(exercise_data_func_list):
#    folders = {}
#    exercises = Exercise.objects.all()
#    paths = map(lambda x: os.path.dirname(x.path), exercises)
#    unique_paths = filter(lambda x: x != "/", set(paths))
#    for path in list(map(lambda x: x.split("/")[1:], unique_paths)):
#        traverse = folders
#        for folder in path:
#            if not ("folders" in traverse):
#                traverse["folders"] = {}
#            if folder in traverse["folders"]:
#                traverse = traverse["folders"][folder]["content"]
#            else:
#                traverse["folders"][folder] = {"content": {}}
#    ordered_folders = OrderedDict(sorted(folders.items(), key=lambda t: t[0]))
#    for exercise in exercises:
#
#        def reduce_data_func(prev, next):
#            prev.update(next(exercise))
#            return prev
#
#        data = reduce(reduce_data_func, exercise_data_func_list, {})
#        paths = list(filter(lambda x: x != "", exercise.path.split("/")[1:-1]))
#        root = reduce(lambda a, b: a["folders"].get(b)["content"], paths, ordered_folders)
#        if "exercises" not in root:
#            root["exercises"] = {}
#        root["exercises"].update({exercise.exercise_key: data})
#    return ordered_folders



def exercise_folder_structure(manager, user, course, exercisefilter,db):
    def recursive_dict():
        return defaultdict(recursive_dict)
    db = course.opentasite
    base = course.get_exercises_path(db)

    newfolder = os.path.join(base, settings.NEW_FOLDER)
    if os.path.isdir(newfolder):
        newcontents = os.listdir(newfolder)
    else:
        newcontents = []
    new_paths = [os.path.join(settings.NEW_FOLDER, item) for item in newcontents]

    trashfolder = os.path.join(base, settings.TRASH_FOLDER)
    if os.path.isdir(trashfolder):
        trashcontents = os.listdir(trashfolder)
    else:
        trashcontents = []
    trash_paths = [os.path.join(settings.TRASH_FOLDER, item) for item in trashcontents]

    # print("MODELHELPERS newcontents = ", newcontents)
    folders = recursive_dict()
    exercises = []
    groups = list(user.groups.values_list("name", flat=True))
    try:
        can_see_unpublished = "Admin" in groups or "Author" in groups or user.has_perm("exercises.view_unpublished")

    except Exception as e:
        logger.error(
            f"ERROR E99234 FOLDER_STRUCTURE UNKNOWN USER {type(e).__name__} course={course} groups={groups} user={user}  does not belong to any group."
        )
        logger.error(f"ERROR E99234 THIS ERROR MUST BE FIXED WHEN IT IS CLEAR WHAT USER TRIGGERS THE ERROR")
        can_see_unpublished = False
    # #print("can_see_unpublished initially = ", can_see_unpublished )
    if can_see_unpublished:
        exercises = manager.filter(course=course).prefetch_related(
            Prefetch(
                "question__answer",
                queryset=Answer.objects.using(db).filter(user=user).order_by("-date"),
                to_attr="useranswers",
            ),
            "meta",
        )
        new_exercises = Exercise.objects.using(db).filter(path__in=new_paths)
        trash_exercises = Exercise.objects.using(db).filter(path__in=trash_paths)
    else:
        exercises = manager.filter(meta__published=True, course=course).exclude(path__in=trash_paths).select_related("meta")
        new_exercises = False
        trash_exercises = False

    #if not hasattr(settings, 'USE_CHATGPT' ) or not settings.USE_CHATGPT :
    #    exercises = exercises.exclude(question__type='aibased')

    #cachekey = user.username + db + 'selectedExercises'
    #selectedExercisesKeys = caches['default'].get( cachekey )
    selectedExercisesKeys = get_selectedExercisesKeys( user, db )
    if selectedExercisesKeys :
        selectedExercises = Exercise.objects.using(db).filter(exercise_key__in=selectedExercisesKeys)
    else :
        selectedExercises = None

    if not exercisefilter.get("unpublished_exercises", False):
        exercises = exercises.filter(meta__published=True)
    if not exercisefilter.get("required_exercises", False):
        exercises = exercises.filter(meta__required=False)
    if not exercisefilter.get("bonus_exercises", False):
        exercises = exercises.filter(meta__bonus=False)
    if not exercisefilter.get("optional_exercises", False):
        optional = exercises.filter(meta__required=False, meta__bonus=False)
        exercises = exercises.difference(optional)
    if new_exercises:
        exercises = exercises.union(new_exercises)
    if trash_exercises:
        exercises = exercises.union(trash_exercises)
    if selectedExercises :
        exercises = exercises.union( selectedExercises)
    #if hasattr( settings, 'USE_CHATGPT' ) and settings.USE_CHATGPT :
    #    pass
    #else :

    paths = map(lambda x: os.path.dirname(x.path), exercises)
    # for path in list( paths ) :
    #    print("PATH = %s " %  path )
    unique_paths = filter(lambda x: x != "", set(paths))
    folders["path"] = [""]
    for path in list(map(lambda x: x.split("/"), unique_paths)):
        root = folders
        fullpath = []
        for item in path:
            fullpath.append(item)
            root = root["folders"][item]["content"]
            if "path" not in root:
                root["path"] = list(fullpath)

    for exercise in exercises:
        allcorrect = True
        for question in exercise.question.all():
            try:
                if hasattr(question, "useranswers") and question.useranswers:
                    if not question.useranswers[0].correct:
                        allcorrect = False
            except ObjectDoesNotExist:
                allcorrect = False
        paths = list(filter(lambda x: x != "", exercise.path.split("/")[:-1]))
        root = reduce(lambda a, b: a["folders"].get(b)["content"], paths, folders)
        if "exercises" not in root:
            root["exercises"] = {}
            root["order"] = []
        exercise_meta = ExerciseMetaSerializer(exercise.meta).data if hasattr(exercise, "meta") else {}
        root["exercises"].update(
            {
                exercise.exercise_key: {
                    "name": exercise.name,
                    "translated_name": json.loads(exercise.translated_name),
                    "correct": allcorrect,
                    "meta": exercise_meta,
                }
            }
        )

    def add_sort_order(node):
        key_func = [("published", lambda x: str(not x)), ("sort_key", str)]

        def sort_key_func(exercisekey):
            try:
                res = "".join([func(node["exercises"][exercisekey]["meta"][key]) for (key, func) in key_func])
            except KeyError:
                res = "ZZZ"
            return res

        if "exercises" in node:
            node["order"] = list(node["exercises"].keys())
            node["order"].sort(key=sort_key_func)
        if "folders" in node:
            for key, value in node["folders"].items():
                add_sort_order(value["content"])

    # print("FOLDERS  = %s " % folders)

    add_sort_order(folders)
    return folders
