from exercises.xmljson import BadgerFish
from xml.etree.ElementTree import fromstring, ParseError
from lxml import etree
from exercises.paths import EXERCISES_PATH
from exercises.util import deep_get, nested_print
from functools import reduce, lru_cache
from PIL import Image
import os.path
import uuid

bf = BadgerFish(xml_fromstring=False)


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
        keyfile.write(key)
    return key


def exercise_key_get_or_create(path):
    try:
        key = exercise_key_get(path)
        return key
    except IOError:
        key = exercise_key_set(path, str(uuid.uuid4()))
        return key


# @lru_cache(maxsize=128)
def exercise_json(path, hide_answers=False):  # {{{
    xmlfile = open(EXERCISES_PATH + '/{path}/exercise.xml'.format(path=path))
    xml = xmlfile.read()
    obj = {}
    try:
        root = fromstring(xml)
        if hide_answers:
            questions = root.findall('./question/expression/..')
            for question in questions:
                expression = question.find('expression')
                question.remove(expression)
        obj = bf.data(root)
    except ParseError as e:
        raise ExerciseParseError(e)
    questions = deep_get(obj, 'exercise', 'question')
    if questions:
        if not isinstance(questions, list):
            questions = [questions]
            obj['exercise']['question'] = questions
    globals_ = deep_get(obj, 'exercise', 'global')
    if globals_:
        if not isinstance(globals_, list):
            globals_ = [globals_]
            obj['exercise']['global'] = globals_
    return obj  # }}}


def exercise_validate_and_json(path):
    return exercise_json(path)


# @lru_cache(maxsize=128)
def exercise_xml(path):  # {{{
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


def question_validate_xmltree(question):
    if question.get('key') == None or question.get('type') == None:
        return False
    return True


# @lru_cache(maxsize=128)
def exercise_xmltree(exercise_path):
    xmlfile = EXERCISES_PATH + '/{path}/exercise.xml'.format(path=exercise_path)
    parser = etree.XMLParser(remove_blank_text=True)
    try:
        root = etree.parse(xmlfile, parser)
        return root
    except etree.XMLSyntaxError as e:
        raise ExerciseParseError(e)


def question_xmltree_get(exercise_xmltree, question_key):
    question = exercise_xmltree.xpath('/exercise/question[@key="{key}"]'.format(key=question_key))[
        0
    ]
    return question


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
        global_data = deep_get(json, 'exercise', 'global')
        if global_data and 'type' in found[0]['@attr']:
            if not isinstance(global_data, list):
                global_data = [global_data]
            global_for_type = list(
                filter(
                    lambda g: '@attr' in g
                    and 'type' in g['@attr']
                    and g['@attr']['type'] == found[0]['@attr']['type'],
                    global_data,
                )
            )
            if len(global_for_type) == 1:
                found[0].update({'global': global_for_type[0]})
        return found[0]
    else:
        return "{}"


def exercise_check_thumbnail(xmltree, path):
    messages = []
    thumbnail_path = EXERCISES_PATH + '/{path}/thumbnail.png'.format(path=path)
    if not os.path.isfile(thumbnail_path):
        figure = xmltree.xpath('/exercise//figure')
        try:
            figurepath = figure[0].text
        except IndexError:
            messages.append('warning', "No figure for exercise")
            return messages
        size = (100, 100)
        try:
            image = Image.open(EXERCISES_PATH + '/{path}/'.format(path=path) + figurepath)
        except IOError:
            messages.append(('error', 'Could not open figure'))
            return messages
        image.thumbnail(size, Image.ANTIALIAS)
        background = Image.new('RGBA', size, (255, 255, 255, 0))
        background.paste(
            image, (round((size[0] - image.size[0]) / 2), round((size[1] - image.size[1]) / 2))
        )
        background.save(thumbnail_path)
        messages.append(('success', 'Created thumbnail'))
    return messages


def invalidate_caches():
    pass
    # exercise_json.cache_clear()
    # exercise_xml.cache_clear()
    # exercise_xmltree.cache_clear()
