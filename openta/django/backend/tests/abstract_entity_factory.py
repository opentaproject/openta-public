# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from typing import Any, Generic, Optional, TypeVar
import logging
from django.db.models.base import Model
from faker import Faker

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AbstractEntityFactory(Generic[T]):
    """An abstract base class for entity factories.

    An entity can be a Django model or any other data class.

    """

    __faker: Faker
    _default: Optional[T]

    def __init__(self, faker: Faker) -> None:
        self.__faker = faker
        self._default = None

    @property
    def faker(self):
        return self.__faker

    def build(self, **kwargs: str) -> T:
        """Builds a model object"""

    def create(self, **kwargs: str) -> T:
        """If the entity is a Django model, the entity is buildt and saved to the database.

        Do not override this method if the entity is not a Django model.
        """
        raise TypeError("This entity does not support saving to the database.")

    @property
    def default(self) -> T:
        """Return the last built / created entity."""
        if not self._default:
            self._default = self.build()
        return self._default
