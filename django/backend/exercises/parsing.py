from xmljson import badgerfish as bf
from xml.etree.ElementTree import fromstring, ParseError
from exercises.paths import EXERCISES_PATH
from exercises.util import deep_get, nested_print
from functools import reduce


def exercise_json(path):  # {{{
    xmlfile = open(EXERCISES_PATH + '/{path}/exercise.xml'.format(path=path))
    xml = xmlfile.read()
    obj = bf.data(fromstring(xml))
    questions = deep_get(obj, 'exercise', 'question')
    if questions:
        if not isinstance(questions, list):
            questions = [questions]
        questions = map(lambda q: {q['@key']: q}, questions)
        questions = reduce(lambda a, b: {**a, **b}, questions)
        obj['exercise']['question'] = questions
    return obj  # }}}


def exercise_validate_and_json(path):
    try:
        json = exercise_json(path)
        if not deep_get(json, 'exercise', '@key'):
            raise ValueError('No key')
        return (True, json)
    except ValueError as err:
        print(err)
        return (False, {})
    except ParseError as err:
        print(err)
        return (False, {})
    except IOError as err:
        print(err)
        return (False, {})


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
    if not '@key' in question:
        return False
    return True


def question_json_get(exercise_path, question_key):
    json = exercise_json(exercise_path)
    question_json = deep_get(json, 'exercise', 'question', question_key)
    return question_json
