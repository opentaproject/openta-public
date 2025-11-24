# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import importlib
import logging
import os.path
import sys

from exercises.questiontypes.safe_run import safe_run

from django.contrib.auth.models import User
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


def pythonic_runner(studentanswerdict, questiondict, globaldict, result_queue):
    try:
        er = "A"
        path = questiondict["runtime"]["@path"]
        er = "B"
        filename = questiondict.get("@file", "questions")
        er = "C"
        functionname = questiondict["@function"]
        er = "D"
        sys.path.append(path)
        #print(f"RUNNER_FILENAME = {filename}")
        questions = importlib.import_module(filename)
        er = "F" + er
        func = getattr(questions, functionname)
        er = "G" + er
        #print(f" ER = {er} func={func}")
        response = func(studentanswerdict, questiondict, globaldict)
        #print(f" RESPONSE = {response}")
    except SyntaxError as e:
        response = {}
        response["correct"] = False
        response["warning"] = f"B2-pythonic {er}: Syntax Error :" + functionname + ": " + str(e)

    except NameError as e:
        response = {}
        response["correct"] = False
        response["warning"] = f"B1-pythonic  {er} Name Error:  " + functionname + " " + "  : " + str(e)
        logger.error(f"PYTHONIC ERROR = {response}")
    except KeyError as e:
        response = {}
        response["correct"] = False
        response["warning"] = (
            "B3: Key Error {er}: Probably missing previous answer or wrong key : " + functionname + ": " + str(e)
        )
    except OSError as e:
        response = {}
        response["correct"] = False
        estring = (str(e)).split(" ", 1)
        filename = os.path.basename(estring[0])
        try:
            secondpart = estring[1]
        except:
            secondpart = ""
        response["warning"] = "A3: " + (filename + " " + secondpart)[0:120]
    except Exception as e:
        response = {}
        response["correct"] = False
        username = questiondict.get("@user", None)
        subdomain = questiondict.get("@path", "").split("/")[2]
        user = User.objects.using(subdomain).get(username=username)
        #print(f" user = {user} {user.is_staff}")
        if user.is_staff:
            response["warning"] = "A1: " + str(type(e).__name__) + " : " + functionname + ": " + (str(e))[0:120]
        else:
            response["warning"] = f"Error  {str(type(e).__name__)}"

    result_queue.put(response)


def pythonic(studentanswerdict, questiondict, globaldict):
    """
    Starts a process with external_question that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    invalid_strings = ["_"]
    expression1 = studentanswerdict["studentanswer"]
    for i in invalid_strings:
        if i in expression1:
            return {"error": _("Answer contains invalid character ") + i}
    return safe_run(pythonic_runner, args=(studentanswerdict, questiondict, globaldict))
