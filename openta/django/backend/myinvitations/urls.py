# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.urls import re_path as url


from . import views

app_name = "invitations"
urlpatterns = [
    url(r"^send-invite/$", views.SendInvite.as_view(), name="send-invite"),
    url(r"^send-json-invite/$", views.SendJSONInvite.as_view(), name="send-json-invite"),
    url(r"^send-many-invites/$", views.SendManyInvites.as_view(), name="send-many-invites"),
    url(r"^send-many-form/$", views.SendManyInvitesPage.as_view(), name="send-many-form"),
    url(r"^accept-invite/(?P<key>\w+)/?$", views.AcceptInvite.as_view(), name="accept-invite"),
]
