from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.shortcuts import render, redirect, reverse
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth.models import User
from django.contrib.auth.views import login
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.forms import SetPasswordForm
from django.views.generic.edit import FormView
from django.contrib import messages
from django.utils.translation import ugettext as _


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


@api_view(['GET'])
def login_status(request):
    groups = []
    dbgroups = request.user.groups.all()
    for group in dbgroups:
        groups.append(group.name)
    return Response(
        {'username': request.user.get_username(), 'admin': request.user.is_staff, 'groups': groups}
    )


def login_required(view):
    def new_view(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect('/login')
        return view(request, *args, **kwargs)

    return new_view


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
    messages.add_message(request._request, messages.SUCCESS, 'Activationnn, please login.')
    return login(request._request, 'registration/login.html')


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


# return login(request._request, 'registration/login.html', extra_context={'success_msg':'Activation success, please login.'})

# return login(request._request, 'registration/login.html', extra_context={'success_msg':'Activation success, please login.'})


def main(request):
    return render(request, "base_main.html")
    # return HttpResponseRedirect('/static/index.html')
