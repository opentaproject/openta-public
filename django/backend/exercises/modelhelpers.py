from exercises.models import Exercise, ExerciseMeta, Question, Answer, ImageAnswer
from course.models import Course
from exercises.parsing import exercise_xmltree, question_xmltree_get
from exercises.question import question_check
from django.contrib.auth.models import User
from exercises.serializers import ExerciseSerializer, ExerciseMetaSerializer, AnswerSerializer
import json
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch, Count, Case, When, Avg, Q, F
import os
from functools import reduce
from collections import OrderedDict, defaultdict

# import cProfile
import pprofile
from .util import nested_print
import datetime
from django.utils import timezone
import pytz
import pprint


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


def e_student_activity(exercise):
    t1h = timezone.now() - datetime.timedelta(hours=1)
    t24h = timezone.now() - datetime.timedelta(hours=24)
    t1w = timezone.now() - datetime.timedelta(days=7)
    n_questions = exercise.question.all().count()
    if n_questions == 0:
        return {'activity': {'1h': 0, '24h': 0, '1w': 0, 'all': 0}}

    return {
        'activity': {
            '1h': round(
                Answer.objects.filter(
                    date__gt=t1h, question__exercise=exercise, user__groups__name="Student"
                ).count()
                / n_questions
            ),
            '24h': round(
                Answer.objects.filter(
                    date__gt=t24h, question__exercise=exercise, user__groups__name="Student"
                ).count()
                / n_questions
            ),
            '1w': round(
                Answer.objects.filter(
                    date__gt=t1w, question__exercise=exercise, user__groups__name="Student"
                ).count()
                / n_questions
            ),
            'all': round(
                Answer.objects.filter(
                    question__exercise=exercise, user__groups__name="Student"
                ).count()
                / n_questions
            ),
        }
    }


def p_student_activity(data):
    max_1h = max(data.values(), key=lambda exercise: exercise['activity']['1h'])
    max_24h = max(data.values(), key=lambda exercise: exercise['activity']['24h'])
    max_1w = max(data.values(), key=lambda exercise: exercise['activity']['1w'])
    max_all = max(data.values(), key=lambda exercise: exercise['activity']['all'])
    # for item in data.:
    #    print(item)
    return {
        'max_1h': max_1h['activity']['1h'],
        'max_24h': max_24h['activity']['24h'],
        'max_1w': max_1w['activity']['1w'],
        'max_all': max_all['activity']['all'],
    }


def e_student_attempts_mean(exercise):  # {{{
    users = User.objects.filter(groups__name='Student', is_active=True)
    attempts = users.filter(answer__question__exercise=exercise).annotate(
        attempts=Count('answer')
    )  # .values_list('username', 'attempts')
    n_questions = Question.objects.filter(exercise=exercise).count()
    mean_attempts = attempts.aggregate(Avg('attempts'))
    if mean_attempts['attempts__avg'] is not None:
        avg = mean_attempts['attempts__avg'] / n_questions
    else:
        avg = 0
    return {
        'attempts_mean': avg,
        #'attempts': attempts.values_list('username', 'attempts')
    }  # }}}


def e_student_attempts_median(exercise):  # {{{
    users = User.objects.filter(groups__name='Student', is_active=True)
    attempts = users.filter(answer__question__exercise=exercise).annotate(
        attempts=Count('answer')
    )  # .values_list('username', 'attempts')
    n_questions = Question.objects.filter(exercise=exercise).count()
    count = attempts.count()
    median = 0
    if count == 0:
        return {'attempts_median': median}
    values = attempts.order_by('attempts').values_list('attempts', flat=True)
    if count % 2 == 1:
        median = values[int(round(count / 2))]
    else:
        median = sum(values[count / 2 - 1 : count / 2 + 1]) / 2.0
    # mean_attempts = attempts.aggregate(Avg('attempts'))
    return {
        'attempts_median': median / n_questions,
        #'attempts': attempts.values_list('username', 'attempts')
    }  # }}}


def e_student_tried(exercise):  # {{{
    users = User.objects.filter(groups__name='Student', is_active=True, email__isnull=False)
    ntried = users.filter(answer__question__exercise=exercise).distinct().count()
    n_students = users.count()
    return {'ntried': ntried, 'percent_tried': ntried / n_students}  # }}}


