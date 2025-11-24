from django.urls import re_path as url


from translations import views

urlpatterns = [
    url( r"^edit/$", views.edit_translation, name="edit_translation",),
    url( r"^course/(?P<course_pk>[0-9]+)/translation/edit$",  views.edit_translation, name="edit_translation",),
    url( r"^course/(?P<course_pk>[0-9]+)/notifymissingstring/(?P<language>[\w\.-]+)$", views.notifymissingstring,),
    url( r"^course/(?P<course_pk>[0-9]+)/translationdict/(?P<language>[\w\.-]*)$", views.translationdict,),
    url( r"^exercise/(?P<exercise>[\w\.-]+)/changedefaultlanguage/(?P<language>[\w\.-]+)$", views.exercise_translate,),
    url( r"^exercise/(?P<exercise>[\w\.-]+)/remove/(?P<language>[\w\.-]+)$", views.exercise_translate,),
    url( r"^exercise/(?P<exercise>[\w\.-]+)/views/(?P<language>[\w\.-]+)$", views.exercise_translate,),
    url( r"^exercise/(?P<exercise>[\w\.-]+)/translate/(?P<language>[\w\.-]+)$", views.exercise_translate,),
]
