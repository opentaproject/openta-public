from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class SameSiteMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        subpath = settings.SUBPATH.strip('/')
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
