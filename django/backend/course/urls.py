from django.conf.urls import url, include
from course.views import get_course
from course.views import get_courses
from course.views import CourseUpdateView
from course.views import upload_exercises
from course.views.export import export_course_exercises_async
from course.views.export import export_course_async
from course.views.export import import_server_view
from course.views import course_duplicate_async

urlpatterns = [
    url(r'^course/(?P<course_pk>[0-9]+)/$', get_course),
    url(r'^courses/', get_courses),
    url(r'^course/(?P<course_pk>[\w\.-]+)/updateoptions/$', CourseUpdateView),
    url(r'^course/(?P<course_pk>[\w\.-]+)/uploadexercises/$', upload_exercises),
    url(r'^course/(?P<course_pk>[0-9]+)/exportexercisesasync/$', export_course_exercises_async),
    url(r'^course/(?P<course_pk>[0-9]+)/export/$', export_course_async),
    url(r'^course/(?P<course_pk>[0-9]+)/duplicate/$', course_duplicate_async),
    url(r'^server/import/$', import_server_view),
]
