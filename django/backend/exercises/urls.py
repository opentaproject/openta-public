from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import url
from exercises import views

urlpatterns = [
    url(r'^course/(?P<course_pk>[0-9]+)/exercises/$', views.exercise_list),
    url(r'^course/(?P<course_pk>[0-9]+)/exercises/reload/$', views.exercises_reload),
    url(r'^course/(?P<course_pk>[0-9]+)/exercises/reload/json/$', views.exercises_reload_json),
    url(r'^course/(?P<course_pk>[0-9]+)/exercises/tree/$', views.exercise_tree),
    url(r'^exercises/test/$', views.exercises_test),
    url(r'^exercises/add/$', views.exercises_add),
    url(r'^exercises/movefolder/$', views.exercises_move_folder),
    url(r'^exercises/renamefolder/$', views.exercises_rename_folder),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/delete$', views.exercise_delete),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/move$', views.exercise_move),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/samefolder$', views.other_exercises_from_folder),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/json$', views.exercise_json),
    url(r'^exercise/(?P<exercise>[\w\.-]+)$', views.exercise),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/test$', views.exercise_test_view),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/xml$', views.exercise_xml),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/history$', views.exercise_history),
    url(
        r'^exercise/(?P<exercise>[\w\.-]+)/history/(?P<name>[\w\.\ :]+)/xml$',
        views.exercise_xml_history,
    ),
    url(
        r'^exercise/(?P<exercise>[\w\.-]+)/history/(?P<name>[\w\.\ :]+)/json$',
        views.exercise_json_history,
    ),
    url(
        r'^exercise/(?P<exercise>[\w\.-]+)/asset/(?P<asset>[\w\.\-\ \(\)]+)$', views.exercise_asset
    ),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/download_assets$', views.exercise_download_assets),
    url(
        r'^exercise/(?P<exercise>[\w\.-]+)/studentasset/(?P<asset>[\w\.\-\ \(\)]+)$',
        views.exercise_student_asset,
    ),
    url(
        r'^exercise/(?P<exercise>[\w\.-]+)/asset/(?P<asset>[\w\.\-\ \(\)]+)/delete$',
        views.exercise_asset_delete,
    ),
    url(
        r'^exercise/(?P<exercise>[\w\.-]+)/question/(?P<question>[\w\.\-]+)/check$',
        views.exercise_check,
    ),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/save$', views.exercise_save),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/imageupload$', views.upload_answer_image),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/listassets$', views.exercise_list_assets),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/uploadasset$', views.exercise_upload_asset),
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
    url(
        r'^course/(?P<course_pk>[0-9]+)/statistics/statsperexercise',
        views.get_statistics_per_exercise,
    ),
    url(r'^course/(?P<course_pk>[0-9]+)/statistics/resultsasync/$', views.get_results_async),
    url(
        r'^course/(?P<course_pk>[0-9]+)/statistics/customresult$', views.enqueue_custom_result_excel
    ),
    url(r'^statistics/customresult/(?P<task>[0-9]+)$', views.progress_custom_result_excel),
    url(r'^course/(?P<course_pk>[0-9]+)/statistics/results/excel$', views.get_results_excel),
    url(r'^statistics/exercise/(?P<exercise>[\w\.-]+)/activity', views.get_activity_exercise),
    url(r'^audit/unsent/$', views.get_current_unsent_audits),
    url(
        r'^audit/new/exercise/(?P<heap>[\w]+)/(?P<exercise>[\w\.-]+)/(?P<n_audits>[0-9]+)$',
        views.get_new_audit,
    ),
    url(r'^audit/get/exercise/(?P<exercise>[\w\.-]+)$', views.get_current_audits_exercise),
    url(r'^audit/stats/exercise/(?P<exercise>[\w\.-]+)$', views.get_current_audits_stats),
    url(r'^audit/update/(?P<pk>[0-9]+)/$', views.update_audit),
    url(r'^audit/update_student/(?P<pk>[0-9]+)/$', views.student_audit_update),
    url(r'^audit/send/(?P<pk>[0-9]+)/$', views.send_audit),
    url(r'^audit/delete/(?P<pk>[0-9]+)/$', views.delete_audit),
    url(r'^audit/add/$', views.add_audit),
    url(r'^auditresponsefile/new/(?P<pk>[0-9]+)/$', views.upload_audit_response_file),
    url(r'^auditresponsefile/view/(?P<pk>[0-9]+)/$', views.audit_response_file_view),
    url(r'^auditresponsefile/view/(?P<pk>[0-9]+)/thumb$', views.audit_response_file_thumb_view),
    url(r'^auditresponsefile/delete/(?P<pk>[0-9]+)/$', views.delete_audit_response_file),
    url(
        r'^course/(?P<course_pk>[0-9]+)/results/user/(?P<user_pk>[0-9]+)/$', views.get_user_results
    ),
    url(r'^exercise/(?P<exercise>[\w\.-]+)/recentresults', views.get_recent_results),
]

urlpatterns += staticfiles_urlpatterns()
