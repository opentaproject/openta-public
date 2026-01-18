# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import asyncio
import time
import random
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django

django.setup()
from exercises.management.commands.recalculate import dotask
from concurrent.futures import ProcessPoolExecutor
import sys
import warnings
import traceback
import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)


def longjob(num, course_key):
    accept_new = True
    res = dotask(20, num, accept_new)
    if res == None:
        return num
    k = 0
    while not res == None:
        k = k + 1
        try:
            res = dotask(20, num, accept_new, course_key)
        except Exception as e:
            print("Excption in longjob %s %s %s" % (type(e), str(e), traceback.format_exc()))
    return num


async def main(loop):
    print("entering main")
    loop = asyncio.get_event_loop()
    executor = ProcessPoolExecutor(max_workers=8)
    tasks = []
    nworkers = 8
    course_key = None
    course_key = "EXAMPLE"
    if os.path.exists("/tmp/whitelist.txt"):
        print("/tmp/whitelist.txt exists so process only those ")
        nworkers = 1
    if os.path.exists("/tmp/recalculated.txt"):
        print("/tmp/recalculated.txt exists so exclude those")
    for i in range(nworkers):
        tasks.append(loop.run_in_executor(executor, longjob, i, course_key))
    data = await asyncio.gather(*tasks)


loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
