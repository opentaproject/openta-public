from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from exercises.applymacros import apply_macros_to_node
from exercises.xmljson import BadgerFish
from exercises.models import Exercise, Question, Answer
from exercises.serializers import AnswerSerializer
from exercises.parsing import (
    question_json_get,
    exercise_xmltree,
    question_xmltree_get,
    global_and_question_xmltree_get,
    get_questionkeys_from_xml,
)
from exercises.views.asset import dispatch_asset_path

from exercises.util import deep_get
from lxml import etree
import os
from exercises.views.asset import dispatch_asset_path
from ratelimit.utils import is_ratelimited
from django.utils.translation import ugettext as _
import exercises.paths as paths
import os
import json
import logging
import random
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

question_check_dispatch = {}
question_json_hooks = {}
sensitive_tags = {}
sensitive_attrs = {}
bf = BadgerFish(xml_fromstring=False)


class QuestionError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def get_all_answers(dbhooks):  # exercise_key, question_id, user_id ) :
    exercise_key = dbhooks['exercise_key']
    question_id = dbhooks['question_id']
    user_id = dbhooks['user_id']
    all_answers = {}
    dbexercise = Exercise.objects.get(exercise_key=exercise_key)
    questions = Question.objects.filter(exercise=dbexercise)
    for question in Question.objects.filter(exercise=dbexercise):
        try:
            previous_answer = get_previous_answers(question.pk, user_id, 1)[0]
            all_answers[question.question_key] = previous_answer['answer']
        except:
            pass
    return all_answers


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
            previous_answer = Answer.objects.filter(user__pk=user_id, question=question).latest(
                'date'
            )
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
    hide_attrs=[],
):
    question_check_dispatch[question_type] = grading_function
    question_json_hooks[question_type] = json_hook
    sensitive_tags[question_type] = hide_tags
    sensitive_attrs[question_type] = hide_attrs


def question_check(request, user, user_agent, exercise_key, question_key, answer_data):
    # print("QUESTION CHECK ANSER_DATA = ", answer_data)
    dbexercise = Exercise.objects.get(exercise_key=exercise_key)
    try:
        dbquestion = Question.objects.get(exercise=dbexercise, question_key=question_key)
        usermacros = get_usermacros(user, exercise_key, question_key)
        username = str(user)
    except ObjectDoesNotExist:
        return {
            'error': 'Invalid question',
            'author_error': (
                'You must save the exercise (save '
                'button in toolbar) before the question '
                'can be evaluated.'
            ),
        }
    usermacros['@call'] = 'question_check'
    question_json = question_json_get(dbexercise.get_full_path(), question_key, usermacros)
    if dbquestion.type in question_json_hooks:
        question_json = question_json_hooks[dbquestion.type](
            question_json, question_json, dbquestion.pk, user.pk, exercise_key
        )
    try:
        xmltree = exercise_xmltree(dbexercise.get_full_path())
    except NameError as e:
        return {'error': 'xmltree failed'}
    [global_xmltree, question_xmltree] = global_and_question_xmltree_get(
        xmltree, question_key, usermacros
    )
    # THESE AREA ADDED FOR USE IN  IN MACROS IN PYTHONIC
    question_xmltree.append(etree.fromstring('<exercisekey>' + exercise_key + '</exercisekey>'))
    question_xmltree.set('exerciseseed', usermacros['@exerciseseed'])
    question_xmltree.set('questionseed', usermacros['@questionseed'])
    question_xmltree.set('exercise_key', exercise_key)
    question_xmltree.set(
        'path', os.path.join(dbexercise.course.get_exercises_path(), dbexercise.path)
    )
    question_xmltree.set('user', str(user))
    # studentassetpath = os.path.join( paths.STUDENT_ASSET_PATH , str(user) , exercise_key ) ## NEED THIS
    studentassetpath = paths.get_student_asset_path(user, dbexercise)
    exerciseassetpath = os.path.join(
        dbexercise.course.get_exercises_path(), dbexercise.path
    )  ## NEED THIS
    question_xmltree.set('studentassetpath', studentassetpath)  ## NEED THIS
    question_xmltree.set('exerciseassetpath', exerciseassetpath)  ## NEED THIS
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
    if (
        (not settings.RUNNING_DEVSERVER)
        and rate_limit is not None
        and rate_limit.text is not None
        and not user.is_staff
    ):
        rate = rate_limit.text.strip()
        if (not settings.RUNNING_DEVSERVER) and is_ratelimited(
            request, group='question_custom_rate', key='user', rate=rate, increment=True
        ):
            error_msg = _('Answer rate exceeded, ' 'please wait before trying again. (Rate: ')
            return {'error': error_msg + rate + ')'}
    try:
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
            if user.groups.filter(name='Author').exists() and result.get('debug', False):
                result['warning'] = result.get('warning', '') + " DEBUG: " + result.get('debug')

            else:
                result.pop('debug', None)
            if user.has_perm('exercises.log_question'):
                Answer.objects.create(
                    user=user,
                    question=dbquestion,
                    # question_key=dbquestion.question_key,
                    # exercise_key=dbexercise.exercise_key,
                    answer=answer_data,
                    grader_response=json.dumps(result),
                    correct=correct,
                    user_agent=user_agent,
                )

            usermacros = get_usermacros(user, exercise_key, question_key)
            previous_answers = get_previous_answers(dbquestion.pk, user.pk)
            result['previous_answers'] = previous_answers
            result['n_attempts'] = usermacros['@nattempts']
            try:
                result['used_variable_list'] = question_json['used_variable_list']
            except:
                result['used_variable_list'] = []
            usermacros['@call'] = 'question_check'
            xmltree = exercise_xmltree(dbexercise.get_full_path())
            # NOTE MUST KEEP THIS IN CASE random is updated
            question_xmltree = question_xmltree_get(xmltree, question_key, usermacros)
            if not request.user.has_perm("exercises.view_solution"):
                question_xmltree = hide_sensitive_tags_in_question(question_xmltree)
            bfdata = bf.data(question_xmltree)
            result['question'] = bfdata['question']

            if not dbexercise.meta.feedback:
                result['correct'] = None
            return result
        else:
            return {'error': 'No grading function for question type ' + dbquestion.type}
    except Exception as e:
        raise NameError(str(e))


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


