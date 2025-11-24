# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from faker.proxy import Faker
import pytest
from exercises.models import Exercise
from exercises.parsing import exercise_add

from tests.factory import Factory
from translations.models import Translation


class TestModels:

    pytestmark = pytest.mark.django_db

    def test_truncated(self, factory: Factory, faker: Faker) -> None:
        text = faker.paragraph(nb_sentences=10)
        translation = factory.create(Translation, translated_text=text)
        assert len(translation.translated_text) > 25
        assert translation.truncated_translation() == text[0:15] + "..." + text[-10:-1]

    def test_truncated_less_than_25(self, factory: Factory, faker: Faker) -> None:
        text = faker.word()
        translation = factory.create(Translation, translated_text=text)
        assert len(translation.translated_text) <= 25
        assert translation.truncated_translation() == text

    def test_has_exercise(self, factory: Factory, faker: Faker) -> None:
        exercise = factory.create(Exercise)
        translation = factory.create(Translation, exercise=exercise)
        assert translation.exercise_name() == exercise.name

    def test_no_exercise(self, factory: Factory, faker: Faker) -> None:
        translation = factory.create(Translation, exercise=None)
        assert translation.exercise_name() == "--"
