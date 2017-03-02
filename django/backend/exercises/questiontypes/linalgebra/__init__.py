'''
This is the server side implementation of the question type linalgebra.
'''

from exercises.question import (
    register_question_type,
)  # This function is used to register the question type
from exercises.question import QuestionError

# Below are imports that are specific to this question type
from multiprocessing import Queue, Process, Pool, TimeoutError
from queue import Empty
import functools
import traceback
import lxml.etree as etree
import operator
from exercises.util import compose
from lxml import etree
import time
import logging
import json
import re

logger = logging.getLogger(__name__)


from .linalgebra import linalgebra, to_latex


def parse_variables(xmlstring):  # {{{
    nvariables = {}
    if xmlstring is not None:
        rawvars = " ".join(xmlstring.split()).split(';')
        for varstring in rawvars:
            tokenval = varstring.split('=')
            if len(tokenval) > 1:
                # print("tokenval = " + str( tokenval) )
                nvariables[tokenval[0].strip()] = tokenval[1].strip()
        # print("FUNCTION leaving parse_variables in init.py" + str( nvariables)  )
    return nvariables  # }}}


# The function below is the core of the server interface and the only mandatory component.
def question_check_linalgebra(question_json, question_xmltree, student_answer, global_xmltree):

    result = {}
    variables = parse_variables(global_xmltree.text)
    try:
        expressions = question_xmltree.find('expression').text.split(
            ';'
        )  # <expression>  are parsed as in compareNumeric; semicolon and everything else discarded
        correct_answer = expressions[0]
        suggested_answer = correct_answer
        print("SUGGESTED = ", suggested_answer)
    except Exception as e:
        print("no tag <expression> found")
    try:
        correct_answers = question_xmltree.find('correctanswer').text.split(';')
        # <correctanswer>   abs( cos(ans) ) === 0 ; pi/2 </correctanswer>
        #  tests equality of LHS with RHS; example correct answer after the semicolon
        # ans == keyword for student numerical answer ; sans = keyword for symbolic student answer
        # see example LHS IF
        #
        expressions = question_xmltree.find('correctanswer').text.split(';')
        correct_answer = correct_answers[0]
        suggested_answer = correct_answers[-1]
        print("CORRECTANSWER:", correct_answer)
        print("SUGGESTED: ", suggested_answer)

    except Exception as e:
        print("no <correctanswer> tag found")
    try:
        equalities = question_xmltree.find('equality').text.split(';')
        correct_answer = equalities[0]
        suggested_answer = equalities[-1]
        suggestedxml = question_xmltree.find('suggested')
        if suggestedxml != None:
            suggested_answer = suggestedxml.text.strip()
        print("suggested_answer  = ", suggested_answer)
        # <equality>  is synonym for <correctanswer>
        print("equalities= ", equalities)
    except Exception as e:
        print("no <equality> tag found")

    try:
        # print("QUESTION_CHECK_CLONED_COMPARE_NUMERIC variables " + str( variables )  )
        if suggested_answer is not None:
            print("SUGGESTED = ", suggested_answer)
        else:
            print("SUGGESTED MISSING")
        xmlvars = []
        xmlvars = global_xmltree.findall('var')
        print("xmlfunctions = ")
        try:
            xmlfunctions = global_xmltree.findall('function')
            for xmlfunction in xmlfunctions:
                print((xmlfunction).text)
                # tokenxml = xmlfunction.find('token')
                # valxml = xmlfunction.find('val')
                # if  valxml is not None and tokenxml is not None:
                #   token = ( xmlfunction.find('token').text).strip()
                #   val = ( xmlfunction.find('val').text ).strip()
                #   #print("token = " + str(token ) )
                #   #print("val = " + str( val ) )
                #   nfunctioniables[token] = str(val)

        except Exception as e:
            print("ERROR IN XML FUNCTION DEFS: e = ", e)
        nvariables = {}
        for token, val in variables.items():
            # print("VARIABLES: token = ", str(token) )
            # print("VARIABLES: val = ", str(val) )
            nvariables[token] = variables[token]
        # print("xmlvars = ")

        for xmlvar in xmlvars:
            tokenxml = xmlvar.find('token')
            valxml = xmlvar.find('val')
            if valxml is not None and tokenxml is not None:
                token = (xmlvar.find('token').text).strip()
                val = (xmlvar.find('val').text).strip()
                # print("token = " + str(token ) )
                # print("val = " + str( val ) )
                nvariables[token] = str(val)

    except:
        print("ERROR IN QUESTION CHEC CLONED COMPARE NUMERIC ")
    # print("QUESTION_CHECK_CLONED_COMPARE_NUMERIC nvariables = " + str( nvariables) )
    # print("student_answer = " + str( student_answer) )
    # print("correct_answer = " + str( correct_answer ) )
    try:
        # print("nvariables = ", nvariables )
        # print("student_answer = ", student_answer)
        # print("correct_answer = ", correct_answer)
        result = linalgebra(nvariables, student_answer, correct_answer)
        result['suggested'] = suggested_answer
        # print("EXITED linalgebra")
    except Exception as e:
        # print( "FAILED ")
        # print( "Unexpected error:",  e )
        result['status'] = 'error'
        result['warning'] = "W3-" + str(e)
        return result
    # print(result)
    # print("LEFT EXCEPT")
    if 'correct' in result:
        result['status'] = 'correct' if result['correct'] else 'incorrect'
    elif 'error' in result:
        w = ''
        # if result['warning'] :
        #         w = result['warning']
        result['warning'] = w + "W4-CORRECT PATH - DELETE LINE"
        result['status'] = 'error'
    # Add the sympy representation in latex form for possible visual checks
    # latex = { 'latex': '' } #to_latex(student_answer) }
    # result.update(latex)
    return result


# This function call registers the question type with the system
register_question_type('linalgebra', question_check_linalgebra)
