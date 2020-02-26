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