def e_student_percent_complete(exercise):  # {{{
    users = User.objects.filter(groups__name='Student', is_active=True, email__isnull=False)
    n_students = users.count()
    # userdata = users.prefetch_related(
    #        Prefetch(
    #            'answer_set',
    #            queryset = Answer.objects.filter(question__exercise=exercise).filter(correct=True).filter(date__lt=datetime.datetime.combine(exercise.meta.deadline_date, datetime.time(8,0,0, tzinfo=pytz.UTC))).order_by('-date'),
    #            to_attr = 'answers'
    #            ))
    tz = pytz.timezone('Europe/Stockholm')
    deadline_time = datetime.time(23, 59, 59, tzinfo=pytz.timezone('Europe/Stockholm'))
    course = Course.objects.first()
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    questions = Question.objects.filter(exercise=exercise)
    complete = []
    correct_answer = []
    for question in questions:
        correct_answer.append(
            set(
                users.filter(answer__correct=True, answer__question=question)
                .values_list('username', flat=True)
                .distinct()
            )
        )
        if exercise.meta.deadline_date:
            complete.append(
                set(
                    users.filter(
                        answer__correct=True,
                        answer__question=question,
                        answer__date__lt=tz.localize(
                            datetime.datetime.combine(exercise.meta.deadline_date, deadline_time)
                        ),
                        imageanswer__exercise=question.exercise,
                    )
                    .values_list('username', flat=True)
                    .distinct()
                )
            )
        else:
            complete.append(
                set(
                    users.filter(answer__correct=True, answer__question=question)
                    .values_list('username', flat=True)
                    .distinct()
                )
            )
    allcomplete = set.intersection(*map(set, complete)) if complete else []
    allcorrect_answer = set.intersection(*map(set, correct_answer)) if correct_answer else []

    return {
        'percent_complete': len(allcomplete) / n_students,
        'percent_correct': len(allcorrect_answer) / n_students,
        'ncomplete': len(allcomplete),
        'ncorrect': len(allcorrect_answer),
        'nstudents': n_students,
        'deadline': exercise.meta.deadline_date,
    }  # }}}


def exercise_list_data(exercise_data_func_list):  # {{{
    exercises = Exercise.objects.all()
    result = {}
    for exercise in exercises:

        def reduce_data_func(prev, next):
            prev.update(next(exercise))
            return prev

        data = reduce(reduce_data_func, exercise_data_func_list, {})
        result[exercise.exercise_key] = data
    return result  # }}}


def post_process_list(data, data_func_list):  # {{{
    def reduce_data_func(prev, next):
        prev.update(next(data))
        return prev

    result = reduce(reduce_data_func, data_func_list, {})
    return result  # }}}


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
    def recursive_dict():
        return defaultdict(recursive_dict)

    folders = recursive_dict()
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
        root = folders
        fullpath = []
        for item in path:
            fullpath.append(item)
            root = root['folders'][item]['content']
            if 'path' not in root:
                root['path'] = list(fullpath)

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
                key=lambda exercisekey: "".join(
                    [
                        func(node['exercises'][exercisekey]['meta'][key])
                        for (key, func) in [('published', lambda x: str(not x)), ('sort_key', str)]
                    ]
                )
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


def exercise_test(exercise_key):  # {{{
    dbexercise = Exercise.objects.get(exercise_key=exercise_key)
    dbquestions = Question.objects.filter(exercise=dbexercise)
    xmltree = exercise_xmltree(dbexercise.path)
    user = User.objects.get(username='tester')
    results = []
    for dbquestion in dbquestions:
        if dbquestion.type == 'compareNumeric':
            question_key = dbquestion.question_key
            question_xml = question_xmltree_get(xmltree, question_key)
            answer_element = question_xml.find('expression')
            if answer_element is not None:
                answer = answer_element.text.split(';')[0]
                result = {}
                try:
                    result = question_check(user, "tester", exercise_key, question_key, answer)
                except Exception as e:
                    result['exception'] = str(e)
                result.update({'answer': answer})
                results.append(result)
    return results  # }}}


