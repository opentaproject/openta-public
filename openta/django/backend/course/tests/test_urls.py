# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from enum import Enum
import json
import logging
import pathlib
from typing import Any, Optional

from _pytest.fixtures import FixtureRequest
from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.client import Client
import pytest
from rest_framework import status

from course.models import Course
from tests.factory import Factory

from .conftest import CourseJSONComparator, CourseStudentJSONComparator

logger = logging.getLogger(__name__)


class UserType(Enum):
    superuser = 1
    admin = 2
    student = 3


class BaseTestURLs:
    """Tests base class"""

    pytestmark = pytest.mark.django_db
    user_type: UserType

    @pytest.fixture(autouse=True)
    def user(self, client: Client, factory: Factory) -> User:
        is_superuser = self.user_type == UserType.superuser
        is_staff = self.user_type == UserType.admin

        user = factory.create(User, is_superuser=is_superuser, is_staff=is_staff)

        if is_staff:
            perm_edit_exercise = Permission.objects.get(codename="edit_exercise")
            group = factory.create(Group, name="Author")
            group.permissions.add(perm_edit_exercise)
            group.user_set.add(user)
            group.save()

        client.force_login(user)
        return user

    # url(r'^course/(?P<course_pk>[0-9]+)/pages/(?P<path>.+)/$', get_pages),
    def test_get_pages(self, client: Client, factory: Factory) -> None:
        course = factory.create(Course, published=True)
        d = pathlib.Path(".") / course.get_pages_path()
        d.mkdir(parents=True, exist_ok=True)
        content = "<html><h1> hello from pytest</h1></html>"
        p = d / "index.html"
        p.write_text(content)
        assert p.read_text() == content
        url = f"/course/{course.pk}/pages/index.html"
        r = client.get(url)
        assert r.status_code == 200
        stream = b"".join(r.streaming_content)
        assert b"hello from pytest" in stream


class CourseUpdateTests:
    """Tests for updating the course view"""

    @pytest.mark.xfail(reason="course_update is not done ")
    def test_course_update(self, client: Client, factory: Factory):
        course = factory.create(Course, published=True)
        url = f"/course/{course.pk}/updateoptions/"
        r = client.get(url)
        logger.debug(json.dumps(r.json(), indent=2))
        # TODO: finish this test


class CanUploadTests:
    """Mixin clas for testing course file uploads"""

    # see https://miguendes.me/how-to-use-fixtures-as-arguments-in-pytestmarkparametrize

    @pytest.mark.parametrize(
        "url_suffix,file_buffer,reply_status,err_key",
        [
            ("uploadexercises", "zip_buffer_small", status.HTTP_200_OK, None),
            (
                "uploadexercises",
                "zip_buffer_large",
                status.HTTP_400_BAD_REQUEST,
                "file_size_limit",
            ),
            (
                "uploadexercises",
                "",
                status.HTTP_400_BAD_REQUEST,
                "file_content",
            ),
            (
                "uploadexercises",
                "text_buffer",
                status.HTTP_400_BAD_REQUEST,
                "file_format",
            ),
            ("uploadzip", "zip_buffer_small", status.HTTP_200_OK, None),
            (
                "uploadzip",
                "zip_buffer_large",
                status.HTTP_400_BAD_REQUEST,
                "file_size_limit",
            ),
            ("uploadzip", "", status.HTTP_400_BAD_REQUEST, "file_content"),
            (
                "uploadzip",
                "text_buffer",
                status.HTTP_400_BAD_REQUEST,
                "file_format",
            ),
        ],
    )
    def test_upload_file(
        self,
        url_suffix: str,
        file_buffer: str,
        reply_status: int,
        err_key: Optional[str],
        request: FixtureRequest,
    ) -> None:
        if self.user_type == UserType.student:
            pytest.skip("students cannot upload courses")

        client = request.getfixturevalue("client")
        factory = request.getfixturevalue("factory")
        faker = request.getfixturevalue("faker")

        if file_buffer:
            content = request.getfixturevalue(file_buffer).getvalue()
            file = SimpleUploadedFile(faker.file_name(extension="zip"), content=content)
            post_data = {"data": {}, "file": file}
        else:
            post_data = {"data": {}}

        course = factory.create(Course, published=True)
        url = f"/course/{course.pk}/{url_suffix}/"

        r = client.post(url, post_data, format="multipart")
        logger.debug(json.dumps(r.json(), indent=2))

        assert r.status_code == reply_status
        if err_key:
            assert err_key in r.json()


