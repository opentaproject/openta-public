# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
from django.shortcuts import render
import os
import re
from zipfile import BadZipFile
from django.http import HttpRequest, HttpResponse
from utils import get_subdomain_and_db

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.http.response import JsonResponse
from django.utils.datastructures import MultiValueDictKeyError
from users.models import OpenTAUser
from exercises.models import Exercise
from django.utils.translation import gettext as _
from backend.middleware import verify_or_create_database_connection
from django.views.generic.edit import UpdateView
from rest_framework.decorators import api_view, parser_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status

from backend.serializers import UploadResult, UploadResultSerializer
from course.export_import import import_course_exercises, import_course_zip
from course.forms import CourseFormFrontend
from course.models import Course
from course.serializers import CourseSerializer, CourseStudentSerializer
from exercises.views.file_handling import serve_file

logger = logging.getLogger(__name__)


class CourseUpdate(UpdateView):
    model = Course
    form_class = CourseFormFrontend
    # fields = ['course_name', 'registration_password', 'registration_by_password', 'owners']
    readonly_fields = ("course_key", "lti_key", "lti_secret")
    success_url = "/" + "course/{id}/updateoptions/"

    def get_context_data(self, **kwargs):
        logger.debug(f"COURSE_UPDATE context_data = {vars(self)} ")
        logger.debug(f"COURSE_UPDATE request = {self.request} ")
        request = self.request
        subdomain, db = get_subdomain_and_db(self.request)
        context = super().get_context_data(**kwargs)
        context["submit_text"] = _("Save")
        contextkeys = list(context.keys())
        logger.debug(f"CONTEXT = {contextkeys}")
        obj = context["object"]
        logger.debug(f"CONTEXT.OBJECT= {vars(obj)}")
        return context

    def get_object(self, queryset=None):
        logger.debug(f"COURSE_UPDATE OBJECT = {self.kwargs}")
        db = self.kwargs["subdomain"]
        if settings.RUNTESTS:
            db = "default"
        obj = self.model.objects.using(db).get(pk=self.kwargs["pk"])
        # if 'subpath' in self.kwargs :
        #    #logger.debug("FOUND SUBPATH IN COURSSE KWARGS")
        obj.subpath = self.kwargs.get("subpath")
        obj.subpath = ""
        return obj


# FIXME: running this code in a test generates: NameError: name '_subpath' is not defined
# FIXME: this function is named like a class would be


@permission_required("course.administer_course")
def CourseUpdateView(request, course_pk):
    # logger.debug("COURS UPDATE VIEW")
    subdomain, db = get_subdomain_and_db(request)
    logger.debug(f"COURSE_UPDATE_VIEW DB={db} subdomain={subdomain}")
    courses = Course.objects.using(db).filter(pk=course_pk)
    course = courses[0];
    courseurl = request.build_absolute_uri("/") + course.course_name + "/"
    settings.SUBDMAIN = subdomain
    logger.debug(f"COURSE_URL = {courseurl}")
    if not courseurl == course.url:
        course.url = courseurl
        #course.opentasite = subdomain
        courses.update(url=courseurl)
    subpath = ""
    result = CourseUpdate.as_view()(request, pk=course_pk, subpath=subpath, subdomain=subdomain)
    if request.method == "POST":
        result.set_cookie("submitted", "true")
    else:
        result.set_cookie("submitted", "false")
    return result


@api_view(["GET"])
def get_course(request, course_pk):
    subdomain, db = get_subdomain_and_db(request)
    course = Course.objects.using(db).get(pk=course_pk)
    if request.user.is_superuser or request.user.is_staff:
        scourse = CourseSerializer(course)
    else:
        scourse = CourseStudentSerializer(course)
    return Response(scourse.data)


