from django.core.exceptions import ObjectDoesNotExist
from exercises.models import Exercise, Question, Answer
from exercises.serializers import AnswerSerializer, UserSerializer
from exercises.parsing import question_json_get, question_xmltree_get, exercise_xmltree
from exercises.util import deep_get
from lxml import etree
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


def get_previous_answers(question_id, user_id, n_answers=10):
    """
    Previous attempts (time ordered with most recent first) at the question by user.
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
    json_hook=lambda safe_json, full_json, q_id, u_id: safe_json,
    hide_tags=[],
    hide_attrs=[],
):
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
            'author_error': 'You must save the exercise (save button in toolbar) before the question can be evaluated.',
        }
    question_json = question_json_get(dbexercise.path, question_key)
    if dbquestion.type in question_json_hooks:
        question_json = question_json_hooks[dbquestion.type](
            question_json, question_json, dbquestion.pk, user.pk
        )
    xmltree = exercise_xmltree(dbexercise.path)
    question_xmltree = question_xmltree_get(xmltree, question_key)
    global_xmltree = (
        xmltree.xpath(
            '/exercise/global[@type="{type}"] | /exercise/global[not(@type)]'.format(
                type=dbquestion.type
            )
        )
        or [None]
    )[0]
    rate_limit = (question_xmltree.xpath('//rate') or [None])[0]
    if rate_limit is not None and rate_limit.text is not None and not user.is_staff:
        rate = rate_limit.text.strip()
        print(rate)
        if is_ratelimited(
            request, group='question_custom_rate', key='user', rate=rate, increment=True
        ):
            return {
                'error': _('Answer rate exceeded, please wait before trying again. (Rate: ')
                + rate
                + ')'
            }

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
            dbanswer = Answer.objects.create(
                user=user,
                question=dbquestion,
                question_key=dbquestion.question_key,
                exercise_key=dbexercise.exercise_key,
                answer=answer_data,
                grader_response=json.dumps(result),
                correct=correct,
                user_agent=user_agent,
            )

        n_attempts = get_number_of_attempts(dbquestion.pk, user.pk)
        previous_answers = get_previous_answers(dbquestion.pk, user.pk)
        result['n_attempts'] = n_attempts
        result['previous_answers'] = previous_answers
        return result
    else:
        return {'error': 'No grading function for question type ' + dbquestion.type}


def question_json_hook(safe_question, full_question, question_id, user_id):
    type = deep_get(safe_question, '@attr', 'type')
    if type is not None and type in question_json_hooks:
        return question_json_hooks[type](safe_question, full_question, question_id, user_id)
    return safe_question


def get_sensitive_tags():
    return sensitive_tags


def get_sensitive_attrs():
    return sensitive_attrs
