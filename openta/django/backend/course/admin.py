# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.contrib import admin
from django.conf import settings
from django.contrib.auth.hashers import make_password
from utils import get_subdomain_and_db
from twofactor.views import delete_otp_secret
from django import forms
from course.models import Course

# from invitations.models import Invitation # REMOVED_INVITATIONS
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.core.mail import EmailMessage
from course.forms import CustomUserForm
from django.template.response import TemplateResponse
from import_export.admin import ImportExportActionModelAdmin

# from myinvitations.admin import InvitationAdmin # REMOVED_INVITATIONS

from backend.user_utilities import create_activation_link, send_activation_mail
from backend.forms import EmailUsersForm

from .forms import CourseForm
from .models import Course
from users.models import OpenTAUser


class OpenTAUserInline(admin.StackedInline):
    def __init__(self, *args, **kwargs):
        # print(f"self= {self} {self.__dict__} ")
        # print(f"vars = {vars(self)}")
        # print(f"kwargs = {kwargs}")
        # print(f"dir = {dir(self)}")
        # self.exclude = ('courses',)
        super(OpenTAUserInline, self).__init__(*args, **kwargs)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(OpenTAUserInline, self).get_fieldsets(request, obj)
        # print(f"fieldsets = {fieldsets}")
        # print(f"user = {request.user}")
        # print(f"obj = {obj}")
        if not request.user.username == "super":
            fieldsets[0][1]["fields"].remove("courses")
        return fieldsets

    # def get_queryset():
    #    print(f"QUERYSET = {queryset}")
    #    return super(OpenTAUserInline, self).__init__(*args, **kwargs)
    #    return self.queryset

    model = OpenTAUser
    can_delete = True
    verbose_name_plural = "OpenTAUser"


class CustomUserAdmin(UserAdmin):

    form = CustomUserForm

    def delete_view(self, request, object_id=None, extra_context=None):
        messages.add_message(
            request,
            messages.WARNING,
            f"Do you really want to delete user? Perhaps it is better to make user inactive. Go back and  untick the box Active",
        )
        return super(CustomUserAdmin, self).delete_view(request, object_id=object_id, extra_context=extra_context)

    def get_queryset(self, request):
        db, subdomain = get_subdomain_and_db(request)
        qs = super(UserAdmin, self).get_queryset(request)
        ########  EXCLUDE SUPERUSERS FROM QUERYSET
        # superusers = list( User.objects.using(db).filter(is_superuser=True).values_list('username',flat=True) )
        # print(f"SUPERUSERS = {superusers}")
        # for superuser in superusers :
        #    qs.exclude(username=superusers)
        #########
        if request.user.username == "super" or not settings.LOCK_SUPER :
            return qs
        else:
            return qs.exclude(username="super")

    def get_inline_instances(self, request, obj=None):
        # _inlines = super().get_inline_instances(request, obj=None)
        # custom_inline = YourDynamicInline(self.model, self.admin_site)
        # _inlines.append(custom_inline)
        # print(f"GET INLINE INSTANCES")
        url = request.get_full_path
        subdomain, db = get_subdomain_and_db(request)
        _inlines = [inline(self.model, self.admin_site) for inline in self.inlines]
        courses = list(Course.objects.all().filter(opentasite=subdomain))
        for course in courses:
            if not course.use_lti:
                _inlines = []
        return _inlines

    def get_form(self, request, obj=None, **kwargs):
        # print(f" GET FORM CUSTOM_USER_ADMIN")
        # print(f" GET FORM CUSTOM_USER_ADMIN KWARGS = {kwargs}  ")
        # print(f" GET FORM CUSTOM_USER_ADMIN OBJ = {obj}   ")
        # print(f" request = {request}")

        form = super().get_form(request, obj, **kwargs)
        if obj == None:
            return form
            # form.base_fields['password1'].initial = make_password('abcdefg')
            # form.base_fields['password2'].initial = make_password('abcdefg')
            # form.base_fields['password1'].required = False
            # form.base_fields['password2'].required = False
            # form.base_fields['password1'].widget =  forms.PasswordInput(attrs={"readonly": True})
            # form.base_fields['password2'].widget =  forms.PasswordInput(attrs={"readonly": True})
            # return form
        is_superuser = request.user.is_superuser
        is_staff = request.user.is_staff
        is_super = request.user.username == "super"
        disabled_fields = set()
        disabled_fields = ("is_superuser", "user_permissions")
        # if is_staff:
        #    disabled_fields = ('user_permissions','groups','is_superuser')
        # if is_superuser :
        #    disabled_fields = ('user_permissions','groups','is_superuser')
        if is_super:
            disabled_fields = set("")
        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True
        # print(f"form = {form} {vars(form)} " )
        form.base_fields["is_staff"].initial = True
        if not "request_username" in form.base_fields:
            form.base_fields["request_username"] = forms.fields.CharField()
        try:
            form.base_fields["request_username"].initial = request.user.username
            # print(f" REQUEST USERNAME OK {form.base_fields['request_username']} " )
            # form.base_fields['password'].initial = obj.get_password()
        except:
            form.base_fields["request_username"].initial = request.user.username
            # print(f"BASE FIELD REQUEST_USERNAME DOES NOT EXIST")
        if kwargs["change"]:
            form.base_fields["password"].disabled = True
            form.base_fields["password"].render_value = False
            form.base_fields["password"].widget = forms.fields.HiddenInput()
        else:
            return form
        # form.base_fields['password'].label = 'Change user password(*)'

        if not is_superuser:
            form.base_fields["user_permissions"].widget = forms.HiddenInput(attrs={"readonly": True})
        # form.base_fields['groups'].disabled = True
        return form

    actions = ["resend_activation", "show_activation", "send_an_email", "make_inactive", "make_active","delete_otp_secret"]
    inlines = (OpenTAUserInline,)
    list_display = (
        "id",
        "lti_user_id",
        "last_login",
        "username",
        "last_name",
        "is_staff",
        "get_courses",
        "number_of_groups",
        "is_active",
    )
    list_select_related = ("opentauser",)
    list_filter = ("opentauser__courses", "is_staff", "is_superuser", "is_active", "groups")
    readonly_fields = ("id",)

    def get_courses(self, instance):
        return list(instance.opentauser.courses.values_list("course_name", flat=True))

    def lti_user_id(self, instance):
        return str(instance.opentauser.lti_user_id)

    def number_of_groups(self, instance):
        return len(instance.groups.all())

    lti_user_id.short_description = "LTI_ID"
    number_of_groups.admin_order_field = "course"

    get_courses.short_description = "All Courses"

    def resend_activation(self, request, queryset):
        for user in queryset:
            try:
                send_activation_mail(
                    user.opentauser.courses.first(),
                    user.username,
                    user.email,
                    "user-activation-and-reset",
                )
                self.message_user(request, "Email sent for " + user.username)
            except Exception as e:
                self.message_user(request, "Email to " + user.username + " failed with " + str(e))

    def send_an_email(self, request, queryset):
        form = None
        if "do_action" in request.POST:
            form = EmailUsersForm(request.POST)
            if form.is_valid():
                form.send_email(request, queryset)
                return None
        else:
            form = EmailUsersForm()

        context = dict(
            self.admin_site.each_context(request),
            queryset=queryset,
            action="send_an_email",
            action_checkbox_name=admin.helpers.ACTION_CHECKBOX_NAME,
            submit_text="Send",
            form=form,
        )
        return TemplateResponse(request, "generic_form.html", context)

    def show_activation(self, request, queryset):
        for user in queryset:
            self.message_user(request, create_activation_link(user.username))

    def delete_otp_secret(self, request, queryset):
        for user in queryset:
            delete_otp_secret( user );


    def make_inactive(self, request, queryset):
        for user in queryset:
            user.is_active = False
            user.save()

            self.message_user(request, f"made {user.username} inactive")

    def make_active(self, request, queryset):
        for user in queryset:
            user.is_active = True
            user.save()
            self.message_user(request, f"made {user.username} active ")

    resend_activation.short_description = "Resend the activation email"
    show_activation.short_description = "Show activation link"
    delete_otp_secret.short_description = "Delete otp secret"
    send_an_email.short_description = "Send an email"


