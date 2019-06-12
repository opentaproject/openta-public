import hashlib
from collections import OrderedDict
import functools
import random
import operator
from exercises.util import compose
from lxml import etree
import logging
import re


def get_used_variable_list(correct_answer):
    # correct_answer =  full_question.get('expression').get('$','NO TEXT IN EXPRESSION').split(';')[0]
    # print("GET USED_VARIALBLE LIST FROM ", correct_answer)
    caretless = re.sub(r"\^", ' ', correct_answer)
    caretless = re.sub(r"[A-z][A-Za-z0-9]*\(", ' (', caretless)  # STRIP FUNCTIONS
    caretless = re.sub(r"[\[\]\.]", ' ', caretless)
    caretless = re.sub(r"[\,\+\-\*]", ' ', caretless)
    caretless = re.sub(r"\W+[0-9]+\W+", ' ', caretless)
    caretless = re.sub(r"@[A-z0-9]*", ' ', caretless)  # strip macros
    # print("caretless = ", caretless )
    lis = re.findall(r'([A-z][A-Za-z0-9]*)', caretless)  # get all variable names
    used_variable_list = []
    [
        used_variable_list.append(item)
        for item in lis
        if ((item not in used_variable_list) and (item not in ['e', 'E', 'pi', 'I']))
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
        # print("VARIABLES = ", variables)
        for var in variables:
            # print("var = ", type(var), var)
            res[var.get('name')] = var.get('value')
        # print("RES = ", res)
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
    # print("ress = ", ress )
    if not node.find('variables') is None:
        node = node.find('variables')
    # print("NOW ANALYZE node ", etree.tostring(node) )
    variables = node.findall('var')
    # print("variables = ", variables)
    for var in variables:
        # print("var= ", etree.tostring(var ))
        token = ((var.find('token')).text).strip()
        # print("token= ", token)
        value = None
        if not (var.find('value')) is None:
            value = ((var.find('value')).text).strip()
            # print("value= ", value)
            # ress[token] = value
        if token is not None and value is not None:
            ress.append({'name': token, 'value': value, 'tex': 'TeX'})
    # print("FNALLY ress = ", ress)
    return ress


def parse_blacklist(node):
    tokens = node.xpath('./blacklist/token') + node.xpath('./variables/blacklist/token')
    ret = []
    for token in tokens:
        if hasattr(token, 'text'):
            # print("BLACKLIST TOKEN ", token.text.strip(' \t\n\r') )
            ret.append(token.text.strip(' \t\n\r'))
    return ret


def getallvariables(global_xmltree, question_xmltree):
    '''
    allowglobals='True' (default) determines whether or not student 
        is permitted to use the globally defined variables
    exposeglobals='False' (default) determines whether or not the
        variables are exposed explicitly in the list of allowed variables
    blacklist allows cherrypicking of variables from the globals list,
        both disallowing use and exposure.
        '''
    variables = []
    blacklist = set([])
    correct_answer = ''
    # print("GETALLVARIABLES")
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
    # print("ALLOWGLOBALS = ", allowglobals)
    ret = {}
    try:
        # print("A - parse variables in question_xmltree")
        variables += parse_xml_variables(question_xmltree)
        # print("A - variables in question_xmltree are ",  parse_xml_variables(question_xmltree) )
        # print("B - parse variables in global xmltree ", parse_xml_variables( global_xmltree ) )
        if allowglobals and global_xmltree is not None:
            variables += parse_xml_variables(global_xmltree)
        # print("C done - variables = ", variables)
        # variables_element = question_xmltree.find('variables')
        # if variables_element is not None:
        #         if not variables_element.text is None:
        #             variables += new_parse_variables(variables_element.text)
        # if  allowglobals and global_xmltree is not None and global_xmltree.text is not None:
        #          global_variables = new_parse_variables(global_xmltree.text)
        #          variables += global_variables
        unique_vars = OrderedDict((var['name'], var) for var in variables)
        variables = list(unique_vars.values())
        assigned_variables = set([var['name'] for var in variables])
        # print("ASSIGNED ARE ", assigned_variables)
        correct_answer = question_xmltree.find('expression').text.split(';')[0]
        used_variable_list = set(get_used_variable_list(correct_answer))
        undefined_variables = used_variable_list - assigned_variables
        # print("VARIABLE_PARSER used_variable_list = ", used_variable_list)
        # print("VARIABLE_PARSER undefined_variables = ",undefined_variables)
        arbitrarily_assigned_variables = [
            {'name': var, 'value': str(random.random())} for var in undefined_variables
        ]
        # print("VARIABLE_PARSERS  arbitrarily_assigned_variables",  arbitrarily_assigned_variables )
        variables = variables + arbitrarily_assigned_variables
        ret['authorvariables'] = variables
        # print("VARIABLE_PARSER new variables = ", variables )
        if global_xmltree is not None:
            blacklist.update(parse_blacklist(global_xmltree))
        blacklist.update(parse_blacklist(question_xmltree))
    except Exception as e:
        raise NameError("CANNOT PARSE VARIABLES" + str(e))
        # print("GETALLVARIABLES ERROR")
    # print("blacklist: ", blacklist)
    # print("getallvariables: ", variables )
    # print("correct_anwer: ", correct_answer )
    ret['variables'] = variables
    ret['blacklist'] = blacklist
    ret['correct_answer'] = correct_answer
    return ret
