"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.edit import CreateView
from .forms import UserCreateForm, UserCreateFormNoPassword
from django.contrib.auth import views as auth_views
from backend import views as backendviews

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(
        r'^register/$',
        CreateView.as_view(
            template_name='register.html', form_class=UserCreateForm, success_url='/register'
        ),
    ),
    url(
        r'^register_nopw/$',
        CreateView.as_view(
            template_name='register.html',
            form_class=UserCreateFormNoPassword,
            success_url='/register_nopw',
        ),
    ),
    url(
        r'^activate/(?P<username>[\w.@+-]+)/(?P<token>[\w.:\-_=]+)/$',
        backendviews.activate,
        name='user-activation',
    ),
    url(
        r'^activateandreset/(?P<username>[\w.@+-]+)/(?P<token>[\w.:\-_=]+)/$',
        backendviews.activate_and_reset,
        name='user-activation-and-reset',
    ),
    url(r'^loggedin/', backendviews.login_status),
    url(r'^', include('exercises.urls')),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^$', backendviews.login_required(backendviews.main)),
]
