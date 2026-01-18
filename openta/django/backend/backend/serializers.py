# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from rest_framework_dataclasses.serializers import DataclassSerializer
from dataclasses import dataclass


@dataclass
class UploadResult:
    status: str
    message: str


class UploadResultSerializer(DataclassSerializer[UploadResult]):
    """Used when replying to a zip file upload"""

    class Meta:
        dataclass = UploadResult
