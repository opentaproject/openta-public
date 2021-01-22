import logging
from selenium import webdriver
from django.core.mail import get_connection
from django.conf import settings
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib import messages
from exercises.paths import _subpath



from course.models import Course

logger = logging.getLogger(__name__)


def send_email_object(email):
    course = Course.objects.first()
    docustom = bool( course.email_host and course.email_host_password and course.email_reply_to and course.email_host_user  )
    if ( hasattr(settings, 'USE_CUSTOM_SMTP_EMAIL') and settings.USE_CUSTOM_SMTP_EMAIL ) or  docustom:
        with get_connection(
            host=course.email_host,
            port='587',
            username=course.email_username,
            password=course.email_host_password,
            use_tls=True,
        ) as connection:
            email.connection = connection
        try:
            n_sent = email.send()
            logger.info('send_email_object success' + " (" + str(n_sent) + " delivered)")
        except Exception as e:
            logger.error(str(e))
            raise e
    else:
        try:
            n_sent = email.send()
            logger.info('send_email_object success' + " (" + str(n_sent) + " delivered)")
        except Exception as e:
            logger.error('send_email_object fail' + str(e))
            raise e
    return n_sent


def response_from_messages(messages):
    result = dict(status=set())
    result['messages'] = messages
    for msg in messages:
        result['status'].add(msg[0])
    if 'error' not in result['status']:
        result['success'] = True
    return result


def get_localized_template(template_name):
    """Get major language version of template."""
    course = Course.objects.first()
    try:
        first_language = course.languages.split(',')[0]
    except AttributeError:
        first_language = 'en'
    try:
        template = get_template(template_name + '.' + first_language)
    except TemplateDoesNotExist as exception:
        logger.error(template_name + '.' + first_language + " does not exist")
        raise exception
    return template


class OpenTAStaticLiveServerTestCase(StaticLiveServerTestCase):
    """Override server url with subpath.

    The standard test case class only gives the base URL to the server. To
    enable testing of both normal and subpath usage this class adds /subpath
    to live_server_url.

    """

    @property
    def live_server_url(self):
        return super().live_server_url + '/' + _subpath() 
