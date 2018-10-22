from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from course.models import Course
from exercises.parsing import exercise_xmltree, question_xmltree_get
from exercises.question import question_check
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


def e_student_activity(exercise):
    t1h = timezone.now() - datetime.timedelta(hours=1)
    t24h = timezone.now() - datetime.timedelta(hours=24)
    t1w = timezone.now() - datetime.timedelta(days=7)
    n_questions = exercise.question.all().count()
    if n_questions == 0:
        return {'activity': {'1h': 0, '24h': 0, '1w': 0, 'all': 0}}

    activity_1h = round(
        Answer.objects.filter(
            date__gt=t1h, question__exercise=exercise, user__groups__name="Student"
        ).count()
        / n_questions
    )
    activity_24h = round(
        Answer.objects.filter(
            date__gt=t24h, question__exercise=exercise, user__groups__name="Student"
        ).count()
        / n_questions
    )
    activity_1w = round(
        Answer.objects.filter(
            date__gt=t1w, question__exercise=exercise, user__groups__name="Student"
        ).count()
        / n_questions
    )
    activity_all = round(
        Answer.objects.filter(question__exercise=exercise, user__groups__name="Student").count()
        / n_questions
    )
    return {
        'activity': {'1h': activity_1h, '24h': activity_24h, '1w': activity_1w, 'all': activity_all}
    }


def p_student_activity(data):
    try:
        max_1h = max(data.values(), key=lambda exercise: exercise['activity']['1h'])
        max_24h = max(data.values(), key=lambda exercise: exercise['activity']['24h'])
        max_1w = max(data.values(), key=lambda exercise: exercise['activity']['1w'])
        max_all = max(data.values(), key=lambda exercise: exercise['activity']['all'])
    except ValueError:
        return {'max_1h': 0, 'max_24h': 0, 'max_1w': 0, 'max_all': 0}
    return {
        'max_1h': max_1h['activity']['1h'],
        'max_24h': max_24h['activity']['24h'],
        'max_1w': max_1w['activity']['1w'],
        'max_all': max_all['activity']['all'],
    }


def e_student_attempts_mean(exercise):
    users = User.objects.filter(groups__name='Student', is_active=True)
    attempts = users.filter(answer__question__exercise=exercise).annotate(attempts=Count('answer'))
    n_questions = Question.objects.filter(exercise=exercise).count()
    mean_attempts = attempts.aggregate(Avg('attempts'))
    if mean_attempts['attempts__avg'] is not None:
        avg = mean_attempts['attempts__avg'] / n_questions
    else:
        avg = 0
    return {'attempts_mean': avg}


def e_student_attempts_median(exercise):
    users = User.objects.filter(groups__name='Student', is_active=True)
    attempts = users.filter(answer__question__exercise=exercise).annotate(attempts=Count('answer'))
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
    return {'attempts_median': median / n_questions}


def get_all_who_tried(exercise):
    users = (
        User.objects.filter(groups__name='Student', is_active=True, email__isnull=False)
        .filter(Q(answer__question__exercise=exercise) | Q(imageanswer__exercise=exercise))
        .exclude(groups__name='View')
        .exclude(groups__name='Admin')
        .exclude(groups__name='Author')
        .exclude(username='student')
        .distinct()
    )
    return users


def e_student_tried(exercise):
    users = User.objects.filter(groups__name='Student', is_active=True, email__isnull=False)
    n_tried = get_all_who_tried(exercise).count()
    n_students = users.count()
    return {'ntried': n_tried, 'percent_tried': n_tried / n_students if n_students > 0 else 0}


def has_audit_response_waiting(exercise):
    """Get number of audits that has updates."""
    return dict(
        response_awaits=AuditExercise.objects.filter(exercise=exercise, updated=True).count()
    )


