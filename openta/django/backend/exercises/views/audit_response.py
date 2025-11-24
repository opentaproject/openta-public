# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
import os

from exercises.models import AuditExercise, AuditResponseFile
from PIL import Image
from pypdf import PdfReader
from utils import get_subdomain_and_db
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from django.core.exceptions import ObjectDoesNotExist

from .api import serve_file

logger = logging.getLogger(__name__)


@api_view(["POST"])
@parser_classes((MultiPartParser,))
def upload_audit_response_file(request, pk):
    subdomain, db = get_subdomain_and_db( request)
    dbaudit = AuditExercise.objects.using(db).get(pk=pk)
    if request.FILES["file"].size > 10e6:
        return Response("Image larger than 10mb", status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        trial_image = Image.open(request.FILES["file"])
        trial_image.verify()
        image_answer = AuditResponseFile(
            auditor=request.user,
            audit=dbaudit,
            image=request.FILES["file"],
            filetype=AuditResponseFile.IMAGE,
        )
        image_answer.save()
        return Response({})
    except Exception as e:
        try:
            reader = PdfReader(request.FILES["file"], strict=True)
            pdf_answer = AuditResponseFile(
                auditor=request.user,
                audit=dbaudit,
                pdf=request.FILES["file"],
                filetype=AuditResponseFile.PDF,
            )
            pdf_answer.save()
            return Response({})

        except Exception as e:
            return Response("Invalid audit response file", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def audit_response_file_view(request, pk):
    subdomain_and_db = get_subdomain_and_db( request)
    try:
        audit_response = AuditResponseFile.objects.using(db).get(pk=pk)
        if (
            audit_response.audit.student == request.user
            or audit_response.auditor == request.user
            or request.user.is_staff
        ):
            if audit_response.filetype == "IMG":
                return serve_file(
                    "/" + audit_response.image.name,
                    os.path.basename(audit_response.image.name),
                    content_type="image/jpeg",
                    dev_path=audit_response.image.path,
                    source="audit_response",
                )
            if audit_response.filetype == "PDF":
                return serve_file(
                    "/" + audit_response.pdf.name,
                    os.path.basename(audit_response.pdf.name),
                    content_type="application/pdf",
                    dev_path=audit_response.pdf.path,
                    source="audit_response",
                )
        else:
            return Response("Not authorized", status.HTTP_500_INTERNAL_SERVER_ERROR)
    except ObjectDoesNotExist:
        return Response("Invalid audit response file id", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def audit_response_file_thumb_view(request, pk):
    subdomain_and_db = get_subdomain_and_db( request)
    try:
        audit_response = AuditResponseFile.objects.using(db).get(pk=pk)
        if (
            audit_response.audit.student == request.user
            or audit_response.auditor == request.user
            or request.user.is_staff
        ):
            return serve_file(
                "/" + audit_response.image_thumb.url,
                os.path.basename(audit_response.image.name),
                content_type="image/jpeg",
                dev_path= audit_response.image_thumb.url,
                source="audit_response",
            )
        else:
            return Response("Not authorized", status.HTTP_500_INTERNAL_SERVER_ERROR)
    except ObjectDoesNotExist:
        return Response("invalid answer image id", status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def delete_audit_response_file(request, pk):
    subdomain_and_db = get_subdomain_and_db( request)
    try:
        audit_response = AuditResponseFile.objects.using(db).get(pk=pk)
    except ObjectDoesNotExist:
        return Response({"deleted": 0, "error": "Id not found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if not request.user == audit_response.auditor and not request.user.is_staff:
        return Response({"deleted": 0, "error": "Permission denied"})
    deleted, deltype = audit_response.delete()
    return Response({"deleted": deleted})
