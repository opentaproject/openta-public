from xml.etree.ElementTree import fromstring, ParseError, tostring
from exercises.applymacros import apply_macros_to_exercise
from lxml import etree
from PIL import Image
from django.utils.timezone import now
import os.path
import uuid
import time
import logging
from subprocess import check_output, CalledProcessError

from exercises.paths import *
from exercises.util import deep_get

from exercises.xmljson import BadgerFish
import exercises.paths as paths
import re

logger = logging.getLogger(__name__)

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
    return os.path.isfile(os.path.join(path, paths.EXERCISE_XML))


def fromString(xml):
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml, parser=parser)
    return root


def fromString(xml):
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml, parser=parser)
    return root


def list_exercises_in_folder(path):
    exerciselist = []
    for root, _, filenames in os.walk(path, followlinks=True):
        for filename in filenames:
            if filename == paths.EXERCISE_XML:
                name = os.path.basename(os.path.normpath(root))
                exerciselist.append({'name': name, 'path': root})
    return exerciselist


def exercise_key_get(path):
    key_path = os.path.join(path, EXERCISE_KEY)
    with open(key_path) as keyfile:
        exercisekey = keyfile.read().strip(" \n")
        return exercisekey


def _exercise_key_set(path, key):
    key_path = os.path.join(path, EXERCISE_KEY)
    with open(key_path, 'w') as keyfile:
        keyfile.write(key)
    return key


def _exercise_key_delete(path):
    key_path = os.path.join(path, EXERCISE_KEY)
    os.remove(key_path)


def exercise_key_get_or_create(path):
    try:
        key = exercise_key_get(path)
        return key
    except IOError:
        key = _exercise_key_set(path, str(uuid.uuid4()))
        return key


def exercise_json(path, hide_answers=False, sensitive_tags={}, sensitive_attrs={}):
    xml_path = os.path.join(path, EXERCISE_XML)
    with open(xml_path, mode='rb') as fil:
        xml = fil.read()
    return exercise_xml_to_json(xml, hide_answers, sensitive_tags, sensitive_attrs)


def exercise_xml_to_json(xml, hide_answers=False, sensitive_tags={}, sensitive_attrs={}):
    """
    Converts exercise xml to json using the custom xmljson module. Enforces
    list structure of question and global tags.

    Args:
        xml: xml data (string)
        hide_answers: Removes sensitive tags/attributes (i.e. if student)
        sensitive_tags: { question_type: [tag1, tag2, ...], ... }
        sensitive_attrs: { question_type: [attr1, attr2, ...], ... }
        without_layout: Discard layout information (normally the children of
            each node is added in layout order in __children__ for convenience,
            this is a possible source for stray sensitive tags/attributes)

    Returns:
        Dictionary corresponding to the JSON representation.
    """
    # print("PARSING: exercise_xml_to_json")
    obj = {}
    taglist = []
    try:
        root = fromString(xml)
        if hide_answers:
            for question_type, tags in sensitive_tags.items():
                questions = root.findall('./question[@type="{type}"]'.format(type=question_type))
                for question in questions:
                    for tag in tags:
                        if tag not in taglist:
                            taglist = taglist + [tag]
                        nodes = question.findall('.//' + tag)
                        if not isinstance(nodes, list):
                            nodes = []
                        for node in nodes:
                            parent = node.getparent()
                            parent.remove(node)
                        if tag == 'value':
                            variablesnode = question.find('variables')
                            if not variablesnode is None:
                                variablesnode.text = 'replaced by sensitive tag value'
            for question_type, attrs in sensitive_attrs.items():
                for attr in attrs:
                    nodes = root.findall(
                        './/question[@type="{type}"]/*[@{attr}]'.format(
                            type=question_type, attr=attr
                        )
                    )
                    for node in nodes:
                        node.attrib.pop(attr, None)
            if 'value' in taglist:
                globalnodes = root.findall('./global')
                if len(globalnodes) > 0:
                    globalnode = globalnodes[0]
                    # print("global text = ", globalnode.text)
                    globalnode.text = 'replaced by sensitive tag value'
                    valuenodes = globalnode.findall('.//value')
                    for valuenode in valuenodes:
                        # print("REMOVE VALUENODE")
                        parent = valuenode.getparent()
                        parent.remove(valuenode)

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

    globals_ = deep_get(obj, 'exercise', 'global')
    if globals_:
        if not isinstance(globals_, list):
            globals_ = [globals_]
            nglobals = []
            for global_ in globals_:
                if hide_answers:
                    print("GLOBAL_ = ", global_)
                    global_['$'] = 'HIDE THE TEXT'
                    global_['$children$'][0]['$'] = 'HIDE THE TEXT 2'
                nglobals = nglobals + [global_]
            obj['exercise']['global'] = nglobals
    return obj


