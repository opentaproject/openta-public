# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import json
import logging
from lxml import etree
import pytest

from django.contrib.auth.models import Group, Permission, User
from django.test.client import Client
from faker.proxy import Faker
from pytest_mock import MockerFixture

from course.models import Course
from exercises.models import Exercise
from tests.factory import Factory
from translations.models import Translation
from backend.xmltools import string_to_xml

logger = logging.getLogger(__name__)


@pytest.fixture()
def default_user(client: Client, factory: Factory) -> User:
    user = factory.create(User, is_superuser=False, is_staff=False)
    client.force_login(user)
    return user


@pytest.fixture()
def permitted_user(client: Client, factory: Factory) -> User:
    user = factory.create(User, is_superuser=False, is_staff=False)
    user.is_staff = True

    perm_edit_exercise = Permission.objects.get(codename="edit_exercise")
    group = factory.create(Group, name="Author")
    group.permissions.add(perm_edit_exercise)
    group.user_set.add(user)
    group.save()

    client.force_login(user)
    return user


@pytest.fixture()
def lang_code(faker: Faker) -> str:
    return faker.language_code()


def ex_xml(name: str) -> str:
    """Generates simple XML for an exercise with a name and no translations."""
    exercise = etree.Element("exercise")
    exercisename = etree.Element("exercisename")
    exercisename.text = name
    exercise.append(exercisename)
    return etree.tostring(exercise).decode("utf-8")


def ex_xml_translated(name: str, lang_codes: list[str]) -> str:
    """Generates simple XML for an exercise with a name and with 'lang_code' number of translations."""
    exercise = etree.Element("exercise")
    exercisename = etree.Element("exercisename")
    exercisename.text = name
    exercise.append(exercisename)

    for idx, lang_code in enumerate(lang_codes):
        alt = etree.Element("alt", lang=lang_code)
        alt.text = f"{name} ({lang_code})"
        exercisename.append(alt)

    return etree.tostring(exercise).decode("utf-8")


class TestNotifyMissingString:

    pytestmark = pytest.mark.django_db

    def base_url(self, course: Course, lang_code: str) -> str:
        return f"/course/{course.pk}/notifymissingstring/{lang_code}"

    @pytest.fixture(autouse=True)
    def user(self, default_user: User) -> User:
        return default_user

    @pytest.mark.xfail(reason="should return HTTP 201")
    def test_course(self, client: Client, factory: Factory, faker: Faker, lang_code: str, mocker: MockerFixture):
        # mock is declared for where function is used
        mocked_fn = mocker.patch("translations.views.auto_translate_strings", return_value=faker.sentence())

        course = factory.create(Course, published=True, use_auto_translation=True, languages=lang_code)
        data = {"string_": faker.sentence(), "altkey": faker.sentence()}
        r = client.post(self.base_url(course, lang_code), data)
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 201
        mocked_fn.assert_called

    @pytest.mark.xfail(reason="should return HTTP 404: course not in database")
    def test_no_course(self, client: Client, faker: Faker, lang_code: str):
        """Test for when course is not in the database"""
        data = {"string_": faker.sentence(), "altkey": faker.sentence()}
        url = f"/course/1/notifymissingstring/{lang_code}"
        r = client.post(url, data)
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 404

    @pytest.mark.xfail(reason="should return HTTP 400: invalid data in request")
    def test_string_not_given(self, client: Client, factory: Factory, faker: Faker, lang_code: str):
        """Test for when the string is missing the request"""
        course = factory.create(Course, published=True)
        r = client.post(self.base_url(course, lang_code))
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 400
        assert "string_" in r.json().keys()

    @pytest.mark.xfail(reason="should return HTTP 400: invalid data in request")
    def test_altkey_not_given(self, client: Client, factory: Factory, faker: Faker, lang_code: str):
        """Test for when the altkey is missing the request"""
        course = factory.create(Course, published=True)
        data = {"string_": faker.sentence()}
        r = client.post(self.base_url(course, lang_code), data)
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 400
        assert "altkey" in r.json().keys()

    @pytest.mark.skip(reason="cannot send byte in 'string_' parameter")
    def test_string_as_bytes(self, client: Client, factory: Factory, faker: Faker, lang_code: str):
        """Test for when the altkey is missing the request"""
        course = factory.create(Course, published=True)
        data = {"string_": faker.binary(length=10), "altkey": faker.sentence()}
        r = client.post(self.base_url(course, lang_code), data)
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 200

    @pytest.mark.xfail(reason="should return HTTP 400: use_auto_translation is False")
    def test_course_not_auto_translate(self, client: Client, factory: Factory, faker: Faker, lang_code: str):
        course = factory.create(Course, published=True, use_auto_translation=False)
        data = {"string_": faker.sentence(), "altkey": faker.sentence()}
        r = client.post(self.base_url(course, lang_code), data)
        assert r.status_code == 400
        logger.debug(json.dumps(r.json(), indent=2))
        assert "course.use_auto_translation" in r.json().keys()

    @pytest.mark.xfail(reason="should return HTTP 400: no languages assigned")
    def test_course_languges(self, client: Client, factory: Factory, faker: Faker, lang_code: str):
        course = factory.create(Course, published=True, use_auto_translation=True)
        data = {"string_": faker.sentence(), "altkey": faker.sentence()}
        r = client.post(self.base_url(course, lang_code), data)
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 400
        assert "course.languages" in r.json().keys()


