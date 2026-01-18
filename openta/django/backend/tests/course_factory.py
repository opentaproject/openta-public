# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
import os
import shutil

from django.conf import settings
from faker.proxy import Faker

from course.models import Course
from tests.user_factory import UserFactory

from .abstract_entity_factory import AbstractEntityFactory

logger = logging.getLogger(__name__)


class CourseFactory(AbstractEntityFactory[Course]):
    """An object used in test suites used to create one or more Courses.

    Note: if the course is set to published, then it gets added to the default user's profile.

    The model objects contain fake data that is populated using Faker.

    """

    __site: str
    __user_factory: UserFactory

    def __init__(self, faker: Faker, user_factory: UserFactory) -> None:
        super().__init__(faker)
        self.__user_factory = user_factory
        self.__site = self.faker.unique.word()
        self.__create_subdomain()

    def __del__(self):
        site_path = f"{settings.VOLUME}/{self.__site}"
        shutil.rmtree(site_path, ignore_errors=True)

    def build(self, **kwargs: str) -> Course:
        defaults = {
            "opentasite": self.__site,
            "course_name": self.faker.name(),
            "motd": self.faker.paragraph(),
            "course_long_name": self.faker.paragraph(),
            **kwargs,
        }
        course: Course = Course(**defaults)

        self._default = course
        return course

    def create(self, **kwargs: str) -> Course:
        course = self.build(**kwargs)
        course.save()

        if course.published:
            user = self.__user_factory.default
            user.opentauser.courses.add(course)
            user.opentauser.save()

        return course

    def __create_subdomain(self):
        site_path = f"{settings.VOLUME}/{self.__site}"
        # delete the path if it already exist
        shutil.rmtree(site_path, ignore_errors=True)
        os.mkdir(site_path)
        f = open(f"{settings.VOLUME}/{self.__site}/dbname.txt", "w")
        f.write(self.faker.word())
        f.close()
        logger.debug("created subdomain: %s", site_path)
