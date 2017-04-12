from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from exercises.serializers import (
    ExerciseSerializer,
    AnswerSerializer,
    ImageAnswerSerializer,
    AuditExerciseSerializer,
)
from exercises import parsing
from exercises.question import question_check
from exercises.modelhelpers import (
    serialize_exercise_with_question_data,
    exercise_folder_structure,
    student_attempts_exercises,
    exercise_test,
)
from exercises.paths import EXERCISES_PATH
from exercises.util import nested_print
from exercises.views.file_handling import serve_file
from django.utils.translation import ugettext as _
from django.http import FileResponse, HttpResponse, StreamingHttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import permission_required
from django.template.response import TemplateResponse
from django.template import loader
from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch
from ratelimit.decorators import ratelimit
from PIL import Image
import PyPDF2
import logging
import backend.settings as settings
import json
import time
import random

import sys
import os

# sys.path.insert(0, os.path.realpath(os.path.dirname(__file__) + '/../../../../questiontypes'))
# import question_types

logger = logging.getLogger(__name__)


@permission_required('exercises.reload_exercise')
@api_view(['POST', 'GET'])
def exercises_reload_streaming(request):  # {{{
    exercises = Exercise.objects.sync_with_disc()
    base = loader.get_template('base_streaming.html')
    template = loader.get_template('messages.html')

    def next_exercise():
        yield base.render()
        for progress in exercises:
            # c = RequestContext(request._request)
            rendered = loader.render_to_string('reload_progress.html', {'progress': progress})
            yield rendered  # template.render(c)

    return StreamingHttpResponse(next_exercise())


# }}}


@permission_required('exercises.reload_exercise')
@api_view(['POST', 'GET'])
def exercises_reload(request):  # {{{
    i_am_sure = request.data.get('i_am_sure', False)

    @transaction.atomic
    def sync():
        mess = []
        exercises = Exercise.objects.sync_with_disc(i_am_sure)
        for progress in exercises:
            mess = mess + progress
        return mess

    mess = sync()
    return render(request._request, "exercises_reload.html", {'progress': mess})


# }}}


@permission_required('exercises.reload_exercise')
@api_view(['POST', 'GET'])
def exercises_reload_json(request):  # {{{
    i_am_sure = request.data.get('i_am_sure', False)

    @transaction.atomic
    def sync():
        mess = []
        exercises = Exercise.objects.sync_with_disc(i_am_sure)
        for progress in exercises:
            mess = mess + progress
        return mess

    mess = sync()
    return Response(mess)  # }}}


@api_view(['GET'])
def exercise(request, exercise):  # {{{
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    data = serialize_exercise_with_question_data(dbexercise, request.user)
    return Response(data)  # }}}


@api_view(['GET'])
def exercise_list(request):  # {{{
    """
    List all exercises
    """
    responselist = {}
    # exercises = Exercise.objects.all()
    exercises = Exercise.objects.prefetch_related(
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
            for question in exercise.question.all():  # questions:
                try:
                    if hasattr(question, 'useranswers') and question.useranswers:
                        if not question.useranswers[0].correct:
                            allcorrect = False
                        answerserializer = AnswerSerializer(question.useranswers[0])
                        response = json.loads(question.useranswers[0].grader_response)
                        data['question'][question.question_key] = answerserializer.data
                        data['question'][question.question_key]['response'] = response
                    else:
                        allcorrect = False
                except ObjectDoesNotExist:
                    allcorrect = False
            data['correct'] = allcorrect
            responselist[exercise.exercise_key] = data
    return Response(responselist)  # }}}


@api_view(['GET'])
def exercise_tree(request):  # {{{
    """
    Get exercise tree
    """
    return Response(exercise_folder_structure(Exercise.objects, request.user))  # }}}


@api_view(['GET'])
def other_exercises_from_folder(request, exercise):  # {{{
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    other = []
    if request.user.has_perm('exercises.edit_exercise'):
        other = Exercise.objects.filter(folder=dbexercise.folder).prefetch_related('meta')
    else:
        other = Exercise.objects.filter(
            folder=dbexercise.folder, meta__published=True
        ).prefetch_related('meta')

    serializer = ExerciseSerializer(other, many=True)
    inorder = sorted(
        serializer.data,
        key=lambda item: "".join(
            [
                func(item['meta'][key])
                for (key, func) in [('published', lambda x: str(not x)), ('sort_key', str)]
            ]
        ),
    )
    return Response(inorder)  # }}}


@api_view(['GET'])
def exercise_json(request, exercise):  # {{{
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    try:
        hide_answers = not request.user.has_perm("exercises.view_solution")
        exercisejson = parsing.exercise_json(dbexercise.path, hide_answers=hide_answers)
        # questions = deep_get(exercisejson, 'exercise', 'question')
        return Response(exercisejson)
    except parsing.ExerciseParseError as e:
        return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)  # }}}


