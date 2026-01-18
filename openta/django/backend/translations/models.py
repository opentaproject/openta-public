# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import hashlib
import logging
import threading
from django import forms
from django.conf import settings

from django.contrib import admin
from django.core.cache import caches
from django.db import models
from exercises.models import Exercise
from course.models import Course

logger = logging.getLogger(__name__)


# Create your models here.
def t_hshkey(txt):
    txt = " ".join(txt.split())
    return (hashlib.md5(txt.encode()).hexdigest())[0:7]


def t_cache_and_key(course, exercise):
    txt = "%s%s" % (course.course_key, exercise.exercise_key)
    cache = caches["translations"]
    cachekey = (hashlib.md5(txt.encode()).hexdigest())[0:7]
    return (cache, cachekey)


#
# def handle_exercise_saved(sender, **kwargs):
#    logger.info("HANDLE EXERCISE_SAVED IN TRANSLATIONS")
#    exercise = kwargs['exercise']
#    course = kwargs['course']
#    course_pk = course.pk
#    if course.use_auto_translation:
#        langs = exercise.course.get_languages()
#        (cache,cachekey) = cache_and_key( course,exercise)
#        if not cache.has_key( cachekey ):
#            xml = exercise_xml(exercise.get_full_path())
#            TranslationThread( xml,langs,course,exercise ).start()


# FIXME: move this class to another module?

# https://stackoverflow.com/questions/11899088/is-django-post-save-signal-asynchronous/11904222#11904222
class TranslationThread(threading.Thread):
    def __init__(self, xml, langs, course, exercise, **kwargs):
        self.xml = xml
        self.langs = langs
        self.course = course
        self.exercise = exercise
        super(TranslationThread, self).__init__(**kwargs)

    def run(self):
        course_pk = self.course.pk
        from translations.views import translate_xml_language

        logger.error("RUN TRANSLATION THREAD {course_pk} ")
        xml = translate_xml_language(self.xml, self.langs, course_pk, self.exercise, False)
        (cache, cachekey) = t_cache_and_key(self.course, self.exercise)
        cache.set(cachekey, xml, None)


class Translation(models.Model):
    # Retain hashkey in model for backward compatibility; not used in code paths
    hashkey = models.CharField(max_length=64, default="", blank=True)
    altkey = models.CharField(max_length=64, default="", blank=True)
    language = models.CharField(max_length=8, default="", blank=True)
    translated_text = models.TextField(default="", blank=True)
    original_text = models.TextField(default="", blank=True)
    exercise = models.ForeignKey(
        Exercise,
        related_name="translation",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.id}: {self.original_text}: {self.language} -> {self.translated_text}"

    def truncated_translation(self):
        if len(self.translated_text) > 25:
            return self.translated_text[0:15] + "..." + self.translated_text[-10:-1]
        else:
            return self.translated_text

    def truncated_original_text(self):
        if len(self.original_text) > 25:
            return self.original_text[0:15] + "..." + self.original_text[-10:-1]
        else:
            return self.original_text

    def save(self, *args, **kwargs):
        cache = caches["translations"]
        courses = Course.objects.all()
        for course in courses:
            course_pk = course.pk
            cachekey = f"{settings.SUBDOMAIN}{course_pk}{self.language}"
            cache.delete(cachekey)
            # print(f"TRANSLATIONS MODELS DELETE CACHEKEY {cachekey}")
        super().save(*args, **kwargs)

    def exercise_name(self):
        try:
            return self.exercise.name
        except AttributeError as e:
            return "--"


class TranslationAdminForm(forms.ModelForm):
    class Meta:
        model = Translation
        fields = "__all__"
        # readonly_fields =   ('id','subdomain','db_name','db_label','last_activity','creator','data')
        # widgets = {
        #    'items': JSONFormWidget(schema=OpenTASite.ITEMS_SCHEMA)
        # }


class TranslationAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(TranslationAdmin, self).get_queryset(request)
        if request.user.username == "super":
            return qs
        else:
            return qs.filter(exercise__isnull=True)

    #   #if self.exercise == 'super_super' :
    #   #    return qs
    #   #else :
    #   #    return qs.filter(exercise='abc')

    model = Translation
    form = TranslationAdminForm

    def get_list_display(self, request):
        list_display = ["id", "language", "altkey", "original_text", "translated_text"]
        return list_display

    # list_display = (
    #    "id",
    #    "hashkey",
    #    "altkey",
    #    "language",
    #    "truncated_translation",
    #    "exercise_name",
    # )
    search_fields = ["original_text", "translated_text", "altkey"]


# exercise_saved_translation.connect(handle_exercise_saved)
admin.site.register(Translation, TranslationAdmin)
