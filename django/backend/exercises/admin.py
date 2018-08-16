from django.contrib import admin
from django.utils.html import format_html
from backend.settings import SUBPATH
from django.contrib.auth.models import User
from django.shortcuts import render
from django.db.models import Prefetch, Max, F, Count, Sum, Value
from django.contrib import messages
from django.template.response import TemplateResponse
from django import forms
from django.utils.translation import ugettext as _
from django.core.mail import EmailMessage
from django.contrib.admin import DateFieldListFilter

import datetime
from django.utils import timezone
import pytz
import random

from .models import Exercise
from .models import Question
from .models import Answer
from .models import ImageAnswer
from .models import AuditExercise
from .models import AuditResponseFile

from .models import ExerciseMeta
from course.models import Course
from backend import forms as backendforms
from backend import views as backendviews
import exercises.modelhelpers as modelhelpers


class ImageAnswerAdmin(admin.ModelAdmin):
    list_filter = ['exercise', 'user__id']
    search_fields = ['user__id', 'user__username', 'exercise__name']
    list_per_page = 20

    readonly_fields = ('id',)
    # list_display = ['__str__','_image_thumb',]
    # search_fields = ['user__username', 'exercise__name',]
    # list_per_page = 10
    class Media:
        css = {'screen': ('css/uikit.min.css',)}
        js = ('js/jquery.js', 'js/uikit.js', 'js/components/lightbox.js')

    def get_list_display(self, request):
        if request.user.has_perm('exercises.view_student_id'):
            return ['get_username', 'get_exercise_name', 'date', '_image_thumb']
        else:
            return ['get_userid', 'get_exercise_name', 'date', '_image_thumb']

    def get_username(self, answer):
        return answer.user.username

    get_username.short_description = 'User'

    def get_userid(self, answer):
        return answer.user.id

    get_userid.short_description = 'User id'

    def get_exercise_name(self, answer):
        try:
            return answer.exercise.name
        except AttributeError:
            return "__Orphan__"

    get_exercise_name.short_description = 'Exercise'

    def _image_thumb(self, image_answer):
        # return format_html('<a href="/{}imageanswer/{}"><img src="/{}imageanswerthumb/{}"/></a>',SUBPATH, image_answer.pk, SUBPATH, image_answer.pk)
        return format_html(
            '<a href="/{}imageanswer/{}" data-uk-lightbox data-lightbox-type="image"><img src="/{}imageanswerthumb/{}"/></a>',
            SUBPATH,
            image_answer.pk,
            SUBPATH,
            image_answer.pk,
        )


class GetSamplePassedForm(forms.Form):
    number_of_samples = forms.IntegerField(label='How many samples?')
    seed = forms.IntegerField(label='Random seed (optional, default value based on exercise id)')


class ExerciseAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'path',
        'get_percent_complete',
        'get_attempts',
        'get_questions',
        'get_thumbnail',
        'get_required',
        'get_bonus',
        'get_deadline',
    ]
    list_filter = [
        'meta__required',
        'meta__bonus',
        'meta__published',
        ('meta__deadline_date', DateFieldListFilter),
    ]
    list_per_page = 10
    search_fields = ['name', 'path', 'meta__deadline_date']
    ordering = ['meta__deadline_date']
    readonly_fields = ('exercise_key',)

    def get_queryset(self, request):
        qs = super(ExerciseAdmin, self).get_queryset(request)
        return qs.annotate(attempts=Count('question__answer'))

    def get_percent_complete(self, exercise):
        data = modelhelpers.e_student_percent_complete(exercise)
        return "{:.0f}%".format(data['percent_complete'] * 100)

    get_percent_complete.short_description = 'Students progress'

    def get_attempts_db(self, exercise):
        return exercise.attempts

    def get_attempts(self, exercise):
        data = modelhelpers.e_student_attempts_median(exercise)
        median_attempts = data['attempts_median'] if data['attempts_median'] is not None else 0
        return "{:.0f}".format(median_attempts)

    get_attempts.short_description = 'Median attempts (per question)'

    def get_questions(self, exercise):
        return exercise.question.count()

    get_questions.short_description = 'Questions'

    def get_required(self, exercise):
        return exercise.meta.required

    get_required.short_description = 'Obligatory'

    def get_bonus(self, exercise):
        return exercise.meta.bonus

    get_bonus.short_description = 'Bonus'

    def get_deadline(self, exercise):
        return exercise.meta.deadline_date

    get_deadline.short_description = 'Deadline'
    get_deadline.admin_order_field = 'meta__deadline_date'

    def get_thumbnail(self, exercise):
        return format_html(
            '<img src="/{}exercise/{}/asset/thumbnail.png"/></a>', SUBPATH, exercise.exercise_key
        )

    get_thumbnail.short_description = 'Figure'


class AnswerAdmin(admin.ModelAdmin):
    # readonly_fields = ('id',)
    list_filter = ['question__exercise', 'user__id']
    search_fields = ['user__username', 'question__exercise__name']
    list_per_page = 20

    def get_list_display(self, request):
        if request.user.has_perm('exercises.view_student_id'):
            return [
                'get_username',
                'get_answer',
                'correct',
                'get_exercise_name',
                'get_question',
                'date',
            ]
        else:
            return [
                'get_userid',
                'get_answer',
                'correct',
                'get_exercise_name',
                'get_question',
                'date',
            ]

    def get_question(self, answer):
        try:
            return answer.question.question_key
        except AttributeError:
            return "__Orphan__"

    get_question.short_description = 'Question'

    def get_answer(self, answer):
        if answer.correct:
            return format_html('<span style="color: green">{}</span>', answer.answer)
        else:
            return format_html('<span style="color: red">{}</span>', answer.answer)

    def get_username(self, answer):
        return answer.user.username

    get_username.short_description = 'User'

    def get_userid(self, answer):
        return answer.user.id

    get_userid.short_description = 'User id'

    def get_exercise_name(self, answer):
        try:
            return answer.question.exercise.name
        except AttributeError:
            return "__Orphan__"

    get_exercise_name.short_description = 'Exercise'


class AuditExerciseAdmin(admin.ModelAdmin):
    list_display = [
        'exercise',
        'student',
        'auditor',
        'date',
        'message',
        'sent',
        'published',
        'revision_needed',
        'force_passed',
    ]
    list_filter = ['sent', 'published', 'force_passed', 'revision_needed']
    list_per_page = 20
    search_fields = ['student__username', 'auditor__username', 'exercise__name']
    ordering = ['date']
    readonly_fields = ('id',)


admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(Question)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(ImageAnswer, ImageAnswerAdmin)
admin.site.register(ExerciseMeta)
admin.site.register(AuditResponseFile)
admin.site.register(AuditExercise, AuditExerciseAdmin)

# Register your models here.
