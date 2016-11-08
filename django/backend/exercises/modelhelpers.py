from exercises.models import Exercise, ExerciseMeta, Question, Answer, ImageAnswer
from exercises.parsing import exercise_xmltree, question_xmltree_get
from exercises.question import question_check
from django.contrib.auth.models import User
from exercises.serializers import ExerciseSerializer, ExerciseMetaSerializer, AnswerSerializer
import json
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch, Count, Case, When, Avg
import os
from functools import reduce
from collections import OrderedDict

# import cProfile
import pprofile
from .util import nested_print
import datetime
from django.utils import timezone
import pytz


def e_name(exercise):
    return {'name': exercise.name}


def e_path(exercise):
    return {'path': exercise.path}


def e_student_attempt_count(exercise):
    return {
        'attempts': Answer.objects.filter(
            question__exercise=exercise, user__groups__name="Student"
        ).count()
    }


def e_student_mean_attempt_count(exercise):
    users = User.objects.filter(groups__name='Student')
    attempts = users.filter(answer__question__exercise=exercise).annotate(
        attempts=Count('answer')
    )  # .values_list('username', 'attempts')
    mean_attempts = attempts.aggregate(Avg('attempts'))
    return {
        'mean_attempts': mean_attempts['attempts__avg'],
        #'attempts': attempts.values_list('username', 'attempts')
    }


def e_student_percent_complete(exercise):
    users = User.objects.filter(groups__name='Student')
    n_students = users.count()
    # userdata = users.prefetch_related(
    #        Prefetch(
    #            'answer_set',
    #            queryset = Answer.objects.filter(question__exercise=exercise).filter(correct=True).filter(date__lt=datetime.datetime.combine(exercise.meta.deadline_date, datetime.time(8,0,0, tzinfo=pytz.UTC))).order_by('-date'),
    #            to_attr = 'answers'
    #            ))
    questions = Question.objects.filter(exercise=exercise)
    correct = []
    for question in questions:
        if exercise.meta.deadline_date:
            correct.append(
                set(
                    users.filter(
                        answer__correct=True,
                        answer__question=question,
                        answer__date__lt=datetime.datetime.combine(
                            exercise.meta.deadline_date, datetime.time(8, 0, 0, tzinfo=pytz.UTC)
                        ),
                    )
                    .values_list('username', flat=True)
                    .distinct()
                )
            )
        else:
            correct.append(
                set(
                    users.filter(answer__correct=True, answer__question=question)
                    .values_list('username', flat=True)
                    .distinct()
                )
            )
    allcorrect = set.intersection(*map(set, correct))
    return {'percent': len(allcorrect) / n_students, 'deadline': exercise.meta.deadline_date}


def exercise_list_data(exercise_data_func_list):
    exercises = Exercise.objects.all()
    result = {}
    for exercise in exercises:

        def reduce_data_func(prev, next):
            prev.update(next(exercise))
            return prev

        data = reduce(reduce_data_func, exercise_data_func_list, {})
        result[exercise.exercise_key] = data
    return result


def folder_structure(exercise_data_func_list):  # {{{
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
    # print(ordered_folders)
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
    return ordered_folders  # }}}


def exercise_folder_structure(manager, user):  # {{{
    folders = {}
    exercises = []
    if user.has_perm('exercises.edit_exercise'):
        exercises = manager.prefetch_related(
            Prefetch(
                'question__answer',
                queryset=Answer.objects.filter(user=user).order_by('-date'),
                to_attr="useranswers",
            ),
            'meta',
        )
    else:
        exercises = manager.filter(meta__published=True).select_related('meta')
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
        allcorrect = True
        for question in exercise.question.all():  # questions:
            try:
                if hasattr(question, 'useranswers') and question.useranswers:
                    if not question.useranswers[0].correct:
                        allcorrect = False
            except ObjectDoesNotExist:
                allcorrect = False
        paths = list(filter(lambda x: x != '', exercise.path.split('/')[1:-1]))
        root = reduce(lambda a, b: a['folders'].get(b)['content'], paths, folders)
        if 'exercises' not in root:
            root['exercises'] = {}
            root['order'] = []
        root['exercises'].update(
            {
                exercise.exercise_key: {
                    'name': exercise.name,
                    'correct': allcorrect,
                    'meta': ExerciseMetaSerializer(exercise.meta).data
                    if hasattr(exercise, 'meta')
                    else {},
                }
            }
        )

    def add_sort_order(node):
        if 'exercises' in node:
            node['order'] = list(node['exercises'].keys())
            node['order'].sort(
                key=lambda exercisekey: node['exercises'][exercisekey]['meta']['sort_key']
            )
        if 'folders' in node:
            for key, value in node['folders'].items():
                add_sort_order(value['content'])

    add_sort_order(folders)
    return folders  # }}}


def serialize_exercise_with_question_data(exercise, user):  # {{{
    questions = Question.objects.filter(exercise=exercise)
    correct = exercise.user_is_correct(user)
    serializer = ExerciseSerializer(exercise)
    data = serializer.data
    data['question'] = {}
    data['correct'] = correct
    # try:
    #    meta = ExerciseMeta.objects.get(exercise=exercise)
    #    metaser = ExerciseMetaSerializer(meta)
    #    data['meta'] = metaser.data
    # except ObjectDoesNotExist:
    #    pass
    image_answers = ImageAnswer.objects.filter(user=user, exercise=exercise)
    image_answers_ids = [image_answer.pk for image_answer in image_answers]
    data['image_answers'] = image_answers_ids
    for question in questions:
        try:
            dbanswer = Answer.objects.filter(user=user, question=question).latest('date')
            serializer = AnswerSerializer(dbanswer)
            response = json.loads(dbanswer.grader_response)
            data['question'][question.question_key] = serializer.data
            data['question'][question.question_key]['response'] = response
        except ObjectDoesNotExist:
            pass
    return data  # }}}


def student_attempts_exercises():  # {{{
    exercises = Exercise.objects.all()
    allattempts = []
    folders = folder_structure([e_name, e_path, e_student_attempt_count])
    return folders  # }}}


def student_statistics_exercises():  # {{{
    data = exercise_list_data(
        [e_name, e_path, e_student_percent_complete, e_student_mean_attempt_count]
    )
    return data  # }}}


def exercise_test(exercise_key):
    dbexercise = Exercise.objects.get(exercise_key=exercise_key)
    dbquestions = Question.objects.filter(exercise=dbexercise)
    xmltree = exercise_xmltree(dbexercise.path)
    user = User.objects.get(username='tester')
    results = []
    for dbquestion in dbquestions:
        question_key = dbquestion.question_key
        question_xml = question_xmltree_get(xmltree, question_key)
        answer = question_xml.find('expression').text.split(';')[0]
        result = {}
        try:
            result = question_check(user, "tester", exercise_key, question_key, answer)
        except Exception as e:
            result['exception'] = str(e)
        result.update({'answer': answer})
        results.append(result)
    return results
