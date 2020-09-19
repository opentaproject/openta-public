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
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

def longjob(num):
    res = dotask(20)
    k = 0
    while len(res) > 0  :
        k = k + 1
        res = dotask(20)
    return num

async def main(loop) :
    print('entering main')
    loop = asyncio.get_event_loop()
    executor = ProcessPoolExecutor(max_workers=12)
    tasks = []
    nworkers = 4;
    for  i in range( nworkers) :
        tasks.append( loop.run_in_executor(executor, longjob, i ) )
    data = await asyncio.gather(*tasks)

loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
