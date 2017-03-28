from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view, parser_classes
from django.contrib.auth.decorators import permission_required
from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from exercises.views.file_handling import serve_file
import backend.settings as settings
from exercises.paths import EXERCISES_PATH
import os


@api_view(['GET'])
def exercise_asset(request, exercise, asset):  # {{{
    if not asset.lower().endswith(('.png', '.pdf', '.jpg', '.jpeg', '.svg', '.tiff')):
        return Response({}, status.HTTP_403_FORBIDDEN)
    content_type = ''
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    if asset.lower().endswith('.pdf'):
        if not dbexercise.meta.solution and not request.user.has_perm('exercises.view_solution'):
            return Response({}, status.HTTP_403_FORBIDDEN)
        content_type = 'application/pdf'

    return serve_file(
        "/"
        + settings.SUBPATH
        + "exerciseasset/{path}/{asset}".format(path=dbexercise.path, asset=asset),
        asset,
        dev_path='{root}/{path}/{asset}'.format(
            root=EXERCISES_PATH, path=dbexercise.path, asset=asset
        ),
        content_type=content_type,
    )
    # }}}


@permission_required('exercises.edit_exercise')
@api_view(['GET'])
def exercise_list_assets(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    files = os.listdir(os.path.join(EXERCISES_PATH, dbexercise.path))
    return Response(files)
