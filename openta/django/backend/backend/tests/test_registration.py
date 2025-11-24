# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import datetime
import logging
from django.core import mail
from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings

from users.models import OpenTAUser
from exercises.tests.test_utils import create_course

logger = logging.getLogger(__name__)


class TestRegistration(TestCase):
    """Test user registration."""

    def test_register_domain_valid(self):
        course_other = create_course("other_course_name", datetime.time(0, 0, 0))
        course = create_course("course_name", datetime.time(0, 0, 0))
        course.registration_domains = "valid.ext"
        course.save()
        registration_data = dict(email="user@valid.ext")
        response = self.client.post(
            "/" + settings.SUBPATH + "register_by_domain/{course_pk}/".format(course_pk=course.pk),
            data=registration_data,
        )
        print(f" DOMAIN VALID {OpenTAUser.objects.all()}")
        self.assertEqual(OpenTAUser.objects.all().count(), 2)
        user = OpenTAUser.objects.first()
        self.assertIn(course, user.courses.all())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("course_name", mail.outbox[0].subject)

    def test_register_domain_invalid(self):
        course = create_course("course_name", datetime.time(0, 0, 0))
        course.registration_domains = "valid.ext"
        course.save()
        registration_data = dict(email="user@invalid.ext")
        response = self.client.post(
            "/" + settings.SUBPATH + "register_by_domain/{course_pk}/".format(course_pk=course.pk),
            data=registration_data,
        )
        print(f" DOMAIN IN_VALID {OpenTAUser.objects.all()}")
        self.assertEqual(OpenTAUser.objects.all().count(), 1)
        self.assertTrue("uk-alert-danger" in str(response.content))

    def test_register_domain_existing_user(self):
        course = create_course("course_name", datetime.time(0, 0, 0))
        course.registration_domains = "valid.ext"
        course.save()
        user = User.objects.create(username="user@valid.ext", email="user@valid.ext", password="pw")
        openta_user, _ = OpenTAUser.objects.get_or_create(user=user)
        registration_data = dict(email="user@valid.ext")
        response = self.client.post(
            "/" + settings.SUBPATH + "register_by_domain/{course_pk}/".format(course_pk=course.pk),
            data=registration_data,
        )
        logger.debug("response: %s", response.content)
        print(f" EXISTING_USER  {OpenTAUser.objects.all()}")
        self.assertEqual(OpenTAUser.objects.all().count(), 2)
        user = OpenTAUser.objects.first()
        self.assertIn(course, user.courses.all())
