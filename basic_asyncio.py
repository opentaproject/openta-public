import asyncio
import time
import random
from concurrent.futures import ProcessPoolExecutor
import sys
import warnings
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)



def longjob(context):
    num = context['num']
    k = 0
    timebeg = time.time()
    while  k < 5 :
        k = k + 1
        sleeptime =  random.randint(1,5)
        print("job %s iterate %s  sleeping for %s  seconds " % (num,k , sleeptime ) )
        time.sleep(sleeptime)
    return int( 1000 * ( time.time() - timebeg ) )

async def main(loop) :
    print('entering main')
    loop = asyncio.get_event_loop()
    executor = ProcessPoolExecutor(max_workers=12)
    tasks = []
    nworkers = 3;
    for  i in range( nworkers) :
        context = {'num' : i }
        tasks.append( loop.run_in_executor(executor, longjob, context ) )
    data = await asyncio.gather(*tasks)
    print("DATA = ", data )

loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop)) 