def e_student_percent_complete(exercise):
    """Get statistics on completed status.

    Completed means that the student has performed all the required activities
    before the deadline (if there is one)

    Returns:
        dict: containing::

            {
                'percent_complete': Fraction of students that have completed the exercise
                'percent_correct': Fraction of students that have answered questions correctly
                'ncomplete': Number of completed students
                'ncorrect': Number of currect students
                'nstudents': Number of active students
            }

    """
    users = User.objects.filter(groups__name='Student', is_active=True, email__isnull=False)
    n_students = users.count()
    tz = pytz.timezone('Europe/Stockholm')
    deadline_time = datetime.time(23, 59, 59)
    course = Course.objects.first()
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    deadline_date = exercise.meta.deadline_date
    questions = Question.objects.filter(exercise=exercise)
    complete = []
    correct_answer = []
    for question in questions:
        # How many have the correct answer?
        correct_answer.append(
            set(
                users.filter(answer__correct=True, answer__question=question)
                .values_list('username', flat=True)
                .distinct()
            )
        )

        # How many are complete?
        extra_filters = []
        if deadline_date is not None:
            deadline_date_time = datetime.datetime.combine(deadline_date, deadline_time)
            # If there is a deadline then the answer need to be correct before deadline
            extra_filters.append(Q(answer__date__lt=tz.localize(deadline_date_time)))

        if exercise.meta.image:
            # If there is an image/pdf required it needs to be present
            extra_filters.append(Q(imageanswer__exercise=question.exercise))

        complete.append(
            set(
                users.filter(answer__correct=True, answer__question=question, *extra_filters)
                .values_list('username', flat=True)
                .distinct()
            )
        )

    allcomplete = set.intersection(*map(set, complete)) if complete else []
    allcorrect_answer = set.intersection(*map(set, correct_answer)) if correct_answer else []

    return {
        'percent_complete': len(allcomplete) / n_students if n_students > 0 else 0,
        'percent_correct': len(allcorrect_answer) / n_students if n_students > 0 else 0,
        'ncomplete': len(allcomplete),
        'ncorrect': len(allcorrect_answer),
        'nstudents': n_students,
        'deadline': deadline_date,
    }


def exercise_list_data(exercise_data_func_list, course):
    exercises = Exercise.objects.filter(course=course)
    result = {}
    for exercise in exercises:

        def reduce_data_func(prev, next):
            prev.update(next(exercise))
            return prev

        data = reduce(reduce_data_func, exercise_data_func_list, {})
        result[exercise.exercise_key] = data
    return result


def post_process_list(data, data_func_list):
    def reduce_data_func(prev, next):
        prev.update(next(data))
        return prev

    result = reduce(reduce_data_func, data_func_list, {})
    return result


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


def exercise_folder_structure(manager, user, course):
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


def serialize_exercise_with_question_data(exercise, user):
    """
    Serialize an exercise together with question and image answer data for the specified user.

    Args:
        exercise: Exercise instance (Django ORM)
        user: User instance (Django ORM)

    Returns:
        Dictionary corresponding to a JSON representation of the exercise together with user data.

    """
    questions = Question.objects.filter(exercise=exercise)
    correct = exercise.user_is_correct(user)
    tried_all = exercise.user_tried_all(user)
    serializer = ExerciseSerializer(exercise)
    data = serializer.data

    data['question'] = {}
    data['tried_all'] = tried_all
    data['correct'] = correct
    data['response_awaits'] = has_audit_response_waiting(exercise)['response_awaits']
    if not exercise.meta.feedback:
        data['correct'] = None
    image_answers = ImageAnswer.objects.filter(user=user, exercise=exercise)
    image_answers_serialized = ImageAnswerSerializer(image_answers, many=True)
    image_answers_ids = [image_answer.pk for image_answer in image_answers]
    data['image_answers'] = image_answers_ids
    data['image_answers_data'] = image_answers_serialized.data
    try:
        audit = AuditExercise.objects.get(student=user, exercise=exercise)
        saudit = AuditExerciseSerializer(audit)
        data['audit'] = saudit.data
    except AuditExercise.DoesNotExist:
        pass

    for question in questions:
        try:
            dbanswer = Answer.objects.filter(user=user, question=question).latest('date')
            serializer = AnswerSerializer(dbanswer)
            response = json.loads(dbanswer.grader_response)
            data['question'][question.question_key] = serializer.data
            data['question'][question.question_key]['response'] = response
            if not exercise.meta.feedback:
                data['question'][question.question_key]['correct'] = None
                data['question'][question.question_key]['response']['correct'] = None
        except ObjectDoesNotExist:
            pass
    return data


def exercise_test(exercise_key):
    requests = RequestFactory()
    request = requests.get('/test')
    dbexercise = Exercise.objects.get(exercise_key=exercise_key)
    dbquestions = Question.objects.filter(exercise=dbexercise)
    xmltree = exercise_xmltree(dbexercise.get_full_path())
    user = User.objects.get(username='tester')
    results = []
    for dbquestion in dbquestions:
        if dbquestion.type in ['compareNumeric', 'linearAlgebra']:
            question_key = dbquestion.question_key
            question_xml = question_xmltree_get(xmltree, question_key)
            answer_element = question_xml.find('expression')
            if answer_element is not None:
                answer = answer_element.text.split(';')[0]
                result = {}
                try:
                    result = question_check(
                        request, user, "tester", exercise_key, question_key, answer
                    )
                except Exception as e:
                    result['exception'] = str(e)
                result.update({'answer': answer})
                results.append(result)
    return results


def get_passed_exercises(exercise_queryset, user):
    """Get exercises with correct answer by user.

    Args:
        exercise_queryset (django queryset): Exercises to be checked
        user (django user): User to check for
    Returns:
    (list of dict): List with dictionaries containing the structure
        {
            'exercise_name': ...
            'exercise_key': ...
            'deadline': ...
        }
    """
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
    return passed_rendered


