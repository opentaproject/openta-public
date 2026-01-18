# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
This is the server side implementation of the question type compareNumeric.
"""

import logging

from exercises.question import (  # This function is used to register the question type
    QuestionError,
    register_question_class,
)
from exercises.questiontypes.linear_algebra import linearAlgebra

logger = logging.getLogger(__name__)


class compareNumeric(linearAlgebra):
    name = "compareNumeric"
    hide_tags = ["expression", "value"]

    def __init__(self):
        pass


register_question_class(compareNumeric)
