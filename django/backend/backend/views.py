from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth.models import User
from django.contrib.auth.views import login
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters


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
    return login(
        request._request,
        'registration/login.html',
        extra_context={'success_msg': 'Activation success, please login.'},
    )
    # return redirect('login', extra_context={'msg': 'Activated, please log in'})

    # return login(request._request, 'registration/login.html', extra_context={'success_msg':'Activation success, please login.'})


def main(request):
    return render(request, "base_main.html")
    # return HttpResponseRedirect('/static/index.html')
