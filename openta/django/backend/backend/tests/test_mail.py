# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import datetime
from django.test import TestCase
from django.core import mail

from exercises.tests.test_utils import create_course
from backend.user_utilities import send_activation_mail


class TestMail(TestCase):
    """Test mail functionality"""

    databases = "__all__"

    def test_activation_mail(self):
        course = create_course("course_name", datetime.time(0, 0, 0))
        send_activation_mail(course, "username", "user@domain.com")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("course_name", mail.outbox[0].subject)
