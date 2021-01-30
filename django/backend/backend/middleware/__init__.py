from django.utils.deprecation import MiddlewareMixin
from django.db import models
from django.conf import settings
from exercises.paths import _subpath
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site




class SameSiteMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        subpath =  ( _subpath(uri=request.get_full_path(),session=request.session )  ).strip('/')
        sessionid = 'sessionid%s' % subpath
        csrftoken = 'csrftoken%s' % subpath
        for cookie in [
            sessionid,
            csrftoken,
            'launch_presentation_return_url',
            'displayStyle',
            'csrf_cookie_name',
            'cookieTest',
        ]:
            if cookie in response.cookies:
                response.cookies[cookie]['samesite'] = 'None'
                response.cookies[cookie]['secure'] = True
        return response

class SubpathMiddleware(MiddlewareMixin):
    def process_request(self, request, response=None):
        subpath =  ( _subpath(uri=request.get_full_path())  ).strip('/')
        settings.DB_NAME = subpath
        settings.MEDIA_ROOT = '/srv/multicourse/%s/media' %  subpath
        settings.EXERCISES_PATH = '/srv/multicourse/%s/exercises' % subpath
        settings.SUBDOMAIN = subpath
        print("DB_NAME = ", settings.DB_NAME, " MEDIA_ROOT = ", settings.MEDIA_ROOT , "EXERCISES_PATH = ", settings.EXERCISES_PATH ,  " SUBPAHT = ", settings.SUBPATH , " <")


# https://stackoverflow.com/questions/26659877/django-dynamically-set-site-id-in-settings-py-based-on-url

class DynamicSiteDomainMiddleware(MiddlewareMixin):

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        domain = ( request.get_host()   ).split(':')[0]
        print("DOMAIN MIDDLEWARE CALLED SELF" , domain)
        try:
            current_site = Site.objects.get(domain=domain)
        except Site.DoesNotExist:
            current_site = Site.objects.get(id=settings.DEFAULT_SITE_ID)
        print("CURRENT_SITE = ", current_site.id, current_site)

        request.current_site = current_site
        settings.SITE_ID = current_site.id
        settings.SUBDOMAIN = domain.split('.')[0]
        print("SUBDOMAIN ", settings.SUBDOMAIN)
        settings.DB_NAME = settings.SUBDOMAIN
        print("CURRENT_SITE = ", current_site.id, current_site)

        response = self.get_response(request)
        return response

