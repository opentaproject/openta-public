from django.contrib import admin

from .models import QueueTask,RegradeTask


class QueueTaskAdmin(admin.ModelAdmin):
    list_display = ['pk', 'date', 'name', 'progress', 'status', 'result_file']
    list_per_page = 20
    search_fields = ['name', 'status', 'result_text']
    ordering = ['-date']
    readonly_fields = ('id',)


class RegradeTaskAdmin(admin.ModelAdmin):
    list_display = ['pk','task_id', 'exercise','resultsfile','status']
    list_per_page = 20
    readonly_fields = ('pk',)


admin.site.register(QueueTask, QueueTaskAdmin)
admin.site.register(RegradeTask,RegradeTaskAdmin)

