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
