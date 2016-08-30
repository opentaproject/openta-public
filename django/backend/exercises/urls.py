from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import url
from exercises import views

urlpatterns = [
    url(r'^exercises/$', views.exercise_list),
    url(r'^exercises/reload/$', views.exercises_reload),
    url(r'^exercises/tree/$', views.exercise_tree),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/samefolder$', views.other_exercises_from_folder),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/json$', views.exercise_json),
    url(r'^exercise/(?P<exercise>[\w\.-]+)$', views.exercise),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/xml$', views.exercise_xml),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/asset/(?P<asset>[\w\.]+)$', views.exercise_asset),
    url(
        r'^exercise/(?P<exercise>[\w\.-]+)/question/(?P<question>[\w]+)/check$',
        views.exercise_check,
    ),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/save$', views.exercise_save),
    url(
        r'^exercise/(?P<exercise>[\w\.-]+)/question/(?P<question>[\w]+)/latest$',
        views.question_last_answer,
    ),
]

urlpatterns += staticfiles_urlpatterns()
