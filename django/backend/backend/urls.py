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
from django.urls import path
from django.contrib import admin
from backend import views as backendviews
from django.conf import settings
from django.conf.urls.static import static


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
    url(r'^(?P<course_pk>[0-9]+)/?$', backendviews.main),
    url(r'^(?P<course_name>[\w\.\ -]+)/login$', backendviews.login, name='login'),
    url(r'^login/$', backendviews.login, name='login'),
    url(r'^', include('django.contrib.auth.urls')),
    path(
        'register_by_password/<int:course_pk>/',
        backendviews.RegisterByPassword.as_view(),
        name='register-with-password',
    ),
    path(
        'register_by_domain/<int:course_pk>/',
        backendviews.RegisterUserDomain.as_view(),
        name='register-with-domain',
    ),
    url(
        r'^register_by_password/(?P<course_pk>[0-9]+)/register/(?P<password>[\w]+)$',
        backendviews.validate_and_show_registration,
    ),
    url(r'^view_toggle/$', backendviews.view_toggle),
    url(r'^$', backendviews.main),
    url(r'^', include('workqueue.urls')),
    url(r'^', include('course.urls')),
    url(r'^', include('opentalti.urls')),
    url(r'^logout/?$', backendviews.logout),
    url(r'^logout/(?P<course_name>[\w\.\ -]+)/?$', backendviews.logout),
    url(r'^logout/(?P<course_name>[\w\.\ -]+)/(?P<lti_status>[\w]+)/$', backendviews.logout),
    url(r'^' + settings.MEDIA_TAG + '/(?P<asset>[\w\.\-\ \/]+)$', backendviews.serve_public_media),
    url(r'^(?P<course_name>[\w\.\ -]+)/?$', backendviews.login, name='login_course_short'),
    url(r'^hijack/', include('hijack.urls',namespace='hijack')),
]

urlpatterns = [url(r'^' + settings.SUBPATH, include(internalurlpatterns))] + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

admin.site.site_header = 'OpenTA Admin'
