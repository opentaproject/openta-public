# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.conf.urls import include
from django.urls import re_path as url
from course.views import get_course, get_pages
from course.views import get_courses
from course.views import CourseUpdateView
from course.views import upload_exercises, upload_zip
from course.views.export import export_course_exercises_async
from course.views.export import export_course_async
from course.views.export import import_server_view
from course.views import course_duplicate_async

urlpatterns = [
    url(r"^course/(?P<course_pk>[0-9]+)/$", get_course),
    url(r"^course/(?P<course_pk>[0-9]+)/pages/(?P<path>.+)", get_pages),
    url(r"^courses/", get_courses),
    url(r"^course/(?P<course_pk>[\w\.-]+)/updateoptions/$", CourseUpdateView),
    url(r"^course/(?P<course_pk>[\w\.-]+)/uploadexercises/$", upload_zip),
    url(r"^course/(?P<course_pk>[\w\.-]+)/uploadzip/$", upload_zip),
    url(r"^course/(?P<course_pk>[0-9]+)/exportexercisesasync/$", export_course_exercises_async),
    url(r"^course/(?P<course_pk>[0-9]+)/export/$", export_course_async),
    url(r"^course/(?P<course_pk>[0-9]+)/duplicate/$", course_duplicate_async),
    url(r"^server/import/$", import_server_view),
]
