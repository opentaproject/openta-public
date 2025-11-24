# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""
Middleware to simulate a slow connection
"""

import time
import random


def simulate_slow(get_response):
    """
    Simulate a slow connection by waiting a random amount of time for each request.
    """

    def middleware(request):
        response = get_response(request)
        time.sleep(random.uniform(0, 2))
        return response

    return middleware
