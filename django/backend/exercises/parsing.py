from xml.etree.ElementTree import fromstring, ParseError
from lxml import etree
from PIL import Image
from django.utils.timezone import now
import os.path
import uuid
import time
import logging
from subprocess import check_output, CalledProcessError

import exercises.paths as paths
from exercises.util import deep_get
from exercises.xmljson import BadgerFish

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


def is_exercise(base_path, path):
    return os.path.isfile(base_path + '/{path}/exercise.xml'.format(path=path))


def list_exercises_in_folder(base_path, path):
    full_path = os.path.join(base_path, *path.split('/'))
    exerciselist = []
    for root, directories, filenames in os.walk(full_path, followlinks=True):
        for filename in filenames:
            if filename == 'exercise.xml':
                name = os.path.basename(os.path.normpath(root))
                relpath = root[len(base_path) :]
                exerciselist.append({'name': name, 'relpath': relpath})
    return exerciselist


def exercise_key_get(base_path, path):
    with open(base_path + '/{path}/exercisekey'.format(path=path)) as keyfile:
        exercisekey = keyfile.read().strip(" \n")
        return exercisekey


def exercise_key_set(base_path, path, key):
    with open(base_path + '/{path}/exercisekey'.format(path=path), 'w') as keyfile:
        keyfile.write(key)
    return key


def exercise_key_get_or_create(base_path, path):
    try:
        key = exercise_key_get(base_path, path)
        return key
    except IOError:
        key = exercise_key_set(base_path, path, str(uuid.uuid4()))
        return key


def exercise_json(base_path, path, hide_answers=False, sensitive_tags={}, sensitive_attrs={}):
    xmlfile = open(base_path + '/{path}/exercise.xml'.format(path=path))
    xml = xmlfile.read()
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
    obj = {}
    try:
        root = fromstring(xml)
        if hide_answers:
            for question_type, tags in sensitive_tags.items():
                questions = root.findall('./question[@type="{type}"]'.format(type=question_type))
                for question in questions:
                    for tag in tags:
                        node = question.find(tag)
                        question.remove(node)
            for question_type, attrs in sensitive_attrs.items():
                for attr in attrs:
                    nodes = root.findall(
                        './/question[@type="{type}"]/*[@{attr}]'.format(
                            type=question_type, attr=attr
                        )
                    )
                    for node in nodes:
                        node.attrib.pop(attr, None)
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
    return obj


def exercise_validate_and_json(path):
    return exercise_json(path)


def exercise_xml(base_path, path):
    xmlfile = open(base_path + '/{path}/exercise.xml'.format(path=path))
    xml = xmlfile.read()
    return xml


def exercise_save(base_path, exercise, xml, backup=None):
    messages = []
    logger.info('Saving ' + exercise)
    if backup is not None:
        exercise_path = os.path.join(base_path, *exercise.split('/'))
        backup_path = os.path.join(exercise_path, 'history')
        backup_file = os.path.join(backup_path, backup)
        os.makedirs(backup_path, exist_ok=True)
        try:
            with open(backup_file, 'w') as file:
                file.write(xml)
        except IOError:
            messages.append(('warning', "Couldn't write backup file"))
    with open(base_path + '/{path}/exercise.xml'.format(path=exercise), 'w') as file:
        file.write(xml)
    messages.append(('success', 'Saved exercise'))
    return messages


def question_validate(question):
    if '@attr' not in question or 'key' not in question['@attr']:
        return False
    return True


def question_validate_xmltree(question):
    if question.get('key') is None or question.get('type') is None:
        return False
    return True


def exercise_xmltree(base_path, exercise_path):
    xmlfile = base_path + '/{path}/exercise.xml'.format(path=exercise_path)
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


def question_json_get(base_path, exercise_path, question_key):
    json = exercise_json(base_path, exercise_path)
    questions = deep_get(json, 'exercise', 'question')
    found = list(
        filter(
            lambda q: ('@attr' in q and 'key' in q['@attr'] and q['@attr']['key'] == question_key),
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
                    lambda g: (
                        '@attr' in g
                        and 'type' in g['@attr']
                        and g['@attr']['type'] == found[0]['@attr']['type']
                    ),
                    global_data,
                )
            )
            if len(global_for_type) == 1:
                found[0].update({'global': global_for_type[0]})
        return found[0]
    else:
        return "{}"


def exercise_check_thumbnail(base_path, xmltree, path):
    messages = []
    thumbnail_path = base_path + '/{path}/thumbnail.png'.format(path=path)
    if not os.path.isfile(thumbnail_path):
        figure = xmltree.xpath('/exercise//figure')
        try:
            figurepath = figure[0].text.strip()
        except (IndexError, NameError, AttributeError) as e:
            return messages
        full_figurepath = base_path + '/{path}/'.format(path=path) + figurepath
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


def exercise_add(base_path, folder, name):
    path = os.path.join(base_path, folder, name)
    template_path = os.path.join(paths.TEMPLATE_EXERCISE_PATH, "exercise.xml")
    if not os.path.isdir(base_path):
        os.makedirs(path, exist_ok=True)
    # if not os.path.isdir(os.path.join(base_path, folder)):
    #    return {'error': 'There is no such folder!'}
    if os.path.isdir(path):
        return {'error': 'There is already a folder in the file tree with this name.'}
    if is_exercise(base_path, path):
        return {'error': 'There is already an exercise with that name in the file tree'}
    os.makedirs(path, exist_ok=True)
    xmlpath = os.path.join(path, "exercise.xml")
    template_data = "<exercise>\n\t<exercisename>\n\t\t{name}\n\t</exercisename>\n</exercise>".format(
        name=name
    )
    try:
        with open(template_path, 'r') as file:
            template_data = file.read().replace('__exercise_name__', name)
    except IOError:
        pass
    try:
        with open(xmlpath, 'w') as file:
            file.write(template_data)
    except IOError:
        return {'error': 'Could not write exercise xml file.'}
    return {'success': True, 'path': os.path.join(folder, name)}


