from django.conf.urls import url, include
from course.views import get_course
from course.views import get_courses
from course.views import CourseUpdateView

urlpatterns = [
    url(r'^course/(?P<course_pk>[0-9]+)/$', get_course),
    url(r'^courses/', get_courses),
    url(r'^course/(?P<course>[\w\.-]+)/updateoptions/$', CourseUpdateView),
]
