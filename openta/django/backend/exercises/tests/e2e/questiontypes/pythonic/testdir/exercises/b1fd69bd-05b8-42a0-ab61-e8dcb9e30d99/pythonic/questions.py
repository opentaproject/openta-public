# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import os.path

# from sympy.abc import _clash1, _clash2, _clash # dont impport clashes
from pprint import pformat

import numpy as np
from django.utils.translation import gettext as _
from exercises.utils.string_formatting import ascii_to_sympy
from sympy import *
from sympy.core.sympify import SympifyError

ns = {}
# Taylor clashes
ns.update(
    {
        "zeta": zeta,
        "Q": Q,
        "O": O,
        "beta": beta,
        "S": S,
        "gamma": gamma,
        "ff": Symbol("ff"),
        "FF": Symbol("FF"),
    }
)


lambdifymodules = ["numpy", {"cot": lambda x: 1.0 / numpy.tan(x)}]

# from numpy  import *
# from numpy import genfromtxt
# trainingSet  = genfromtxt('training_set.csv',delimiter=',')
# validationSet  = genfromtxt('evaluation_set.csv',delimiter=',')
# t1 = genfromtxt('t1.csv',delimiter=',')
# t2 = genfromtxt('t2.csv',delimiter=',')
# t3 = genfromtxt('t3.csv',delimiter=',')
# w1 = genfromtxt('w1.csv',delimiter=',')
# w2 = genfromtxt('w2.csv',delimiter=',')
# w3 = genfromtxt('w3.csv',delimiter=',')
# beta = 2


def getOmegas(csvars, dataSet):
    hOmega = 0
    cOmega = 0
    beta = 2
    t1 = csvars["t1"]
    t2 = csvars["t2"]
    t3 = csvars["t3"]
    w1 = csvars["w1"]
    w2 = csvars["w2"]
    w3 = csvars["w3"]
    t1t = np.transpose([t1])
    t2t = np.transpose([t2])
    t3t = np.transpose([t3])
    xi = np.transpose(dataSet[:, [0, 1]])
    nsamples = np.shape(xi)[1]
    zeta = dataSet[:, 2]
    av1 = np.tanh(beta * (np.dot(w1, xi) + t1t))
    av1 = np.tanh(beta * (np.dot(w1, xi) + t1t))
    av2 = np.tanh(beta * (np.dot(w2, av1) + t2t))
    output = np.tanh(beta * (np.dot(w3, av2) + t3t))
    hOmega = (0.5 * np.sum((output - zeta) ** 2)) / nsamples
    cOmega = (0.5 * np.sum(np.abs(np.sign(output) - zeta))) / nsamples
    return {"HOmega": hOmega, "COmega": cOmega}


# omegaTraining = getOmegas( trainingSet )
# omegaValidation = getOmegas( validationSet )
# print("OmegaTraining = ", omegaTraining )
# print("OmegaValidation = ", omegaValidation )


# def questionhandler(functionname) :
#    if functionname == 'simple_symbolic' :
#        return simple_symbolic
#    if functionname == 'has_determinant_one' :
#        return has_determinant_one
#    if functionname == 'dotrainingset' :
#        return dotrainingset
#    if functionname == 'doevaluationset' :
#        return doevaluationset
#    if functionname == 'add_one' :
#        return add_one
#


def dotrainingset(studentanswerdict, questiondict, globaldict):
    response = {}
    # print("studentanswerdict = ", studentanswerdict )
    try:
        print(f" STUDENTANSWERDICT = {studentanswerdict}")
        print(f" QUESTIONDICT = {questiondict}")
        print(f" GLOBALDICT = {globaldict}")
        exerciseassetpath = questiondict["@exerciseassetpath"]
        trainingSet = np.genfromtxt(os.path.join(exerciseassetpath, "training_set.csv"), delimiter=",")
        studentassetpath = questiondict["@studentassetpath"]
        print(f"STUDENTASSETPATH = {studentassetpath}")
        csvfiles = ["t1", "t2", "t3", "w1", "w2", "w3"]
        csvars = {}
        for csvfile in csvfiles:
            filename = os.path.join(studentassetpath, csvfile + ".csv")
            fileexists = os.path.isfile(filename)
            if fileexists:
                csvars[csvfile] = np.genfromtxt(filename, delimiter=",")
            else:
                response["correct"] = False
                response["warning"] = "A2: file " + filename + " does not exist"
                return response
        res = getOmegas(csvars, trainingSet)
        if res["COmega"] < 0.01 and res["HOmega"] < 0.02:
            response["correct"] = True
        else:
            response["correct"] = False
        response["warning"] = "$ C_{\\Omega} $ = " + str(res["COmega"]) + " $ H_{\\Omega} =  $ " + str(res["HOmega"])
        response["hint"] = "executed correctly"
        return response
    except Exception as e:
        response["correct"] = False
        response["warning"] = "file __init__.py : " + str(e)
        return response


