# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging

from faker.proxy import Faker

from translations.models import Translation

from .abstract_entity_factory import AbstractEntityFactory
from .exercise_factory import ExerciseFactory

logger = logging.getLogger(__name__)


class TranslationFactory(AbstractEntityFactory[Translation]):
    """An object used in test suites used to create one or more Translations.

    The model objects contain fake data that is populated using Faker.

    """

    __exercise_factory: ExerciseFactory

    def __init__(self, faker: Faker, exercise_factory: ExerciseFactory) -> None:
        super().__init__(faker)
        self.__exercise_factory = exercise_factory

    def build(self, **kwargs: str) -> Translation:
        default_text = self.faker.sentence()
        defaults = {
            "altkey": self.faker.uuid4(),
            "language": self.faker.language_code(),
            "translated_text": default_text,
            "original_text": default_text,
            "exercise": self.__exercise_factory.default,
            **kwargs,
        }
        translation: Translation = Translation(**defaults)

        if translation.exercise:
            translation.exercise.save()

        self._default = translation
        return translation

    def create(self, **kwargs: str) -> Translation:
        translation = self.build(**kwargs)
        translation.save()
        return translation
