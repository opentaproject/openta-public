from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import PermissionDenied
from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from exercises.serializers import ExerciseSerializer, AnswerSerializer, ImageAnswerSerializer
from exercises.serializers import AuditExerciseSerializer
from exercises import parsing
import exercises.question as question_module
from exercises.modelhelpers import serialize_exercise_with_question_data
from exercises.modelhelpers import exercise_folder_structure, exercise_test
from exercises.views.file_handling import serve_file
from exercises.time import before_deadline
from exercises.util import deep_get
from utils import response_from_messages
from django.utils.translation import ugettext as _
from django.http import StreamingHttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import permission_required
from django.template.response import TemplateResponse
from django.template import loader
from django.utils.timezone import now
from django.db import transaction
from django.db.models import Prefetch
from ratelimit.decorators import ratelimit
from django.views.decorators.cache import never_cache
from PIL import Image
import datetime
import PyPDF2
import logging
import backend.settings as settings
import json

import os

logger = logging.getLogger(__name__)


@permission_required('exercises.reload_exercise')
@api_view(['POST', 'GET'])
def exercises_reload_streaming(request):
    exercises = Exercise.objects.sync_with_disc()
    base = loader.get_template('base_streaming.html')

    def next_exercise():
        yield base.render()
        for progress in exercises:
            rendered = loader.render_to_string('reload_progress.html', {'progress': progress})
            yield rendered

    return StreamingHttpResponse(next_exercise())


@permission_required('exercises.reload_exercise')
@api_view(['POST', 'GET'])
def exercises_reload(request):
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


@api_view(['POST', 'GET'])
def exercises_reload_json(request):
    if not request.user.has_perm('exercises.reload_exercise'):
        raise PermissionDenied(_("Permission denied"))
    i_am_sure = request.data.get('i_am_sure', False)

    @transaction.atomic
    def sync():
        mess = []
        exercises = Exercise.objects.sync_with_disc(i_am_sure)
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
def exercise_list(request):
    """
    List all exercises
    """
    responselist = {}
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
def exercise_tree(request):
    """
    Get exercise tree
    """
    return Response(exercise_folder_structure(Exercise.objects, request.user))


@never_cache
@api_view(['GET'])
def other_exercises_from_folder(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    other = []
    if request.user.has_perm('exercises.edit_exercise'):
        other = Exercise.objects.filter(folder=dbexercise.folder).prefetch_related('meta')
    else:
        other = Exercise.objects.filter(
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
    try:
        hide_answers = not request.user.has_perm("exercises.view_solution")
        full_exercisejson = parsing.exercise_json(dbexercise.path, hide_answers=False)
        hide_tags = question_module.get_sensitive_tags()
        hide_attrs = question_module.get_sensitive_attrs()
        safe_exercisejson = parsing.exercise_json(
            dbexercise.path,
            hide_answers=hide_answers,
            sensitive_attrs=hide_attrs,
            sensitive_tags=hide_tags,
        )
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
                modified_question = question_module.question_json_hook(
                    safe_question, full_question, dbquestion.pk, request.user.pk
                )
                safe_exercisejson['exercise']['question'].append(modified_question)
        return Response(safe_exercisejson)
    except parsing.ExerciseParseError as e:
        return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@permission_required('exercises.edit_exercise')
@never_cache
@api_view(['GET'])
def exercise_xml(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    return Response({'xml': parsing.exercise_xml(dbexercise.path)})


@permission_required('exercises.edit_exercise')
@api_view(['POST'])
def exercise_save(request, exercise):
    messages = []
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    backup_name = "{:%Y%m%d_%H:%M:%S_%f_}".format(now()) + request.user.username + ".xml"
    try:
        messages += parsing.exercise_save(dbexercise.path, request.data['xml'], backup_name)
    except IOError as e:
        messages.append(('error', str(e)))
    try:
        messages += Exercise.objects.add_exercise(dbexercise.path)
    except parsing.ExerciseParseError as e:
        messages.append(('warning', str(e)))
    result = response_from_messages(messages)
    return Response(result)


@ratelimit(key='user', rate='5/1m')
@api_view(['POST'])
def exercise_check(request, exercise, question):
    answer_data = request.data['answerData']
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    if not dbexercise.meta.published and not request.user.has_perm('exercises.edit_exercise'):
        return Response({'error': _('Exercise not activated.')}, status.HTTP_403_FORBIDDEN)

    if getattr(request, 'limited', False) and not request.user.is_staff:
        return Response({'error': _('You are limited to ') + "5" + _(" tries per minute.")})

    agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    result = question_module.question_check(
        request, request.user, agent, exercise, question, answer_data
    )
    return Response(result)


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
def answer_image_view(request, image_id):
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


@api_view(['GET'])
def answer_image_thumb_view(request, image_id):
    try:
        image_answer = ImageAnswer.objects.get(pk=image_id)
        if image_answer.user == request.user or request.user.is_staff:
            return serve_file(
                '/' + settings.SUBPATH + image_answer.image_thumb.url,
                os.path.basename(image_answer.image.name),
                content_type="image/jpeg",
                dev_path='./media/' + image_answer.image_thumb.url,
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
    if image_answer.exercise.meta.deadline_date is not None and not before_deadline(
        image_answer.date, image_answer.exercise.meta.deadline_date
    ):
        if now() > image_answer.date + datetime.timedelta(minutes=10):
            return Response(
                {'deleted': 0, 'error': _('You cannot delete after the deadline has passed.')}
            )

    deleted, deltype = image_answer.delete()
    return Response({'deleted': deleted})
