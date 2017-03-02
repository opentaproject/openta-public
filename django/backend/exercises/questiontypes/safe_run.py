from multiprocessing import Queue, Process, Pool, TimeoutError
from queue import Empty
import logging

logger = logging.getLogger(__name__)


def safe_run(function, args):
    """
    Starts a process with function that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    q = Queue()
    p = Process(target=function, args=args, kwargs={'result_queue': q})
    p.start()
    try:
        starttime = time.perf_counter()
        response = q.get(True, 6)
        timedelta = time.perf_counter() - starttime
        logger.info(
            "Safe run of "
            + function.__name__
            + " took "
            + str(timedelta)
            + 's, with args: '
            + json.dumps(args)
        )
        p.join(1)
        if p.is_alive():
            p.terminate()
            p.join(1)
        return response
    except Empty as e:
        logger.error('Safe run timed out!')
        p.terminate()
        p.join(1)
        if p.is_alive():
            logger.error('Safe run still alive after termination!')
        return {'error': _('Could not parse expression')}
