# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging

from django.contrib.auth.models import Group
from faker.proxy import Faker

from .abstract_entity_factory import AbstractEntityFactory

logger = logging.getLogger(__name__)


class GroupFactory(AbstractEntityFactory[Group]):
    """A factory used in test suites to aid in creating one or more Groups.

    The model objects contain fake data that is populated using Faker.

    """

    def __init__(self, faker: Faker) -> None:
        super().__init__(faker)

    def build(self, **kwargs: str) -> Group:
        profile = self.faker.simple_profile()
        defaults = {"name": profile["username"], **kwargs}
        group = Group(**defaults)
        self._default = group

        return group

    def create(self, **kwargs: str) -> Group:
        group = self.build(**kwargs)
        group.save()
        return group
