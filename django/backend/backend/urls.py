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
from backend import views as backendviews
from .settings import SUBPATH

internalurlpatterns = [
    url(r'^administration/', admin.site.urls),
    url(
        r'^activateandreset/(?P<username>[\w.@+-]+)/(?P<token>[\w.:\-_=]+)/$',
        backendviews.activate_and_reset,
        name='user-activation-and-reset',
    ),
    url(
        r'^activate/(?P<username>[\w.@+-]+)/(?P<token>[\w.:\-_=]+)/$',
        backendviews.activate,
        name='user-activation',
    ),
    url(r'^loggedin/', backendviews.login_status),
    url(r'^', include('exercises.urls')),
    url(r'^password_reset/$', backendviews.password_reset, name='password-reset'),
    url(r'^password_reset/done/$', backendviews.password_reset_done, name='password-reset-done'),
    url(r'^reset/done/', backendviews.password_reset_complete, name='password-reset-complete'),
    url(r'^login/$', backendviews.login, name='login'),
    url(r'^', include('django.contrib.auth.urls')),
    url(
        r'^register_by_password/$',
        backendviews.RegisterByPassword.as_view(),
        name='register-with-password',
    ),
    url(
        r'^register_by_domain/$',
        backendviews.RegisterUserDomain.as_view(),
        name='register-with-domain',
    ),
    url(
        r'^register_by_password/register/(?P<password>[\w]+)$',
        backendviews.validate_and_show_registration,
    ),
    url(r'^batch_add_users$', backendviews.BatchAddUserView.as_view()),
    url(r'^$', backendviews.main),
    url(r'^', include('workqueue.urls')),
    url(r'^', include('course.urls')),
    url(r'^media/(?P<asset>[\w\.\-\ \/]+)$', backendviews.serve_media),
]

urlpatterns = [
    url(r'^' + SUBPATH, include(internalurlpatterns)),
    url(r'^hijack/', include('hijack.urls')),
]

admin.site.site_header = 'OpenTA Admin'
