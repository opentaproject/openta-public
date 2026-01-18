# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import datetime
import io
import logging
import os
from django.views.decorators.cache import never_cache
import time
import traceback
import zipfile

import exercises.paths as paths
from exercises.assets import (
    add_asset,
    asset_types,
    delete_asset,
    has_asset,
    list_assets,
    run_asset,
)
from exercises.models import Exercise
from course.models import Course
from exercises.parsing import exercise_xmltree
from exercises.views.file_handling import serve_file
from PIL import Image
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from utils import get_subdomain, get_subdomain_and_db

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from django.views.decorators.cache import cache_control

logger = logging.getLogger(__name__)



DEFAULT_THUMBNAIL_SIZE = 10


def dispatch_asset_path(request, exercise):
    _ = bool( request.user)
    user = request.user
    return _dispatch_asset_path(user, exercise)


def _dispatch_asset_path(user, exercise):
    """Dispatch asset path depending on user type.

    Args:
        request (HttpRequest): Django request object.
        exercise (Exercise): Exercise model object.

    Returns:
        str: Path to asset folder.

    """
    asset_path = None
    if user.has_perm("exercises.edit_exercise") or user.is_staff:
        asset_path = paths.get_exercise_asset_path(user, exercise)
    else:
        asset_path = paths.get_student_asset_path(user, exercise)

    return asset_path


