# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from rest_framework.decorators import api_view, parser_classes
from django.core import serializers
from django.contrib.auth.models import Group, User
import os
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound, HttpResponseServerError
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from django.shortcuts import redirect, render
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import permission_required
from django.utils.translation import gettext as _
from django.contrib.auth import logout as syslogout
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from rest_framework.response import Response
from django.conf import settings
from django.core.files.base import File
from django.db import transaction
import time
import logging

from course.models import Course
from course.export_import import import_course_exercises, export_course_exercises
from course.export_import import export_server
from course.export_import import import_server
import workqueue.util as workqueue
import tempfile
import subprocess

logger = logging.getLogger(__name__)
from utils import get_subdomain_and_db


def export_course_exercises_pipeline(task, course):
    task.status = "Working"
    task.save()
    dirpath = str(tempfile.mkdtemp())
    output_filename = None
    try:
        for filename, progress in export_course_exercises(course=course, output_path=dirpath):
            # logger.error("FILENAME = %s PROGRESS = %s " % (filename, progress) )
            task.progress = progress * 100
            task.status = filename
            task.save()
            output_filename = filename
        if output_filename is None:
            task.result_file = None
            task.done = False
            task.status = "No exercises to export"
            task.progress = 100
            task.save()
        else:
            # logger.error("OUTPUT FILENAME = %s PROGRESS = %s " % (output_filename, progress) )
            task.result_file = File(open(output_filename, "rb"))
            task.done = True
            task.status = "Done"
            task.progress = 100
            task.save()
            # logger.error("TASK SAVED OUTPUT FILENAME = %s PROGRESS = %s " % (output_filename, progress) )
            # logger.error("TASK RESULT FILE %s " % task.result_file )
            # logger.error("DB_NAME = %s " %  settings.DB_NAME )
    except Exception as e:
        task.status = str(e)
        task.save()


@permission_required("exercises.edit_exercises")
@api_view(["GET"])
def export_course_exercises_async(request, course_pk):
    # logger.error("EXPORT COURSE EXERCISES ASYNC")
    # logger.error("OPENTASITE = %s " %  dbcourse.opentasite)
    subdomain, db = get_subdomain_and_db(request)
    dbcourse = Course.objects.using(db).get(pk=course_pk)
    # if settings.MULTICOURSE :
    #    subdomain = str( dbcourse.opentasite )
    # else :
    #    subdomain = settings.SUBDOMAIN
    task_id = workqueue.enqueue_task(
        "course_exercises_export", export_course_exercises_pipeline, course=dbcourse, subdomain=subdomain
    )
    return Response({"task_id": task_id})


def export_course_pipeline(task, course):
    # logger.error("EXPORT COURSE PIPELINE")
    # print(f"EXPORT COURSE EXERCISES PIPELINE {task} {vars(task)}  ")
    subdomain = task.subdomain
    # print(f"EXPORT_COURSE_SUBDOMAIN = {subdomain}")
    task.status = "Working"
    task.save()
    dirpath = str(tempfile.mkdtemp())
    output_filename = None
    # logger.error(" DIRPATH = " + str(dirpath))
    # print(f"TASK = {task} course={course}")
    try:
        # for status, progress, filename in export_course(course=course, output_path=dirpath):
        for task_result in export_server(output_path=dirpath, subdomain=subdomain):
            task.progress = task_result.progress * 100
            task.status = task_result.status
            task.save()
            output_filename = task_result.result
        task.result_file = File(open(output_filename, "rb"))
        task.done = True
        task.status = "Done"
        task.progress = 100
        task.save()
    except Exception as e:
        task.status = str(e)
        task.done = True
        task.save()


@permission_required("exercises.edit_exercises")
@api_view(["GET"])
def export_course_async(request, course_pk):
    # logger.error("EXPORT COURSE ASYNC")
    subdomain, db = get_subdomain_and_db(request)
    dbcourse = Course.objects.get(pk=course_pk)
    task_id = workqueue.enqueue_task("course_export", export_course_pipeline, course=dbcourse, subdomain=subdomain)
    return Response({"task_id": task_id})


