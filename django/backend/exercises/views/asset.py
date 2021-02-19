from rest_framework import status
from django.contrib import messages
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view, parser_classes
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, FileResponse
from exercises.models import Exercise
from exercises.views.file_handling import serve_file
from exercises.paths import _subpath
from django.conf import settings
import exercises.paths as paths
from exercises.assets import list_assets, add_asset, delete_asset, has_asset
from exercises.parsing import exercise_xmltree
import zipfile
import tempfile
import os
import io
from PIL import Image
import datetime
import logging

logger = logging.getLogger(__name__)


asset_types = (
    '.pdf',
    '.jpg',
    '.jpeg',
    '.svg',
    '.tiff',
    '.tif',
    '.png',
    '.gif',
    '.py',
    '.csv',
    '.txt',
    '.m',
    '.tex',
    '.gz',
    '.zip',
)

THUMBNAIL_FILENAME = 'thumbnail.png'
DEFAULT_THUMBNAIL_SIZE = 10


def dispatch_asset_path(request, exercise):
    user = request.user
    return( _dispatch_asset_path( user, exercise) )

def _dispatch_asset_path(user , exercise):
    """Dispatch asset path depending on user type.

    Args:
        request (HttpRequest): Django request object.
        exercise (Exercise): Exercise model object.

    Returns:
        str: Path to asset folder.

    """
    asset_path = None
    #logger.info("DISPATCH_ASSET_PATH")
    if user.has_perm('exercises.edit_exercise'):
        #logger.info("PERM ASSET PATH = "+ str( asset_path) )
        asset_path = paths.get_exercise_asset_path(user,exercise)
        #logger.info("PERM ASSET PATH = "+ str( asset_path) )
    else:
        #logger.info("ELSE ASSET_PATH" +   str( exercise) )
        #logger.info("DBEXERCISE = " + str(  exercise.course.course_key) )
        # course_key = dbexercise.course.course_key
        asset_path = paths.get_student_asset_path(user, exercise)
    #logger.info("_DISPATCH_ASSET_PATH ASSET_PATH = " +  str( asset_path ) )

    return asset_path


