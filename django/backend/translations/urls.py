from django.conf.urls import url, include
from translations import views

urlpatterns = [
    url(
        r'^course/(?P<course_pk>[0-9]+)/notifymissingstring/(?P<language>[\w\.-]+)$',
        views.notifymissingstring,
    ),
    url(r'^course/(?P<course_pk>[0-9]+)/translationdict/$', views.translationdict),
    url(r'^course/(?P<course_pk>[0-9]+)/updatetranslationdict/$', views.updatetranslationdict),
    url(
        r'^exercise/(?P<exercise>[\w\.-]+)/changedefaultlanguage/(?P<language>[\w\.-]+)$',
        views.exercise_translate,
    ),
    url(
        r'^exercise/(?P<exercise>[\w\.-]+)/remove/(?P<language>[\w\.-]+)$', views.exercise_translate
    ),
    url(
        r'^exercise/(?P<exercise>[\w\.-]+)/views/(?P<language>[\w\.-]+)$', views.exercise_translate
    ),
    url(
        r'^exercise/(?P<exercise>[\w\.-]+)/translate/(?P<language>[\w\.-]+)$',
        views.exercise_translate,
    ),
]
