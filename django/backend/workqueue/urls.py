from django.conf.urls import url, include
from .views import get_task_result_file, get_task_result, task_progress

urlpatterns = [
    url(r'^queuetask/(?P<task>[0-9]+)/resultfile$', get_task_result_file),
    url(r'^queuetask/(?P<task>[0-9]+)/result$', get_task_result),
    url(r'^queuetask/(?P<task>[0-9]+)$', task_progress),
    url(r'^django-rq/', include('django_rq.urls')),
]