class TestURLsSuperuser(BaseTestURLs, CourseUpdateTests, CanUploadTests):
    """Test suite for superusers"""

    user_type = UserType.superuser

    def test_get_courses_not_published(self, client: Client, factory: Factory) -> None:
        """Course list returned by server should match the courses in the database."""

        course = factory.create(Course, published=False)

        r = client.get("/courses/")

        rjson = r.json()
        assert r.status_code == 200
        logger.debug(json.dumps(rjson, indent=2))
        assert len(rjson) == 1
        assert CourseJSONComparator(rjson[0]) == course

    def test_get_courses(self, client: Client, factory: Factory) -> None:
        """Course list returned by server should match the courses in the database."""

        def create_course(_: int):
            return factory.create(Course)

        courses = list(map(create_course, [1, 2]))

        r = client.get("/courses/")

        rjson = r.json()
        assert r.status_code == 200
        assert len(rjson) == len(courses)
        logger.debug(json.dumps(rjson, indent=2))

        def compare(j: dict[str, Any], c: Course) -> None:
            assert CourseJSONComparator(j) == c

        map(compare, zip(rjson, courses))

    def test_get_course(self, client: Client, factory: Factory) -> None:
        """Course returned by server should match the course in the database."""

        course = factory.create(Course)

        r = client.get(f"/course/{course.pk}/")

        rjson = r.json()
        assert r.status_code == 200
        assert CourseJSONComparator(rjson) == course


class TestURLsAdmin(BaseTestURLs, CanUploadTests):
    """Test suite for admin users"""

    user_type = UserType.admin

    def test_get_courses_not_assigned(self, client: Client, factory: Factory) -> None:
        """Course list returned by server should be empty if course is not assigned to user."""

        factory.create(Course, published=False)

        r = client.get("/courses/")

        rjson = r.json()
        assert r.status_code == 200
        assert len(rjson) == 0

    def test_get_courses_assigned(self, client: Client, factory: Factory) -> None:
        """Course list returned by server should not be empty if course if course assigned to user."""

        course = factory.create(Course, published=True)

        r = client.get("/courses/")

        rjson = r.json()
        assert r.status_code == 200
        logger.debug(json.dumps(rjson, indent=2))
        assert len(rjson) == 1
        assert CourseJSONComparator(rjson[0]) == course

    def test_get_course(self, client: Client, factory: Factory) -> None:
        """Course returned by server should match the course in the database."""

        course = factory.create(Course, published=False)
        r = client.get(f"/course/{course.pk}/")

        rjson = r.json()
        assert r.status_code == 200
        logger.debug(json.dumps(rjson, indent=2))
        assert CourseJSONComparator(rjson) == course

    @pytest.mark.parametrize(
        "url_suffix,file_buffer,reply_status,err_key",
        [
            ("uploadexercises", "zip_buffer_small", status.HTTP_403_FORBIDDEN, "exercise"),
            ("uploadzip", "zip_buffer_small", status.HTTP_403_FORBIDDEN, "exercise"),
        ],
    )
    def test_upload_file_no_permissions(
        self,
        url_suffix: str,
        file_buffer: str,
        reply_status: int,
        err_key: str,
        request: FixtureRequest,
    ) -> None:

        client = request.getfixturevalue("client")
        factory = request.getfixturevalue("factory")
        faker = request.getfixturevalue("faker")

        # first, remove the user from the group
        user = factory.default(User)
        group = factory.default(Group)
        group.user_set.remove(user)
        group.save()

        course = factory.create(Course, published=True)
        url = f"/course/{course.pk}/{url_suffix}/"
        content = request.getfixturevalue(file_buffer).getvalue()
        file = SimpleUploadedFile(faker.file_name(extension="zip"), content=content)
        post_data = {"data": {}, "file": file}

        r = client.post(url, post_data, format="multipart")
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == reply_status
        assert err_key in r.json()


class TestURLsStudent(BaseTestURLs):
    """Test suite for student users"""

    user_type = UserType.student

    def test_get_courses_non_published(self, client: Client, factory: Factory) -> None:
        """Course list returned by server should be empty if course is not published."""

        factory.create(Course, published=False)
        r = client.get("/courses/")

        rjson = r.json()
        assert r.status_code == 200
        assert len(rjson) == 0

    def test_get_courses_published(self, client: Client, factory: Factory) -> None:
        """Course list returned by server should not be empty if course is published."""

        course = factory.create(Course, published=True)

        r = client.get("/courses/")

        rjson = r.json()
        assert r.status_code == 200
        logger.debug(json.dumps(rjson, indent=2))
        assert len(rjson) == 1
        assert CourseStudentJSONComparator(rjson[0]) == course

    def test_get_course(self, client: Client, factory: Factory) -> None:
        """Course returned by server should match the course in the database."""

        course = factory.create(Course, published=True)
        url = f"/course/{course.pk}/"
        r = client.get(url)

        rjson = r.json()
        assert r.status_code == 200
        logger.debug(json.dumps(rjson, indent=2))
        assert CourseStudentJSONComparator(rjson) == course
