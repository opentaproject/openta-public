from django.shortcuts import render
from exercises.applymacros import MacroError
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from exercises.applymacros import apply_macros_to_exercise, apply_macros_to_node
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import PermissionDenied
from course.models import Course
from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from exercises.serializers import ExerciseSerializer, AnswerSerializer, ImageAnswerSerializer
from exercises.serializers import AuditExerciseSerializer
from exercises import parsing
from exercises.parsing import (
    question_json_get_from_raw_json,
    exercise_xml_to_json,
    exercise_xmltree_from_xml,
)
from exercises.questiontypes.dev_linear_algebra.variableparser import (
    parse_xml_variables,
    getallvariables,
    parse_xml_functions,
)
from exercises.questiontypes.symbolic.symbolic import symbolic_compare_expressions
from exercises.questiontypes.dev_linear_algebra.linear_algebra import (
    linear_algebra_compare_expressions,
)
import exercises.question as question_module
from exercises.question import (
    get_number_of_attempts,
    get_number_of_correct_attempts,
    get_combined_usermacros,
    get_seed,
    get_usermacros,
)
from exercises.modelhelpers import serialize_exercise_with_question_data
from exercises.modelhelpers import exercise_folder_structure, exercise_test
from exercises.views.file_handling import serve_file
from exercises.time import before_deadline
from exercises.util import deep_get, get_hash_from_string
from utils import response_from_messages
from django.utils.translation import ugettext as _
from django.http import StreamingHttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.contrib.auth.decorators import permission_required
from django.template.response import TemplateResponse
from django.template import loader
from django.utils.timezone import now
from django.db import transaction
from django.db.models import Prefetch
from ratelimit.decorators import ratelimit
from django.views.decorators.cache import never_cache
from PIL import Image
import exercises.paths as paths
import datetime, hashlib
import PyPDF2
import logging
from django.conf import settings
import json
import exercises.paths as paths
from xml.etree.ElementTree import fromstring, ParseError, tostring
from lxml import etree

import re
import os
from lxml import etree
import os.path

compare_function = {}
compare_function['symbolic'] = symbolic_compare_expressions
compare_function['devLinearAlgebra'] = linear_algebra_compare_expressions


logger = logging.getLogger(__name__)


