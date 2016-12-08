from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import url
from exercises import views

urlpatterns = [
    url(r'^exercises/$', views.exercise_list),
    url(r'^exercises/reload/$', views.exercises_reload),
    url(r'^exercises/reload/json$', views.exercises_reload_json),
    url(r'^exercises/tree/$', views.exercise_tree),
    url(r'^exercises/test/$', views.exercises_test),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/samefolder$', views.other_exercises_from_folder),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/json$', views.exercise_json),
    url(r'^exercise/(?P<exercise>[\w\.-]+)$', views.exercise),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/test$', views.exercise_test_view),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/xml$', views.exercise_xml),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/asset/(?P<asset>[\w\.]+)$', views.exercise_asset),
    url(
        r'^exercise/(?P<exercise>[\w\.-]+)/question/(?P<question>[\w]+)/check$',
        views.exercise_check,
    ),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/save$', views.exercise_save),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/imageupload$', views.upload_answer_image),
    url(r'^imageanswer/(?P<image_id>[0-9]+)$', views.answer_image_view),
    url(r'^imageanswer/(?P<pk>[0-9]+)/delete$', views.image_answer_delete),
    url(r'^imageanswerthumb/(?P<image_id>[0-9]+)$', views.answer_image_thumb_view),
    url(
        r'^exercise/(?P<exercise>[\w\.-]+)/question/(?P<question>[\w]+)/latest$',
        views.question_last_answer,
    ),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/editmeta', views.ExerciseMetaUpdateView),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/imageanswers', views.image_answers_get),
    url(
        r'^exercisemeta/(?P<pk>[0-9]+)$',
        views.ExerciseMetaUpdate.as_view(),
        name='exercise-meta-update',
    ),
    url(r'^statistics/allstudentattempts', views.get_student_attempts_per_exercise),
    url(r'^statistics/statsperexercise', views.get_statistics_per_exercise),
    url(r'^statistics/results', views.get_results),
    url(r'^statistics/exercise/(?P<exercise>[\w\.-]+)/activity', views.get_activity_exercise),
]

urlpatterns += staticfiles_urlpatterns()
