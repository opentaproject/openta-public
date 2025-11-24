# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
from typing import Any, Optional

from _pytest.config import Config

from conftest import JSONComparator

logger = logging.getLogger(__name__)


class CourseJSONComparator(JSONComparator):
    """Compares JSON seen by an administrator to a course"""

    fields = [
        "course_name",
        "published",
        "pk",
        "icon",
        "registration_password",
        "registration_by_password",
        "registration_by_domain",
        "languages",
        "difficulties",
        "email_reply_to",
        "motd",
        "url",
        "use_auto_translation",
        "use_email",
        "use_lti",
    ]

    def __init__(self, values: dict[str, Any]):
        super().__init__(self.fields, values)


class CourseStudentJSONComparator(JSONComparator):
    """Compares JSON seen by an student to a course"""

    fields = [
        "course_name",
        "published",
        "icon",
        "email_reply_to",
        "pk",
        "languages",
        "motd",
        "url",
        "use_email",
        "use_auto_translation",
    ]

    def __init__(self, values: dict[str, Any]):
        super().__init__(self.fields, values)


def pytest_assertrepr_compare(config: Config, op: str, left: Any, right: Any) -> Optional[list[str]]:
    if isinstance(left, CourseJSONComparator) and op == "==":
        return ["Course JSON does not match the following fields", left.diff]

    if isinstance(left, CourseStudentJSONComparator) and op == "==":
        return ["Course JSON does not match the following fields", left.diff]
