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
        return answer.exercise.name

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
    # readonly_fields = ('id',)
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
    actions = ['get_passed', 'get_sample_passed', 'get_not_passed']
    ordering = ['meta__deadline_date']

    def get_queryset(self, request):
        qs = super(ExerciseAdmin, self).get_queryset(request)
        n_users = User.objects.filter(groups__name='Student', is_active=True).count()
        # return qs.annotate(attempts=Count('question__answer')/Value(n_users)/Count('question'))
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

    def get_sample_passed(self, request, queryset):
        if request.POST.get('post-number-samples'):
            form = GetSamplePassedForm(request.POST)
            if form.is_valid():
                return self.get_passed(
                    request,
                    queryset,
                    samples=form.cleaned_data['number_of_samples'],
                    seed=form.cleaned_data['seed'],
                )
        else:
            seed = 0
            for val in queryset.values_list('pk', flat=True):
                seed = seed + (hash(val) % 100)
            form = GetSamplePassedForm(initial={'number_of_samples': 5, 'seed': seed})
            context = dict(
                self.admin_site.each_context(request),
                action='get_sample_passed',
                queryset=queryset,
                action_checkbox_name=admin.helpers.ACTION_CHECKBOX_NAME,
                form=form,
                submit_text="Get samples",
                hidden={'post-number-samples': 'yes'},
            )
            return TemplateResponse(request, 'generic_form.html', context)

    def get_not_passed(self, request, queryset):
        # self.message_user(request, "Get not passed")
        if request.POST.get('post-email-users'):
            # self.message_user(request, "Post email users")
            context = dict(
                self.admin_site.each_context(request),
                action='get_not_passed',
                queryset=queryset,
                action_checkbox_name=admin.helpers.ACTION_CHECKBOX_NAME,
            )
            return backendviews.email_users(request, context)
        else:
            dbusers = User.objects.filter(groups__name='Student', is_active=True)
            deadline_time = datetime.time(8, 0, 0, tzinfo=pytz.timezone('Europe/Stockholm'))
            course = Course.objects.first()
            if course is not None and course.deadline_time is not None:
                deadline_time = course.deadline_time
            # exercises = queryset.prefetch_related('question')
            questions = Question.objects.filter(exercise__in=queryset).select_related(
                'exercise', 'exercise__meta'
            )
            users = []
            for question in questions:
                # messages.info(request, question)
                passed = (
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
                notpassed = (
                    User.objects.exclude(username__in=passed)
                    .values_list('username', flat=True)
                    .distinct()
                )
                users.append(set(notpassed))
            not_passed = set.union(*map(set, users))
            dbnot_passed = dbusers.exclude(username="student").filter(
                username__in=not_passed, email__isnull=False
            )
            dbpassed_no_image = dbnot_passed.all()
            for question in questions:
                dbpassed_no_image = dbpassed_no_image.filter(
                    answer__question=question,
                    answer__correct=True,
                    answer__date__lt=datetime.datetime.combine(
                        question.exercise.meta.deadline_date, deadline_time
                    ),
                )

            exercises_render = []
            for exercise in queryset:
                deadline = datetime.datetime.combine(exercise.meta.deadline_date, deadline_time)
                answer = (
                    Answer.objects.filter(
                        correct=True, question__exercise=exercise, date__lt=deadline
                    )
                    .order_by('-date')
                    .first()
                )
                if answer is not None:
                    last_answer = answer.date
                else:
                    last_answer = None
                exercises_render.append(
                    {
                        'name': exercise.name,
                        'last_answer': last_answer,
                        'deadline': deadline,
                        'key': exercise.exercise_key,
                    }
                )

            exercises_list = ",".join(queryset.values_list('exercise_key', flat=True))
            # self.message_user(request, " " + ", ".join(not_passed_email))
            # opts = self.model._meta
            # app_label = opts.app_label
            context = dict(
                self.admin_site.each_context(request),
                SUBPATH=SUBPATH,
                # title="Test",
                # site_header="OpenTA Admin",
                queryset=queryset,
                action_checkbox_name=admin.helpers.ACTION_CHECKBOX_NAME,
                exercises=exercises_render,
                exercises_list=exercises_list,
                last_answer=last_answer,
                users=dbnot_passed,
                users_passed_no_image=dbpassed_no_image,
                show_users=request.user.has_perm('exercises.show_student_id'),
                #       opts=opts,
            )
            request.session['email_users'] = list(dbnot_passed.values_list('pk', flat=True))
            return TemplateResponse(request, 'examine/not_passed_exercises.html', context)

    def get_passed(self, request, queryset, samples=None, seed=None):
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
        if request.POST.get('samples') is not None:
            samples = int(request.POST.get('samples'))
        if request.POST.get('seed') is not None:
            seed = int(request.POST.get('seed'))
        if samples is not None:
            if seed is not None:
                random.seed(seed)
                request.session['seed'] = seed
            if samples > len(passed):
                samples = len(passed)
                messages.info(
                    request, _('Number of samples larger than population, showing all users.')
                )
            passed = random.sample(passed, samples)
        passed_users = User.objects.filter(username__in=passed)
        template_data = []
        for user in passed_users:
            template_user = {'id': user.pk, 'username': user.username, 'exercises': {}}
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
        email_form = backendforms.EmailUsersForm(
            initial={'subject': Course.objects.course_name() + ": " + _('Random control')}
        )
        if request.POST.get('email_students'):
            email_form = backendforms.EmailUsersForm(request.POST)
            for user in request.POST.getlist('selected_users'):
                dbuser = User.objects.get(pk=user)
                if email_form.is_valid():
                    email = EmailMessage(
                        subject=email_form.cleaned_data['subject'],
                        body=email_form.cleaned_data['message'],
                        from_email=Course.objects.course_name().lower() + "@openta.se",
                        to=[dbuser.email],
                    )
                    email.send()
                    if request.user.has_perm('exercises.view_student_id'):
                        userinfo = dbuser.username
                    else:
                        userinfo = user
                    messages.info(request, "Emailed user " + userinfo)

        hidden = {'email_students': 'yes'}
        if samples is not None:
            hidden.update({'samples': samples})
        if seed is not None:
            hidden.update({'seed': seed})
        context = dict(self.admin_site.each_context(request))
        context.update(
            {
                'users': template_data,
                'n_questions': questions.count(),
                'exercises': structure,
                'SUBPATH': SUBPATH,
                'show_users': request.user.has_perm('exercises.view_student_id'),
                'form': email_form,
                'submit_text': 'Send email',
                'action': 'get_passed',
                'hidden': hidden,
                'queryset': queryset,
                'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
            }
        )
        return render(request, 'examine/passed_exercises.html', context)


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