def exercise_delete(base_path, path):
    exercise_path = os.path.join(base_path, *path.split('/'))
    exercise_folder_name = os.path.basename(os.path.normpath(exercise_path))
    date_now = "{:%Y%m%d_%H:%M:%S_%f}".format(now())
    deleted_relative_path = os.path.join(paths.TRASH_PATH, exercise_folder_name + "." + date_now)
    deleted_path = os.path.join(base_path, deleted_relative_path)
    if not os.path.isdir(exercise_path):
        return {'error': 'There is no such exercise folder!'}
    if not is_exercise(path):
        return {'error': 'The folder does not seem to be an exercise'}
    try:
        os.renames(exercise_path, deleted_path)
    except OSError:
        return {'error': 'Could not rename exercise to deleted spec.'}
    return {'success': True, 'path': deleted_relative_path}


def exercise_move(base_path, path, newfolder):
    exercise_path = os.path.join(base_path, *path.split('/'))
    exercise_folder_name = os.path.basename(os.path.normpath(exercise_path))
    exercise_old_folder = os.path.dirname(os.path.normpath(path.strip('/')))
    moved_relative_folder = os.path.join(*newfolder.split('/'))
    moved_exercise_path = os.path.join(moved_relative_folder, exercise_folder_name)
    moved_full_path = os.path.join(base_path, moved_exercise_path)
    date_now = "{:_%Y%m%d_%H:%M:%S_%f}".format(now())

    if exercise_old_folder == moved_relative_folder:
        return {'error': 'Same folder'}
    print(exercise_path)
    if not os.path.isdir(exercise_path):
        return {'error': 'There is no such exercise folder!'}
    if not is_exercise(base_path, path):
        return {'error': 'The folder does not seem to be an exercise'}
    if os.path.isdir(moved_full_path):
        moved_exercise_path += "." + date_now
        moved_full_path = os.path.join(base_path, moved_exercise_path)
    try:
        os.renames(exercise_path, moved_full_path)
    except OSError:
        return {'error': 'Could not move exercise folder.'}
    return {'success': True, 'path': moved_exercise_path}


def exercises_move_folder(base_path, oldfolder, newfolder):
    full_oldfolder = os.path.join(base_path, *oldfolder.split('/'))
    full_newfolder = os.path.join(base_path, *newfolder.split('/'))

    if os.path.isdir(full_newfolder):
        return {'error': 'Folder already exists'}
    if not os.path.isdir(full_oldfolder):
        return {'error': 'Original folder does not exist.'}

    try:
        os.rename(full_oldfolder, full_newfolder)
        exercises = list_exercises_in_folder(base_path, newfolder)
    except OSError:
        return {'error': 'Could not move folder'}
    return {'success': True, 'exercises': exercises}


def list_assets(base_path, exercise_path, types):
    path = os.path.join(base_path, *exercise_path.split('/'))
    all_files = os.listdir(path)
    assets = [{'filename': asset} for asset in all_files if asset.lower().endswith(types)]
    return assets


def has_asset(base_path, exercise_path, asset):
    full_path = os.path.join(base_path, *exercise_path.split('/'))
    file_path = os.path.join(full_path, asset)
    return os.path.isfile(file_path)


def add_asset(base_path, exercise_path, asset_file, types):
    full_path = os.path.join(base_path, *exercise_path.split('/'))
    file_path = os.path.join(full_path, asset_file.name)
    if not asset_file.name.lower().endswith(types):
        return {'error': 'File type not allowed, valid filetypes are: ' + ', '.join(types)}
    if os.path.isfile(file_path):
        return {'error': 'File already exists.'}
    try:
        with open(file_path, 'wb') as asset:
            for chunk in asset_file.chunks():
                asset.write(chunk)
    except IOError:
        return {'error': "Couldn't write to asset file " + file_path}
    return {'success': 'Wrote file'}


def delete_asset(base_path, exercise_path, asset_file):
    full_path = os.path.join(base_path, *exercise_path.split('/'))
    file_path = os.path.join(full_path, asset_file)
    if not os.path.isfile(file_path):
        return {'error': 'No such file!'}
    try:
        os.remove(file_path)
    except IOError:
        return {'error': "Couldn't delete asset file " + file_path}
    if os.path.isfile(file_path):
        return {'error': "Couldn't delete asset file " + file_path}

    return {'success': 'Deleted file'}


def list_history(base_path, exercise_path):
    exercise_full_path = os.path.join(base_path, *exercise_path.split('/'))
    backup_path = os.path.join(exercise_full_path, 'history')
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


def exercise_xml_history(base_path, exercise_path, name):
    exercise_full_path = os.path.join(base_path, *exercise_path.split('/'))
    backup_path = os.path.join(exercise_full_path, 'history')
    fullpath = os.path.join(backup_path, name)
    if not os.path.isfile(fullpath):
        return {'error': 'No such file.'}
    xmlfile = open(fullpath)
    xml = xmlfile.read()
    return {'success': 'Ok', 'xml': xml}


def exercise_json_history(base_path, exercise_path, name):
    exercise_full_path = os.path.join(base_path, *exercise_path.split('/'))
    backup_path = os.path.join(exercise_full_path, 'history')
    fullpath = os.path.join(backup_path, name)
    if not os.path.isfile(fullpath):
        return {'error': 'No such file.'}
    xmlfile = open(fullpath)
    xml = xmlfile.read()
    return exercise_xml_to_json(xml)


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
