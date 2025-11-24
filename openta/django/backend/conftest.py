# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
Configuration used by all Pytest tests.
"""

import io
import logging
import os
import random
import pytest
import zipfile
from typing import Any

from faker.proxy import Faker
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete, m2m_changed
from django.core.files.base import File
from django.core.files.uploadedfile import SimpleUploadedFile
from pytest_mock import MockerFixture

from tests.factory import Factory

logger = logging.getLogger(__name__)

# see: https://www.python.org/dev/peps/pep-0524/
def best_effort_rng(size: int) -> bytes:
    # getrandom() is only available on Linux and Solaris
    if not hasattr(os, "getrandom"):
        return os.urandom(size)

    result = bytearray()
    try:
        # need a loop because getrandom() can return less bytes than
        # requested for different reasons
        while size:
            data = os.getrandom(size, os.GRND_NONBLOCK)
            result += data
            size -= len(data)
    except BlockingIOError:
        # OS urandom is not initialized yet:
        # fallback on the Python random module
        data = bytes(random.randrange(256) for _ in range(size))
        result += data
    return bytes(result)


def zip_buffer(min_file_size: int) -> io.BytesIO:
    """Returns an in-memory file containing zipped content of size min_file_size

    borrowed from: https://stackoverflow.com/questions/2463770/python-in-memory-zip-library
    """
    faker = Faker()
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_STORED, False) as zfile:
        content = best_effort_rng(min_file_size)
        zfile.writestr(faker.file_name(extension="txt"), content)

    # return SimpleUploadedFile(
    #     faker.file_name(extension="zip"), content=zip_buffer.getvalue()
    # )
    return zip_buffer


# see https://www.cameronmaske.com/muting-django-signals-with-a-pytest-fixture/
@pytest.fixture(autouse=True)
def mute_signals(request):
    # Skip applying, if marked with `enabled_signals`
    if "enable_signals" in request.keywords:
        return

    signals = [pre_save, post_save, pre_delete, post_delete, m2m_changed]
    restore = {}
    for signal in signals:
        # Temporally remove the signal's receivers (a.k.a attached functions)
        restore[signal] = signal.receivers
        signal.receivers = []

    def restore_signals():
        # When the test tears down, restore the signals.
        for signal, receivers in restore.items():
            signal.receivers = receivers

    # Called after a test has finished.
    request.addfinalizer(restore_signals)


@pytest.fixture(autouse=True)
def faker() -> Faker:
    return Faker()


@pytest.fixture(autouse=True)
def factory() -> Factory:
    return Factory()


# FIXME: remove when no longer used
@pytest.fixture(autouse=True)
def text_file(faker: Faker) -> File:
    content = faker.sentence().encode("utf-8")
    return SimpleUploadedFile("test.zip", content=content)


@pytest.fixture(autouse=True)
def text_buffer(faker: Faker) -> io.BytesIO:
    return io.BytesIO(faker.sentence().encode("utf-8"))


@pytest.fixture(scope="session")
def zip_buffer_small() -> io.BytesIO:
    """Returns a small zip file"""
    yield zip_buffer(100)


@pytest.fixture(scope="session")
def zip_buffer_large() -> io.BytesIO:
    """Returns a small zip file"""
    yield zip_buffer(110000000)


class JSONComparator:
    """Used to compare JSON returned by server to model objects."""

    def __init__(self, fields: list[str], values: dict[str, Any]):
        for key in fields:
            setattr(self, key, values[key])

    def __eq__(self, other: Any):
        diff = []

        for key in self.fields:
            if key == "pk" and "pk" not in other.__dict__.keys():
                if "pk" in self.fields and self.pk != other.id:
                    diff.append("pk")

            elif self.__dict__[key] != other.__dict__[key]:
                diff.append(key)

        self.diff = ", ".join(diff)
        # print(f" DIFF = {self.diff}")
        return len(self.diff) <= 0
