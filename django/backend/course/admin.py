from django.contrib import admin
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.template.response import TemplateResponse

from backend.user_utilities import create_activation_link, send_activation_mail
from backend.forms import EmailUsersForm
from utils import send_email_object

from .forms import CourseForm
from .models import Course
from users.models import OpenTAUser


class OpenTAUserInline(admin.StackedInline):
    model = OpenTAUser
    can_delete = False
    verbose_name_plural = 'OpenTAUser'


class CustomUserAdmin(UserAdmin):
    actions = ['resend_activation', 'show_activation', 'send_an_email']
    inlines = (OpenTAUserInline,)
    list_display = (
        'id',
        'lti_user_id',
        'last_login',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'get_courses',
        'number_of_groups',
    )
    list_select_related = ('opentauser',)
    list_filter = ('opentauser__courses', 'is_staff', 'is_superuser', 'is_active', 'groups')
    readonly_fields = ('id',)

    def get_courses(self, instance):
        return list(instance.opentauser.courses.values_list('course_name', flat=True))

    def lti_user_id(self, instance):
        return str(instance.opentauser.lti_user_id)

    def number_of_groups(self, instance):
        return len(instance.groups.all())

    lti_user_id.short_description = 'LTI_ID'
    number_of_groups.admin_order_field = 'groups__name'

    get_courses.short_description = 'Courses'

    def resend_activation(self, request, queryset):
        for user in queryset:
            try:
                send_activation_mail(
                    user.opentauser.courses.first(),
                    user.username,
                    user.email,
                    'user-activation-and-reset',
                )
                self.message_user(request, "Email sent for " + user.username)
            except Exception as e:
                self.message_user(request, "Email to " + user.username + ' failed with ' + str(e))

    def send_an_email(self, request, queryset):
        form = None
        if 'do_action' in request.POST:
            form = EmailUsersForm(request.POST)
            if form.is_valid():
                form.send_email(request, queryset)
                return None
        else:
            form = EmailUsersForm()

        context = dict(
            self.admin_site.each_context(request),
            queryset=queryset,
            action='send_an_email',
            action_checkbox_name=admin.helpers.ACTION_CHECKBOX_NAME,
            submit_text='Send',
            form=form,
        )
        return TemplateResponse(request, 'generic_form.html', context)

    def show_activation(self, request, queryset):
        for user in queryset:
            self.message_user(request, create_activation_link(user.username))

    resend_activation.short_description = "Resend the activation email"
    show_activation.short_description = "Show activation link"
    send_an_email.short_description = "Send an email"


class CourseAdmin(admin.ModelAdmin):
    form = CourseForm
    list_display = ('id','published', 'course_name','course_key')
    readonly_fields = ('course_key', 'lti_key', 'lti_secret')


admin.site.register(Course, CourseAdmin)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
