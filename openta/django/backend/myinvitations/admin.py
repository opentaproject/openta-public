# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.contrib import admin
from django import forms
from course.models import Course
from django.contrib import messages
from .forms import InvitationAdminAddManyForm
from django.http import Http404, HttpResponse
from django.core.exceptions import ValidationError

from invitations.utils import (
    get_invitation_admin_add_form,
    get_invitation_admin_change_form,
    get_invitation_model,
)

from myinvitations.forms import InvitationAdminAddForm, InvitationAdminAddManyForm


Invitation = get_invitation_model()
# InvitationAdminAddForm = get_invitation_admin_add_form()
InvitationAdminChangeForm = get_invitation_admin_change_form()
import logging

logger = logging.getLogger(__name__)


class InvitationAdmin(admin.ModelAdmin):

    list_display = ("email", "sent", "accepted", "key", "role")

    def role(self, obj):
        CHOICES = {"1": "Student", "2": "View", "3": "Author", "4": "Admin"}
        if obj.key:
            return CHOICES.get(obj.key[0], "none")
        return ""

    def add_view(self, request, form_url="", extra_context=None):
        # print(f"CUSTOM ADD_VIEW")
        form = self.get_form(request)
        iss = Invitation.objects.all()
        for i in iss:
            print(f" {i.email}")
            if not i.email:
                i.delete()
        print(f"FORM = {form}")
        meta = form.Meta
        form.Meta.fields = [
            "email",
        ]
        extra_context = extra_context or {}
        extra_context["form"] = form
        print(f" SELF = {self}")
        if False:
            extra_context["show_save"] = False
            extra_context["show_save_and_continue"] = False
            extra_context["show_save_and_add_another"] = False
        try:
            return super(InvitationAdmin, self).add_view(request, form_url=form_url, extra_context=extra_context)
        except Exception as e:
            return HttpResponse(f"{form} {vars(form)} ")

    def get_form(self, request, obj=None, **kwargs):
        logger.error(f"CUSTOM GET_FORM")
        if obj:
            kwargs["form"] = InvitationAdminChangeForm
        else:
            logger.debug(f"CUSTOM  ADMIN_ADD_FORM ")
            form = InvitationAdminAddManyForm
            kwargs["form"] = form
            kwargs["form"].user = request.user
            kwargs["form"].request = request
        # print(f"INVITATION ADMIN SUPER CALLED")
        form = super().get_form(request, obj, **kwargs)
        # form.base_fields['key'].widget = forms.fields.HiddenInput()
        return super(InvitationAdmin, self).get_form(request, obj, **kwargs)


admin.site.unregister(Invitation)
admin.site.register(Invitation, InvitationAdmin)