@api_view(["GET"])
def get_pages(request, course_pk, path):
    # https://v320c.localhost:8000/course/1/pages/homepage/index.html
    subdomain, db = get_subdomain_and_db(request)
    logger.debug("GET COURSE PAGES %s %s ", (course_pk, path))
    course = Course.objects.using(db).get(pk=course_pk)
    course_key = str(course.course_key)
    logger.debug("GET COURSE PAGES %s %s", course_key, path)
    filename = os.path.join(course.get_pages_path(), path)
    logger.debug("FILENAME = %s", filename)
    dev_path = filename
    prod_path = dev_path
    filebasename = os.path.basename(dev_path)
    devpath = dev_path
    accel_xpath = re.sub(f"{settings.VOLUME}", "", dev_path)
    return serve_file(
        prod_path, filebasename, dev_path=dev_path, devpath=devpath, accel_xpath=accel_xpath, source="get_pages"
    )


@api_view(["GET"])
def get_courses(request, *args):
    subdomain, db = get_subdomain_and_db(request)
    courses = Course.objects.using(db).all()
    user = request.user
    try:
        opentauser, created = OpenTAUser.objects.using(db).get_or_create(user=user)
        if created:
            opentauser.save()
    except Exception as e:
        logger.error(f"COURSE ERROR 491 User {user}  does not have opentauser and fix failed. {type(e).__name__} ")
        return Response({}, status.HTTP_403_FORBIDDEN)
    try:
        if request.user.is_superuser:
            scourse = CourseSerializer(courses, many=True)
        elif request.user.is_staff:
            courses_owned = courses.filter(owners=request.user)
            courses_enrolled = courses.filter(pk__in=opentauser.courses.values_list("pk", flat=True))
            scourse = CourseSerializer(courses_owned | courses_enrolled, many=True)
        else:
            try:
                courses = opentauser.courses.filter(published=True)
                scourse = CourseStudentSerializer(courses, many=True)
            except Exception as e:
                logger.error(f"ERROR : E491b COURSE courses={courses} {settings.SUBDOMAIN} user={request.user}")
                return Response({}, status.HTTP_403_FORBIDDEN)
        # for s in  scourse.data:
        #    sl = dict(s)
        #    langs = sl['languages']
        #    logger.error(f" LANGS = {langs}")
        return Response(scourse.data)
    except Exception as e:
        logger.error(
            f"ERROR 491c: {type(e).__name__} No courses exist for subdomain={settings.SUBDOMAIN} user={request.user}"
        )
        return Response({}, status.HTTP_403_FORBIDDEN)


