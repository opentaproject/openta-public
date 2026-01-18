# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging

from django.contrib.auth.models import User
from faker.proxy import Faker

from .abstract_entity_factory import AbstractEntityFactory
from .openta_user_factory import OpenTAUserFactory

logger = logging.getLogger(__name__)


class UserFactory(AbstractEntityFactory[User]):
    """An object used in test suites used to create one or more Users.

    The model objects contain fake data that is populated using Faker.

    """

    __openta_user_factory: OpenTAUserFactory

    def __init__(self, faker: Faker, openta_user_factory: OpenTAUserFactory) -> None:
        super().__init__(faker)
        self.__openta_user_factory = openta_user_factory

    def build(self, **kwargs: str) -> User:
        profile = self.faker.simple_profile()
        defaults = {
            "username": profile["username"],
            "first_name": self.faker.first_name(),
            "last_name": self.faker.last_name(),
            "email": self.faker.email(),
            **kwargs,
        }
        user = User(**defaults)
        self._default = user

        openta_user = self.__openta_user_factory.default
        openta_user.user = user
        return user

    def create(self, **kwargs: str) -> User:
        user = self.build(**kwargs)
        user.save()
        user.opentauser.save()
        return user