def exercise_xml(path):
    xml_path = os.path.join(path, EXERCISE_XML)
    # xmlfile = open(xml_path)
    # xml = xmlfile.read()
    with open(xml_path, mode='rb') as fil:
        xml = fil.read()
    return xml


def exercise_save(path, xml, backup=None):
    messages = []
    logger.info('Saving ' + path)
    if backup is not None:
        backup_path = os.path.join(path, EXERCISE_HISTORY)
        backup_file = os.path.join(backup_path, backup)
        os.makedirs(backup_path, exist_ok=True)
        try:
            with open(backup_file, 'w') as file:
                file.write(xml)
        except IOError:
            messages.append(('warning', "Couldn't write backup file"))
    xml_path = os.path.join(path, paths.EXERCISE_XML)
    with open(xml_path, 'w') as file:
        file.write(xml)
    messages.append(('success', 'Saved exercise'))
    return messages


def question_validate_xmltree(question):
    if question.get('key') is None or question.get('type') is None:
        return False
    return True


def exercise_xmltree(path):
    xml_path = os.path.join(path, paths.EXERCISE_XML)
    parser = etree.XMLParser(remove_blank_text=True)
    try:
        root = etree.parse(xml_path, parser)
        return root
    except etree.XMLSyntaxError as e:
        # print("PARSING: exercise_xmltree failed", xml )
        raise ExerciseParseError(e)


def question_xmltree_get(exercise_xmltree, question_key, usermacros={}):
    return global_and_question_xmltree_get(exercise_xmltree, question_key, usermacros)[1]


def question_json_get(path, question_key, usermacros={}):
    usermacros['@call'] = 'QUESTION_JSON_GET'
    raw_json = exercise_json(path, True)
    exercise_key = exercise_key_get(path)
    return question_json_get_from_raw_json(raw_json, exercise_key, question_key, usermacros)


def question_json_get_from_raw_json(raw_json, exercise_key, question_key, usermacros={}):
    questions = deep_get(raw_json, 'exercise', 'question')
    found = list(
        filter(
            lambda q: ('@attr' in q and 'key' in q['@attr'] and q['@attr']['key'] == question_key),
            questions,
        )
    )
    if len(found) == 1:
        global_data = deep_get(raw_json, 'exercise', 'global')
        # print("GLOBAL DATA = ", global_data )
        if global_data:  # and 'type' in found[0]['@attr']:
            if not isinstance(global_data, list):
                global_data = [global_data]
            global_for_type = list(
                filter(
                    lambda g: (
                        ('@attr' not in g)
                        or (
                            '@attr' in g
                            and 'type' in g['@attr']
                            and g['@attr']['type'] == found[0]['@attr']['type']
                        )
                    ),
                    global_data,
                )
            )
            if len(global_for_type) == 1:
                # print("UPDATE GLOBAL DATA")
                found[0].update({'global': global_for_type[0]})
        found[0]['exercise_key'] = exercise_key
        return found[0]
    else:
        return "{}"


def exercise_check_thumbnail(xmltree, path):
    messages = []
    thumbnail_path = os.path.join(path, EXERCISE_THUMBNAIL)
    if not os.path.isfile(thumbnail_path):
        figure = xmltree.xpath('/exercise//figure')
        try:
            figurepath = figure[0].text.strip()
        except (IndexError, NameError, AttributeError) as e:
            return messages
        full_figurepath = os.path.join(path, figurepath)
        _, ext = os.path.splitext(figurepath)
        iext = ext.lower()
        size = (100, 100)
        if iext == '.pdf':
            messages.append(('info', 'Trying to create thumbnail from pdf...'))
            try:
                check_output(['convert', '-thumbnail', "100x100", full_figurepath, thumbnail_path])
            except (CalledProcessError, IOError) as e:
                messages.append(('warning', "Thumbnail creation failed for pdf"))
                messages.append(('warning', str(e)))
                return messages
        else:
            try:
                image = Image.open(full_figurepath)
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


def exercise_add(folder, name):
    full_path = os.path.join(folder, name)
    template_path = os.path.join(TEMPLATE_EXERCISE_PATH, "exercise.xml")
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    if os.path.isdir(full_path):
        return {'error': 'There is already a folder in the file tree with this name.'}
    if is_exercise(full_path):
        return {'error': 'There is already an exercise with that name in the file tree'}
    os.makedirs(full_path, exist_ok=True)
    xml_path = os.path.join(full_path, paths.EXERCISE_XML)
    template_data = "<exercise>\n\t<exercisename>\n\t\t{name}\n\t</exercisename>\n</exercise>".format(
        name=name
    )
    try:
        with open(template_path, 'r') as file:
            template_data = file.read().replace('__exercise_name__', name)
    except IOError:
        pass
    try:
        with open(xml_path, 'w') as file:
            file.write(template_data)
    except IOError:
        return {'error': 'Could not write exercise xml file.'}
    return {'success': True, 'path': os.path.join(folder, name)}


