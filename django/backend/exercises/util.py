import json as JSON
import functools
import re, hashlib


def nested_print(d):
    print(JSON.dumps(d, indent=4))
    return


def deep_get(dictionary, *keys, default=None):
    result = functools.reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)
    if result is None:
        return default
    else:
        return result


def compose(*funcs):
    return lambda x: functools.reduce(lambda v, f: f(v), funcs, x)


def get_hash_from_string(string):
    string_to_hash = str(re.sub(r'(\s|\\n)*', '', str(string)))
    globalhash = (hashlib.md5(string_to_hash.encode('utf-8')).hexdigest())[:10]
    res = ''
    for c in globalhash :
        if c.isdigit() :
            c = chr(int(c) + 97 ) 
        res = res + c
    return res 

def index_of_matching_right_paren(beg, expression):
    level = 1
    ind = beg + 1
    while level > 0 and ind < len(expression):
        if expression[ind] == ')':
            level = level - 1
        elif expression[ind] == '(':
            level = level + 1
        ind = ind + 1
    assert expression[beg] == '(', 'LEFT PAREN WRONG'
    assert expression[ind-1] == ')', 'RIGHT PAREN WRONG'
    return ind 

def index_of_matching_right_paren(beg, expression):
    level = 1
    ind = beg + 1
    while level > 0 and ind < len(expression):
        if expression[ind] == ')':
            level = level - 1
        elif expression[ind] == '(':
            level = level + 1
        ind = ind + 1
    return ind - 1