@permission_required('exercises.edit_exercise')
@api_view(['GET'])
def exercise_xml(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    return Response({'xml': parsing.exercise_xml(dbexercise.path)})


@permission_required('exercises.edit_exercise')
@api_view(['POST'])
def exercise_save(request, exercise):  # {{{
    result = {}
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    try:
        result = parsing.exercise_save(dbexercise.path, request.data['xml'])
        Exercise.objects.add_exercise(dbexercise.path)
        parsing.invalidate_caches()
        return Response(result)
    except parsing.ExerciseParseError as e:
        result = {'success': True, 'warning': str(e)}
        return Response(result)
    except IOError as e:
        result = {'success': False, 'error': str(e)}
        return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  # }}}


@ratelimit(key='user', rate='5/1m')
@api_view(['POST'])
def exercise_check(request, exercise, question):  # {{{
    answer_data = request.data['answerData']
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    if not dbexercise.meta.published and not request.user.has_perm('exercises.edit_exercise'):
        return Response({'error': _('Exercise not activated.')}, status.HTTP_403_FORBIDDEN)

    if getattr(request, 'limited', False) and not request.user.is_staff:
        return Response({'error': _('You are limited to ') + "5" + _(" tries per minute.")})

    agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    result = question_check(request, request.user, agent, exercise, question, answer_data)
    return Response(result)  # }}}


@api_view(['GET'])
def question_last_answer(request, exercise, question):  # {{{
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    dbquestion = Question.objects.get(exercise=dbexercise, question_key=question)
    dbanswer = Answer.objects.filter(user=request.user, question=dbquestion).latest('date')
    serializer = AnswerSerializer(dbanswer)
    return Response(serializer.data)  # }}}


@api_view(['POST'])
@parser_classes((MultiPartParser,))
def upload_answer_image(request, exercise):
    # print(request.FILES['file'])
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    if request.FILES['file'].size > 10e6:
        return Response("Image larger than 10mb", status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        trial_image = Image.open(request.FILES['file'])
        trial_image.verify()
        image_answer = ImageAnswer(
            user=request.user,
            exercise=dbexercise,
            exercise_key=exercise,
            image=request.FILES['file'],
            filetype=ImageAnswer.IMAGE,
        )
        image_answer.save()
        return Response({})
    except Exception as e:
        if not dbexercise.meta.allow_pdf:
            return Response("Invalid image", status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            PyPDF2.PdfFileReader(request.FILES['file'])
            image_answer = ImageAnswer(
                user=request.user,
                exercise=dbexercise,
                exercise_key=exercise,
                pdf=request.FILES['file'],
                filetype=ImageAnswer.PDF,
            )
            image_answer.save()
            return Response({})

        except PyPDF2.utils.PdfReadError:
            return Response("Invalid image", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def answer_image_view(request, image_id):  # {{{
    try:
        image_answer = ImageAnswer.objects.get(pk=image_id)
        print(image_answer.image.name)
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
        # }}}


@api_view(['GET'])
def answer_image_thumb_view(request, image_id):  # {{{
    try:
        image_answer = ImageAnswer.objects.get(pk=image_id)
        if image_answer.user == request.user or request.user.is_staff:
            return serve_file(
                '/' + settings.SUBPATH + image_answer.image_thumb.url,
                os.path.basename(image_answer.image.name),
                content_type="image/jpeg",
                dev_path='media/' + image_answer.image_thumb.url,
            )
        else:
            return Response("Not authorized", status.HTTP_500_INTERNAL_SERVER_ERROR)
    except ObjectDoesNotExist:
        return Response("invalid answer image id", status.HTTP_500_INTERNAL_SERVER_ERROR)
        # }}}


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
    print(results)
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
    deleted, deltype = image_answer.delete()
    return Response({'deleted': deleted})
