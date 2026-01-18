# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
from typing import Any, Type, TypeVar

from django.contrib.auth.models import Group, User
from django.db.models.base import Model
from faker.proxy import Faker

from course.models import Course
from exercises.models import Exercise
from tests.abstract_entity_factory import AbstractEntityFactory
from tests.course_factory import CourseFactory
from translations.models import Translation
from users.models import OpenTAUser

from .openta_user_factory import OpenTAUserFactory
from .user_factory import UserFactory
from .group_factory import GroupFactory
from .translation_factory import TranslationFactory
from .exercise_factory import ExerciseFactory

logger = logging.getLogger(__name__)

T = TypeVar("T")
M = TypeVar("M", bound=Model, covariant=True)


class Factory:
    """Parent factory that creates all entity factories."""

    __faker: Faker
    __factories: dict[str, AbstractEntityFactory[T]]

    def __init__(self):
        self.__faker = Faker()
        self.__factories = {}

        openta_user_factory = OpenTAUserFactory(self.__faker)
        user_factory = UserFactory(self.__faker, openta_user_factory)
        group_factory = GroupFactory(self.__faker)
        course_factory = CourseFactory(self.__faker, user_factory)
        exercise_factory = ExerciseFactory(self.__faker, course_factory)
        translation_factory = TranslationFactory(self.__faker, exercise_factory)

        self.__factories[User] = user_factory
        self.__factories[Group] = group_factory
        self.__factories[OpenTAUser] = openta_user_factory
        self.__factories[Course] = course_factory
        self.__factories[Exercise] = exercise_factory
        self.__factories[Translation] = translation_factory

    def build(self, klass: Type[T], **kwargs: str) -> T:
        """Build an entity of type klass."""
        sub_factory = self.__sub_factory(klass)
        return sub_factory.build(**kwargs)

    def create(self, klass: Type[M], **kwargs: Any) -> M:
        """Save an entity of type klass to the database.

        Klass must be derived from a Django model."""
        sub_factory = self.__sub_factory(klass)
        return sub_factory.create(**kwargs)

    def default(self, klass: Type[T]) -> T:
        """Return the last created entity of type klass."""
        sub_factory = self.__sub_factory(klass)
        return sub_factory.default

    def __sub_factory(self, klass: Type[T]) -> AbstractEntityFactory[T]:
        if klass not in self.__factories:
            raise KeyError(f"factory does not exist for entity type: {klass}")
        return self.__factories[klass]
