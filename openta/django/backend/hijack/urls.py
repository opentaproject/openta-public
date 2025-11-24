# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.urls import path

from hijack import views

app_name = "hijack"
urlpatterns = [
    path("acquire/", views.AcquireUserView.as_view(), name="acquire"),
    path("release/", views.ReleaseUserView.as_view(), name="release"),
]
