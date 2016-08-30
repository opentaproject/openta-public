from xmljson import badgerfish as bf
from xml.etree.ElementTree import fromstring, ParseError
from exercises.paths import EXERCISES_PATH
from exercises.util import deep_get, nested_print
from functools import reduce


class ExerciseParseError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def exercise_json(path):  # {{{
    xmlfile = open(EXERCISES_PATH + '/{path}/exercise.xml'.format(path=path))
    xml = xmlfile.read()
    obj = bf.data(fromstring(xml))
    questions = deep_get(obj, 'exercise', 'question')
    if questions:
        if not isinstance(questions, list):
            questions = [questions]
            obj['exercise']['question'] = questions
    #    questions = map( lambda q: { q['@key']: q }, questions)
    #    questions = reduce(lambda a, b: {**a, **b}, questions)
    return obj  # }}}


def exercise_validate_and_json(path):
    try:
        json = exercise_json(path)
    except ParseError as e:
        raise ExerciseParseError(e)
    if not deep_get(json, 'exercise', '@key'):
        raise ExerciseParseError('No exercise key')
    return json


# except ValueError as err:
#     print(err)
#     return (False, {}, err)
# except ParseError as err:
#     print(err)
#     return (False, {}, err)
# except IOError as err:
#     print(err)
#     return (False, {}, err)


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
    # question_json = deep_get(json, 'exercise', 'question', question_key)
    questions = deep_get(json, 'exercise', 'question')
    found = list(filter(lambda q: q['@key'] == question_key, questions))
    if len(found) == 1:
        return found[0]
    else:
        return "{}"
