import hashlib, sympy
from collections import OrderedDict
import functools
import random
import operator
from .parsers import ascii_to_sympy
from exercises.util import compose
from lxml import etree
import logging
import re
from django.core.cache import cache
from exercises.util import get_hash_from_string


def get_used_variable_list(correct_answer):
    caretless = re.sub('\'+', '', correct_answer)
    caretless = re.sub(r"\^", ' ', caretless)
    caretless = re.sub(r"[A-z][A-Za-z0-9]*\(", ' (', caretless)  # STRIP FUNCTIONS
    caretless = re.sub(r"[\[\]\.]", ' ', caretless)
    caretless = re.sub(r"[\,\+\-\*]", ' ', caretless)
    caretless = re.sub(r"\W+[0-9]+\W+", ' ', caretless)
    caretless = re.sub(r"@[A-z0-9]*", ' ', caretless)  # strip macros
    lis = re.findall(r'([A-z][A-Za-z0-9]*)', caretless)  # get all variable names
    used_variable_list = []
    [
        used_variable_list.append(item)
        for item in lis
        if ((item not in used_variable_list) and (item not in ['e', 'E', 'pi', 'I', 'ff', 'FF']))
    ]  # SELECT UNIQUE ITEMS
    return used_variable_list


def new_parse_variables(variables):  # {{{
    '''
    Parses the variable field.
    Takes a string with variables in the format "var1=x; var2=y; var3=z" and converts into a list of the form
    [ { 'name': 'var1', 'value': 'x'}, ... ]
    '''
    rawvars = " ".join(variables.split()).split(';')
    res = {}
    try:
        pipeline = compose(
            functools.partial(filter, operator.truth),
            functools.partial(map, lambda x: x.split('=')),
            functools.partial(
                map, lambda x: {'name': x[0].strip(' \n\t'), 'value': x[1].strip(' \n\t')}
            ),
        )
        variables = list(pipeline(rawvars))
        for var in variables:
            res[var.get('name')] = var.get('value')
        return variables  # }}}
    except IndexError:
        raise QuestionError("Cannot parse variables")


def parse_xml_variables(node):
    '''
    Parses variables defined through the XML syntax <var>...</var>
    '''
    # print("ANALYZE NODE = ", etree.tostring( node) )
    ress = []
    res = []
    textvariables = []
    if not node.text is None:
        ress = ress + new_parse_variables(node.text)
    if not node.find('variables') is None:
        node = node.find('variables')
    variables = node.findall('var')
    for var in variables:
        token = ((var.find('token')).text).strip()
        if token in ['ff', 'FF', 'I']:
            raise NameError('Variable ' + token + ' is disallowed')
        value = None
        if not (var.find('value')) is None:
            value = ((var.find('value')).text).strip()
        if token is not None and value is not None:
            ress.append({'name': token, 'value': value, 'tex': 'TeX'})
    return ress


def parse_xml_functions(node):
    '''
    Parses variables defined through the XML syntax <var>...</var>
    '''
    # print("ANALYZE NODE = ", etree.tostring( node) )
    ress = []
    res = []
    textvariables = []
    # if not node.text is None:
    #    ress = ress + new_parse_functions(node.text)
    if not node.find('functions') is None:
        node = node.find('functions')
    functions = node.findall('func')
    for func in functions:
        token = ((func.find('token')).text).strip()
        if token in ['ff', 'FF', 'I']:
            raise NameError('Function name ' + token + ' is disallowed')
        value = None
        if not (func.find('value')) is None:
            value = ascii_to_sympy( ((func.find('value')).text).strip() )
        args = []
        if not (func.find('args')) is None:
            args = ((func.find('args')).text).strip()
        if token is not None and value is not None:
            ress.append({'name': token, 'args': args, 'value': value, 'tex': 'TeX'})
    # print("RESS = ", ress )
    return ress


def parse_blacklist(node):
    tokens = node.xpath('./blacklist/token') + node.xpath('./variables/blacklist/token')
    ret = []
    for token in tokens:
        if hasattr(token, 'text'):
            # print("BLACKLIST TOKEN ", token.text.strip(' \t\n\r') )
            ret.append(token.text.strip(' \t\n\r'))
    return ret


def getallvariables(global_xmltree, question_xmltree, assign_all_numerical=True):
    '''
    allowglobals='True' (default) determines whether or not student 
        is permitted to use the globally defined variables
    exposeglobals='False' (default) determines whether or not the
        variables are exposed explicitly in the list of allowed variables
    blacklist allows cherrypicking of variables from the globals list,
        both disallowing use and exposure.
        '''
    bigstring = 'getallvariables'
    if global_xmltree  is not None:
        bigstring =  etree.tostring(global_xmltree,encoding='UTF-8')   
    if question_xmltree is not None:
          bigstring = bigstring +  etree.tostring(question_xmltree,encoding='UTF-8')  
    varhash = get_hash_from_string( str( bigstring) )
    ret = cache.get(varhash)
    if ret is not None:
        return ret
    variables = []
    blacklist = set([])
    correct_answer = ''
    if 'allowglobals' in question_xmltree.attrib:
        allowglobals = question_xmltree.attrib['allowglobals']
        if (
            allowglobals == 'False'
            or allowglobals == 'false'
            or allowglobals == 'no'
            or allowglobals == 'No'
        ):
            allowglobals = False
    else:
        allowglobals = True

    if 'exposeglobals' in question_xmltree.attrib:
        exposeglobals = question_xmltree.attrib['exposeglobals']
        if (
            exposeglobals == 'False'
            or exposeglobals == 'false'
            or exposeglobals == 'no'
            or exposeglobals == 'No'
        ):
            exposeglobals = False
    else:
        exposeglobals = True

    ret = {}
    try:
        variables += parse_xml_variables(question_xmltree)
        if allowglobals and global_xmltree is not None:
            variables += parse_xml_variables(global_xmltree)
        unique_vars = OrderedDict((var['name'], var) for var in variables)
        variables = list(unique_vars.values())
        assigned_variables = set([var['name'] for var in variables])
        correct_answer = question_xmltree.find('expression').text.split(';')[0]
        used_variable_list = set(get_used_variable_list(correct_answer))
        undefined_variables = used_variable_list - assigned_variables
        if assign_all_numerical:
            arbitrarily_assigned_variables = [
                {'name': var, 'value': str(random.random())} for var in undefined_variables
            ]
            variables = variables + arbitrarily_assigned_variables
        ret['authorvariables'] = variables
        if global_xmltree is not None:
            blacklist.update(parse_blacklist(global_xmltree))
        blacklist.update(parse_blacklist(question_xmltree))
    except Exception as e:
        raise NameError("CANNOT PARSE VARIABLES" + str(e))
    ret['used_variables'] = used_variable_list
    if not exposeglobals:
        variables = list(
            filter(lambda item: (item['name'] in used_variable_list), variables)
        )  # GET RID OF CLASHES WITH FUNCTIONS
    # print("GETALL VARIABLESS = ", variables )
    funs = parse_xml_functions(global_xmltree)
    ret['variables'] = variables
    ret['authorvariables'] = variables
    ret['blacklist'] = blacklist
    ret['correct_answer'] = correct_answer
    ret['functions'] = funs
    cache.set(varhash, ret, 60 * 60 ) 
    return ret
