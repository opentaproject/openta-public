# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.contrib import admin
from users.models import OpenTAUser
from import_export.admin import ExportActionMixin


class OpenTAUserAdmin(ExportActionMixin, admin.ModelAdmin):

    pass

    def get_list_display(self,request):
        return ['id','lti_user_id','user','email','lti_roles']
    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            del actions["export_admin_action"]
        return actions


admin.site.register(OpenTAUser, OpenTAUserAdmin)
