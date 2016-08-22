from xmljson import badgerfish as bf
import traceback
from xml.etree.ElementTree import fromstring
import os
import sys
import functools
import operator
import json as JSON
import exercises.symbolic as symbolic
from time import sleep
from random import random
from exercises.paths import EXERCISES_PATH


def deep_get(dictionary, *keys):
    return functools.reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)


def nested_print(d):
    print(JSON.dumps(d, indent=4))
    return


def compose(*funcs):
    return lambda x: functools.reduce(lambda v, f: f(v), funcs, x)


def exercises():  # {{{
    exerciselist = []
    try:
        exerciselist = [
            name
            for name in os.listdir(EXERCISES_PATH)
            if os.path.isdir(os.path.join(EXERCISES_PATH, name))
        ]
    except Exception:
        print(traceback.format_exc())
        pass
    print(exerciselist)
    return exerciselist  # }}}


def exerciseJSON(path):  # {{{
    obj = {}
    try:
        # print(EXERCISES_PATH + '/{path}/problem.xml'.format(path=path))
        xmlfile = open(EXERCISES_PATH + '/{path}/problem.xml'.format(path=path))
        xml = xmlfile.read()
        obj = bf.data(fromstring(xml))
    except Exception:
        print("exerciseJSON: Error reading or parsing JSON for {path}".format(path=path))
        print(traceback.format_exc())
        pass
    return obj  # }}}


def exerciseXML(path):  # {{{
    xml = ''
    try:
        xmlfile = open(EXERCISES_PATH + '/{path}/problem.xml'.format(path=path))
        xml = xmlfile.read()
    except Exception:
        print("exerciseXML: Error reading XML for {path}".format(path=path))
        print(traceback.format_exc())
        pass
    return xml  # }}}


def parseIngress(ingress):  # {{{
    rawvars = ingress.split(';')
    pipeline = compose(
        functools.partial(filter, operator.truth),
        functools.partial(map, lambda x: x.split('=')),
        functools.partial(map, lambda x: {'name': x[0].strip(), 'value': x[1].strip()}),
    )
    variables = list(pipeline(rawvars))
    return variables  # }}}


def exerciseCheck(exercise, question, expression):  # {{{
    json = exerciseJSON(exercise)
    print(JSON.dumps(json, indent=4))
    # print(JSON.dumps(deep_get(json,'problem','thecorrectanswer'), indent=4))
    questions = deep_get(json, 'problem', 'thecorrectanswer')
    if question < len(questions):
        variables = parseIngress(questions[0].get('$'))
        correct = questions[question].get('$').replace(';', '')
        result = symbolic.compareNumeric(JSON.dumps(variables), expression, correct)
        latex = {'latex': symbolic.toLatex(expression)}
        result.update(latex)
        # Need to merge with result dictionary...
        return result

        # nested_print(questions[question].get('$'))
    # nested_print(questions[1].get('$'))

    return True  # }}}


def exerciseSave(exercise, xml):  # {{{
    print('Saving ' + exercise)
    with open(EXERCISES_PATH + '/{path}/problem.xml'.format(path=exercise), 'w') as file:
        file.write(xml)
    # sleep(0.5)
    # if random() > 0.5:
    #    raise IOError('Simulated IOError')
    return {'success': True}  # }}}
