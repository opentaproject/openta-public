import json as JSON
import functools


def nested_print(d):
    print(JSON.dumps(d, indent=4))
    return


def deep_get(dictionary, *keys, default=None):
    result = functools.reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)
    if result == None:
        return default
    else:
        return result


def compose(*funcs):
    return lambda x: functools.reduce(lambda v, f: f(v), funcs, x)
