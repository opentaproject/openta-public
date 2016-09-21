from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect, reverse
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth.models import User
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import SetPasswordForm
from django.views.generic.edit import FormView
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from course.models import Course
from course.serializers import CourseSerializer
from backend.forms import RegisterWithPasswordForm, BatchAddUsersForm
from django.views.generic.edit import CreateView
from .forms import UserCreateForm, UserCreateFormNoPassword
from ratelimit.decorators import ratelimit
from ratelimit.mixins import RatelimitMixin
import csv
from io import StringIO
import chardet


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


class RegisterByPassword(RatelimitMixin, FormView):
    template_name = 'registration/register_with_password.html'
    form_class = RegisterWithPasswordForm
    ratelimit_key = 'ip'
    ratelimit_rate = '5/30s'

    def form_valid(self, form):
        if getattr(self.request, 'limited', False):
            return render(
                self.request, 'rate_limit.html', context={'rate': _('5 times per 30 seconds')}
            )
        course = Course.objects.first()
        if (
            course.registration_by_password
            and course.registration_password == form.cleaned_data['password']
        ):
            return redirect('/register_by_password/register/' + course.registration_password)
        return redirect('/register_by_password')


@ratelimit(key='ip', rate='5/30s')
def validate_and_show_registration(request, password):
    if getattr(request, 'limited', False):
        return render(request, 'rate_limit.html', context={'rate': _('5 times per 30 seconds')})
    course = Course.objects.first()
    if course.registration_by_password and course.registration_password == password:
        return RegisterUser.as_view()(request)


class BatchAddUserView(FormView):
    template_name = 'batch_add_users.html'
    form_class = BatchAddUsersForm

    def form_valid(self, form):
        print('Valid...')
        print(form.cleaned_data['batch_file'])
        raw = form.cleaned_data['batch_file'].read()
        encoding = chardet.detect(raw)
        uni = raw.decode('latin-1')  # encoding['encoding'])
        dialect = csv.Sniffer().sniff(uni)
        # print(uni)
        data = list(
            csv.reader(StringIO(uni), dialect=dialect)
        )  # delimiter='\t', lineterminator='\n'))
        labels = data[0]
        # print(labels)
        users = []
        for row in data[1:]:
            parsed_row = [{label.replace(' ', '_'): value} for label, value in zip(labels, row)]
            res = {}
            for item in parsed_row:
                res = {**res, **item}
            users.append(res)

        return render(self.request, 'batch_add_users.html', {'form': form, 'users': users})
