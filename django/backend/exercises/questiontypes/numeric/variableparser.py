import hashlib
from collections import OrderedDict
import functools
import operator
from exercises.util import compose
from lxml import etree
import logging
import re


def new_parse_variables(variables):  # {{{
    '''
    Parses the variable field.
    Takes a string with variables in the format "var1=x; var2=y; var3=z" and converts into a list of the form
    [ { 'name': 'var1', 'value': 'x'}, ... ]
    '''
    rawvars = " ".join(variables.split()).split(';')
    try:
        pipeline = compose(
            functools.partial(filter, operator.truth),
            functools.partial(map, lambda x: x.split('=')),
            functools.partial(
                map, lambda x: {'name': x[0].strip(' \n\t'), 'value': x[1].strip(' \n\t')}
            ),
        )
        variables = list(pipeline(rawvars))
        return variables  # }}}
    except IndexError:
        raise QuestionError("Cannot parse variables")


def parse_xml_variables(node):
    '''
    Parses variables defined through the XML syntax <var>...</var>
    '''
    variables = node.xpath('./var')
    res = []
    if variables is None:
        return res
    for var in variables:
        token = var.find('token')
        value = var.find('val')
        if token is not None and value is not None:
            res.append({'name': token.text, 'value': value})
    return res


def parse_blacklist(node):
    tokens = node.xpath('./blacklist/token')
    ret = []
    for token in tokens:
        if hasattr(token, 'text'):
            ret.append(token.text.strip(' \t\n\r'))
    return ret


def getallvariables(global_xmltree, question_xmltree):
    variables = []
    blacklist = set([])
    correct_answer = ''
    # print("GETALLVARIABLES")
    ret = {}
    try:
        variables += parse_xml_variables(question_xmltree)
        if global_xmltree is not None:
            variables += parse_xml_variables(global_xmltree)
        variables_element = question_xmltree.find('variables')
        if variables_element is not None:
            variables += new_parse_variables(variables_element.text)
        if global_xmltree is not None and global_xmltree.text is not None:
            global_variables = new_parse_variables(global_xmltree.text)
            variables += global_variables

        unique_vars = OrderedDict((var['name'], var) for var in variables)
        variables = list(unique_vars.values())
        # print("variables = ", variables )
        correct_answer = question_xmltree.find('expression').text.split(';')[0]
        if global_xmltree is not None:
            blacklist.update(parse_blacklist(global_xmltree))
        blacklist.update(parse_blacklist(question_xmltree))
    except:
        print("NUMERIC GETALLVARIABLES ERROR")
    # print("blacklist: ", blacklist)
    # print("getallvariables: ", variables )
    # print("correct_anwer: ", correct_answer )
    ret['variables'] = variables
    ret['blacklist'] = blacklist
    ret['correct_answer'] = correct_answer
    return ret
