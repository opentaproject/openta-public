# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

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
from backend import views as backendviews
from twofactor import views as twofactorviews
from sms.views import bug_report

# from myinvitations import  views as myinvitationsviews  # REMOVED_INVITATIONS
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.urls import re_path as url
from django.conf.urls import handler500, handler403
import logging
logger = logging.getLogger(__name__)



admin.autodiscover()
admin.site.enable_nav_sidebar = False
if settings.USE_INVITATIONS:
    try :
        from django.contrib.sites.models import Site
        admin.site.unregister(Site)
    except Exception as e:
        logger.error('ERROR IN UNREGISTERING SITE')



if settings.HANDLER_500 :
    handler500 = "backend.views.custom_error_500_view"
    handler403 = "backend.views.custom_error_403_view"

adminurl = settings.ADMINURL
internalurlpatterns = [
    # url(r'^trigger_error/(?P<msg>[\w.:\-_=]+)/?$', backendviews.trigger_error),
    path('bug_report/', bug_report, name='bug_report'),
    url(r"^" + adminurl + "/?", admin.site.urls),
    url(
        r"^activateandreset/(?P<username>[\w.@+-]+)/(?P<token>[\w.:\-_=]+)/$",
        backendviews.activate_and_reset,
        name="user-activation-and-reset",
    ),
    url(
        r"^(?P<course_name>[ \w-]+)/activateandreset/(?P<username>[\w.@+-]+)/(?P<token>[\w.:\-_=]+)/$",
        backendviews.course_activate_and_reset,
    ),
    url(
        r"^activate/(?P<username>[\w.@+-]+)/(?P<token>[\w.:\-_=]+)/$",
        backendviews.activate,
        name="user-activation",
    ),
    url(r"^loggedin/", backendviews.login_status),
    url(r"^launch_sidecar", backendviews.launch_sidecar_new),
    url(r"^health/(?P<subdomain>[\w.@+-]+)/(?P<username>[\w.@+-]+)", backendviews.health),
    url(r"^health/(?P<subdomain>[\w.@+-]+)", backendviews.health),
    url(r"^health", backendviews.health),
    url(r"^test500", backendviews.test500),
    url(r"^", include("exercises.urls")),
    url(r"^pw_change/", backendviews.pw_change, name="pw_change"),
    url(r"^otp_validate/", twofactorviews.otp_validate, name="otp_validate"),
    url(r"^password_reset/$", backendviews.password_reset, name="password-reset"),
    url(r"^password_reset/done/$", backendviews.password_reset_done, name="password-reset-done"),
    url(r"^reset/done/", backendviews.password_reset_complete, name="password-reset-complete"),
    url(r"^(?P<course_pk>[0-9]+)/?$", backendviews.main),
    url(r"^(?P<course_pk>[0-9]+)/(?P<exerciseKey>\w\w\w[\w\.-]+)/$", backendviews.main), # FIXED TO AVOID INSTRUTURE HITTING THIS PATTERN INCORRECTLY
    url(r"^(?P<course_pk>[0-9]+)/?$", backendviews.main),
    url(r"^(?P<course_name>[\w\.\ -]+)/login/?$", backendviews.login, name="login"),
    url(r"^login/(?P<course_name>[\w\.\ -]+)/?$", backendviews.login, name="login"),
    url(r"^login/$", backendviews.login, name="login"),
    url(r"^frontend_log/$", backendviews.frontend_log, name="frontend_log"),
    url(r"^", include("django.contrib.auth.urls")),
    path(
        "register_by_password/<int:course_pk>/",
        backendviews.RegisterByPassword,
        name="register-with-password",
    ),
    path(
        "register_by_domain/<int:course_pk>/<slug:anonymoususer>/",
        backendviews.RegisterUserDomain.as_view(),
        name="register-with-domain",
    ),
    path(
        "register_by_domain/<int:course_pk>/",
        backendviews.RegisterUserDomain.as_view(),
        name="register-with-domain",
    ),
    url(
        r"^register_by_password/(?P<course_pk>[0-9]+)/register/(?P<password>[\w]+)$",
        backendviews.validate_and_show_registration,
    ),
    url(r"^view_toggle/$", backendviews.view_toggle),
    url(r"^$", backendviews.main),
    url(r"^home/?$", backendviews.main),
    url(r"^", include("workqueue.urls")),
    url(r"^", include("course.urls")),
    url(r"^", include("opentalti.urls")),
    path("logout/", backendviews.UserLogoutView.as_view(), name="logout"),
    url(r"^logout/(?P<course_name>[\w\.\ -]+)/?$", backendviews.logout),
    url(r"^logout/(?P<course_name>[\w\.\ -]+)/(?P<lti_status>[\w]+)/$", backendviews.logout),
    url(r"^media/public/(?P<asset>[\w\.\-\ \/]+)$", backendviews.serve_public_media),
    url(
        r"^(?P<subdomain>[\w\.\ -]+)/media/public/(?P<asset>[\w\.\-\ \/]+)$", backendviews.serve_subdomain_public_media
    ),
    url(r"^(?P<course_name>[\w\.\ -]+)/?$", backendviews.login, name="login_course_short"),
    # url(r'^hijack/', include('hijack.urls', namespace='hijack')),
    # url(r'^hijack/', include('hijack.urls')),
    url(r"^", include("translations.urls")),
    url(r"^........-....-....-....-............/?", backendviews.main),

    path("hijack/", include("hijack.urls")),
]
urlpatterns = [
    url(r"^" + settings.SUBPATH, include(internalurlpatterns)),
] + static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT,
)
if settings.USE_INVITATIONS:
    urlpatterns += [
        path("django-rq/", include("django_rq.urls")),
        path("invitations/", include("myinvitations.urls")),
    ]
if 'django_ragamuffin' in settings.INSTALLED_APPS :
    urlpatterns += [    url(r'.*django_ragamuffin/', include('django_ragamuffin.urls')) ]
print(f"URL_PATTERNS = {urlpatterns}")
admin.site.site_header = "OpenTA Admin"
