# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import importlib
from django.conf import settings
import json
import urllib3
import logging
import os.path
import sys
from exercises.questiontypes.safe_run import safe_run
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from sympy.core.sympify import SympifyError
import sympy
from sympy import *
import numpy as np
from pprint import pformat
from exercises.utils.string_formatting import ascii_to_sympy
logger = logging.getLogger(__name__)
import re as reg
ns = {}
# Taylor clashes
ns.update(
    {
        "zeta": zeta,
        "Q": Q,
        "O": O,
        "S": S,
    }
)



def mathematica_form(student_answer) :
    # print("STUDENT_ANSWER = ", student_answer)
    s = str(srepr(sympy.sympify(ascii_to_sympy(student_answer))))
    # print("S = ", s )
    s = reg.sub(r"\'", "", s)
    s = reg.sub(r"\[", "{", s)
    s = reg.sub(r"\]", "}", s)
    s = reg.sub(r"\(", "[", s)
    s = reg.sub(r"\)", "]", s)
    s = reg.sub(r"Global.", "", s)
    translations = {
        "Mul": "Times",
        "Pow": "Power",
        "Add": "Plus",
        "Integer": "Identity",
        "Symbol": "Identity",
        "cos": "Cos",
        "sin": "Sin",
        "tan": "Tan",
        "pi": "Pi",
        "abs": "Abs",
    }
    for key in translations.keys():
        s = reg.sub(r"%s" % key, translations[key], s)
    s = reg.sub(r"Identity\[([^\]]+)\]", r"\1", s)
    s = reg.sub(r"MutableDenseMatrix", "Identity", s)
    # print("S = ", s )
    return s




def simple_symbolic(studentanswerdict, questiondict, globaldict):
    # Do some initial formatting
    response = {}
    expression1 = (questiondict["expression"]).split(";")[0]
    invalid_strings = ["_", "[", "]"]
    expression2 = studentanswerdict["studentanswer"]
    try:
        for i in invalid_strings:
            if i in expression1:
                response["error"] = _("Answer contains invalid character ") + i
                raise SympifyError("illegal character")
        sexpression1 = ascii_to_sympy(expression1)
        sexpression2 = ascii_to_sympy(expression2)
        sympy1 = sympy.sympify(sexpression1, ns)
        sympy2 = sympy.sympify(sexpression2, ns)
        print(f"sympy1 = {sympy1}")
        print(f"sympy2 = {sympy2}")
        diffy = sympy.simplify(( sympy1  ) - (  sympy2) )
        if diffy == 0:
            response["correct"] = True
        else:
            response["correct"] = False
            response["warning"] = "reduces to " + str(diffy)
    except SympifyError:
        response["error"] = _("Failed to evaluate expression.")
    except Exception as e:
        response["error"] = _("Unknown error " + str(e) + "  check your expression.")
    return response  # }}}




def mathematica_runner(studentanswerdict, questiondict, globaldict, result_queue):
    er = '1';
    try:
        path = questiondict["runtime"]["@path"]
        print(f"QUESTIONDICT = {questiondict}")
        print(f"PATH = {path}")
        s = questiondict.get('wl', 'studentanswer == expression ' )
        imports = questiondict.get('import',[])
        print(f"{type(imports)}")
        if not isinstance(  imports, list ) :
            imports = [imports]
        preface = f'SetDirectory[\"{path}\"] ; ' 
        msg = ''
        files_found = True
        for i in imports :
            fpath = os.path.join(path,i) 
            if not i.split('.')[-1]  in ['m','wl'] :
                files_found = False;
                msg = f"file {i} is of wrong type; Import must be of type .m or .wl ";
                break;
            elif not   os.path.exists( fpath ):
                files_found = False
                msg = f"file {i} not found ";
                break;
            else :
                preface = preface + f"Import[\"{i}\"]; "
                print(f"IMPORT = {i}")
        print(f"PREFACE = {preface}")
        if True or files_found :
            student_answer = studentanswerdict['studentanswer']
            correct_answer = questiondict['expression']
            print(f"STUDENT_ANSWER: {student_answer}")
            print(f"CORRECT_ANSWER: {correct_answer}")
            sa =  student_answer 
            ca =  correct_answer 
            expression =   reg.sub(r'expression', '(' + ca + ')' ,s)
            expression =   reg.sub(r'studentanswer','(' + sa + ')' ,expression)
            wlcode = f" {preface} {expression}"
            http = urllib3.PoolManager()
            fields = {"In": wlcode};
            mathurl = settings.WOLFRAM_ENGINE + ":8000/app/json2";
            html = http.request("POST",   mathurl ,fields=fields)
            print("DATA = ", html.data )
            res = json.loads( html.data )
            try :
                res = json.loads( res );
            except Exception as e :
                logger.error(f" JSON INCORRECT {type(e).__name__} {str(e)}")
            res['correct'] = ( res['correct'] == 'True') 
            response = res;
            print(f"DATA = {res} { type(res) } ")
            # response =  {'correct' : False , 'warning' : f"{msg}"} 
            #if "True" in res :
            #    response = {'correct' : True }
            #elif isinstance(res,bool) and res :
            #    response = {'correct' : True }
            #elif  'Failed'  in res :
            #    response = {'correct' : False, 'warning' : "Expression failed to parse"}
            #else :
            #    response = {'correct' : False, 'warning' : res }
        #response = simple_symbolic(studentanswerdict, questiondict, globaldict)
        #else :
        #    response =  {'correct' : False , 'warning' : msg} 
        print(f"RESPONSE = {response}")
    except SyntaxError as e:
        response = {}
        response["correct"] = False
        response["warning"] = f"B2-mathematica {er}: Syntax Error: " +  str(e)

    except NameError as e:
        response = {}
        response["correct"] = False
        response["warning"] = f"B1-mathematica  {er} Name Error: " + str(e)
        logger.error(f"PYTHONIC ERROR = {response}")
    except KeyError as e:
        response = {}
        response["correct"] = False
        response["warning"] = (
            "B3: Key Error {er}: Probably missing previous answer or wrong key : "+ str(e)
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
        print(f" user = {user} {user.is_staff}")
        if user.is_staff:
            response["warning"] = "A1: " + str(type(e).__name__) + " : " + (str(e))[0:120]
        else:
            response["warning"] = f"Error  {str(type(e).__name__)}"

    result_queue.put(response)


def mathematica(studentanswerdict, questiondict, globaldict):
    """
    Starts a process with external_question that will be terminated if it takes too long. This implementation uses multiprocessing.Process.
    """
    invalid_strings = ["_"]
    expression1 = studentanswerdict["studentanswer"]
    for i in invalid_strings:
        if i in expression1:
            return {"error": _("Answer contains invalid character ") + i}
    return safe_run(mathematica_runner, args=(studentanswerdict, questiondict, globaldict))
