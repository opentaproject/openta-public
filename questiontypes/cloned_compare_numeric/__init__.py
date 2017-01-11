'''
This is the server side implementation of the question type ClonedCompareNumeric.
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


from .cloned_compare_numeric import cloned_compare_numeric, to_latex


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
def question_check_cloned_compare_numeric(
    question_json, question_xmltree, student_answer, global_xmltree
):

    variables = parse_variables(global_xmltree.text)
    correct_answer = question_xmltree.find('expression').text.split(';')[0]
    try:
        # print("QUESTION_CHECK_CLONED_COMPARE_NUMERIC variables " + str( variables )  )
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
    result = {}
    try:
        # print("nvariables = ", nvariables )
        # print("student_answer = ", student_answer)
        # print("correct_answer = ", correct_answer)
        result = cloned_compare_numeric(nvariables, student_answer, correct_answer)
        # print("EXITED cloned_compare_numeric")
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
register_question_type('ClonedCompareNumeric', question_check_cloned_compare_numeric)