@permission_required('exercises.reload_exercise')
@api_view(['POST', 'GET'])
def exercises_reload_streaming(request, course_pk):
    try:
        dbcourse = Course.objects.get(pk=course_pk)
    except Course.DoesNotExist:
        logger.error('Requested course does not exist pk: %d', course_pk)
        return Response({'error': 'Invalid course'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    exercises = Exercise.objects.sync_with_disc(dbcourse)

    base = loader.get_template('base_streaming.html')

    def next_exercise():
        yield base.render()
        for progress in exercises:
            rendered = loader.render_to_string('reload_progress.html', {'progress': progress})
            yield rendered

    return StreamingHttpResponse(next_exercise())


@permission_required('exercises.reload_exercise')
@api_view(['POST', 'GET'])
def exercises_reload(request, course_pk):
    i_am_sure = request.data.get('i_am_sure', False)
    try:
        dbcourse = Course.objects.get(pk=course_pk)
    except Course.DoesNotExist:
        logger.error('Requested course does not exist pk: %d', course_pk)
        return Response({'error': 'Invalid course'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def sync():
        mess = []
        exercises = Exercise.objects.sync_with_disc(dbcourse, i_am_sure)
        for progress in exercises:
            mess = mess + progress
        return mess

    mess = sync()
    return render(request._request, "exercises_reload.html", {'progress': mess})


@api_view(['POST', 'GET'])
def exercises_reload_json(request, course_pk):
    if not request.user.has_perm('exercises.reload_exercise'):
        raise PermissionDenied(_("Permission denied"))
    i_am_sure = request.data.get('i_am_sure', False)
    try:
        dbcourse = Course.objects.get(pk=course_pk)
    except Course.DoesNotExist:
        logger.error('Requested course does not exist pk: %d', course_pk)
        return Response({'error': 'Invalid course'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def sync():
        mess = []
        exercises = Exercise.objects.sync_with_disc(dbcourse, i_am_sure)
        for progress in exercises:
            mess = mess + progress
        return mess

    mess = sync()
    return Response(mess)


@never_cache
@api_view(['GET'])
def exercise(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    data = serialize_exercise_with_question_data(dbexercise, request.user)
    return Response(data)


@never_cache
@api_view(['GET'])
def exercise_list(request, course_pk):
    """
    List all exercises
    """
    request.session['course_pk'] = course_pk
    responselist = {}
    exercises = Exercise.objects.filter(course__pk=course_pk).prefetch_related(
        Prefetch(
            'question__answer',
            queryset=Answer.objects.filter(user=request.user).order_by('-date'),
            to_attr="useranswers",
        ),
        Prefetch(
            'imageanswer',
            queryset=ImageAnswer.objects.filter(user=request.user),
            to_attr="userimageanswers",
        ),
        'meta',
    )
    for exercise in exercises:
        if exercise.meta.published or request.user.has_perm('exercises.edit_exercise'):
            exerciseserializer = ExerciseSerializer(exercise)
            data = exerciseserializer.data
            data['question'] = {}
            data['image_answers'] = [image_answer.pk for image_answer in exercise.userimageanswers]
            try:
                audit = AuditExercise.objects.get(student=request.user, exercise=exercise)
                saudit = AuditExerciseSerializer(audit)
                data['audit'] = saudit.data
            except AuditExercise.DoesNotExist:
                pass
            allcorrect = True
            questions = exercise.question.all()
            tried_all = True
            if not questions:
                tried_all = False
            for question in exercise.question.all():
                try:
                    if hasattr(question, 'useranswers') and question.useranswers:
                        if not question.useranswers[0].correct:
                            allcorrect = False
                        answerserializer = AnswerSerializer(question.useranswers[0])
                        response = json.loads(question.useranswers[0].grader_response)
                        data['question'][question.question_key] = answerserializer.data
                        data['question'][question.question_key]['response'] = response
                        if not exercise.meta.feedback:
                            data['question'][question.question_key]['correct'] = None
                            data['question'][question.question_key]['response']['correct'] = None
                    else:
                        allcorrect = False
                        tried_all = False
                except ObjectDoesNotExist:
                    allcorrect = False
            if exercise.meta.feedback:
                data['correct'] = allcorrect
            data['tried_all'] = tried_all
            responselist[exercise.exercise_key] = data
    return Response(responselist)


@never_cache
@api_view(['GET'])
def exercise_tree(request, course_pk):
    """
    Get exercise tree
    """
    try:
        dbcourse = Course.objects.get(pk=course_pk)
    except Course.DoesNotExist:
        logger.error('Requested course does not exist pk: %d', course_pk)
        return Response({'error': 'Invalid course'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(exercise_folder_structure(Exercise.objects, request.user, dbcourse))


@never_cache
@api_view(['GET'])
def other_exercises_from_folder(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    course_exercises = Exercise.objects.filter(course=dbexercise.course)
    other = []
    if request.user.has_perm('exercises.edit_exercise') or request.user.has_perm(
        'exercises.view_unpublished'
    ):
        other = course_exercises.filter(folder=dbexercise.folder).prefetch_related('meta')
    else:
        other = course_exercises.filter(
            folder=dbexercise.folder, meta__published=True
        ).prefetch_related('meta')

    serializer = ExerciseSerializer(other, many=True)
    actions_for_key = [('published', lambda x: str(not x)), ('sort_key', str)]

    def sort_key_func(item):
        return "".join([func(item['meta'][key]) for (key, func) in actions_for_key])

    inorder = sorted(serializer.data, key=sort_key_func)
    return Response(inorder)


@never_cache
@api_view(['GET'])
def exercise_json(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    user = request.user
    try:
        errormsg = None
        hide_answers = not request.user.has_perm("exercises.view_solution")
        xml = parsing.exercise_xml(dbexercise.get_full_path())
        if True or '@' in xml:
            usermacros = get_usermacros(user, exercise)
            usermacros['@call'] = 'exercise_json'
            usermacros['@combined_user_macros'] = get_combined_usermacros(exercise, xml, user)
        else:
            usermacros = {}  # if usermacros = {} then no macroparsing is done
        root = etree.fromstring(xml)
        try:
            root = apply_macros_to_node(root, usermacros)
            xml = etree.tostring(root)
        except MacroError as e:
            extype = type(e).__name__
            errormsg = extype + str(e)
        except Exception as e:
            extype = type(e).__name__
            errormsg = extype
        full_exercisejson = parsing.exercise_xml_to_json(xml)
        hide_tags = question_module.get_sensitive_tags()
        hide_attrs = question_module.get_sensitive_attrs()
        safe_exercisejson = parsing.exercise_xml_to_json(
            xml, hide_answers=hide_answers, sensitive_tags=hide_tags, sensitive_attrs=hide_attrs
        )
        full_exercisejson['exercise']['exercise_key'] = exercise
        # print("API CALL exercise_json")
        # def question_json_get(path, question_key, usermacros={}):

        # if 'question' in safe_exercisejson['exercise']:
        #    safe_and_full = zip(safe_exercisejson['exercise']['question'],
        #                        full_exercisejson['exercise']['question'])
        #    safe_exercisejson['exercise']['question'] = []
        #    for safe_question, full_question in safe_and_full:
        #        question_key = deep_get(full_question, '@attr', 'key')
        #        dbquestion = Question.objects.filter(
        #            exercise=dbexercise, question_key=question_key).first()
        #        full_question['exercise_key'] = exercise
        #        modified_question = question_module.question_json_hook(
        #            safe_question, full_question, dbquestion.pk, request.user.pk)
        #        safe_exercisejson['exercise']['question'].append(modified_question)
        # def question_json_get_from_raw_json(raw_json, exercise_key, question_key, usermacros={}):
        exercise_key = exercise
        if 'question' in safe_exercisejson['exercise']:
            safe_and_full = zip(
                safe_exercisejson['exercise']['question'], full_exercisejson['exercise']['question']
            )
            safe_exercisejson['exercise']['question'] = []
            for safe_question, full_question in safe_and_full:
                question_key = deep_get(full_question, '@attr', 'key')
                dbquestion = Question.objects.filter(
                    exercise=dbexercise, question_key=question_key
                ).first()
                full_question = question_json_get_from_raw_json(
                    full_exercisejson, exercise_key, question_key, {}
                )
                full_question['exercise_key'] = exercise
                modified_question = question_module.question_json_hook(
                    safe_question, full_question, dbquestion.pk, request.user.pk, exercise
                )
                safe_exercisejson['exercise']['question'].append(modified_question)
        if errormsg:
            safe_exercisejson['error'] = errormsg
        return Response(safe_exercisejson)
    except parsing.ExerciseParseError as e:
        return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@permission_required('exercises.view_xml')
@never_cache
@api_view(['GET'])
def exercise_xml(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    return Response({'xml': parsing.exercise_xml(dbexercise.get_full_path())})


def validate_exercise_globals(xml):
    #
    # CHECK EXERCISE GLOBALS AND QUESTIONS IF GLOBALS CHANGE
    # DONT BOTHER CHECKING QUESTIONS IF QUESTIONS CHANGE
    # SINCE AUTHOR TYPICALLY CHECKS THIS ANYWAY
    #
    return []
    cache_seconds = 60 * 60
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml, parser=parser)
    global_xpath = (
        '/exercise/global[@type="{type}"] | /exercise/global[not(@type)] | /exercise/global'
    )
    global_xmltree = (root.xpath(global_xpath) or [None])[0]
    globalhash = get_hash_from_string(str(etree.tostring(global_xmltree, encoding=str)))
    messages = cache.get(globalhash)
    if messages is not None:
        return messages
    else:
        messages = []
    messages = []
    xml_variables = parse_xml_variables(global_xmltree)
    funcsubs = parse_xml_functions(global_xmltree)
    obj = exercise_xml_to_json(xml)
    questions = obj['exercise']['question']
    types_to_check = []
    for question in questions:
        types_to_check = types_to_check + [question['@attr']['type']]
    types_to_check = list(set(types_to_check).intersection(set(['symbolic', 'devLinearAlgebra'])))
    if len(types_to_check) == 0:
        return []
    expressions = [x['name'] + ' == ' + x['value'] for x in xml_variables]
    try:
        for question_type in types_to_check:
            symex = compare_function[question_type]
            variables = xml_variables
            funcsubs = parse_xml_functions(global_xmltree)
            precision = 1.0e-6
            result = {}
            for expression in expressions:
                expr = "QuestionType " + question_type + " :Error in global definitions: "
                print("TESTING EXPRSSION ", expression)
                result = symex(precision, variables, expression, '0 == 0', True, [], [], funcsubs)
                if (not result.get('correct')) or result.get('error'):
                    print("FAILED")
                    msg = expr + result.get('error', '') + result.get('debug', '')
                    msg = re.sub(r"[\'<>]", '', msg)
                    messages.append(('error', msg))
                    return messages

            question_xmltrees = root.findall(
                './question[@type="{type}"]'.format(type=question_type)
            )
        for question_xmltree in question_xmltrees:
            result = {}
            ret = getallvariables(global_xmltree, question_xmltree, assign_all_numerical=False)
            used_variables = list(ret['used_variables'])
            variables = ret['variables']
            funcsubs = ret['functions']
            authorvariables = ret['authorvariables']
            blacklist = ret['blacklist']
            correct_answer = ret['correct_answer']
            precision = 1.0e-6
            question_type = question['@attr']['type']
            symex = compare_function[question_type]
            try:
                expr = correct_answer + '  '
                result = symex(
                    precision,
                    variables,
                    correct_answer,
                    correct_answer,
                    True,
                    [],
                    used_variables,
                    funcsubs,
                )
                if result.get('error'):
                    msg = "Error in question with answer " + expr + ":   " + result.get('debug', '')
                    msg = re.sub(r"[\'<>]", '', msg)
                    messages.append(('error', msg))
                    return messages
                else:
                    pass

            except:
                msg = "Error in question with answer " + expr + ":   " + result.get('debug', '')
                msg = re.sub(r"[\'<>]", '', msg)
                messages.append(('error', msg))
                return messages
    except Exception as e:
        messages.append(('error', type(e).__name__ + str(e)))
        return messages
    cache.set(globalhash, messages, cache_seconds)
    return messages


def validate_exercise_xml(xml):
    messages = []
    return messages
    try:
        messages = validate_exercise_globals(xml)
        xmlschema = etree.XMLSchema(etree.parse(paths.EXERCISE_XSD))
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(xml, parser=parser)
        xmlschema.assert_(root)
        messages.append(('success', 'XML OK '))
    except etree.XMLSyntaxError as err:
        messages.append(('error', "Parsing Error:{0}".format(err)))
    except AssertionError as err:
        msg = "{0}".format(err)
        if 'Element \'text\': This element is not expected' in msg:
            msg = "The &lt;text&gt; tag is not expeced. \n Is it nested? \n It should not be:  Suggested fix: Change  for instance &lt;text&gt; string1 &lt;text&gt; string2 &lt;/text&gt; string3 &lt;/text&gt; to &lt;text&gt; string1 &lt;/text&gt;&lt;text&gt; string2 string3 &lt;/text&gt; "
        elif 'Element \'exercise\': Character content other than whitespace is not allowed ' in msg:
            msg = "The &lt;exercise&gt; tag should not contain character content; Suggestion: wrap the desired character content with &lt;text&gt ... &lt;/text&gt; so that &lt;text&gt; is a direct child of &lt;exercise&gt;"
        elif 'Element \'qmath\': This element is not expected' in msg:
            msg = msg + ' You may need to wrap the element with &lt;text&gt tag '
        elif 'Element \'asciimath\': This element is not expected' in msg:
            msg = msg + ' You may need to wrap the element with &lt;text&gt tag '
        messages.append(('error', 'XML Error: ' + msg))
    except NameError as e:
        messages.append(
            ('error', "From validate_exercise_xml: " + type(e).__name__ + "  :  " + str(e))
        )
    return messages


@permission_required('exercises.edit_exercise')
@api_view(['POST'])
def exercise_save(request, exercise):
    messages = []
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    backup_name = "{:%Y%m%d_%H:%M:%S_%f_}".format(now()) + request.user.username + ".xml"
    xml = request.data['xml']
    try:
        messages += parsing.exercise_save(dbexercise.get_full_path(), xml, backup_name)
    except IOError as e:
        messages.append(('error', str(e)))

    @transaction.atomic
    def update_exercise():
        return Exercise.objects.add_exercise(dbexercise.path, dbexercise.course)

    try:
        messages += update_exercise()
    except parsing.ExerciseParseError as e:
        messages.append(('warning', str(e)))
    messages = messages + validate_exercise_xml(xml)
    result = response_from_messages(messages)
    return Response(result)


@ratelimit(key='user', rate='5/1m')
@api_view(['POST'])
def exercise_check(request, exercise, question):
    answer_data = request.data['answerData']
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    if not dbexercise.meta.published and not request.user.has_perm('exercises.edit_exercise'):
        return Response({'error': _('Exercise not activated.')}, status.HTTP_403_FORBIDDEN)

    if (
        getattr(request, 'limited', False)
        and not request.user.is_staff
        and not settings.RUNNING_DEVSERVER
    ):
        return Response(
            {'error': _('You are limited to ') + "5" + _(" exercise check tries per minute.")}
        )

    agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    try:
        result = question_module.question_check(
            request, request.user, agent, exercise, question, answer_data
        )
        return Response(result)
    except NameError as e:
        return Response({'error': "Origin: exercise_check. " + str(e)})


@never_cache
@api_view(['GET'])
def question_last_answer(request, exercise, question):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    dbquestion = Question.objects.get(exercise=dbexercise, question_key=question)
    dbanswer = Answer.objects.filter(user=request.user, question=dbquestion).latest('date')
    serializer = AnswerSerializer(dbanswer)
    return Response(serializer.data)


@api_view(['POST'])
@parser_classes((MultiPartParser,))
def upload_answer_image(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    if request.FILES['file'].size > 10e6:
        return Response(
            {
                'error': _(
                    "File larger than 10mb, please try to reduce the size "
                    "and upload again. (For images try to reduce the resolution"
                    " and for pdf files it is most likely large embedded images)"
                )
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        trial_image = Image.open(request.FILES['file'])
        trial_image.verify()
        image_answer = ImageAnswer(
            user=request.user,
            exercise=dbexercise,
            # exercise_key=exercise,
            image=request.FILES['file'],
            filetype=ImageAnswer.IMAGE,
        )
        extension = image_answer.image.path.split('.')[-1]
        image_answer.save()
        # if  not 'tif' in extension :
        image_answer.compress()
        return Response({})
    except Exception as e:
        if not dbexercise.meta.allow_pdf:
            return Response("Invalid image", status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            PyPDF2.PdfFileReader(request.FILES['file'])
            image_answer = ImageAnswer(
                user=request.user,
                exercise=dbexercise,
                # exercise_key=exercise,
                pdf=request.FILES['file'],
                filetype=ImageAnswer.PDF,
            )
            image_answer.save()
            return Response({})

        except PyPDF2.utils.PdfReadError:
            return Response("Invalid image", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def answer_image_view(request, image_id):
    try:
        image_answer = ImageAnswer.objects.get(pk=image_id)
        if image_answer.user == request.user or request.user.is_staff:
            if image_answer.filetype == 'IMG':
                return serve_file(
                    '/' + settings.SUBPATH + image_answer.image.name,
                    os.path.basename(image_answer.image.name),
                    content_type="image/jpeg",
                    dev_path=image_answer.image.path,
                )
            if image_answer.filetype == 'PDF':
                return serve_file(
                    '/' + settings.SUBPATH + image_answer.pdf.name,
                    os.path.basename(image_answer.pdf.name),
                    content_type="application/pdf",
                    dev_path=image_answer.pdf.path,
                )
        else:
            return Response("Not authorized", status.HTTP_500_INTERNAL_SERVER_ERROR)
    except ObjectDoesNotExist:
        return Response("invalid answer image id", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def answer_image_thumb_view(request, image_id):
    try:
        image_answer = ImageAnswer.objects.get(pk=image_id)
        if image_answer.user == request.user or request.user.is_staff:
            return serve_file(
                "/" + settings.SUBPATH + image_answer.image_thumb.url,
                os.path.basename(image_answer.image.name),
                content_type="image/jpeg",
                dev_path='./' + image_answer.image_thumb.url,
            )
        else:
            return Response("Not authorized", status.HTTP_500_INTERNAL_SERVER_ERROR)
    except ObjectDoesNotExist:
        return Response("invalid answer image id", status.HTTP_500_INTERNAL_SERVER_ERROR)


@permission_required('exercises.administer_exercise')
@api_view(['GET'])
def exercise_test_view(request, exercise):
    return Response(exercise_test(exercise))


@permission_required('exercises.administer_exercise')
def exercises_test(request):
    def format_test(exercise):
        return {
            'exercise': exercise.exercise_key,
            'questions': exercise_test(exercise.exercise_key),
            'exercise_name': exercise.name,
        }

    exercises = Exercise.objects.all()
    results = [format_test(exercise) for exercise in exercises]
    return TemplateResponse(request, 'exercises_test.html', {'results': results})


@api_view(['GET'])
def image_answers_get(request, exercise):
    image_answers = ImageAnswer.objects.filter(user=request.user, exercise__exercise_key=exercise)
    image_answers_serialized = ImageAnswerSerializer(image_answers, many=True)
    image_answers_id_list = [image_answer.pk for image_answer in image_answers]
    return Response({'ids': image_answers_id_list, 'data': image_answers_serialized.data})


@api_view(['POST'])
def image_answer_delete(request, pk):
    try:
        image_answer = ImageAnswer.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return Response(
            {'deleted': 0, 'error': 'Id not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    if not request.user == image_answer.user and not request.user.is_staff:
        return Response({'deleted': 0, 'error': 'Permission denied'})
    if image_answer.exercise.meta.deadline_date is not None and not before_deadline(
        image_answer.exercise.course, image_answer.date, image_answer.exercise.meta.deadline_date
    ):
        if now() > image_answer.date + datetime.timedelta(minutes=10):
            return Response(
                {'deleted': 0, 'error': _('You cannot delete after the deadline has passed.')}
            )

    image_answer.remove()  # REMOVE THE FILE
    deleted, deltype = image_answer.delete()  # REMOVE THE DATABASE ENTRY
    return Response({'deleted': deleted})
