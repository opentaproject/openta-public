import hashlib, sympy
from deepdiff import DeepDiff 
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
from django.conf import settings
from exercises.util import get_hash_from_string
from .string_formatting import declash
from exercises.question import QuestionError


def get_functions_from_obj(variablesobj, foundvariables=[]):
    vars_ = variablesobj.get('func', {})
    if not isinstance(vars_, list):
        vars_ = [vars_]
    for var in vars_:
        try:
            token = (var.get('token').get('$')).strip()
            if (not token is '') and (token not in foundvariables):
                foundvariables = foundvariables + [token]
        except:
            pass
    return foundvariables


def get_more_variables_from_obj(variablesobj, foundvariables=[]):
    variablestring = variablesobj.get('$', '')
    variablelist = variablestring.split(';')
    for variable in variablelist:
        variable = variable.strip()
        if '=' in variable:
            token = (variable.split('=')[0]).strip()
            if (not token is '') and (token not in foundvariables):
                foundvariables = foundvariables + [token]
    vars_ = variablesobj.get('var', {})
    if not isinstance(vars_, list):
        vars_ = [vars_]
    for var in vars_:
        try:
            token = (var.get('token').get('$')).strip()
            if (not token is '') and (token not in foundvariables):
                foundvariables = foundvariables + [token]
        except:
            pass
    return foundvariables

def get_more_functions_from_obj(variablesobj, foundvariables=[]):
    variablestring = variablesobj.get('$', '')
    variablelist = variablestring.split(';')
    for variable in variablelist:
        variable = variable.strip()
        if '=' in variable:
            token = (variable.split('=')[0]).strip()
            token = ( token.split('(')[0] ).strip()
            if (not token is '') and (token not in foundvariables):
                foundvariables = foundvariables + [token]
    vars_ = variablesobj.get('var', {})
    if not isinstance(vars_, list):
        vars_ = [vars_]
    for var in vars_:
        try:
            token = (var.get('token').get('$')).strip()
            if (not token is '') and (token not in foundvariables):
                foundvariables = foundvariables + [token]
        except:
            pass
    return foundvariables





def remove_blacklist_variables_from_obj(variablesobj, foundvariables=[]):
    variablestring = variablesobj.get('$', '')
    variablelist = variablestring.split(';')
    tokens = variablesobj.get('token', {})
    if not isinstance(tokens, list):
        tokens = [tokens]
    for tokendict in tokens:
        if not tokendict.get('$') is None:
            # #print("FOUND TOKEN TO REMOVE ", tokendict.get('$') )
            token = (tokendict.get('$')).strip()
            if token in foundvariables:
                foundvariables.remove(token)
    return foundvariables




def get_used_variable_list(correct_answer):
    caretless = re.sub('\'+', '', correct_answer)
    # MOVED HERE SINCE the @ SIGN WAS BEING STRIPPED BEFORE MACROS IDENTIFIED
    caretless = re.sub(r"@[A-z0-9]*", ' ', caretless)  # strip macros
    caretless = re.sub(r"\^", ' ', caretless)
    caretless = re.sub(r"[A-z][A-Za-z0-9]*\(", ' (', caretless)  # STRIP FUNCTIONS
    caretless = re.sub(r"[\[\]\.]", ' ', caretless)
    caretless = re.sub(r"[\,\+\-\*]", ' ', caretless)
    caretless = re.sub(r"\W+[0-9]+\W+", ' ', caretless)
    lis = re.findall(r'([A-z][A-Za-z0-9]*)', caretless)  # get all variable names
    used_variable_list = []
    [
        used_variable_list.append(item)
        for item in lis
        if ((item not in used_variable_list) and (item not in ['e', 'E', 'pi', 'I', 'ff', 'FF']))
    ]  # SELECT UNIQUE ITEMS
    return used_variable_list