def get_combined_usermacros(exercise, xml, user):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    usermacros = {}
    question_keys = get_questionkeys_from_xml(xml)
    for question_key in question_keys:
        # question_key =   str( question['@attr']['key'] )
        usermacros[question_key] = {}
        dbquestion = Question.objects.get(exercise=dbexercise, question_key=question_key)
        username = str(user)
        n_attempts = get_number_of_attempts(dbquestion.pk, user.pk)
        n_correct = get_number_of_correct_attempts(dbquestion.pk, user.pk)
        usermacros[question_key]['@definedby'] = 'get_combined_usermacros'
        usermacros[question_key]['@nattempts'] = str(n_attempts)
        usermacros[question_key]['@ncorrect'] = str(n_correct)
        usermacros[question_key]['@user'] = username
        usermacros[question_key]['@exercise_key'] = str(exercise)
        usermacros[question_key]['@question_key'] = question_key
        usermacros[question_key]['@questionseed'] = get_seed(user.pk, str(exercise), dbquestion.pk)
        usermacros[question_key]['@exerciseseed'] = get_seed(user.pk, str(exercise))
        usermacros[question_key]['@userpk'] = str(user.pk)
    return usermacros


def get_usermacros(user, exercise_key, question_key=None):

    dbexercise = Exercise.objects.get(exercise_key=exercise_key)
    usermacros = {}
    username = str(user)
    usermacros['@definedby'] = "get_usermacros"
    usermacros['@user'] = username
    usermacros['@exercise_key'] = str(exercise_key)
    usermacros['@exerciseseed'] = get_seed(user.pk, str(exercise_key))
    usermacros['@userpk'] = str(user.pk)
    exerciseassetpath = os.path.join(dbexercise.course.get_exercises_path(), dbexercise.path)
    usermacros['@exerciseassetpath'] = exerciseassetpath
    studentassetpath = paths.get_student_asset_path(user, dbexercise)
    usermacros['@studentassetpath'] = studentassetpath
    if question_key:
        dbquestion = Question.objects.get(exercise=dbexercise, question_key=question_key)
        n_attempts = get_number_of_attempts(dbquestion.pk, user.pk)
        n_correct = get_number_of_correct_attempts(dbquestion.pk, user.pk)
        usermacros['@exerciseassetpath'] = exerciseassetpath
        studentassetpath = paths.get_student_asset_path(user, dbexercise)
        usermacros['@nattempts'] = str(n_attempts)
        usermacros['@ncorrect'] = str(n_correct)
        usermacros['@question_key'] = dbquestion.question_key
        usermacros['@questionseed'] = get_seed(user.pk, str(exercise_key), dbquestion.pk)
    return usermacros


def get_number_of_correct_attempts(question_id, user_id):
    """
    Number of attempts by user at question.
    Args:
        question_id: question primary key
        user_id: user primary key
    Returns:
        Number of attempts (int)
    """
    answers = Answer.objects.filter(user__pk=user_id, question__pk=question_id, correct=True)
    ncorrect = answers.count()
    return ncorrect


def get_seed(user_id, exercise_key=None, question_id=None):
    """
    Number of attempts by user at question.
    Args:
        question_id: question primary key
        user_id: user primary key
    Returns:
        Number of attempts (int)
    """
    if question_id:
        random.seed(exercise_key + str(question_id))
    else:
        random.seed(exercise_key)
    r = random.randrange(123, 55321, 1)
    if settings.REFRESH_SEED_ON_CORRECT_ANSWER and question_id:
        return str(r + get_number_of_correct_attempts(question_id, user_id) + user_id)
    else:
        return str(r + user_id)


def hide_sensitive_tags_in_question(root):
    hide_tags = get_sensitive_tags()
    hide_attrs = get_sensitive_attrs()
    question_type = root.attrib['type']
    tags_to_hide = hide_tags[question_type]
    for tag in tags_to_hide:
        nodes = root.findall('.//' + tag)
        for node in nodes:
            parent = node.getparent()
            parent.remove(node)
    attr_to_hide = hide_attrs[question_type]
    for attr in attr_to_hide:
        nodes = root.findall("./*/[@" + attr + "]")
        for node in nodes:
            node.attrib.pop(attr, None)
    return root