@api_view(['DELETE'])
def exercise_asset_delete(request, exercise, asset):
    if not asset.lower().endswith(asset_types):
        return Response({}, status.HTTP_403_FORBIDDEN)
    dbexercise = Exercise.objects.get(exercise_key=exercise)

    if not request.user.has_perm('exercises.edit_exercise') and not dbexercise.meta.student_assets:
        return Response({}, status.HTTP_403_FORBIDDEN)

    res = delete_asset(dispatch_asset_path(request, dbexercise), asset)
    if 'error' in res:
        return Response(res, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(res)


@api_view(['GET'])
def exercise_student_asset(request, exercise, asset):
    if not asset.lower().endswith(asset_types):
        return Response({}, status.HTTP_403_FORBIDDEN)
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    asset_path = "{path}/{asset}".format(
        path=paths.get_student_asset_path(request.user, dbexercise), asset=asset
    )
    dev_path = "{path}/{asset}".format(
        path=paths.get_student_asset_path(request.user, dbexercise), asset=asset
    )
    print("EXERCISE_STUDENT ASSET DEV_PATH_STUDENT_ASSET = ", dev_path)
    prod_path = dev_path.replace(settings.VOLUME,_subpath( uri=request.get_full_path(), session=request.session))
    print("prod_path = ", prod_path)
    return serve_file(
        prod_path,
        asset,
        dev_path=dev_path,
        content_type=get_content_type(asset),
    )


@api_view(['GET'])
def exercise_download_assets(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    path = "{path}".format(path=dispatch_asset_path(request, dbexercise))
    tmpfile = io.BytesIO()
    zipf = zipfile.ZipFile(tmpfile, 'w', zipfile.ZIP_DEFLATED)
    for root, _, files in os.walk(path):
        for file in files:
            if 'exercisekey' not in file and 'history' not in file :
                fullpath = os.path.join(root, file)
                relpath = os.path.relpath(fullpath, start=path)
                zipf.write(fullpath, relpath)
    zipf.close()
    content_type = 'application/zip'
    zipfilename = (os.path.basename(path)).strip() + '.zip'
    dt = '{0:%Y%m%d-%H%M%S}'.format(datetime.datetime.now())
    response = HttpResponse(tmpfile.getvalue(), content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename=' + dt + '-' + zipfilename
    return response


@api_view(['GET'])
def exercise_asset(request, exercise, asset):
    #logger.info("GET EXERCISE_ASSET")
    if not asset.lower().endswith(asset_types):
        return Response({}, status.HTTP_403_FORBIDDEN)
    dbexercise = Exercise.objects.get(exercise_key=exercise)

    xmltree = exercise_xmltree(dbexercise.get_full_path())
    solution_assets = xmltree.xpath('//solution/asset')
    for asset_node in solution_assets:
        if hasattr(asset_node, "text") and asset_node.text.strip() == asset:
            if not dbexercise.meta.solution and not request.user.has_perm(
                'exercises.view_solution'
            ):
                return Response({}, status.HTTP_403_FORBIDDEN)

    if asset == THUMBNAIL_FILENAME:
        if not has_asset(dbexercise.get_full_path(), asset):
            image = Image.new(
                "RGBA", (DEFAULT_THUMBNAIL_SIZE, DEFAULT_THUMBNAIL_SIZE), (255, 255, 255, 0)
            )
            response = HttpResponse(content_type="image/png")
            image.save(response, format='PNG')
            return response
    dev_path =  '{root}/{path}/{asset}'.format(
            root=dbexercise.course.get_exercises_path(), path=dbexercise.path, asset=asset
        )
    dev_path = paths.get_exercise_asset_path(request.user , dbexercise) + '/' + asset
    #logger.info("1 EXERCISE_ASSET ASSET = "+ asset )
    print("2 EXERCISE_ASSET DEV_PATH = "+ dev_path)
    prod_path = str( dev_path ).replace(settings.VOLUME ,_subpath(uri=request.get_full_path(), session=request.session))
    logger.info("3 EXERCISE_ASSET PROD_PATH = " +  prod_path)
    return serve_file(
        prod_path,
        asset,
        dev_path=dev_path,
        content_type=get_content_type(asset),
    )


@api_view(['GET'])
def exercise_list_assets(request, exercise):
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    # if not request.user.has_perm('exercises.edit_exercise') and not dbexercise.meta.student_assets:
    #    return Response({}, status.HTTP_403_FORBIDDEN)
    assets = list_assets(dispatch_asset_path(request, dbexercise), asset_types)
    return Response(assets)


@api_view(['POST'])
@parser_classes((MultiPartParser,))
def exercise_upload_asset(request, exercise):
    print("EXERCISE_UPLOAD_ASSET")
    if request.FILES['file'].size > 10e6:
        return Response("File larger than 10mb", status.HTTP_500_INTERNAL_SERVER_ERROR)
    try:
        dbexercise = Exercise.objects.get(exercise_key=exercise)
        course_pk = dbexercise.course.course_key
        if (
            not request.user.has_perm('exercises.edit_exercise')
            and not dbexercise.meta.student_assets
        ):
            return Response({}, status.HTTP_403_FORBIDDEN)
        res = add_asset(
            dispatch_asset_path(request, dbexercise),
            request.FILES['file'],
            asset_types,
            course_pk,
            request.user.is_staff,
        )
        if 'error' in res:
            return Response(res, status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(res)

    except Exception as e:
        return Response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_content_type(asset):
    content_type = None
    if asset.lower().endswith('.pdf'):
        content_type = 'application/pdf'
    if asset.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.tiff', '.tif')):
        content_type = 'image'
    return content_type
