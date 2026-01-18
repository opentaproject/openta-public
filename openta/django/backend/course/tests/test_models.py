# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
import pytest
from datetime import time, tzinfo
import datetime

from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import ValidationError
from faker.proxy import Faker
from pytest_django.fixtures import SettingsWrapper

from tests.factory import Factory
from course.models import Course, pytztimezone, tzlocalize

logger = logging.getLogger(__name__)


# FIXME: saving a course behaves differently based on settings.MULTICOURSE
# FIXME: saving a course when settings.MULTICOURSE is true, checks for a file in the file system
# FIXME: saving a course creates groups
# FIXME: saving a course may create a user named "student"


@pytest.fixture(autouse=True)
def user(factory: Factory) -> User:
    return factory.create(User, username="student")


class BaseTestModels:
    """Base class for tests for the Course model."""

    pytestmark = pytest.mark.django_db

    def test_creates_default_user(self, factory: Factory, user: User) -> None:
        """Creates a course and checks that a user named 'student' is created"""
        user.opentauser.delete()
        user.delete()

        course = factory.create(Course)

        user = User.objects.filter(username="student").first()
        assert user != None
        assert user.opentauser != None
        assert course in user.opentauser.courses.all()

    def test_save_anonymous_student(self, factory: Factory) -> None:
        # when there are no groups
        course = factory.create(Course, allow_anonymous_student=True)
        assert course.allow_anonymous_student

        group = Group.objects.filter(name="AnonymousStudent").first()
        assert group != None

        permission_ids = list(Permission.objects.filter(codename="log_question").values_list("pk", flat=True))
        group_permission_ids = list(group.permissions.values_list("pk", flat=True))

        assert group_permission_ids == permission_ids

    def test_save_anonymous_student_not_allowed(self, factory: Factory) -> None:
        course = factory.create(Course, allow_anonymous_student=False)
        assert not course.allow_anonymous_student

        group = Group.objects.filter(name="AnonymousStudent").first()
        assert group == None

    def test_clean_google_auth_invalid(self, factory: Factory) -> None:
        settings.VALIDATE_GOOGLE_AUTH_STRING = True
        course = factory.build(Course, use_auto_translation=True, google_auth_string="")

        with pytest.raises(ValidationError):
            course.clean()

    def test_clean_translation_no_lang(self, factory: Factory) -> None:
        course = factory.build(Course, use_auto_translation=True, languages="")

        with pytest.raises(ValidationError):
            course.clean()

    def test_pages_path(self, factory: Factory) -> None:
        course = factory.create(Course)
        coursekey = str(course.course_key)
        expected = f"{settings.VOLUME}/{course.opentasite}/pages/{coursekey}"
        assert course.get_pages_path() == expected

    def test_student_answr_images_path(self, factory: Factory) -> None:
        course = factory.create(Course)
        expected = f"{settings.VOLUME}/openta/media/answerimages/{course.get_exercises_folder()}"
        assert course.get_student_answerimages_path() == expected

    def test_exercise_folder(self, factory: Factory) -> None:
        course = factory.create(Course)
        assert course.get_exercises_folder() == str(course.course_key)

    def test_registration_domains_none(self, factory: Factory, faker: Faker) -> None:
        course = factory.create(Course, registration_domains=None)
        assert course.registration_domains == None
        assert course.get_registration_domains() == None

    def test_registration_domains(self, factory: Factory, faker: Faker) -> None:
        hostnames: list[str] = [faker.hostname() for _ in range(2)]
        hostnames_as_str = ",".join(hostnames)
        course = factory.create(Course, registration_domains=hostnames_as_str)

        assert course.registration_domains == hostnames_as_str
        assert course.get_registration_domains() != None
        assert course.get_registration_domains() == hostnames

    def test_deadline_time_none(self, factory: Factory) -> None:
        dt = datetime.time(hour=23, minute=59, second=0, tzinfo=pytztimezone(settings.TIME_ZONE))
        course = factory.create(Course)
        assert course.get_deadline_time() == dt

    def test_deadline_time(self, factory: Factory) -> None:
        dt = datetime.datetime.now()
        course = factory.create(Course, deadline_time=dt)
        assert course.get_deadline_time() == dt

    def test_language_none(self, factory: Factory) -> None:
        course: Course = factory.create(Course)
        assert course.get_languages() == None

    def test_language(self, factory: Factory, faker: Faker) -> None:
        langs: list[str] = [faker.language_code() for _ in range(2)]
        langs_as_str: str = ",".join(langs)
        course = factory.create(Course, languages=langs_as_str)

        assert course.get_languages() == langs


class TestModelsMulticourse(BaseTestModels):
    """Tests for the Course model when settings.MULTICOUSE is True."""

    @pytest.fixture(autouse=True)
    def settings_non_multicourse(self, settings: SettingsWrapper) -> None:
        settings.MULTICOURSE = True

    def test_save(self, factory: Factory) -> None:
        if 'opentasites' in settings.INSTALLED_APPS :
            from opentasites.models import OpenTASite
            course = factory.create(Course)
            site = OpenTASite.objects.filter(subdomain=course.opentasite).first()
            assert site != None

    def test_exercise(self, factory: Factory) -> None:
        course = factory.create(Course)
        expected = f"{settings.VOLUME}/{course.opentasite}/exercises/{course.get_exercises_folder()}"
        assert course.get_exercises_path() == expected


class TestModelsNonMulticourse(BaseTestModels):
    """Tests for the Course model when settings.MULTICOUSE is False."""

    @pytest.fixture(autouse=True)
    def settings_non_multicourse(self, settings: SettingsWrapper, user: User) -> None:
        settings.MULTICOURSE = False

    def test_save(self, factory: Factory) -> None:

        course = factory.create(Course)
        if 'opentasites' in settings.INSTALLED_APPS :
            from opentasites.models import OpenTASite
            site = OpenTASite.objects.filter(subdomain=course.opentasite).first()
            assert site == None

    def test_exercise_path(self, factory: Factory) -> None:
        course = factory.create(Course)
        expected = f"{settings.VOLUME}/openta/exercises/{course.get_exercises_folder()}"
        assert course.get_exercises_path() == expected
