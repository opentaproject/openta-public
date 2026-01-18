# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# from django.conf.urls import url
from django.urls import re_path as url

# django.conf.urls.url() is deprecated in favor of django.urls.re_path()
from exercises import views

urlpatterns = [
    # path('exercise/', include('exercises.regrade.urls') ),
    url(r"^course/(?P<course_pk>[0-9]+)/exercises/$", views.exercise_list),
    url(r"^course/(?P<course_pk>[0-9]+)/exercises/(?P<user_pk>[0-9]+)/$", views.user_exercise_list),
    url(r"^course/(?P<course_pk>[0-9]+)/exercises/reload/$", views.exercises_reload),
    url(r"^course/(?P<course_pk>[0-9]+)/exercises/reload/json/$", views.exercises_reload_json),
    url(r"^course/(?P<course_pk>[0-9]+)/exercises/validate/$", views.exercises_validate),
    url(r"^course/(?P<course_pk>[0-9]+)/exercises/validate/json/$", views.exercises_validate_json),
    url(r"^course/(?P<course_pk>[0-9]+)/exercises/tree/$", views.exercise_tree),
    url(r"^course/(?P<course_pk>[0-9]+)/exercises/tree/(?P<fstring>[0-9]+)/$", views.exercise_tree),
    url(r"^exercises/test/$", views.exercises_test),
    url(r"^exercises/add/$", views.exercises_add),
    url(r"^folder/add/$", views.exercises_move_folder),
    url(r"^folder/rename/$", views.exercises_move_folder),
    url(r"^folder/move/$", views.exercises_move_folder),
    # url(r'^folder/(?P<folderPath>[\w\.-]+)/delete$', views.folder_delete),
    url(r"^exercises/movefolder/$", views.exercises_move_folder),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/delete$", views.exercise_delete),
    # url(r'^exercise/(?P<exercise>[\w\.-]+)/move$', views.exercise_move),
    url(r"^webwork_save_result/(?P<identifier>.*)$", views.webwork_save_result),
    url(r"^webwork_forward/.*$", views.webwork_forward),
    url(r"^(?P<course_pk>[0-9]+)/lti/webwork_forward/.*$", views.webwork_forward),
    url(r"^lti/webwork_forward/.*$", views.webwork_forward),
    url(r"^exercise/move$", views.exercise_move),
    url(r"^exercise/handle$", views.exercise_handle),
    url(r"^folder/handle$", views.folder_handle),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/samefolder/(?P<subdomain>[\w\.-]+)/$", views.other_exercises_from_folder),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/json$", views.exercise_json),
    url(r"^exercise/(?P<exercise>[\w\.-]+)$", views.exercise),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/$", views.exercise),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/test$", views.exercise_test_view),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/xml$", views.exercise_xml),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/history$", views.exercise_history),
    url(
        r"^exercise/(?P<exercise>[\w\.-]+)/history/(?P<name>[\w\.\ :]+)/xml$",
        views.exercise_xml_history,
    ),
    url(
        r"^exercise/(?P<exercise>[\w\.-]+)/history/(?P<name>[\w\.\ :]+)/json$",
        views.exercise_json_history,
    ),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/asset/(?P<asset>[\w\.\-\ \(\)]*)$", views.exercise_asset),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/clean_assets/$", views.exercise_clean_assets),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/download_assets$", views.exercise_download_assets),
    url(
        r"^exercise/(?P<exercise>[\w\.-]+)/studentasset/(?P<asset>[\w\.\-\ \(\)]+)$",
        views.exercise_student_asset,
    ),
    url( r"^(?P<course_pk>[0-9]+)/lti/exercise/(?P<exercise>[\w\.-]+)/studentasset/(?P<asset>[\w\.\-\ \(\)]+)$", 
        views.exercise_student_asset,
    ),
    url(
        r"^exercise/(?P<exercise>[\w\.-]+)/asset/(?P<asset>[\w\.\-\ \(\)]+)/delete$",
        views.exercise_asset_delete,
    ),
    url(
        r"^exercise/(?P<exercise>[\w\.-]+)/asset/(?P<asset>[\w\.\-\ \(\)]+)/run$",
        views.exercise_assets_handle,
    ),
    url(
        r"^exercise/(?P<exercise>[\w\.-]+)/asset/(?P<asset>[\w\.\-\ \(\)]+)/handle$",
        views.exercise_assets_handle,
    ),
    url(
        r"^exercise/(?P<exercise>[\w\.-]+)/question/(?P<question>[\w\.\-]+)/check$",
        views.exercise_check,
    ),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/save$", views.exercise_save),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/imageupload$", views.upload_answer_image),
    url(
        r"^exercise/(?P<exercise>[\w\.-]+)/imageupload/(?P<action>[a-z]+)/imageanswer/(?P<asset>[0-9]+)$",
        views.reupload_answer_image,
    ),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/(.*)/htdocs/(.*)$", views.webwork_htdocs),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/blobupload$", views.upload_blob),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/listassets$", views.exercise_list_assets),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/uploadasset$", views.exercise_upload_asset),
    url(r"^exercise/(?P<instruction>[\w\.-]+)/selected_exercises$", views.exercise_set_selected_exercises),
    url(r"^imageanswer/(?P<image_id>[0-9]+)$", views.answer_image_view),
    url(r"^imageanswer/(?P<pk>[0-9]+)/delete$", views.image_answer_delete),
    url(r"^imageanswerthumb/(?P<image_id>[0-9]+)$", views.answer_image_thumb_view),
    url(
        r"^exercise/(?P<exercise>[\w\.-]+)/question/(?P<question>[\w]+)/latest$",
        views.question_last_answer,
    ),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/editmeta", views.ExerciseMetaUpdateView),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/imageanswers", views.image_answers_get),
    url(
        r"^exercisemeta/(?P<pk>[0-9]+)$",
        views.ExerciseMetaUpdate.as_view(),
        name="exercise-meta-update",
    ),
    url(
        r"^course/(?P<course_pk>[0-9]+)/statistics/statsperexercise",
        views.get_statistics_per_exercise,
    ),
    url(
        r"^course/(?P<course_pk>[0-9]+)/course_statistics/(?P<activityRange>[\w]+)/",
        views.get_course_statistics,
    ),
    url(r"^course/(?P<course_pk>[0-9]+)/statistics/resultsasync/?$", views.get_results_async),
    url(r"^course/(?P<course_pk>[0-9]+)/statistics/customresult$", views.enqueue_custom_result_excel),
    url(r"^statistics/customresult/(?P<task>[0-9]+)$", views.progress_custom_result_excel),
    url(r"^course/(?P<course_pk>[0-9]+)/statistics/results/excel$", views.get_results_excel),
    url(r"^statistics/exercise/(?P<exercise>[\w\.-]+)/activity", views.get_activity_exercise),
    url(r"^audit/unsent/$", views.get_current_unsent_audits),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/send_my_audits/$", views.send_my_audits),
    url(
        r"^audit/new/exercise/(?P<heap>[\w]+)/(?P<exercise>[\w\.-]+)/(?P<n_audits>[0-9]+)$",
        views.get_new_audit,
    ),
    url(
        r"^audit/newbyuser/exercise/(?P<username>[\w\.\@]+)/(?P<exercise>[\w\.-]+)/$",
        views.get_new_audit_by_user,
    ),
    url(r"^audit/get/exercise/(?P<exercise>[\w\.-]+)$", views.get_current_audits_exercise),
    url(r"^audit/stats/exercise/(?P<exercise>[\w\.-]+)$", views.get_current_audits_stats),
    url(r"^audit/update/(?P<pk>[0-9]+)/$", views.update_audit),
    url(r"^audit/update_student/(?P<pk>[0-9]+)/$", views.student_audit_update),
    url(r"^audit/send/(?P<pk>[0-9]+)/$", views.send_audit),
    url(r"^audit/delete/(?P<pk>[0-9]+)/$", views.delete_audit),
    url(r"^audit/add/$", views.add_audit),
    url(r"^auditresponsefile/new/(?P<pk>[0-9]+)/$", views.upload_audit_response_file),
    url(r"^auditresponsefile/view/(?P<pk>[0-9]+)/$", views.audit_response_file_view),
    url(r"^auditresponsefile/view/(?P<pk>[0-9]+)/thumb$", views.audit_response_file_thumb_view),
    url(r"^auditresponsefile/delete/(?P<pk>[0-9]+)/$", views.delete_audit_response_file),
    url(r"^course/(?P<course_pk>[0-9]+)/results/user/(?P<user_pk>[0-9]+)/*$", views.get_user_results),
    url(
        r"^course/(?P<course_pk>[0-9]+)/results/user/(?P<user_pk>[0-9]+)/(?P<exercise>[\w\.-]+)/$",
        views.get_user_exercise_results,
    ),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/recentresults", views.get_recent_results),

    url(
        r"^exercise/(?P<exercise>[\w\.-]+)/regrade_resultsasync/(?P<question_key>[\w\.-]+)",
        views.get_regrade_results_async,
    ),

    url(
        r"^exercise/(?P<exercise>[\w\.-]+)/analyze_resultsasync/(?P<question_key>[\w\.-]+)",
        views.get_analyze_results_async,
    ),
    url(r"^exercise/(?P<exercise>[\w\.-]+)/accept_regrade/(?P<yesno>[\w.]+)", views.accept_regrade),
url(r"^exercise/(?P<exercise>[\w\.-]+)/accept_analyze/(?P<yesno>[\w.]+)", views.accept_analyze),
]

urlpatterns += staticfiles_urlpatterns()
