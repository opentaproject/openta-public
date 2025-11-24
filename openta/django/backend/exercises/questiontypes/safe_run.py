# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import json
import logging
import time
from multiprocessing import Process, Queue, set_start_method
from queue import Empty

from django.conf import settings
from django.utils.translation import gettext as _

# SEE https://stackoverflow.com/questions/46908035/apps-arent-loaded-yet-exception-occurs-when-using-multi-processing-in-django

if settings.OS == "OSX":
    set_start_method("fork")

logger = logging.getLogger(__name__)


def safe_run(function, args):
    """
    Starts a process with function that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    timedelta = "TIMEOUT ERROR"
    q = Queue()
    p = Process(target=function, args=args, kwargs={"result_queue": q})
    p.start()
    try:
        starttime = time.perf_counter()
        response = q.get(True, settings.CHATGPT_TIMEOUT)
        timedelta = time.perf_counter() - starttime
        logger.debug(
            "Safe run of " + function.__name__ + " took " + str(timedelta) + "s, with args: " + json.dumps(args)
        )
        p.join(1)
        if p.is_alive():
            p.terminate()
            p.join(1)
        return response
    except Empty:
        logger.error("Safe run timed out!")
        logger.debug(
            "Safe run of " + function.__name__ + " took " + str(timedelta) + "s, with args: " + json.dumps(args)
        )
        p.terminate()
        p.join(1)
        if p.is_alive():
            logger.error("Safe run still alive after termination!")
        return {"error": _("Could not parse expression")}