def get_passed_exercises(exercise_queryset, user):
    questions = Question.objects.filter(exercise__in=exercise_queryset)
    passed_questions_pk_list = questions.filter(
        answer__user=user, answer__correct=True
    ).values_list('pk', flat=True)

    failed_questions = questions.exclude(pk__in=passed_questions_pk_list)
    failed_exercises_pk_list = failed_questions.values_list('exercise__pk', flat=True)
    passed_exercises = exercise_queryset.exclude(pk__in=failed_exercises_pk_list).select_related(
        'meta'
    )
    passed_rendered = []
    for passed in passed_exercises:
        passed_rendered.append(
            {
                'exercise_name': passed.name,
                'exercise_key': passed.exercise_key,
                'deadline': passed.meta.deadline_date,
            }
        )
    return passed_rendered  # }}}


def get_passed_exercises_with_image_data(
    exercise_queryset, user, deadline=True, image_deadline=True
):  # {{{
    """
    Generate data containing which exercises from the queryset that user have passed and uploaded image for before the deadline.

    Args:
        user: Django User instance
        exercise_queryset: The exercises to be tested

    Returns:
        List
        [
            {
                'exercise_name':
                'answers': [ 
                    {
                        'answer':
                        'date':
                    }
                    ]
                'deadline':
            }
        ]

    """
    extra_question_filters = []
    extra_answer_filters = []
    deadline_time = Course.objects.deadline_time()
    if deadline:
        extra_question_filters.append(
            Q(answer__date__date__lt=F('exercise__meta__deadline_date'))
            | (
                Q(answer__date__date=F('exercise__meta__deadline_date'))
                & Q(answer__date__hour__lte=deadline_time.hour)
            )
        )
        extra_answer_filters.append(
            Q(date__date__lt=F('question__exercise__meta__deadline_date'))
            | (
                Q(date__date=F('question__exercise__meta__deadline_date'))
                & Q(date__hour__lte=deadline_time.hour)
            )
        )
    if image_deadline:
        extra_question_filters.append(
            Q(exercise__imageanswer__date__date__lt=F('exercise__meta__deadline_date'))
            | (
                Q(exercise__imageanswer__date__date=F('exercise__meta__deadline_date'))
                & Q(exercise__imageanswer__date__hour__lte=deadline_time.hour)
            )
        )

    questions = Question.objects.filter(exercise__in=exercise_queryset)
    passed_questions_pk_list = questions.filter(
        answer__user=user,
        answer__correct=True,
        exercise__imageanswer__user=user,
        *extra_question_filters
    ).values_list('pk', flat=True)

    failed_questions = questions.exclude(pk__in=passed_questions_pk_list)
    failed_exercises_pk_list = failed_questions.values_list('exercise__pk', flat=True)
    passed_exercises = exercise_queryset.exclude(pk__in=failed_exercises_pk_list).select_related(
        'meta'
    )
    # .prefetch_related(
    #             Prefetch(
    #                 'question__answer',
    #                 queryset=Answer.objects.filter(
    #                     correct=True,
    #                     user=user,
    #                     *extra_answer_filters
    #                     ).order_by('-date'),
    #                 )).select_related('meta')
    # .order_by('pk')\
    # .distinct()
    passed_rendered = []
    for passed in passed_exercises:
        # question_data = {}
        # for q in passed.question.all():
        #    question_data[q.question_key] = {
        #            'answer': q.answer.first().answer,
        #            'date': q.answer.first().date
        #            }
        passed_rendered.append(
            {
                'exercise_name': passed.name,
                'exercise_key': passed.exercise_key,
                #'answers': question_data,
                'deadline': passed.meta.deadline_date,
            }
        )
    return passed_rendered  # }}}


def get_passed_students(exercise):
    students = User.objects.filter(groups__name='Student')
    deadline_time = datetime.time(8, 0, 0, tzinfo=pytz.timezone('Europe/Stockholm'))
    course = Course.objects.first()
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    questions = Question.objects.filter(exercise=exercise).select_related(
        'exercise', 'exercise__meta'
    )
    users = []
    for question in questions:
        users.append(
            set(
                students.filter(
                    imageanswer__exercise=question.exercise,
                    answer__question=question,
                    answer__correct=True,
                    answer__date__lt=datetime.datetime.combine(
                        question.exercise.meta.deadline_date, deadline_time
                    ),
                )
                .values_list('pk', flat=True)
                .distinct()
            )
        )
    passed = set.intersection(*map(set, users))
    return students.filter(pk__in=passed)
