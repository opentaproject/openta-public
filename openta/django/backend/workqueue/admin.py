# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.contrib import admin
from django.conf import settings

from .models import QueueTask, RegradeTask


class QueueTaskAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(QueueTaskAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(subdomain=settings.SUBDOMAIN)
        else:
            return qs

    list_display = ["pk", "subdomain", "date", "name", "progress", "status", "result_file"]
    list_per_page = 20
    search_fields = ["name", "status", "result_text"]
    ordering = ["-date"]
    readonly_fields = ("id",)


class RegradeTaskAdmin(admin.ModelAdmin):
    list_display = ["pk", "task_id", "subdomain", "status", "exercise_key", "resultsfile"]
    list_per_page = 20
    readonly_fields = ("pk",)


admin.site.register(QueueTask, QueueTaskAdmin)
admin.site.register(RegradeTask, RegradeTaskAdmin)