def get_passed_exercises_with_image_data(
    exercise_queryset, user, deadline=True, image_deadline=True, require_image=True
):
    """
    Generate data containing which exercises from the queryset that user have
    passed and uploaded image for before the deadline.

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
    deadline_time = Course.objects.deadline_time()
    if deadline:
        extra_question_filters.append(
            Q(answer__date__date__lt=F('exercise__meta__deadline_date'))
            | (
                Q(answer__date__date=F('exercise__meta__deadline_date'))
                & Q(answer__date__hour__lt=deadline_time.hour)
            )
        )
    if image_deadline:
        extra_question_filters.append(
            Q(exercise__imageanswer__date__date__lt=F('exercise__meta__deadline_date'))
            | (
                Q(exercise__imageanswer__date__date=F('exercise__meta__deadline_date'))
                & Q(exercise__imageanswer__date__hour__lt=deadline_time.hour)
            )
        )

    if require_image:
        extra_question_filters.append(Q(exercise__imageanswer__user=user))

    questions = Question.objects.filter(exercise__in=exercise_queryset)
    passed_questions_pk_list = questions.filter(
        answer__user=user, answer__correct=True, *extra_question_filters
    ).values_list('pk', flat=True)

    failed_questions = questions.exclude(pk__in=passed_questions_pk_list)
    failed_exercises_pk_list = failed_questions.values_list('exercise__pk', flat=True)
    failed_by_audit = exercise_queryset.filter(
        audits__student=user, audits__published=True, audits__revision_needed=True
    )
    failed_by_audit_pk_list = failed_by_audit.values_list('pk', flat=True)
    all_failed_pk_list = list(set(failed_by_audit_pk_list) | set(failed_exercises_pk_list))

    passed_exercises = exercise_queryset.exclude(pk__in=all_failed_pk_list).select_related('meta')
    force_passed_exercises = exercise_queryset.filter(
        pk__in=(AuditExercise.objects.get_force_passed_exercises_pk(user))
    )
    total_passed = passed_exercises | force_passed_exercises
    total_passed = total_passed.distinct()
    passed_rendered = []
    for passed in total_passed:
        passed_rendered.append(
            {
                'exercise_name': passed.name,
                'exercise_key': passed.exercise_key,
                'deadline': passed.meta.deadline_date,
            }
        )
    return passed_rendered


AnalyzeResults = namedtuple(
    'AnalyzeResults',
    ['answered_set', 'answered_on_time_set', 'with_image_set', 'with_image_on_time_set'],
)


def analyze_exercise(exercise):
    """Get students to be audited.

    If exercise feedback is enabled this returns all student that have answered
    correctly and submitted an image answer.
    If exercise feedback is disabled this returns all students that have uploaded
    an image before deadline.
    """
    students = get_all_who_tried(exercise)
    tz = pytz.timezone('Europe/Stockholm')
    deadline_time = datetime.time(23, 59, 59)
    course = Course.objects.first()
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time

    questions = Question.objects.filter(exercise=exercise).select_related(
        'exercise', 'exercise__meta'
    )
    deadline_date = datetime.datetime.now(tz) + datetime.timedelta(days=1)
    if exercise.meta.deadline_date is not None:
        deadline_date = exercise.meta.deadline_date
    users_answered_questions = []
    users_answered_questions_ontime = []
    for question in questions:
        if exercise.meta.feedback:
            users_answered_questions.append(
                students.filter(answer__question=question, answer__correct=True)
                .values_list('pk', flat=True)
                .distinct()
            )

            users_answered_questions_ontime.append(
                students.filter(
                    answer__question=question,
                    answer__correct=True,
                    answer__date__lt=tz.localize(
                        datetime.datetime.combine(deadline_date, deadline_time)
                    ),
                )
                .values_list('pk', flat=True)
                .distinct()
            )
        else:
            users_answered_questions.append(
                students.filter(answer__question=question).values_list('pk', flat=True).distinct()
            )

            users_answered_questions_ontime.append(
                students.filter(
                    answer__question=question,
                    answer__date__lt=tz.localize(
                        datetime.datetime.combine(deadline_date, deadline_time)
                    ),
                )
                .values_list('pk', flat=True)
                .distinct()
            )

    def _to_set(list_of_lists):
        if list_of_lists:
            return set.intersection(*map(set, list_of_lists))
        else:
            return set([])

    set_passed_users_answered_questions = _to_set(users_answered_questions)
    set_passed_users_answered_questions_ontime = _to_set(users_answered_questions_ontime)

    users_submitted_image_ontime = (
        students.filter(
            imageanswer__exercise=exercise,
            imageanswer__date__lt=tz.localize(
                datetime.datetime.combine(deadline_date, deadline_time)
            ),
        )
        .values_list('pk', flat=True)
        .distinct()
    )

    users_submitted_image = (
        students.filter(imageanswer__exercise=exercise).values_list('pk', flat=True).distinct()
    )

    return AnalyzeResults(
        answered_set=set_passed_users_answered_questions,
        answered_on_time_set=set_passed_users_answered_questions_ontime,
        with_image_set=set(users_submitted_image),
        with_image_on_time_set=set(users_submitted_image_ontime),
    )


def duration_to_string(sec):
    days = int(sec / (3600 * 24.0))
    hours = int((sec - 3600.0 * 24.0 * days) / 3600.0)
    minutes = int((sec - 3600.0 * 24 * days - 3600.0 * hours) / 60.0)
    str_ = ''
    if days > 0:
        str_ = str_ + str(days) + ' days'
    if hours > 0:
        str_ = str_ + ' ' + str(hours) + ' hours'
    if minutes > 0:
        str_ = str_ + ' ' + str(minutes) + ' minutes'
    return str_


def analyze_exercise_for_student(exercise, student_pk):
    tz = pytz.timezone('Europe/Stockholm')
    deadline_time = datetime.time(23, 59, 59)
    course = Course.objects.first()
    if course is not None and course.deadline_time is not None:
        deadline_time = course.deadline_time
    questions = Question.objects.filter(exercise=exercise).select_related(
        'exercise', 'exercise__meta'
    )
    deadline_date = datetime.datetime.now(tz) + datetime.timedelta(days=1)
    if exercise.meta.deadline_date is not None:
        deadline_date = exercise.meta.deadline_date
    if deadline_date is not None:
        deadline_date_time = tz.localize(datetime.datetime.combine(deadline_date, deadline_time))

    passed_all = True
    passed_all_on_time = True
    submitted_image = True
    submitted_image_on_time = True
    for question in questions:
        if not Answer.objects.filter(user__pk=student_pk, question=question, correct=True).exists():
            passed_all = False
        if deadline_date is not None:
            correct_before_deadline = Answer.objects.filter(
                user__pk=student_pk, question=question, correct=True, date__lt=deadline_date_time
            )
            if not correct_before_deadline.exists():
                passed_all_on_time = False

    if not ImageAnswer.objects.filter(user__pk=student_pk, exercise=exercise).exists():
        submitted_image = False
    if deadline_date is not None:
        image_before_deadline = ImageAnswer.objects.filter(
            user__pk=student_pk,
            exercise=exercise,
            date__lt=tz.localize(datetime.datetime.combine(deadline_date, deadline_time)),
        )
        if not image_before_deadline.exists():
            submitted_image_on_time = False

    message = ""
    pass_ = True
    if questions.count() > 0:
        if passed_all_on_time:
            message = message + "Answers OK and on time. "
        elif passed_all:
            pass_ = False
            message = message + "Answers OK but "
            latest = 0
            for question in questions:
                dbanswer = Answer.objects.filter(
                    user__pk=student_pk, correct=True, question=question
                ).earliest('date')
                submitted_at = dbanswer.date
                due_at = tz.localize(datetime.datetime.combine(deadline_date, deadline_time))
                diff = submitted_at - due_at
                latest = max(diff.total_seconds(), latest)
            message = message + duration_to_string(latest) + ' late.\n'
        else:
            pass_ = False
            message = message + "Answers wrong or incomplete. "
    if exercise.meta.image:
        if submitted_image_on_time:
            message = message + "Image on time. "
        elif submitted_image:
            pass_ = False
            message = message + "Image  "
            image_answer = ImageAnswer.objects.filter(user=student_pk, exercise=exercise).latest(
                'date'
            )
            submitted_at = image_answer.date
            due_at = tz.localize(datetime.datetime.combine(deadline_date, deadline_time))
            diff = submitted_at - due_at
            latest = diff.total_seconds()
            message = message + duration_to_string(latest) + ' late.\n'
        else:
            pass_ = False
            message = message + "Image missing. "

    return (pass_, message)


def get_students_to_be_audited(exercise):
    analyze_results = analyze_exercise(exercise)

    questions = Question.objects.filter(exercise=exercise).select_related(
        'exercise', 'exercise__meta'
    )
    students = get_all_who_tried(exercise)
    passed = set(students.values_list('pk', flat=True))
    if questions.count() > 0:
        passed = set.intersection(passed, analyze_results.answered_on_time_set)
    if exercise.meta.image:
        passed = set.intersection(passed, analyze_results.with_image_on_time_set)
    return students.filter(pk__in=passed)


def get_students_not_to_be_audited(exercise):
    """Get who are active but not scheduled for audit
    """
    active_students = get_all_who_tried(exercise)
    passed_students = get_students_to_be_audited(exercise)
    return active_students.exclude(pk__in=passed_students)