def doevaluationset(studentanswerdict, questiondict, globaldict):
    response = {}
    exerciseassetpath = questiondict["@exerciseassetpath"]
    evaluationSet = np.genfromtxt(os.path.join(exerciseassetpath, "evaluation_set.csv"), delimiter=",")
    studentassetpath = questiondict["@studentassetpath"]

    csvfiles = ["t1", "t2", "t3", "w1", "w2", "w3"]
    csvars = {}
    for csvfile in csvfiles:
        filename = os.path.join(studentassetpath, csvfile + ".csv")
        csvars[csvfile] = np.genfromtxt(filename, delimiter=",")
    res = getOmegas(csvars, evaluationSet)
    if res["COmega"] < 1.0 and res["HOmega"] < 1.0:
        response["correct"] = True
    else:
        response["correct"] = False
    response["warning"] = "$ C_{\\Omega} $ = " + str(res["COmega"]) + " $ H_{\\Omega} =  $ " + str(res["HOmega"])
    return response


def doevaluationset(studentanswerdict, questiondict, globaldict):
    response = {}
    exerciseassetpath = questiondict["@exerciseassetpath"]
    evaluationSet = np.genfromtxt(os.path.join(exerciseassetpath, "evaluation_set.csv"), delimiter=",")
    studentassetpath = questiondict["@studentassetpath"]
    csvfiles = ["t1", "t2", "t3", "w1", "w2", "w3"]
    csvars = {}
    for csvfile in csvfiles:
        filename = os.path.join(studentassetpath, csvfile + ".csv")
        csvars[csvfile] = np.genfromtxt(filename, delimiter=",")
    res = getOmegas(csvars, evaluationSet)
    if res["COmega"] < 1.0 and res["HOmega"] < 1.0:
        response["correct"] = True
    else:
        response["correct"] = False
    response["warning"] = "$ C_{\\Omega} $ = " + str(res["COmega"]) + " $ H_{\\Omega} =  $ " + str(res["HOmega"])
    return response


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
        sympy1 = sympify(sexpression1, ns)
        sympy2 = sympify(sexpression2, ns)
        diffy = simplify(sympy1 - sympy2)
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


def has_determinant_one(studentanswerdict, questiondict, globaldict):
    # Do some initial formatting
    response = {}
    expression2 = sympify(ascii_to_sympy(studentanswerdict["studentanswer"]))
    diffy = expression2.det()  # Matrix([[1,0],[0,1]]) gives correct answer
    try:
        if diffy == 1:
            response["correct"] = True
        else:
            response["correct"] = False
            response["warning"] = "reduces to " + str(diffy)
            response["warning"] = "<pre>" + pformat(studentanswerdict) + "</pre>"
    except SympifyError:
        response["error"] = _("Failed to evaluate expression.")
    except Exception as e:
        response["error"] = _("Unknown error " + str(e) + "  check your expression.")
    return response  # }}}


def add_one(studentanswerdict, questiondict, globaldict):
    # Do some initial formatting
    # print("PYTHONIC_INIT: questiondict = ", questiondict)
    # print("ALL_ANSWERS = ", get_all_answers( studentanswerdict['dbhooks'] ) )
    response = {}
    expression2 = sympify(ascii_to_sympy(studentanswerdict["studentanswer"]))
    expressionfromone = sympify(ascii_to_sympy(studentanswerdict["all_answers"]["4"]))
    diffy = (expression2 - expressionfromone).det()
    try:
        if diffy == 1:
            response["correct"] = True
        else:
            response["correct"] = False
            response["warning"] = "reduces to " + str(diffy)
            response["warning"] = "<pre>" + pformat(studentanswerdict) + "</pre>"
    except SympifyError:
        response["error"] = _("Failed to evaluate expression.")
    except Exception as e:
        response["error"] = _("Unknown error " + str(e) + "  check your expression.")
    return response  # }}}
