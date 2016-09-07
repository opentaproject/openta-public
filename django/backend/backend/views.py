from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http.response import HttpResponseRedirect
from django.shortcuts import render


@api_view(['GET'])
def login_status(request):
    return Response({'username': request.user.get_username(), 'admin': request.user.is_staff})


def login_required(view):
    def new_view(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect('/login')
        return view(request, *args, **kwargs)

    return new_view


def main(request):
    return render(request, "base_main.html")
    # return HttpResponseRedirect('/static/index.html')
