import json as JSON
import functools


def nested_print(d):
    print(JSON.dumps(d, indent=4))
    return


def compose(*funcs):
    return lambda x: functools.reduce(lambda v, f: f(v), funcs, x)