class CourseAdmin(admin.ModelAdmin):
    form = CourseForm
    list_display = ("id", "published", "course_name", "course_key")
    #readonly_fields = ("course_key", "lti_key", "lti_secret")


# class CustomGroupAdmin(GroupAdmin):

#
# NOT NECESSARY SINCE IT REVERTS TO DEFAULT
#

# def get_queryset(self,request ) :
#    db, subdomain = get_subdomain_and_db(request)
#    qs = super(GroupAdmin,self).get_queryset(request)
#    return qs

# def nochange_view(self, request, object_id, form_url='', extra_context=None) :
#    print(f"CHANGE_VIEW")
#    #print(f"CHANGE VIEW {self} {vars(self)} ")
#    #print(f"CHANGE VIEW EXTRA {extra_context}")
#    #form = self.get_form(request)
#    #print(f"INITIAL = {form.base_fields['data']}")
#    #data = form.base_fields['data']
#    #self.data['creator']
#    #print(f"INITIAL = {form.base_fields['data'].get('creator','none') }")
#    ##print(f" FORM = {form} {vars(form)}")
#    #print(f" BASE_FIELDS = {form.base_fields}")
#    #data = form.base_fields['data']
#    #print(f"DATA = {data } {dir(data)}")
#    #print(f"DATA pythone {data.to_python}")
#    #pyt = data.to_python
#    #print(f"pyt = {pyt} {vars(pyt)} ")
#    #ini = data.initial
#    #print(f" INI = {ini} {vars(ini)}")
#    #print(f"CREATOR = {form.base_fields['creator'].initial }")
#    #data = form.base_fields['data'].initial
#    #print(f"DATA = {data} { data.get('description','none')}")
#    return super().change_view( request, object_id, form_url, extra_context=extra_context)


# def get_form(self, request, obj=None, **kwargs):
#    print(f"GET GROUP FORM")
#    form = super().get_form(request, obj, **kwargs)
#    form.base_fields['permissions'].readonly = True
#    form.base_fields['permissions'].disabled = True
#    #form.base_fields['permissions'].widget = forms.HiddenInput(attrs={"readonly": True,"disabled":True})
#    print(f"KEYS = {form.base_fields.keys()}")
#    return form


admin.site.register(Course, CourseAdmin)
admin.site.unregister(User)
# admin.site.unregister(Group)
# admin.site.register(Group, CustomGroupAdmin)
admin.site.register(User, CustomUserAdmin)