def parse_variables(variables):  # {{{
    '''
    Parses the variable field.
    Takes a string with variables in the format "var1=x; var2=y; var3=z" and converts into a list of the form
    [ { 'name': 'var1', 'value': 'x'}, ... ]
    '''
    variables = declash( variables )
    rawvars = " ".join(variables.split()).split(';')
    test = list( filter( lambda x: len( x.split('=') ) > 2  , rawvars)  )
    if  not test == [] :
            raise QuestionError(
                "Equal signs occur in the variable definition of %s; check for a missed semicolon." % 
                    ( test[0].split('=') )[0] )
    res = {}
    try:
        pipeline = compose(
            functools.partial(filter, operator.truth),
            functools.partial(map, lambda x: x.split('=')),
            functools.partial(filter, lambda x: not '(' in x[0]),
            functools.partial(filter, lambda x: not '=' in x[1]),
            functools.partial(
                map, lambda x: {'name': x[0].strip(' \n\t'), 'value': x[1].strip(' \n\t')}
            ),
        )
        variables = list(pipeline(rawvars))
        for var in variables:
            res[var.get('name')] = var.get('value')
        return variables
    except IndexError:
        raise QuestionError("Cannot parse variables")


def parse_functions(variables):  # {{{
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
            functools.partial(filter, lambda x: '(' in x[0]),
            functools.partial(
                map,
                lambda x: {
                    'name': (x[0].strip(' \n\t')).split('(')[0],
                    'args': '[' + ((x[0].strip(' \n\t')).split('('))[1].strip(')') + ']',
                    'value': x[1].strip(' \n\t'),
                },
            ),
        )
        variables = list(pipeline(rawvars))
        for var in variables:
            res[var.get('name')] = var.get('value')
        return variables
    except IndexError:
        raise QuestionError("Cannot parse variables")


def parse_xml_variables(node):
    '''
    Parses variables defined through the XML syntax <var>...</var>
    '''
    #print("ANALYZE NODE = ", etree.tostring( node) )
    if node == None :
        return []
    ress = []
    res = []
    textvariables = []
    if not node.text is None:
        ress = ress + parse_variables(node.text)
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
    #print("ANALYZE NODE = ", etree.tostring( node) )
    
    if  node == None:
        return []
    ress = []
    res = []
    textvariables = []
    if not node.text is None:
        ress = ress + parse_functions(node.text)
    if not node.find('functions') is None:
        node = node.find('functions')
    functions = node.findall('func')
    for func in functions:
        token = ((func.find('token')).text).strip()
        if token in ['ff', 'FF', 'I']:
            raise NameError('Function name ' + token + ' is disallowed')
        value = None
        if not (func.find('value')) is None:
            value = ascii_to_sympy(((func.find('value')).text).strip())
        args = []
        if not (func.find('args')) is None:
            args = ((func.find('args')).text).strip()
        if token is not None and value is not None:
            ress.append({'name': token, 'args': args, 'value': value, 'tex': 'TeX'})
    return ress


