import os.path
import exercises.paths as paths
import json
import re
from django.utils.translation import ugettext as _
import traceback
import random
from multiprocessing import Queue, Process, Pool, TimeoutError
from exercises.questiontypes.safe_run import safe_run
from queue import Empty
import time
import logging
import sys
import importlib

logger = logging.getLogger(__name__)


def pythonic_runner(studentanswerdict, questiondict, globaldict, result_queue):
    try:
        path = questiondict['@path']
        filename = questiondict.get('@file', "questions")
        functionname = questiondict['@function']
        sys.path.append(path)
        questions = importlib.import_module(filename)
        func = getattr(questions, functionname)
        response = func(studentanswerdict, questiondict, globaldict)
    except SyntaxError as e:
        response = {}
        response['correct'] = False
        response['warning'] = 'B2: Syntax Error :' + functionname + ': ' + str(e)

    except NameError as e:
        response = {}
        response['correct'] = False
        response['warning'] = 'B1 Name Error:  ' + functionname + ' ' + '  : ' + str(e)
    except KeyError as e:
        response = {}
        response['correct'] = False
        response['warning'] = (
            'B3: Key Error: Probably missing previous answer or wrong key : '
            + functionname
            + ': '
            + str(e)
        )
    except OSError as e:
        response = {}
        response['correct'] = False
        estring = (str(e)).split(' ', 1)
        filename = os.path.basename(estring[0])
        try:
            secondpart = estring[1]
        except:
            secondpart = ''
        response['warning'] = 'A3: ' + (filename + ' ' + secondpart)[0:120]
    except Exception as e:
        response = {}
        response['correct'] = False
        response['warning'] = (
            'A1: ' + str(type(e).__name__) + ' : ' + functionname + ': ' + (str(e))[0:120]
        )
    result_queue.put(response)


def pythonic(studentanswerdict, questiondict, globaldict):
    """
    Starts a process with external_question that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    invalid_strings = ['_']
    expression1 = studentanswerdict['studentanswer']
    for i in invalid_strings:
        if i in expression1:
            return {'error': _('Answer contains invalid character ') + i}
    return safe_run(pythonic_runner, args=(studentanswerdict, questiondict, globaldict))
