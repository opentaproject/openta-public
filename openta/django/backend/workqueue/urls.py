# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.conf.urls import include
from django.urls import re_path as url
from .views import get_task_result_file, get_task_result, task_progress

urlpatterns = [
    url(r"^queuetask/(?P<task>[0-9]+)/resultfile$", get_task_result_file),
    url(r"^queuetask/(?P<task>[0-9]+)/result$", get_task_result),
    url(r"^queuetask/(?P<task>[0-9]+)$", task_progress),
    url(r"^django-rq/", include("django_rq.urls")),
]