@api_view(["DELETE"])
def exercise_asset_delete(request, exercise, asset):
    subdomain, db = get_subdomain_and_db(request)
    user = request.user
    username = user.username
    if not asset.lower().endswith(asset_types):
        return Response({}, status.HTTP_404_NOT_FOUND)
    dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
    _ = bool( dbexercise) # FORCE database execution

    if not user.has_perm("exercises.edit_exercise") and not dbexercise.meta.student_assets:
        logger.error(f" ERROR403 ASSET LINE 100")
        return Response({}, status.HTTP_403_FORBIDDEN)

    res = delete_asset(dispatch_asset_path(request, dbexercise), asset)
    if "error" in res:
        return Response(res, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(res)


def exercise_assets_clean(exercise, path):
    t = time.localtime()
    current_time = time.strftime("%Y-%m-%d", t)
    pat = f"{current_time}"
    all_files = os.listdir(path)
    n = 0
    fd = ""
    b = ""
    for file in all_files:
        if pat in file and file.split(".")[-1] == "txt":
            n = n + 1
            fd = fd + f"{b}{file}"
            b = ", "
            delete_asset(path, file)
    msg = f"deleted {fd}"
    if n == 0:
        msg = "no cleanup to do."
    return ["success", msg]


@api_view(["PATCH"])
def exercise_assets_handle(request, exercise, asset):
    subdomain, db = get_subdomain_and_db(request)
    dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
    path = dispatch_asset_path(request, dbexercise)
    if asset == "cleanup_assets":
        return Response(exercise_assets_clean(exercise, path))
        # t = time.localtime()
        # current_time = time.strftime("%Y-%m-%d", t)
        # pat = f"{current_time}"
        # dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
        # path = dispatch_asset_path(request, dbexercise)
        # all_files = os.listdir(path)
        # for file in all_files :
        #    if pat in file  and file.split('.')[-1] == 'txt' :
        #       #print(f" DELETE {file}")
        #       delete_asset(path, file )
        # return Response( ['success','cleaned up'] )
    subdomain, db = get_subdomain_and_db(request)
    if not asset.lower().endswith(asset_types):
        return Response({}, status.HTTP_404_NOT_FOUND)
    dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)

    if not request.user.has_perm("exercises.edit_exercise") and not dbexercise.meta.student_assets:
        logger.error(f"ERROR403 ASSET LINE 152")
        return Response({}, status.HTTP_403_FORBIDDEN)

    res = run_asset(dispatch_asset_path(request, dbexercise), asset)
    if "error" in res:
        return Response(res, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(res)

@api_view(["GET"])
@never_cache
def exercise_student_asset(request, exercise, asset, course_pk=None):
    subdomain, db = get_subdomain_and_db(request)
    if not asset.lower().endswith(asset_types):
        logger.error(f"ERROR 403 ASSET LINE 166")
        return Response({}, status.HTTP_403_FORBIDDEN)
    dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
    asset_path = "{path}/{asset}".format(path=paths.get_student_asset_path(request.user, dbexercise), asset=asset)
    dev_path = "{path}/{asset}".format(path=paths.get_student_asset_path(request.user, dbexercise), asset=asset)
    #print("EXERCISE_STUDENT ASSET DEV_PATH_STUDENT_ASSET = ", dev_path)
    prod_path = dev_path.replace(settings.VOLUME,'')  #
    if os.path.exists( dev_path ) :
        return serve_file(
            prod_path,
            asset,
            dev_path=dev_path,
            content_type=get_content_type(asset),
            source="exercise_student_asset",
            devpath=dev_path,
            accel_xpath=prod_path,
            )
    else :
        return  HttpResponseNotFound("<h1>Not Found </h1>")


@api_view(["GET"])
def exercise_clean_assets(request, exercise):
    subdomain, db = get_subdomain_and_db(request)
    try:
        dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
        course_pk = dbexercise.course.course_key
        return ["success", f"Wrote file {filename}"]

    except Exception as e:
        msg = f"ERROR E11959c {type(e).__name__}  UPLOAD_ASSET {request.user.username} {subdomain} "
        logger.error(f"{msg}")
        return Response({"error": "Upload failed"})


@api_view(["GET"])
def exercise_download_assets(request, exercise):
    subdomain, db = get_subdomain_and_db(request)
    dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
    path = "{path}".format(path=dispatch_asset_path(request, dbexercise))
    tmpfile = io.BytesIO()
    zipf = zipfile.ZipFile(tmpfile, "w", zipfile.ZIP_DEFLATED)
    for root, _, files in os.walk(path):
        for file in files:
            if "exercisekey" not in file and "history" not in file:
                fullpath = os.path.join(root, file)
                relpath = os.path.relpath(fullpath, start=path)
                zipf.write(fullpath, relpath)
    zipf.close()
    content_type = "application/zip"
    zipfilename = (os.path.basename(path)).strip() + ".zip"
    dt = "{0:%Y%m%d-%H%M%S}".format(datetime.datetime.now())
    response = HttpResponse(tmpfile.getvalue(), content_type=content_type)
    response["Content-Disposition"] = "attachment; filename=" + dt + "-" + zipfilename
    return response


# @api_view(['GET'])
@cache_control(max_age=600)
def exercise_asset(request, exercise, asset):
    subdomain, db = get_subdomain_and_db(request)
    dbexercise = Exercise.objects.using(db).select_related("course","meta").get(exercise_key=str(exercise))
    show_solution = dbexercise.meta.solution
    course_key= dbexercise.course.course_key
    try :
        fullpath = dbexercise.get_full_path();
    except  Exception as err :
        logger.error(f"ERROR 9201234 {type(err)} {str(err)}")
        return None

    settings.SUBDOMAIN = subdomain
    hostname = request.META.get("HTTP_HOST", "HTTP_HOST_MISSING")
    remote = request.META.get('REMOTE_ADDR')
    referer = request.META.get('HTTP_REFERER','')
    agent =  request.META.get('HTTP_USER_AGENT',' undefined').split(' ')[-1]; 
    if not asset  :
        logger.error(f"ERROR403 ASSET LINE 215")
        return HttpResponse( "<h3> empty asset </h3>")

    if not request.user.is_authenticated and  ( hostname  not in referer  ) :
        logger.error(f"ASSET_AUTHENTICATION_0 subdomain={subdomain} user={request.user}  referer={referer} authenticated={request.user.is_authenticated}  asset={asset} agent={agent}")
        #logger.error(f"ASSET_AUTHENTICATION_ERROR_1")
        #logger.error(f"ASSET_AUTHENTICATION_ERROR_2 {request.META['HTTP_USER_AGENT'] }  ")
        #logger.error(f"ASSET_AUTHENTICATION_ERROR_3 {request.user}  {request.user.is_authenticated} ")
        #logger.error(f"ASSET_AUTHENTICATION_ERROR_4 REQUEST = {request}")
        #logger.error(f"ASSET_AUTHENTICATION_ERROR_5 VARS =  {vars(request)} ")
        # ALLOW POST REQUESTS SO A STUDENT CAN PULL UP THE ASSET ON ANOTHER DEVICE
        return HttpResponse(
            '<h3> You must be logged in to see this asset  and have clicked the link. </h3> <em> If you are on Firefox, you may have to "Allow dangerous downloads" in Settings -> Privacy and Security. </em> '
        )
    if not ( "thumbnail" in asset or ( remote in settings.ASSET_WHITELIST  )  ):
        groups = list(request.user.groups.values_list("name", flat=True))
        if "Admin" in groups or "Author" in groups or "View" in groups or request.user.is_staff:
            pass
        else:
            xmltree = exercise_xmltree(fullpath, {})
            all_assets = set([x.text.strip() for x in xmltree.xpath("//asset")])
            figure_assets = set([x.text.strip() for x in xmltree.xpath("//figure")])
            hidden_assets = set([x.text.strip() for x in xmltree.xpath("//hidden//asset")])
            solution_assets = set([x.text.strip() for x in xmltree.xpath("//solution//asset")])
            ok_assets = all_assets.union(figure_assets) - hidden_assets
            if not show_solution:
                ok_assets = ok_assets - solution_assets
            if asset.strip() not in ok_assets:
                messages.add_message(request, messages.ERROR, f"{asset} is not available")
                logger.error(f"USER {request.user} in {subdomain} ASSET { request.get_full_path() } from REMOTE={remote} REFERER={referer} WAS REJECTED")
                return render(request, "base_failed.html")

            else:
                pass
    fetchmode = request.headers.get("Sec-Fetch-Mode", "navigate")
    if settings.CHECK_REFERER and not fetchmode == "no-cors" and not request.user.is_staff:
        try:
            x = datetime.datetime.now()
            ip = request.META.get("REMOTE_ADDR", "REMOTE_ADDR_MISSING")
            hostname = request.META.get("HTTP_HOST", "HTTP_HOST_MISSING")
            forwarded_host = request.META.get("HTTP_X_FORWARDED_HOST", "HTTP_X_FORWARDED_HOST_MISSING")
            referer = request.META.get("HTTP_REFERER", "HTTP_REFERER_MISSING").replace("https://", "").rstrip("/")
            if not ((hostname in forwarded_host) and (hostname in referer)):
                logger.info(
                    f"{x} {ip} ERROR-187 {request.user} FORWARDED_HOST={forwarded_host} HOSTNAME={hostname} REFERER={referer}"
                )
                logger.info(f"{x} {ip} ERROR-187 REQUEST_META = {request.META}")
                logger.info(
                    "%s %s %s EXERCISE-ASSET-ERROR-187  %s !=  %s %s %s "
                    % (x, ip, settings.SUBDOMAIN, hostname, forwarded_host, request.user, request.get_full_path())
                )
                logger.info(f"EXERCISE-ASSET-ERROR 187 continued META = {request.META}")
                if not request.user.is_staff:
                    msg = f"<h1> Error fetching asset {asset}. You must use website link, not the full url.  </h1>"
                    logger.error(
                        f"{x} ERROR ASSET REJECTED IP={ip} subdomain={subdomain} db={db} user={request.user} hostname={hostname} forwarded_host={forwarded_host} referer={referer} full_path={request.get_full_path}\n{msg} "
                    )
                    return HttpResponse(
                        msg
                    )  # FIXME
        except KeyError:
            logger.error(
                "%s %s %s EXERCISE-ASSET-ERROR-188 - KEY ERROR HTTP_X_FORWARDED_HOST MISSING user=%s full_path=%s "
                % (x, ip, settings.SUBDOMAIN, request.user, request.get_full_path())
            )
            logger.error(f"ADDITIONAL info request.META = {request.META}")
            return HttpResponse("<h1> Error 188 fetching %s </h1>" % asset)  # FIXME
        except Exception as e:
            logger.error(
                "%s %s %s UNKNOWN EXERCISE-ASSET-ERROR-189 - OTHER ERROR %s %s %s "
                % (x, ip, settings.SUBDOMAIN, request.user, type(e).__name__, request.get_full_path())
            )
            logger.error(f"ADDITIONAL info request.META = {request.META}")
            logger.error("ERROR STACKTRACE = %s " % str(e))
            logger.error(traceback.print_stack())
            return HttpResponse("<h1> Error 189 fetching %s </h1>" % asset)  # FIXME

    if not asset.lower().endswith(asset_types):
        logger.error(f"ERROR403 ASSET LINE 290")
        return Response({}, status.HTTP_403_FORBIDDEN)
    try:
        full_path = dbexercise.get_full_path()
        xmltree = exercise_xmltree(full_path)
    except Exception as e:
        msg = f"ERROR {type(e).__name__} E554418  EXERCISE_XMLTREE {settings.SUBDOMAIN} {request.user} {exercise} not found"
        logger.error(msg)
        return HttpResponseNotFound("<h1>Page not found</h1>")
    solution_assets = xmltree.xpath("//solution/asset")
    for asset_node in solution_assets:
        if hasattr(asset_node, "text") and asset_node.text.strip() == asset:
            if not dbexercise.meta.solution and not request.user.is_staff :
                logger.error(f"ERROR403 ASSET LINE 306 {request.user} {exercise} {asset} ")
                return HttpResponse("<h1> Request denied </h1>")

    if "thumbnail" in asset:
        try :
            if not has_asset(dbexercise.get_full_path(), asset):
                image = Image.new("RGBA", (DEFAULT_THUMBNAIL_SIZE, DEFAULT_THUMBNAIL_SIZE), (255, 255, 255, 0))
                response = HttpResponse(content_type="image/png")
                image.save(response, format="PNG")
                return response
        except Exception as err :
             return HttpResponseNotFound("<h1>Page not found</h1>")
    dev_path = paths.get_exercise_asset_path(request.user, dbexercise) + "/" + asset
    prod_path = str(dev_path).replace(settings.VOLUME, "")
    accel_xpath = dev_path.replace('/subdomain-data','')

    #if 'exercises' in prod_path : # PROTECT AGAINST BREAKING NON-EXERCISE-ASSET
    #    p = accel_xpath.split('/'); 
    #    p[1] = subdomain
    #    p[3] = course_key
    #    accel_xpath = '/'.join(p)
    #    devpath = dbexercise.exercise_asset_devpath(asset)
    #    p = devpath.split('/'); 
    #    p[2] = subdomain
    #    p[4] = course_key
    #    devpath = '/'.join(p)

    return serve_file(
        prod_path,
        asset,               
        dev_path=dev_path,   #### OK
        content_type=get_content_type(asset),
        source="exercise_asset",
        accel_xpath=accel_xpath, #### BROKEN
        devpath=dev_path,     #### BROKEN / HOPEFULLY FIXED
    )


@api_view(["GET"])
def exercise_list_assets(request, exercise):
    subdomain, db = get_subdomain_and_db(request)
    # print(f"EXERCISE_LIST_ASSETS")
    try:
        dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
        assets = list_assets(dispatch_asset_path(request, dbexercise), asset_types)
    except ObjectDoesNotExist:
        logger.error(f"Error 302 - exercise_list_assets: Exercise {exercise} not found. ")
        assets = []
    # if not request.user.has_perm('exercises.edit_exercise') and not dbexercise.meta.student_assets:
    #    return Response({}, status.HTTP_403_FORBIDDEN)
    return Response(assets)


@api_view(["POST"])
@parser_classes((MultiPartParser,))
def exercise_upload_asset(request, exercise):
    subdomain, db = get_subdomain_and_db(request)
    bool( request.user)
    is_staff = request.user.is_staff
    er = ''
    filename  = f'{request.FILES["file"]}'
    print(f' FILES = {filename}')
    filetype = ( filename.split('.')[-1] ).lower();
    if not is_staff and filetype in ['jpg','jpeg','png','pdf'] :
        res_error = Response({"error": f" You have uploaded {filename} to assets area. This file area is for your own files and is not seen in audits. Close the assets area;  reupload  using the pdf or camera icon on the exercise page. You will see a proper thumbnail or pdf icon on the main exercise page when that is done. "})
    else :
        res_error = None 
    if request.FILES["file"].size > settings.MAX_ASSET_UPLOAD_SIZE:
        msg = f"ERROR E11959a UPLOAD FILE TOO LARGE {request.user.username} {subdomain} FILE_SIZE={request.FILES['file'].size}"
        logger.error(msg)
        return Response({"error": f"File larger than {float( settings.MAX_ASSET_UPLOAD_SIZE)/1.e6} Mb"})
    try:
        dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
        _ = bool( dbexercise ) # FORCE EVALUATION OF QUERYST
        er = er + 'a'
        course_pk = dbexercise.course.course_key
        er = er + 'b'
        if not request.user.has_perm("exercises.edit_exercise") and not dbexercise.meta.student_assets:
            msg = f"ERROR403 E11959b UPLOAD FILE Permission issues {request.user.username} {subdomain} "
            logger.error(msg)
            return Response({}, status.HTTP_403_FORBIDDEN)
        er = er + 'c'
        res = add_asset(
            dispatch_asset_path(request, dbexercise),
            request.FILES["file"],
            asset_types,
            course_pk,
            is_staff,
        )
        if res_error  == None :
            return Response(res)
        else :
            return res_error

    except Exception as e:
        msg = f"ERROR E11959c {er} {type(e).__name__}  UPLOAD_ASSET {request.user.username} {subdomain} "
        logger.error(f"{msg}")
        return Response({"error": "Upload failed"})


def get_content_type(asset):
    content_type = None
    if asset.lower().endswith(".pdf"):
        content_type = "application/pdf"
    if asset.lower().endswith((".png", ".jpg", ".jpeg", ".svg", ".tiff", ".tif")):
        content_type = "image"
    return content_type
