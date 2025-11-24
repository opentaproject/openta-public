# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.urls import re_path as url

from . import views

app_name = "django_lti_auth"

urlpatterns = [
    url(r"^change_password/", views.change_password, name="change_password"),
    url(r"^edit_profile/", views.edit_profile, name="edit_profile"),
    url(r"^lti/config_xml/$", views.config_xml),
    url(r"^lti/$", views.lti_main),
    url(r"^lti/launch_sidecar/$", views.launch_sidecar),
    url(r"^lti/launch_sidecar", views.launch_sidecar),
    url(r"^lti/index/$", views.index),
    url(r"^lti/index/$", views.index),
    url(r"^(?P<course_pk>[0-9]+)/lti/$", views.lti_main),
    url(r"^(?P<course_pk>[0-9]+)/lti/launch_sidecar$", views.launch_sidecar),
    url(r"^(?P<course_name>[\w\.\- ]+)/lti/index/?$", views.index),
    url(r"logout/(?P<course_name>[\w\.\- ]+)/lti/index/?$", views.index),
    url(r"^(?P<course_name>[\w\.-]+)/lti/config_xml/?$", views.config_xml),
    url(
        r"^course/(?P<course_pk>[0-9]+)/lti/canvasgradebook/$",
        views.amend_canvas_gradebook,
    ),
]