def exercise_delete(course_path, path):
    exercise_folder_name = os.path.basename(os.path.normpath(path))
    date_now = "{:%Y%m%d_%H:%M:%S_%f}".format(now())
    deleted_relative_path = os.path.join(TRASH_PATH, exercise_folder_name + "." + date_now)
    deleted_path = os.path.join(course_path, deleted_relative_path)
    if not os.path.isdir(path):
        return {'error': 'There is no such exercise folder!'}
    if not is_exercise(path):
        return {'error': 'The folder does not seem to be an exercise'}
    try:
        os.renames(path, deleted_path)
    except OSError:
        return {'error': 'Could not rename exercise to deleted spec.'}
    return {'success': True, 'path': deleted_relative_path}


def exercise_move(path, new_path):
    date_now = "{:_%Y%m%d_%H:%M:%S_%f}".format(now())

    if path == new_path:
        return {'error': 'Same folder'}
    if not os.path.isdir(path):
        return {'error': 'There is no such exercise folder!'}
    if not is_exercise(path):
        return {'error': 'The folder does not seem to be an exercise'}
    if os.path.isdir(new_path):
        new_path += "." + date_now
    try:
        os.renames(path, new_path)
    except OSError as e:
        return {'error': 'Could not move exercise folder: {}'.format(str(e))}
    return {'success': True, 'path': new_path}


def exercises_move_folder(old_path, new_path):
    if os.path.isdir(new_path):
        return {'error': 'Folder already exists'}
    if not os.path.isdir(old_path):
        return {'error': 'Original folder does not exist.'}

    try:
        os.rename(old_path, new_path)
        exercises = list_exercises_in_folder(new_path)
    except OSError:
        return {'error': 'Could not move folder'}
    return {'success': True, 'exercises': exercises}


def list_history(path):
    backup_path = os.path.join(path, EXERCISE_HISTORY)
    history = []
    if not os.path.isdir(backup_path):
        return []
    content = os.listdir(backup_path)
    for entry in content:
        fullpath = os.path.join(backup_path, entry)
        if os.path.isfile(fullpath) and entry.endswith('.xml'):
            mtime = os.stat(fullpath).st_mtime
            dtime = time.time() - mtime
            history.append({'filename': entry, 'modified': mtime, 'delta_time': dtime})
    return history


def exercise_xml_history(path, name):
    backup_path = os.path.join(path, EXERCISE_HISTORY)
    fullpath = os.path.join(backup_path, name)
    if not os.path.isfile(fullpath):
        return {'error': 'No such file.'}
    with open(fullpath, mode='rb') as fil:
        xml = fil.read()
    # xmlfile = open(fullpath)
    # xml = xmlfile.read()
    return {'success': 'Ok', 'xml': xml}


def exercise_json_history(path, name):
    res = exercise_xml_history(path, name)
    if 'error' in res:
        return res
    return exercise_xml_to_json(res['xml'])


def get_translations(xml):
    """Find translation subtags.

    Returns a dict with the translations corresponding to
    the <alt lang=".."> tags.
    """
    ret_langs = dict()
    alt_langs = xml.xpath('./alt[@lang]')
    for lang in alt_langs:
        ret_langs[lang.get('lang')] = lang.text
    return ret_langs


def getkey(stringin):
    key = re.sub(r'\s+', '', stringin)
    return key


def get_questionkeys_from_xml(xml):
    qnodes = (etree.fromstring(xml)).findall('./question')
    questionlist = []
    for qnode in qnodes:
        questionlist.append(qnode.attrib['key'])
    return questionlist


def global_xmltree_get(exercise_xmltree, question_key, usermacros={}):
    return global_and_question_xmltree_get(exercise_xmltree, question_key, usermacros)[0]


def global_and_question_xmltree_get(exercise_xmltree, question_key, usermacros={}):
    xml = etree.tostring(exercise_xmltree)
    root = etree.fromstring(xml)
    root = apply_macros_to_exercise(root, usermacros)
    global_xpath = (
        '/exercise/global[@type="{type}"] | /exercise/global[not(@type)] | /exercise/global'
    )
    global_xmltree = (root.xpath(global_xpath) or [None])[0]
    question_xmltree = root.xpath('/exercise/question[@key="{key}"]'.format(key=question_key))[0]
    return [global_xmltree, question_xmltree]
