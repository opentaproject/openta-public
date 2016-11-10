from django.contrib import admin
from django.utils.html import format_html
from backend.settings import SUBPATH
from django.contrib.auth.models import User
from django.shortcuts import render
from django.db.models import Prefetch, Max, F
from django.contrib import messages
import datetime
from django.utils import timezone
import pytz

from .models import Exercise
from .models import Question
from .models import Answer
from .models import ImageAnswer

from .models import ExerciseMeta
from course.models import Course


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
    get_deadline.admin_order_field = 'meta__deadline_date'

    def get_passed(self, request, queryset):
        users = User.objects.filter(groups__name='Student')
        deadline_time = datetime.time(8, 0, 0, tzinfo=pytz.timezone('Europe/Stockholm'))
        course = Course.objects.first()
        if course is not None and course.deadline_time is not None:
            deadline_time = course.deadline_time
        exercises = queryset.prefetch_related('question')
        questions = Question.objects.filter(exercise__in=queryset).select_related(
            'exercise', 'exercise__meta'
        )
        users = []
        for question in questions:
            messages.info(request, question)
            users.append(
                set(
                    User.objects.filter(
                        imageanswer__exercise=question.exercise,
                        answer__question=question,
                        answer__correct=True,
                        answer__date__lt=datetime.datetime.combine(
                            question.exercise.meta.deadline_date, deadline_time
                        ),
                    )
                    .values_list('username', flat=True)
                    .distinct()
                )
            )
        passed = set.intersection(*map(set, users))
        passed_users = User.objects.filter(username__in=passed)
        template_data = []
        for user in passed_users:
            template_user = {'id': user.pk, 'exercises': {}}
            for exercise in exercises:
                imageanswers = ImageAnswer.objects.filter(user=user, exercise=exercise)
                template_user['exercises'][exercise.exercise_key] = {
                    'questions': {},
                    'imageanswers': list(imageanswers.values_list('pk', flat=True)),
                }

                for question in exercise.question.all():
                    answer = Answer.objects.filter(
                        user=user,
                        question=question,
                        correct=True,
                        date__lt=datetime.datetime.combine(
                            exercise.meta.deadline_date, deadline_time
                        ),
                    ).latest('date')
                    template_user['exercises'][exercise.exercise_key]['questions'][
                        question.question_key
                    ] = answer.answer
            template_data.append(template_user)

        # for question in questions:
        #    passed_data = passed_data.prefetch_related(
        #            Prefetch(
        #                'answer_set',
        #                queryset = Answer.objects.filter(question=question, correct=True).filter(date__lt=datetime.datetime.combine(exercise.meta.deadline_date, deadline_time)).annotate(latest_date=Max('date')).filter(date=F('latest_date')),
        #                to_attr = 'answers'
        #                ))
        structure = {}
        for exercise in exercises:
            structure[exercise.exercise_key] = {'name': exercise.name, 'questions': {}}
            for question in exercise.question.all():
                structure[exercise.exercise_key]['questions'][question.question_key] = {}

        return render(
            request,
            'examine/passed_exercises.html',
            {
                'users': template_data,
                'n_questions': questions.count(),
                'exercises': structure,
                'SUBPATH': SUBPATH,
            },
        )


admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(ImageAnswer, ImageAnswerAdmin)
admin.site.register(ExerciseMeta)

# Register your models here.
