from exercises.xmljson import badgerfish as bf
from xml.etree.ElementTree import fromstring, ParseError
from exercises.paths import EXERCISES_PATH
from exercises.util import deep_get, nested_print
from functools import reduce
import os.path
import uuid


class ExerciseParseError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ExerciseNotFound(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def is_exercise(path):
    return os.path.isfile(EXERCISES_PATH + '/{path}/exercise.xml'.format(path=path))


def exercise_key_get(path):
    with open(EXERCISES_PATH + '/{path}/exercisekey'.format(path=path)) as keyfile:
        exercisekey = keyfile.read().strip(" \n")
        return exercisekey


def exercise_key_set(path, key):
    with open(EXERCISES_PATH + '/{path}/exercisekey'.format(path=path), 'w') as keyfile:
        print(key)
        keyfile.write(key)
    return key


def exercise_key_get_or_create(path):
    try:
        key = exercise_key_get(path)
        return key
    except IOError:
        key = exercise_key_set(path, str(uuid.uuid4()))
        return key


def exercise_json(path):  # {{{
    xmlfile = open(EXERCISES_PATH + '/{path}/exercise.xml'.format(path=path))
    xml = xmlfile.read()
    obj = {}
    try:
        obj = bf.data(fromstring(xml))
    except ParseError as e:
        raise ExerciseParseError(e)
    questions = deep_get(obj, 'exercise', 'question')
    if questions:
        if not isinstance(questions, list):
            questions = [questions]
            obj['exercise']['question'] = questions
    return obj  # }}}


def exercise_validate_and_json(path):
    return exercise_json(path)


def exercise_xml(path):  # {{{
    print("path: " + path)
    xmlfile = open(EXERCISES_PATH + '/{path}/exercise.xml'.format(path=path))
    xml = xmlfile.read()
    return xml  # }}}


def exercise_save(exercise, xml):  # {{{
    print('Saving ' + exercise)
    with open(EXERCISES_PATH + '/{path}/exercise.xml'.format(path=exercise), 'w') as file:
        file.write(xml)
    return {'success': True}  # }}}


def question_validate(question):
    if not '@attr' in question or not 'key' in question['@attr']:
        return False
    return True


def question_json_get(exercise_path, question_key):
    json = exercise_json(exercise_path)
    questions = deep_get(json, 'exercise', 'question')
    found = list(
        filter(
            lambda q: '@attr' in q and 'key' in q['@attr'] and q['@attr']['key'] == question_key,
            questions,
        )
    )
    if len(found) == 1:
        return found[0]
    else:
        return "{}"