def parse_blacklist(node):
    if node ==  None :
        return []
    tokens = node.xpath('./blacklist/token') + node.xpath('./variables/blacklist/token')
    ret = []
    for token in tokens:
        if hasattr(token, 'text'):
            #print("BLACKLIST TOKEN ", token.text.strip(' \t\n\r') )
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
    if assign_all_numerical :
        bigstring = bigstring + 'numerical'
    if global_xmltree is not None:
        bigstring = str(etree.tostring(global_xmltree, encoding='UTF-8'))
    if question_xmltree is not None:
        qstring = etree.tostring(question_xmltree, encoding='UTF-8')
        bigstring = bigstring + str(qstring)
    varhash = get_hash_from_string(str(bigstring) + str( __file__ ) )
    #print("GLOBAL_XMLTREE", etree.tostring(global_xmltree) )
    #print("QUESTION XMLTREE ", etree.tostring(question_xmltree) )
    #print("GETALLVARIABLES WITH HASH ", varhash)
    ret = cache.get(varhash)
    if settings.DO_CACHE and (ret is not None):
        #print("GOT IT ", varhash)
        #print("RET = ", ret )
        return ret
    #print("RECALCULATE GETALL VARIABLES", varhash)

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
        if ( exposeglobals == 'True' or exposeglobals == 'true' or exposeglobals == 'yes' or exposeglobals == 'Yes'):
            exposeglobals = True
        else :
            exposeglobals = False
    else:
        exposeglobals = False
    global_variables = parse_xml_variables( global_xmltree)
    global_blacklist = parse_blacklist( global_xmltree)
    #print("GLOBAL_BLACKLIST = ", global_blacklist)
    local_variables = parse_xml_variables( question_xmltree)
    local_blacklist = parse_blacklist( question_xmltree)
    #print("LOCALL_BLACKLIST = ", local_blacklist)
    all_variables = global_variables + local_variables
    correct_answer = question_xmltree.find('expression').text.split(';')[0]
    used_variable_list = list( get_used_variable_list(declash( correct_answer) ) )
    global_variable_list = [ x['name'] for x in global_variables]
    local_variable_list = [ x['name'] for x in local_variables]
    vp = global_variable_list + local_variable_list +  used_variable_list
    proper_order  = []
    for v in vp :
        if not v in proper_order :
            proper_order   += [v ]
    #print("PROPER ORDER  = ", proper_order)
    #print("USED = ", used_variable_list)
    #print("GLOBAL =", global_variables)
    #print("LOCALS = ", local_variables)
    #print("EXPOSEGLOBALS = ", exposeglobals)
    all_assignments =  global_variables  + local_variables # EXPOSEGLOBALS THEN GLOBALS ARE BAKED IN
    if exposeglobals :
        okatoms = list(  set( global_variable_list)
            .difference(global_blacklist)
            .union( set( used_variable_list + local_variable_list) )
            .difference(set( local_blacklist) ) )
    else :
        okatoms = list( set( used_variable_list  ).difference( local_blacklist) )
    okatoms = [ re.sub(r"variable",'',item) for item in list( okatoms) ] 
    all_possible_names  = list( set(  used_variable_list + global_variable_list + local_variable_list)   )
    #print("ALL POSSIBLE NAMES = ", all_possible_names)
    #print("ALL ASSIGNED ", all_assignments)
    all_variables = []
    _ret = {};
    _ret['authorvariables'] = []  
    for name in all_possible_names :
        #print("NAME = ", name )
        entry = list( filter( lambda  x :  x['name'] == name , all_assignments) )
        #print("ENTRY = ", entry )
        if len(entry) == 0 :
            entry = [{'name' : name, 'value' : random.random() }]
            entry2  = [{'name': entry[0]['name'], 'value': str( entry[0]['value'] ) } ]
        elif len(entry) > 1 :
            raise QuestionError("Error 267: Duplicate definition of %s " % name )
        else :
            entry  = [{'name': name, 'value' : entry[0].get('value',random.random() ) , 'tex' : entry[0].get('tex',name)}]
            entry2  = [{'name': entry[0]['name'], 'value': str( entry[0]['value'] ) } ]
        all_variables = all_variables + entry
        _ret['authorvariables'] = _ret['authorvariables'] + entry2
    #print("ALLVARIABLES = ", all_variables)
    _ret['variables'] = all_variables
    funs = {}
    if not global_xmltree == None:
        funs = parse_xml_functions(global_xmltree)
    #print("VARIABLES IN VARIABLEPARSER = ", variables)
    okatoms = [ re.sub(r"variable",'',item) for item in list( okatoms) ] 
    _ret['used_variables'] = set( okatoms )
    _ret['variables'] = all_variables
    _ret['blacklist'] = list( set( global_blacklist + local_blacklist) )
    _ret['correct_answer'] = correct_answer
    _ret['functions'] = funs
    _ret['exposeglobals'] = exposeglobals
    avars = _ret['authorvariables']
    _ret['authorvariables'] = []
    for name in proper_order :
        avar =  list( filter(lambda item: (item['name']  == name ), avars) )
        if len(avar) > 0 :
            _ret['authorvariables'] +=  avar
    
    avars = _ret['variables']
    _ret['variables'] = []
    for name in proper_order :
        avar =  list( filter(lambda item: (item['name']  == name ), avars) )
        if len( avar) > 0 :
            _ret['variables'] +=  avar
    #print("AUTHORVARIABLES ", DeepDiff( _ret['authorvariables'], ret['authorvariables'] ,ignore_order=True) )
    #print("TOTAL DIFF ", DeepDiff( ret, _ret ) )
    #print("TYPES = ", type(ret), type(_ret) )
    try :
        cache.set(varhash, _ret, 60 * 60)
    except:
        #print("CACHE FAILED TO SET")
        pass
    #_ret['authorvariables'] = ret['authorvariables']
    #print("_RET = ", ret )
    return _ret
