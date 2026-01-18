# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander
from django.conf import settings

from . import compare_numeric
from . import multiple_choice
from . import linear_algebra
from . import dev_linear_algebra
from . import numeric
from . import linear_algebra
from . import pythonic
from . import textbased
if settings.USE_CHATGPT :
    from . import aibased
from . import symbolic
from . import webworks
from . import mathematica
from . import demo
from . import qm
from . import basic
from . import default
from . import matrix
from . import core
