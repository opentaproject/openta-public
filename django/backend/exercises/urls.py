from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import url
from exercises import views

urlpatterns = [
    url(r'^exercises/$', views.exercise_list),
    url(r'^exercise/(?P<exercise>[\w\.]+)$', views.exercise_json),
    url(r'^exercise/(?P<exercise>[\w\.]+)/xml$', views.exercise_xml),
    url(r'^exercise/(?P<exercise>[\w\.]+)/asset/(?P<asset>[\w\.]+)$', views.exercise_asset),
    url(
        r'^exercise/(?P<exercise>[\w\.]+)/question/(?P<question>[0-9]+)/check$',
        views.exercise_check,
    ),
    url(r'^exercise/(?P<exercise>[\w\.]+)/save$', views.exercise_save),
]

urlpatterns += staticfiles_urlpatterns()