def import_server_pipeline(task, file_path):
    task.status = "Working"
    subdomain = task.subdomain
    task.save()
    #print(f"IMPORT_SERVER_PIPELINE FILE_PATH = {file_path}")
    try:
        # TODO(hamlin): It would be really nice if this was done atomically so that
        # we could safely revert if there are any errors. However this prevents the
        # progress reporting since that is a database commit to the workqueue model.
        # with transaction.atomic():
        for status, progress in import_server(file_path, merge=True, subdomain=subdomain):
            task.progress = progress * 100
            task.status = "( {status} : Wait for done : {percent}% progress ".format(
                status=status, percent=task.progress
            )
            task.save()

        
        task.done = True
        task.status = "Done: Log out now."
        task.progress = 100
        task.save()

    except Exception as e:
        task.status = str(e)
        task.done = True
        task.save()


@api_view(["POST"])
@parser_classes((MultiPartParser,))
def import_server_view(request):
    logger.error("IMPORT SERVER VIEW")
    subdomain, db = get_subdomain_and_db(request)
    # if request.FILES['file'].size > 500e6:
    #    return Response("File larger than 500mb", status.HTTP_500_INTERNAL_SERVER_ERROR)
    staffs = User.objects.using(db).filter(is_staff=True)
    data = serializers.serialize("json", staffs)
    fp = open(f"/tmp/{subdomain}-staffs.txt","w")
    fp.write(data)
    fp.close()

    try:
        if not request.user.has_perm("exercises.edit_exercise"):
            return Response({}, status.HTTP_403_FORBIDDEN)

        upload_path = os.path.join(settings.VOLUME, "deleted")
        try:
            os.makedirs(upload_path, exist_ok=True)
        except Exception as e:
            logger.error(f" FAILED TO MAKE UPLOAD PATH {upload_path} {str(e)} ")

        # Chunked upload support
        upload_id = request.POST.get("uploadId")
        chunk_index = request.POST.get("chunkIndex")
        total_chunks = request.POST.get("totalChunks")
        file_obj = request.FILES.get("file")

        # If no chunking metadata is provided, fall back to legacy single upload
        if not (upload_id and chunk_index is not None and total_chunks):
            _, tmp_filename = tempfile.mkstemp(suffix=".zip", dir=upload_path)
            logger.error(f"IMPORT_SERVER_VIEW (legacy) tmp_filename={tmp_filename}")
            with open(tmp_filename, "wb") as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)
            task_id = workqueue.enqueue_task(
                "server_import", import_server_pipeline, file_path=tmp_filename, subdomain=subdomain
            )
            return Response({"task_id": task_id})

        # Parse chunking metadata
        try:
            chunk_index = int(chunk_index)
            total_chunks = int(total_chunks)
        except Exception:
            return Response("Invalid chunk metadata", status=status.HTTP_400_BAD_REQUEST)

        original_name = request.POST.get("fileName", "upload.zip")
        # Sanitize name for filesystem safety
        original_name = os.path.basename(original_name)

        # Build deterministic partial path from subdomain + upload_id
        partial_path = os.path.join(upload_path, f"{subdomain}-{upload_id}.part")

        # Write current chunk
        mode = "ab" if chunk_index > 0 and os.path.exists(partial_path) else "wb"
        with open(partial_path, mode) as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        # If last chunk, finalize and enqueue task
        if (chunk_index + 1) >= total_chunks:
            # Move to a final temp .zip path
            fd, tmp_filename = tempfile.mkstemp(suffix=".zip", dir=upload_path)
            os.close(fd)
            try:
                os.replace(partial_path, tmp_filename)
            except Exception as e:
                logger.error(f"Failed to finalize uploaded file: {e}")
                return Response("Failed to finalize upload", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            task_id = workqueue.enqueue_task(
                "server_import", import_server_pipeline, file_path=tmp_filename, subdomain=subdomain
            )
            return Response({"task_id": task_id, "file": original_name})

        # Not last chunk: acknowledge
        return Response({"received": chunk_index})

    except Exception as e:
        return Response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
