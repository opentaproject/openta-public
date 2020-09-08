import asyncio
from codetiming import Timer
import random
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from exercises.management.commands.recalculate import dotask
from concurrent.futures import ProcessPoolExecutor

def cpu_heavy(num):
    print('Entering ', num)
    import time
    tbegin = time.time()
    dotask()
    print('Leaving ', num, 1000 * ( time.time() - tbegin ) )
    return num

async def main(loop):
    print('entering main')
    executor = ProcessPoolExecutor(max_workers=3)
    data = await asyncio.gather(*(loop.run_in_executor(executor, cpu_heavy, num) 
                                  for num in range(6)))
    print('got result', data)
    print('leaving main')


loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
