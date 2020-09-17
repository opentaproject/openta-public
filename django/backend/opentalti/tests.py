import datetime
from lxml import etree
from unittest.mock import patch
from io import StringIO

from django.test import TestCase
from django.conf import settings
from importlib import import_module
from django.contrib.auth.models import User
from oauth2 import Request, Consumer, SignatureMethod_HMAC_SHA1

from users.models import OpenTAUser

from exercises.test.test_utils import create_course

LTI_CONFIG_XML = "lti/config_xml/"
LTI_LAUNCH = "lti/"


def get_oath2_data(url, key, secret):
    method = "POST"
    consumer = Consumer(key, secret)
    req = Request.from_consumer_and_token(consumer, {}, method, url, None)
    req.sign_request(SignatureMethod_HMAC_SHA1(), consumer, None)
    return req


class TestLTI(TestCase):
    """Test LTI functionality."""

    fixtures = ["fixtures/auth.json"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._headers = dict(HTTP_HOST="host")

    def setUp(self):
        settings.SESSION_ENGINE = "django.contrib.sessions.backends.file"
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        self.session = store
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key
        self.session["lti_login"] = True
        self.session.save()

    def test_lti_no_published_courses(self):  # FAIL
        url = "/" + settings.SUBPATH + LTI_CONFIG_XML
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_lti_config_xml(self):  # OK
        course_other = create_course("other_course_name", datetime.time(0, 0, 0))
        course = create_course("course_name", datetime.time(0, 0, 0))
        course.registration_domains = "valid.ext"
        course.save()

        url = "/" + settings.SUBPATH + LTI_CONFIG_XML
        response = self.client.post(url, **self._headers)
        self.assertEqual(response.status_code, 200)

        try:
            etree.fromstring(response.content)
        except etree.XMLSyntaxError:
            self.fail("Invalid XML from {}".format(LTI_CONFIG_XML))
        self.assertTrue('OpenTA' in str(response.content), msg=str(response.content))

    @patch("opentalti.views.verify_request_common")
    def test_failed_verification(self, verify_request_common=None):
        course_other = create_course("other_course_name", datetime.time(0, 0, 0))
        course = create_course("course_name", datetime.time(0, 0, 0))
        course.registration_domains = "valid.ext"
        course.save()
        data = dict(
            lti_message_type="basic-lti-launch-request",
            lti_version="LTI-1p0",
            resource_link_id="0",
            custom_user_id="$Custom",
            roles="Learner",
            launch_presentation_return_url='launch_presentation_return_url',
        )
        url = "/" + settings.SUBPATH + LTI_LAUNCH
        response = self.client.post(url, data=data, **self._headers)
        self.assertIn("please try again", str(response.content))

    @patch("opentalti.views.verify_request_common")
    def test_lti_first_launch_student(self, verify_request_common=None):
        course_other = create_course("other_course_name", datetime.time(0, 0, 0))
        course = create_course("course_name", datetime.time(0, 0, 0))
        course.registration_domains = "valid.ext"
        course.save()
        data = dict(
            lti_message_type="basic-lti-launch-request",
            lti_version="LTI-1p0",
            resource_link_id="0",
            custom_user_id="user_id",
            roles="Learner",
            launch_presentation_return_url='launch_presentation_return_url',
        )

        url = "/" + settings.SUBPATH + LTI_LAUNCH
        print("URL TO GIVE = url = ", url)
        response = self.client.post(url, data=data, **self._headers)
        print("RESPONSE = ", response)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(opentauser__lti_user_id="user_id").exists())
        user = User.objects.get(opentauser__lti_user_id="user_id")
        self.assertTrue(
            user.groups.filter(name="Student").exists(), msg="Created user is not in Student group"
        )

    @patch("opentalti.views.verify_request_common")
    def test_lti_first_launch_teacher(self, verify_request_common=None):
        course_other = create_course("other_course_name", datetime.time(0, 0, 0))
        course = create_course("course_name", datetime.time(0, 0, 0))
        course.registration_domains = "valid.ext"
        course.save()

        verify_request_common.return_value = True

        data = dict(
            lti_message_type="basic-lti-launch-request",
            lti_version="LTI-1p0",
            resource_link_id="0",
            custom_user_id="user_id",
            roles="Instructor",
            launch_presentation_return_url='launch_presentation_return_url',
        )

        url = "/" + settings.SUBPATH + LTI_LAUNCH
        response = self.client.post(url, data=data, **self._headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(opentauser__lti_user_id="user_id").exists())
        user = User.objects.get(opentauser__lti_user_id="user_id")
        self.assertTrue(
            user.groups.filter(name="Author").exists(), msg="Created user is not in Author group"
        )

    @patch("opentalti.views.verify_request_common")
    def test_lti_second_launch_student(self, verify_request_common=None):
        course_other = create_course("other_course_name", datetime.time(0, 0, 0))
        course = create_course("course_name", datetime.time(0, 0, 0))
        course.registration_domains = "valid.ext"
        course.save()

        verify_request_common.return_value = True

        data = dict(
            lti_message_type="basic-lti-launch-request",
            lti_version="LTI-1p0",
            resource_link_id="0",
            custom_user_id="user_id",
            roles="Learner",
            launch_presentation_return_url='launch_presentation_return_url',
        )

        url = "/" + settings.SUBPATH + LTI_LAUNCH
        _ = self.client.post(url, data=data, **self._headers)
        response = self.client.post(url, data=data, **self._headers)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertTrue("LTIException" not in str(response.content), msg=str(response.content))
