from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from exercises.models import Exercise, Question, Answer
from exercises.serializers import AnswerSerializer
from exercises.parsing import question_json_get, question_xmltree_get, exercise_xmltree
from exercises.util import deep_get
from lxml import etree
import os
from exercises.views.asset import dispatch_asset_path
from ratelimit.utils import is_ratelimited
from django.utils.translation import ugettext as _
import json
import logging

logger = logging.getLogger(__name__)

question_check_dispatch = {}
question_json_hooks = {}
sensitive_tags = {}
sensitive_attrs = {}


class QuestionError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def get_number_of_attempts(question_id, user_id):
    """
    Number of attempts by user at question.
    Args:
        question_id: question primary key
        user_id: user primary key
    Returns:
        Number of attempts (int)
    """
    answers = Answer.objects.filter(user__pk=user_id, question__pk=question_id)
    return answers.count()


def get_other_answers(question_key, user_id, exercise_key):
    all_answers = {}
    dbexercise = Exercise.objects.get(exercise_key=exercise_key)
    for question in Question.objects.filter(exercise=dbexercise):
        try:
            previous_answer = Answer.objects.filter(user__pk=user_id, question=question)\
                                    .latest('date')
            all_answers[question.question_key] = previous_answer.answer
        except Answer.DoesNotExist:
            all_answers[question.question_key] = None
    return all_answers


def get_previous_answers(question_id, user_id, n_answers=10):
    """ Previous attempts (time ordered with most recent first) at the question by user.

    Args:
        question_id: question primary key
        user_id: user primary key
        n_answers: number of attempts to include (default: 10)
    Returns:
        List of serialized answers (see AnswerSerializer for fields)

    """
    answers = Answer.objects.filter(user__pk=user_id, question__pk=question_id)
    last_answers = answers.order_by('-date')[:n_answers]
    sanswers = AnswerSerializer(last_answers, many=True)
    return sanswers.data


def register_question_type(
        question_type,
        grading_function,
        json_hook=lambda safe_json, full_json, q_id, u_id, e_id: safe_json,
        hide_tags=[],
        hide_attrs=[]):
    question_check_dispatch[question_type] = grading_function
    question_json_hooks[question_type] = json_hook
    sensitive_tags[question_type] = hide_tags
    sensitive_attrs[question_type] = hide_attrs


def question_check(request, user, user_agent, exercise_key, question_key, answer_data):
    dbexercise = Exercise.objects.get(exercise_key=exercise_key)
    try:
        dbquestion = Question.objects.get(exercise=dbexercise, question_key=question_key)
    except ObjectDoesNotExist:
        return {
            'error': 'Invalid question',
            'author_error': (
                'You must save the exercise (save '
                'button in toolbar) before the question '
                'can be evaluated.'
            ),
        }
    question_json = question_json_get(dbexercise.get_full_path(), question_key)
    if dbquestion.type in question_json_hooks:
        question_json = question_json_hooks[dbquestion.type](
            question_json, question_json, dbquestion.pk, user.pk, exercise_key
        )
    xmltree = exercise_xmltree(dbexercise.get_full_path())
    question_xmltree = question_xmltree_get(xmltree, question_key)
    global_xpath = '/exercise/global[@type="{type}"] | /exercise/global[not(@type)]'
    global_xmltree = (xmltree.xpath(global_xpath.format(type=dbquestion.type)) or [None])[0]

    # Add runtime information that can be used in question implementations
    runtime_element = etree.Element("runtime")
    runtime_element.append(etree.fromstring('<exercisekey>' + exercise_key + '</exercisekey>'))
    runtime_element.set('exercise_key', exercise_key)
    runtime_element.set(
        'path', os.path.join(dbexercise.course.get_exercises_path(), dbexercise.path)
    )
    runtime_element.set('user', str(user))
    studentassetpath = dispatch_asset_path(request, dbexercise)
    exerciseassetpath = os.path.join(dbexercise.course.get_exercises_path(), dbexercise.path)
    runtime_element.set('studentassetpath', studentassetpath)
    runtime_element.set('exerciseassetpath', exerciseassetpath)
    question_xmltree.append(runtime_element)

    rate_limit = (question_xmltree.xpath('//rate') or [None])[0]
    if ((not settings.RUNNING_DEVSERVER) and
            rate_limit is not None and
            rate_limit.text is not None and
            not user.is_staff):
        rate = rate_limit.text.strip()
        if is_ratelimited(
            request, group='question_custom_rate', key='user', rate=rate, increment=True
        ):
            error_msg = _('Answer rate exceeded, ' 'please wait before trying again. (Rate: ')
            return {'error': error_msg + rate + ')'}

    if dbquestion.type in question_check_dispatch:
        result = {}
        try:
            result = question_check_dispatch[dbquestion.type](
                question_json, question_xmltree, answer_data, global_xmltree
            )
        except QuestionError as e:
            return {'error': "XML error: " + str(e)}
        if 'zerodivision' in result:
            logger.error(['zerodivision', dbexercise.name, question_key])
        correct = False
        if 'correct' in result:
            correct = result['correct']
        if user.has_perm('exercises.log_question'):
            Answer.objects.create(
                user=user,
                question=dbquestion,
                answer=answer_data,
                grader_response=json.dumps(result),
                correct=correct,
                user_agent=user_agent,
            )

        n_attempts = get_number_of_attempts(dbquestion.pk, user.pk)
        previous_answers = get_previous_answers(dbquestion.pk, user.pk)
        result['previous_answers'] = previous_answers
        result['n_attempts'] = n_attempts
        if not dbexercise.meta.feedback:
            result['correct'] = None
        return result
    else:
        return {'error': 'No grading function for question type ' + dbquestion.type}


def question_json_hook(safe_question, full_question, question_id, user_id, exercise_key):
    type = deep_get(safe_question, '@attr', 'type')
    if type is not None and type in question_json_hooks:
        return question_json_hooks[type](
            safe_question, full_question, question_id, user_id, exercise_key
        )
    return safe_question


def get_sensitive_tags():
    return sensitive_tags


def get_sensitive_attrs():
    return sensitive_attrs