class TestTranslationDict:

    pytestmark = pytest.mark.django_db

    @pytest.fixture(autouse=True)
    def user(self, default_user: User) -> User:
        return default_user

    def base_url(self, course: Course, lang_code: str) -> str:
        return f"/course/{course.pk}/translationdict/{lang_code}"

    @pytest.mark.xfail(reason="JSON response could contain these keys: altkey, translated_text")
    def test_translation(self, client: Client, factory: Factory, lang_code: str):
        """Test for when course is not in the database"""
        course = factory.create(Course, published=True, use_auto_translation=True)
        translation = factory.create(Translation, exercise=None, language=lang_code)
        r = client.post(self.base_url(course, lang_code))
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 200

        rjson = r.json()
        assert len(rjson) == 1
        assert rjson[0]["altkey"] == translation.altkey
        assert rjson[0]["translated_text"] == translation.translated_text

    @pytest.mark.xfail(reason="should return HTTP 404: course not in database")
    def test_no_course(self, client: Client, lang_code: str):
        """Test for when course is not in the database"""
        r = client.post(f"/course/1/translationdict/{lang_code}")
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 404
        assert "course" in r.json().keys()

    @pytest.mark.xfail(reason="should return HTTP 404: translation not found")
    def test_no_translation(self, client: Client, factory: Factory, lang_code: str):
        """Test for when course is not in the database"""
        course = factory.create(Course, published=True, use_auto_translation=True)
        r = client.post(self.base_url(course, lang_code))
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 404
        assert "translations" in r.json().keys()


