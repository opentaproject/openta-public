from django.contrib import admin

from .models import QueueTask


class QueueTaskAdmin(admin.ModelAdmin):
    list_display = ['pk', 'date', 'name', 'progress', 'status', 'result_text', 'result_file']
    list_per_page = 20
    search_fields = ['name', 'status', 'result_text']
    ordering = ['-date']
    readonly_fields = ('id',)


admin.site.register(QueueTask, QueueTaskAdmin)