@api_view(["POST"])
@parser_classes((MultiPartParser,))
def upload_exercises(request, course_pk):
    logger.error("UPLOAD_EXERCISES : course: %s", course_pk)
    subdomain, db = get_subdomain_and_db(request)

    try:
        file_size_limit = settings.EXERCISES_IMPORT_FILE_SIZE_LIMIT
        if request.FILES["file"].size > settings.EXERCISES_IMPORT_FILE_SIZE_LIMIT:
            logger.error(f" FILE SIZE LIMIT EXCEEEDED {request.FILES['file'].size} > {file_size_limit}")
            return JsonResponse(
                {"file_size_limit": f"exceeds {settings.EXERCISES_IMPORT_FILE_SIZE_LIMIT}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dbcourse = Course.objects.using(db).get(pk=course_pk)
        if not request.user.has_perm("exercises.edit_exercise"):
            raise PermissionDenied(detail={"exercise": "cannot edit"})

        tmp_path = request.FILES["file"].temporary_file_path()
        res = import_course_exercises(dbcourse, tmp_path)

        messages = res;
        serializer = UploadResultSerializer(instance=messages, many=True)
        return Response(serializer.data)

    except Course.DoesNotExist:
        raise NotFound(detail={"course": "not found"})

    except BadZipFile:
        raise ValidationError({"file_format": "not a ZIP file"})

    except MultiValueDictKeyError:
        raise ValidationError({"file_content": "bad data in ZIP file"})


@api_view(["POST"])
@parser_classes((MultiPartParser,))
def upload_zip(request, course_pk):
    # logger.debug("course pk %s", course_pk)
    subdomain, db = get_subdomain_and_db(request)

    # Support chunked uploads (same metadata as frontend: FormData fields)
    upload_id = request.POST.get("uploadId")
    chunk_index = request.POST.get("chunkIndex")
    total_chunks = request.POST.get("totalChunks")
    header_filename = request.POST.get("fileName")

    if upload_id and (chunk_index is not None) and total_chunks:
        try:
            chunk_index = int(chunk_index)
            total_chunks = int(total_chunks)
        except Exception:
            return JsonResponse({"error": "invalid chunk metadata"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            import tempfile
            # Ensure a temp directory exists under the volume (consistent with taskresults)
            tempfile.tempdir = f"{settings.VOLUME}/workqueue/taskresults"
            os.makedirs(tempfile.tempdir, exist_ok=True)
            upload_dir = os.path.join(tempfile.tempdir, "chunked-uploads")
            os.makedirs(upload_dir, exist_ok=True)

            part_path = os.path.join(upload_dir, f"{subdomain}-{upload_id}.part")

            # Append this chunk to the part file
            with open(part_path, "ab") as destination:
                fileobj = request.FILES.get("file")
                if not fileobj:
                    return JsonResponse({"file_content": "missing file"}, status=status.HTTP_400_BAD_REQUEST)
                for chunk in fileobj.chunks():
                    destination.write(chunk)

            # If not last chunk, acknowledge and return
            if chunk_index < total_chunks - 1:
                return JsonResponse({"received": chunk_index}, status=202)

            # Last chunk received: finalize and process
            final_name = header_filename or os.path.basename(request.FILES["file"].name)
            # Preserve the original name; ensure it stays intact (contains e.g. exercises-export)
            safe_final_name = os.path.basename(final_name)
            final_path = os.path.join(upload_dir, f"{upload_id}-{safe_final_name}")
            try:
                os.replace(part_path, final_path)
            except Exception:
                os.rename(part_path, final_path)

            # Proceed as in non-chunked path based on filename
            try:
                dbcourse = Course.objects.using(db).get(pk=course_pk)
            except Course.DoesNotExist:
                return JsonResponse({"course": "not found"}, status=status.HTTP_404_NOT_FOUND)

            if not request.user.has_perm("exercises.edit_exercise"):
                raise PermissionDenied(detail={"exercise": "cannot edit"})

            # exercises export import path
            if 'exercises-export' in safe_final_name and safe_final_name.split('.')[-1] in ['zip']:
                try:
                    res = import_course_exercises(dbcourse, final_path)
                    messages = map(lambda msg: UploadResult(status=msg[0], message=msg[1]), res)
                    serializer = UploadResultSerializer(instance=messages, many=True)
                    return Response(serializer.data)
                except BadZipFile:
                    raise ValidationError({"file_format": "not a ZIP file"})
                except MultiValueDictKeyError:
                    raise ValidationError({"file_content": "bad data in ZIP file"})

            # course pages/content zip import path
            try:
                # Reuse same checks as non-chunked path
                if not settings.RUNTESTS:
                    filename = safe_final_name
                else:
                    filename = ''
                destination = dbcourse.get_base_path()
                target =  os.path.join( destination, filename.split(".")[0] ) 
                newdir =  filename.split(".")[0] 
                if os.path.exists( os.path.join( destination, target) ) :
                    return JsonResponse({"error": f"{newdir} already exists; delete or move it first "}, status=status.HTTP_400_BAD_REQUEST)

                res = import_course_zip(dbcourse, final_path, destination)
                messages = map(lambda msg: UploadResult(status=msg[0], message=msg[1]), res)
                serializer = UploadResultSerializer(instance=messages, many=True)
                msg = list(res)
                for progress in Exercise.objects.sync_with_disc(dbcourse, i_am_sure=True):
                    msg = msg + progress
                return Response(serializer.data)
            except BadZipFile:
                raise ValidationError({"file_format": "not a ZIP file"})
            except MultiValueDictKeyError:
                raise ValidationError(detail={"file_content": "bad data in ZIP file"})

        except Exception as e:
            logger.error(f"Chunked upload failed: {type(e).__name__} {str(e)}")
            return JsonResponse({"error": "chunked upload failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Existing non-chunked behavior
    try :
        filename =  request.FILES["file"].name;
    except  Exception as e :
        filename = 'dummy';
    if 'exercises-export' in filename  and filename.split('.')[-1] in  ['zip']  :
        try:
            file_size_limit = settings.EXERCISES_IMPORT_FILE_SIZE_LIMIT
            if request.FILES["file"].size > settings.EXERCISES_IMPORT_FILE_SIZE_LIMIT:
                logger.error(f" FILE SIZE LIMIT EXCEEEDED {request.FILES['file'].size} > {file_size_limit}")
                return JsonResponse(
                    {"file_size_limit": f"exceeds {settings.EXERCISES_IMPORT_FILE_SIZE_LIMIT}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            dbcourse = Course.objects.using(db).get(pk=course_pk)
            if not request.user.has_perm("exercises.edit_exercise"):
                raise PermissionDenied(detail={"exercise": "cannot edit"})

            tmp_path = request.FILES["file"].temporary_file_path()
            res = import_course_exercises(dbcourse, tmp_path)

            messages = map(lambda msg: UploadResult(status=msg[0], message=msg[1]), res)
            serializer = UploadResultSerializer(instance=messages, many=True)
            return Response(serializer.data)

        except Course.DoesNotExist:
            raise NotFound(detail={"course": "not found"})

        except BadZipFile:
            raise ValidationError({"file_format": "not a ZIP file"})

        except MultiValueDictKeyError:
            raise ValidationError({"file_content": "bad data in ZIP file"})

    try:
        if not settings.RUNTESTS :
            filename = request.FILES['file'].name
        else :
            filename = ''
        if request.FILES["file"].size > 100e6:
            return JsonResponse({"file_size_limit": "exceeds 100mb"}, status=status.HTTP_400_BAD_REQUEST)
        dbcourse = Course.objects.using(db).get(pk=course_pk)
        destination = dbcourse.get_base_path()
        target =  os.path.join( destination, filename.split(".")[0] ) 
        newdir =  filename.split(".")[0] 
        if os.path.exists( os.path.join( destination, target) ) :
            return JsonResponse({"error": f"{newdir} already exists; delete or move it first "}, status=status.HTTP_400_BAD_REQUEST)
        # logger.debug("DESTIONATION = %s " % destination)
        if not request.user.has_perm("exercises.edit_exercise"):
            raise PermissionDenied(detail={"exercise": "cannot edit"})

        res = import_course_zip(dbcourse, request.FILES["file"].temporary_file_path(), destination)

        messages = map(lambda msg: UploadResult(status=msg[0], message=msg[1]), res)
        serializer = UploadResultSerializer(instance=messages, many=True)
        msg = res
        for progress in Exercise.objects.sync_with_disc(dbcourse, i_am_sure=True):
            msg = msg + progress
        return Response(serializer.data)

    except Course.DoesNotExist:
        raise NotFound({"course": "not found"})

    except BadZipFile:
        raise ValidationError({"file_format": "not a ZIP file"})

    except MultiValueDictKeyError:
        raise ValidationError(detail={"file_content": "bad data in ZIP file"})


def upload_zip_core(course_pk, filename , subdomain  ):
    logger.error("UPLOAD_ZIP_CORE")
    db = subdomain
    dbcourse = Course.objects.using(db).get(pk=course_pk)
    logger.error(f"UPLOAD_ZIP_CORE {dbcourse}")
    destination = dbcourse.get_base_path()
    logger.error(f"FILENAME = {filename} DESTINATION={destination}")
    res = import_course_zip(dbcourse,  filename, destination)
    messages = res;
    msg = res
    for progress in Exercise.objects.sync_with_disc(dbcourse, i_am_sure=True, db=subdomain):
        msg = msg + progress
    logger.error(f"DONE WITH SYNC WITH_DISC {msg}")
    return Response(msg)
