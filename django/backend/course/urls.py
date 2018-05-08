from django.conf.urls import url, include
from .views import get_current_course
from .views import get_courses
from .views import CourseUpdateView

urlpatterns = [
    url(r'^course/$', get_current_course),
    url(r'^courses/', get_courses),
    url(r'^course/(?P<course>[\w\.-]+)/updateoptions/$', CourseUpdateView),
]