class TranslateCommon:
    """Common test cases for url path 'exercise/__pk__/__action__/__lang_code__'"""

    pytestmark = pytest.mark.django_db

    _url_subpath: str

    def base_url(self, exercise: Exercise, lang_code: str) -> str:
        url = f"/exercise/{exercise.pk}/{self._url_subpath}/{lang_code}"
        logger.debug(f"{url=}")
        return url

    @pytest.fixture(autouse=True)
    def user(self, permitted_user: User) -> User:
        return permitted_user

    @pytest.mark.xfail(reason="should return HTTP 400: invalid data in request")
    def test_xml_not_given(self, client: Client, factory: Factory, lang_code: str):
        """Test for when the 'xml' is missing the request"""
        lang_code = "es"
        exercise = factory.create(Exercise)
        r = client.post(self.base_url(exercise, lang_code), {})
        assert r.status_code == 400
        logger.debug(json.dumps(r.json(), indent=2))
        assert "xml" in r.json().keys()

    @pytest.mark.xfail(reason="should return HTTP 404: exercise not in database")
    def test_no_exercise(self, client: Client, faker: Faker, lang_code: str):
        data = {"xml": faker.word()}
        r = client.post(f"/exercise/1/changedefaultlanguage/{lang_code}", data)
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 404
        assert "exercise" in r.json().keys()

    @pytest.mark.xfail(reason="should return HTTP 404: translations not enabled course")
    def test_course_no_auto_translation(self, client: Client, factory: Factory, faker: Faker, lang_code: str):
        factory.create(Course, use_auto_translation=False)
        exercise = factory.create(Exercise)

        data = {"xml": faker.word()}
        r = client.post(self.base_url(exercise, lang_code), data)
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 404
        assert "course" in r.json().keys()

    @pytest.mark.xfail(reason="should return HTTP 500: the exercise's XML file was not found")
    def test_ex_open_error(self, client: Client, factory: Factory, faker: Faker, mocker: MockerFixture):
        """The exercise's XML file could not be opened"""
        # mock is declared for where function is used
        mocked_fn = mocker.patch("translations.views.exercise_xml", side_effect=FileNotFoundError)
        lang_code = "es"

        factory.create(Course, use_auto_translation=True)
        exercise = factory.create(Exercise)

        translation = faker.sentence()
        data = {"xml": ex_xml_translated(name=translation, lang_codes=[lang_code])}
        r = client.post(self.base_url(exercise, lang_code), data)
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 500
        mocked_fn.assert_called

    @pytest.mark.xfail(reason="should return HTTP 500: the exercise's files could not be backed up")
    def test_ex_backup_error(self, client: Client, factory: Factory, faker: Faker, mocker: MockerFixture):
        """The exercise's files could not be backed up"""
        read_mocked_fn = mocker.patch("translations.views.exercise_xml", return_value="")
        backup_mocked_fn = mocker.patch("translations.views.exercise_save", side_effect=FileNotFoundError)
        lang_code = "es"

        factory.create(Course, use_auto_translation=True)
        exercise = factory.create(Exercise)

        translation = faker.sentence()
        data = {"xml": ex_xml_translated(name=translation, lang_codes=[lang_code])}
        r = client.post(self.base_url(exercise, lang_code), data)
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 500
        read_mocked_fn.assert_called
        backup_mocked_fn.assert_called


class TestChangeDefaultLanguage(TranslateCommon):
    """Tests for url path 'exercise/__pk__/changedefaultlanguage/__lang_code__'"""

    _url_subpath = "changedefaultlanguage"

    def base_url(self, exercise: Exercise, lang_code: str) -> str:
        return f"/exercise/{exercise.pk}/changedefaultlanguage/{lang_code}"

    def test_translate(self, client: Client, factory: Factory, faker: Faker, mocker: MockerFixture):
        # mock is declared for where function is used
        mocked_fn = mocker.patch("translations.views.exercise_xml", return_value="")
        lang_code = "es"

        factory.create(Course, use_auto_translation=True)
        exercise = factory.create(Exercise)

        translation = faker.sentence()
        data = {"xml": ex_xml_translated(name=translation, lang_codes=[lang_code])}
        r = client.post(self.base_url(exercise, lang_code), data)
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 200
        mocked_fn.assert_called
        assert "success" in r.json().keys()

        # check the exercise's XML file for the new translation
        fname = exercise.get_full_path() + "/exercise.xml"
        parser = etree.XMLParser(ns_clean=True)
        tree = etree.parse(fname, parser)
        ex_xml = tree.find("exercisename")
        assert "translation example" not in ex_xml.text


class TestRemoveTranslation(TranslateCommon):
    """Tests for url path 'exercise/__pk__/remove/__lang_code__'"""

    _url_subpath = "remove"

    def test_remove(self, client: Client, factory: Factory, faker: Faker, mocker: MockerFixture):
        # mock is declared for where function is used
        mocked_fn = mocker.patch("translations.views.exercise_xml", return_value="")
        lang_code = "es"

        factory.create(Course, use_auto_translation=True)
        exercise = factory.create(Exercise)

        translation = faker.sentence()
        data = {"xml": ex_xml_translated(name=translation, lang_codes=[lang_code])}
        r = client.post(self.base_url(exercise, lang_code), data)
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 200
        mocked_fn.assert_called
        assert "success" in r.json().keys()

        fname = exercise.get_full_path() + "/exercise.xml"
        with open(fname) as f:
            contents = f.read()
            logger.debug(f"{contents=}")
            assert "<alt>" not in contents


