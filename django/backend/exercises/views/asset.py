from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view, parser_classes
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from exercises.models import Exercise
from exercises.views.file_handling import serve_file
import backend.settings as settings
import exercises.paths as paths
from exercises.parsing import list_assets, add_asset, delete_asset, exercise_xmltree, has_asset
from PIL import Image

asset_types = ('.pdf', '.jpg', '.jpeg', '.svg', '.tiff', '.tif', '.png', '.gif')

THUMBNAIL_FILENAME = 'thumbnail.png'
DEFAULT_THUMBNAIL_SIZE = 10


@permission_required('exercises.edit_exercise')
@api_view(['DELETE'])
def exercise_asset_delete(request, exercise, asset):
    if not asset.lower().endswith(asset_types):
        return Response({}, status.HTTP_403_FORBIDDEN)
    dbexercise = Exercise.objects.get(exercise_key=exercise)

    res = delete_asset(dbexercise.path, asset)
    if 'error' in res:
        return Response(res, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(res)


@api_view(['GET'])
def exercise_asset(request, exercise, asset):
    if not asset.lower().endswith(asset_types):
        return Response({}, status.HTTP_403_FORBIDDEN)
    content_type = ''
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    xmltree = exercise_xmltree(dbexercise.path)
    solution_assets = xmltree.xpath('//solution/asset')
    for asset_node in solution_assets:
        if hasattr(asset_node, "text") and asset_node.text.strip() == asset:
            if not dbexercise.meta.solution and not request.user.has_perm(
                'exercises.view_solution'
            ):
                return Response({}, status.HTTP_403_FORBIDDEN)
    if asset.lower().endswith('.pdf'):
        content_type = 'application/pdf'
    if asset.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.tiff', '.tif')):
        content_type = 'image'

    if asset == THUMBNAIL_FILENAME:
        if not has_asset(dbexercise.path, asset):
            image = Image.new(
                "RGBA", (DEFAULT_THUMBNAIL_SIZE, DEFAULT_THUMBNAIL_SIZE), (255, 255, 255, 0)
            )
            response = HttpResponse(content_type="image/png")
            image.save(response, format='PNG')
            return response

    return serve_file(
        (
            "/"
            + settings.SUBPATH
            + "exerciseasset/{path}/{asset}".format(path=dbexercise.path, asset=asset)
        ),
        asset,
        dev_path='{root}/{path}/{asset}'.format(
            root=paths.EXERCISES_PATH, path=dbexercise.path, asset=asset
        ),
        content_type=content_type,
    )


@permission_required('exercises.edit_exercise')
@api_view(['GET'])
def exercise_list_assets(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    assets = list_assets(dbexercise.path, asset_types)
    return Response(assets)


@permission_required('exercises.edit_exercise')
@api_view(['POST'])
@parser_classes((MultiPartParser,))
def exercise_upload_asset(request, exercise):
    if request.FILES['file'].size > 10e6:
        return Response("File larger than 10mb", status.HTTP_500_INTERNAL_SERVER_ERROR)
    try:
        dbexercise = Exercise.objects.get(exercise_key=exercise)
        res = add_asset(dbexercise.path, request.FILES['file'], asset_types)
        if 'error' in res:
            return Response(res, status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(res)

    except Exception as e:
        return Response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
