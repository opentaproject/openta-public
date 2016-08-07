from pyramid.response import Response, FileResponse
from xmljson import badgerfish as bf
import traceback
from xml.etree.ElementTree import fromstring
import os
import sys


def exercises():  # {{{
    exerciselist = []
    try:
        exerciselist = [
            name
            for name in os.listdir('./exercises/')
            if os.path.isdir(os.path.join('./exercises', name))
        ]
    except Exception:
        print(traceback.format_exc())
        pass
    print(exerciselist)
    return exerciselist  # }}}


# Need to split into JSON reading part and request handling
def exerciseJSON(path):  # {{{
    obj = {}
    try:
        print('./exercises/{path}/problem.xml'.format(path=path))
        xmlfile = open('./exercises/{path}/problem.xml'.format(path=path))
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
        xmlfile = open('./exercises/{path}/problem.xml'.format(path=path))
        xml = xmlfile.read()
    except Exception:
        print("exerciseXML: Error reading XML for {path}".format(path=path))
        print(traceback.format_exc())
        pass
    return xml  # }}}


# This is waiting for rewrite of exerciseJSON
# def checkExercise(exercise, question, expression):
#    json = exer