class TestViewTranslation(TranslateCommon):
    """Tests for url path 'exercise/__pk__/views/__lang_code__'"""

    _url_subpath = "views"

    @pytest.mark.xfail(reason="getting a 400 reply")
    def test_view(self, client: Client, factory: Factory, faker: Faker, mocker: MockerFixture):
        # mock is declared for where function is used
        mocker.patch("translations.views.exercise_xml", return_value="")
        lang_code = "es"

        factory.create(Course, use_auto_translation=True)
        exercise = factory.create(Exercise)

        translation = faker.sentence()
        data = {"xml": ex_xml_translated(name=translation, lang_codes=[lang_code])}
        r = client.post(self.base_url(exercise, lang_code), data)
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 200


class TestTranslate(TranslateCommon):
    """Tests for url path 'exercise/__pk__/translate/__lang_code__'"""

    _url_subpath = "translate"

    def test_translation_not_in_db(self, client: Client, factory: Factory, faker: Faker, mocker: MockerFixture):
        lang_code = "es"
        source = faker.sentence()
        source_tr = source.upper()

        # mock is declared for where function is used
        google_mock = mocker.patch("translations.views.auto_translate_strings", return_value=[source_tr])
        ex_xml_mock = mocker.patch("translations.views.exercise_xml", return_value="")

        factory.create(Course, use_auto_translation=True)
        exercise = factory.create(Exercise)

        data = {"xml": ex_xml(source)}
        r = client.post(self.base_url(exercise, lang_code), data)
        assert r.status_code == 200
        logger.debug(json.dumps(r.json(), indent=2))

        google_mock.assert_called
        ex_xml_mock.assert_called

        fname = exercise.get_full_path() + "/exercise.xml"
        with open(fname) as f:
            contents = f.read()
            logger.debug(f"{contents=}")
            assert source_tr in contents

    def notest_translation_in_db(self, client: Client, factory: Factory, faker: Faker, mocker: MockerFixture):
        lang_code = "es"
        source = faker.sentence()
        source_tr = source.upper() + f"({lang_code})"

        # mock is declared for where function is used
        google_mock = mocker.patch("translations.views.auto_translate_strings", return_value=[source_tr])
        ex_xml_mock = mocker.patch("translations.views.exercise_xml", return_value="")

        factory.create(Course, use_auto_translation=True)
        exercise = factory.create(Exercise)
        xml = ex_xml(source)
        elem = string_to_xml(xml).find("exercisename")
        assert elem is not None
        tr = factory.create(
            Translation,
            language=lang_code,
            exercise=exercise,
            original_text=source,
            translated_text=source,
        )

        data = {"xml": xml}
        r = client.post(self.base_url(exercise, lang_code), data)
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 200

        google_mock.assert_called
        ex_xml_mock.assert_called

        tr.refresh_from_db()
        assert tr.translated_text == source_tr

        fname = exercise.get_full_path() + "/exercise.xml"
        with open(fname) as f:
            contents = f.read()
            logger.debug(f"{contents=}")
            assert source_tr in contents

    def test_translation_in_db_with_others(self, client: Client, factory: Factory, faker: Faker, mocker: MockerFixture):
        current_lang_codes = ["en", "fr"]
        lang_code = "es"
        source = faker.sentence()
        source_tr = source.upper()

        # mock is declared for where function is used
        google_mock = mocker.patch("translations.views.auto_translate_strings", return_value=[source_tr])
        ex_xml_mock = mocker.patch("translations.views.exercise_xml", return_value="")

        factory.create(Course, use_auto_translation=True)
        exercise = factory.create(Exercise)

        for idx, lang in enumerate(current_lang_codes):
            factory.create(
                Translation,
                language=lang,
                exercise=None,
                original_text=source,
                translated_text=source,
            )

        data = {"xml": ex_xml_translated(source, lang_codes=current_lang_codes)}
        r = client.post(self.base_url(exercise, lang_code), data)
        logger.debug(json.dumps(r.json(), indent=2))
        assert r.status_code == 200

        google_mock.assert_called
        ex_xml_mock.assert_called

        fname = exercise.get_full_path() + "/exercise.xml"
        with open(fname) as f:
            contents = f.read()
            logger.debug(f"{contents=}")
            assert source_tr in contents
