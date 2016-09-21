from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.shortcuts import render, redirect, reverse
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth.models import User
from django.contrib.auth import views as auth_views
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.forms import SetPasswordForm
from django.views.generic.edit import FormView
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from course.models import Course
from course.serializers import CourseSerializer
from backend.forms import RegisterWithPasswordForm
from django.views.generic.edit import CreateView
from .forms import UserCreateForm, UserCreateFormNoPassword
from ratelimit.decorators import ratelimit


class ActivateAndReset(FormView):
    template_name = 'registration/set_password.html'
    user = None

    def get_form(self):
        return SetPasswordForm(self.user, **self.get_form_kwargs())

    def form_valid(self, form):
        messages.add_message(
            self.request._request, messages.SUCCESS, _('Password is now set, please login.')
        )
        return redirect(reverse('login'))


class RegisterUser(CreateView):
    template_name = 'register.html'
    form_class = UserCreateForm
    success_url = '/register'


class RegisterUserNoPassword(CreateView):
    template_name = 'register.html'
    form_class = UserCreateFormNoPassword
    success_url = '/register_nopw'


@api_view(['GET'])
def login_status(request):
    groups = []
    dbgroups = request.user.groups.all()
    for group in dbgroups:
        groups.append(group.name)
    return Response(
        {'username': request.user.get_username(), 'admin': request.user.is_staff, 'groups': groups}
    )


# @api_view(['GET'])
@ratelimit(key='ip', rate='5/30s')
def login(request):
    course = Course.objects.first()
    course_data = CourseSerializer(course).data
    extra = {'course': course_data}
    if not getattr(request, 'limited', False):
        return auth_views.login(request, extra_context=extra)
    else:
        return render(request, 'rate_limit.html', context={'rate': _('5 times per 30 seconds')})


@api_view(['GET'])
def activate(request, username, token):
    try:
        key = '%s:%s' % (username, token)
        print(key)
        TimestampSigner().unsign(key, max_age=60 * 60 * 48)  # Valid for 2 days
        user = User.objects.get(username=username)
        user.is_active = True
        user.save()
    except (BadSignature, SignatureExpired):
        return render(request, "activation_failed.html")
    messages.add_message(
        request._request, messages.SUCCESS, _('Activation successful, please logi.')
    )
    return auth_views.login(request._request, 'registration/login.html')


@api_view(['GET', 'POST'])
def activate_and_reset(request, username, token):
    try:
        key = '%s:%s' % (username, token)
        print(key)
        TimestampSigner().unsign(key, max_age=60 * 60 * 48)  # Valid for 2 days
    except (BadSignature, SignatureExpired):
        return render(request, "activation_failed.html")
    user = User.objects.get(username=username)
    user.is_active = True
    user.save()
    return ActivateAndReset.as_view()(request, user=user)


@login_required
def main(request):
    return render(request, "base_main.html")


class RegisterByPassword(FormView):
    template_name = 'registration/register_with_password.html'
    form_class = RegisterWithPasswordForm

    def form_valid(self, form):
        course = Course.objects.first()
        if (
            course.registration_by_password
            and course.registration_password == form.cleaned_data['password']
        ):
            self.request.method = 'GET'
            return RegisterUser.as_view()(self.request)
        return redirect('/register_by_password')
