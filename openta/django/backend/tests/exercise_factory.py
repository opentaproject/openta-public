# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
import shutil

from django.conf import settings
from faker.proxy import Faker

from exercises.models import Exercise

from .abstract_entity_factory import AbstractEntityFactory
from .course_factory import CourseFactory

logger = logging.getLogger(__name__)


class ExerciseFactory(AbstractEntityFactory[Exercise]):
    """An object used in test suites used to create one or more Exercises.

    The model objects contain fake data that is populated using Faker.

    """

    __course_factory: CourseFactory

    def __init__(self, faker: Faker, course_factory: CourseFactory) -> None:
        super().__init__(faker)
        self.__course_factory = course_factory

    def __del__(self):
        site_path = f"{settings.VOLUME}/openta/exercises"
        shutil.rmtree(site_path, ignore_errors=True)

    def build(self, **kwargs: str) -> Exercise:
        name = self.faker.name()
        defaults = {
            "exercise_key": self.faker.uuid4(),
            "name": name,
            "translated_name": name,
            "path": self.faker.file_path(),
            "folder": self.faker.file_name(extension=""),
            "course": self.__course_factory.default,
            **kwargs,
        }
        exercise: Exercise = Exercise(**defaults)

        if exercise.course:
            exercise.course.save()

        self._default = exercise
        return exercise

    def create(self, **kwargs: str) -> Exercise:
        exercise = self.build(**kwargs)

        exercise.save()
        return exercise
