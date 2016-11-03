from django.contrib import admin
from django.utils.html import format_html
from backend.settings import SUBPATH
from django.contrib.auth.models import User
from django.shortcuts import render
from django.db.models import Prefetch
import datetime

from .models import Exercise
from .models import Question
from .models import Answer
from .models import ImageAnswer

from .models import ExerciseMeta


class ImageAnswerAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ['__str__', '_image_thumb']
    search_fields = ['user__username', 'exercise__name']

    def _image_thumb(self, image_answer):
        return format_html(
            '<a href="/{}imageanswer/{}"><img src="/{}imageanswerthumb/{}"/></a>',
            SUBPATH,
            image_answer.pk,
            SUBPATH,
            image_answer.pk,
        )


class ExerciseAdmin(admin.ModelAdmin):
    # readonly_fields = ('id',)
    list_display = ['name', 'path', 'get_required', 'get_bonus', 'get_deadline']
    list_filter = ['meta__required', 'meta__bonus', 'meta__published']
    search_fields = ['name', 'path']
    actions = ['get_passed']

    def get_required(self, exercise):
        return exercise.meta.required

    get_required.short_description = 'Obligatory'

    def get_bonus(self, exercise):
        return exercise.meta.bonus

    get_bonus.short_description = 'Bonus'

    def get_deadline(self, exercise):
        return exercise.meta.deadline_date

    get_deadline.short_description = 'Deadline'

    def get_passed(self, request, queryset):
        users = User.objects.filter(groups__name='Student')
        exercise = queryset.first()
        userdata = users.prefetch_related(
            Prefetch(
                'answer_set',
                queryset=Answer.objects.filter(
                    date__lt=datetime.datetime.combine(
                        exercise.meta.deadline_date, datetime.time(8, 0, 0)
                    )
                ).order_by('-date'),
            )
        )
        return render(request, 'examine/passed_exercises.html', {'users': userdata})


admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(ImageAnswer, ImageAnswerAdmin)
admin.site.register(ExerciseMeta)

# Register your models here.
