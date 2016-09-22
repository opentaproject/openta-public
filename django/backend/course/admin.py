from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.http.response import HttpResponse
from backend.user_utilities import create_activation_link, send_activation_mail

from .models import Course


class CustomUserAdmin(UserAdmin):
    actions = ['resend_activation', 'show_activation']

    def resend_activation(self, request, queryset):
        for user in queryset:
            send_activation_mail(user.username, user.email)
            self.message_user(request, "Email sent for " + user.username)

    def show_activation(self, request, queryset):
        for user in queryset:
            self.message_user(request, create_activation_link(user.username))

    resend_activation.short_description = "Resend the activation email"
    show_activation.short_description = "Show activation link"


admin.site.register(Course)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
