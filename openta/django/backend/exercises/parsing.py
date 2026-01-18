# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import glob
import datetime
import html
import hashlib
import os
import logging
import traceback
import os.path
import random
import re
import time
import uuid
from utils import response_from_messages
from django.conf import settings
from subprocess import CalledProcessError, check_output
from xml.etree.ElementTree import ParseError

from django.utils.timezone import now
from lxml import etree
from PIL import Image
from rest_framework.response import Response
from slugify import slugify

import exercises.paths as paths
from exercises.applymacros import apply_macros_to_exercise
from exercises.paths import *
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


def is_exercise(path):
    return os.path.isfile(os.path.join(path, paths.EXERCISE_XML))


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
                exerciselist.append({"name": name, "path": root})
    return exerciselist


def exercise_key_get(path):
    key_path = os.path.join(path, EXERCISE_KEY)
    with open(key_path) as keyfile:
        exercisekey = keyfile.read().strip(" \n")
        return exercisekey


def _exercise_key_set(path, key):
    key_path = os.path.join(path, EXERCISE_KEY)
    with open(key_path, "w") as keyfile:
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
    xml_path = path
    xml = exercise_xml(xml_path)
    res = exercise_xml_to_json(xml, hide_answers, sensitive_tags, sensitive_attrs)
    return res


#def noget_type_from_node(question):
#    tags = [item.tag for item in question.findall(".//")]
#    attributes = question.attrib
#    qtype = "unknown"
#    if "type" in attributes.keys():
#        qtype = question.attrib["type"]
#    elif "function" in attributes.keys() and "pythonic" in attributes.values():
#        qtype = "pythonic"
#    elif "compareNumeric" in tags or "Numeric" in tags or "linearAlgebra" in tags:
#        qtype = "devLinearAlgebra"
#    elif "expression" in tags:
#        qtype = "devLinearAlgebra"
#    elif "choice" in tags:
#        qtype = "multipleChoice"
#    elif "choices" in tags:
#        qtype = "multipleChoice"
#    return qtype


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
    taglist = []
    # xml = xml.decode('utf-8')
    # xml = re.sub("<code>","<code><![CDATA[",xml)
    # xml = re.sub("</code>","]]></code>",xml)
    # print(f"XML = ", xml )
    root = fromString(xml)
    exercise_key = root.attrib.get('exercise_key','exercise_key')
    #print(f"EXERCSE_KEY IN XML_TO_JSON {exercise_key}")

    global_xmltrees = root.findall("./global")
    global_xml = ''
    for global_xmltree in global_xmltrees :
        global_xml = global_xml + etree.tostring(global_xmltree).decode('utf-8') 
    try:
        from exercises.models import get_qtype_from_xml
        questions = root.findall("./question")
        for question in questions:
            if not question.attrib.get('type', None ) :
                question_xml = etree.tostring( question ).decode('utf-8')
                qtype = get_qtype_from_xml( global_xml, question_xml,exercise_key=exercise_key, src='PARSING_EXERCISE_XML_TO_JSON')
                #qtype = get_type_from_node(question)
                question.attrib["type"] = qtype
        # for question in questions :
        #    print(f"NEW TYPE = {question.attrib['type']}")
        # literals = root.findall('.//literal')
        # for literal in literals :
        #    txt = etree.tostring(literal).decode('utf-8')
        #    txt = re.sub("<","&lt;",txt)
        #    txt = re.sub(">","&gt;",txt)
        #    print(f"LITERAL = {literal} TEXT = {txt}")
        # print(f" LITERALS = ", literals )
        if hide_answers:
            for question_type, tags in sensitive_tags.items():
                questions = root.findall('./question[@type="{type}"]'.format(type=question_type))
                for question in questions:
                    for tag in tags:
                        if tag not in taglist:
                            taglist = taglist + [tag]
                        nodes = question.findall(".//" + tag)
                        if not isinstance(nodes, list):
                            nodes = []
                        for node in nodes:
                            parent = node.getparent()
                            parent.remove(node)
                        if tag == "value":
                            variablesnode = question.find("variables")
                            if settings.MAKE_GLOBALNODE_NONEMPTY:
                                if not variablesnode is None:
                                    variablesnode.text = ""
            for question_type, attrs in sensitive_attrs.items():
                for attr in attrs:
                    nodes = root.findall('.//question[@type="{type}"]/*[@{attr}]'.format(type=question_type, attr=attr))
                    for node in nodes:
                        node.attrib.pop(attr, None)
            if "value" in taglist:
                globalnodes = root.findall("./global")
                if len(globalnodes) > 0:
                    globalnode = globalnodes[0]
                    if settings.MAKE_GLOBALNODE_NONEMPTY:
                        globalnode.text = " "
                    valuenodes = globalnode.findall(".//value")
                    for valuenode in valuenodes:
                        parent = valuenode.getparent()
                        parent.remove(valuenode)

        obj = bf.data(root)

    except ParseError as e:
        raise ExerciseParseError(e)
    questions = deep_get(obj, "exercise", "question")
    if questions:
        if not isinstance(questions, list):
            questions = [questions]
            obj["exercise"]["question"] = questions
    globals_ = deep_get(obj, "exercise", "global")
    if globals_:
        if not isinstance(globals_, list):
            globals_ = [globals_]
            obj["exercise"]["global"] = globals_

    globals_ = deep_get(obj, "exercise", "global")
    if globals_:
        if not isinstance(globals_, list):
            globals_ = [globals_]
            nglobals = []
            for global_ in globals_:
                if hide_answers:
                    global_["$"] = "HIDE THE TEXT"
                    global_["$children$"][0]["$"] = "HIDE THE TEXT 2"
                nglobals = nglobals + [global_]
            obj["exercise"]["global"] = nglobals
    return obj


def exercise_xml(path):
    if os.path.isfile(path.rstrip("/")):  # LET THIS SERVER BOTH HISTORY XML AND ORDINARY XML
        xml_path = path.rstrip("/")
    else:
        xml_path = os.path.join(path, EXERCISE_XML)
    if 'history' in xml_path :
        pass
    else :
        keypath = str( xml_path).replace('exercise.xml','exercisekey')
        if os.path.exists( keypath ):
            exercise_key = str( open(keypath, mode='rb').read().strip().decode('utf-8'));
        else :
            exercise_key = 'exercise_key'
    #print(f"EXERCISE_XML KEY={exercise_key}")
    # xmlfile = open(xml_path)
    # xml = xmlfile.read()
    try:
        with open(xml_path, mode="rb") as fil:
            xml = fil.read()
    except Exception as e:
        logger.error(f"XML NOT FOUND {type(e).__name__} {str(e)}")
        return None
    xmlin = xml;
    xml = xml.decode("utf-8")
    xml = re.sub(r"<p>", "<p/>", xml)  # This hack was inserted 2021-05-12 since <p> ... </p>  is fragile
    xml = re.sub(r"</p>", "<p/>", xml)  # Latest react gives hard fail if dom  contains other than inline elements
    xml = re.sub(r"updated=\"true\"",'',xml)
    #                                # See https://stackoverflow.com/questions/41928567/div-cannot-appear-as-a-descendant-of-p
    # logger.debug("EXERCISE_XML RETURNING %s " % xml )
    root = etree.fromstring(xml);
    target = root;
    try :
        target = denest(root)
        if not target  == None :
            #target.set("updated", "true")
            target.set("exercise_key",exercise_key)
            xml = etree.tostring(target, encoding='UTF-8' ).decode();
        else :
            xml = xmlin 
    except Exception as err:
        #logger.error(f"ERROR = {type(err).__name__} {str(err)}")
        xml = xmlin

    return xml


def is_all_ascii(xml):
    parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
    root = etree.fromstring(xml, parser=parser)
    fields = ["comment", "exercisename", "text", "choice"]
    for field in fields:
        txts = root.findall(".//%s" % field)
        for txt in txts:
            parent = txt.getparent()
            child = parent.find("./%s" % field)
            parent.remove(child)
    asciok = True
    nontextxml = etree.tostring(root, encoding="ascii")
    sub = ""
    if "&#" in str(nontextxml):
        beg = str(nontextxml).find("&#")
        end = min(len(nontextxml), beg + 12)
        # logger.debug("NOT OK!")
        sub = str(nontextxml)[beg:end]
        asciok = False
    return (asciok, sub)


def exercise_save(path, xml, backup=None,username='',src=''):
    messages = []
    logger.error(f"Saving {path} {username}")
    if backup is not None:
        backup_path = os.path.join(path, EXERCISE_HISTORY)
        backup_file = os.path.join(backup_path, backup)
        os.makedirs(backup_path, exist_ok=True)
        try:
            with open(backup_file, "w") as file:
                file.write(xml)
        except IOError:
            messages.append(("warning", "Couldn't write backup file"))
    xml_path = os.path.join(path, paths.EXERCISE_XML)
    try :
        t = str( datetime.datetime.now().strftime("%F %T.%f")[:-3] )
        parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
        root = etree.fromstring(xml, parser=parser)
        for e in root.iter():
            e.attrib.pop("hashkey", None)
        root.set('updated',t)
        root.set('by' , username )
        #root = denest(root)
        newxml = etree.tostring(root).decode('utf-8')
        with open(xml_path, "w") as file:
            file.write(newxml)
    except Exception as e :
        logger.error(f"ERROR WRITING NEWXML {str(e)} ")
        with open(xml_path, "w") as file:
            file.write(xml)

    messages.append(("success", "Saved exercise"))
    # ( isok,sub) = is_all_ascii( xml )
    # if not isok :
    #    messages.append(('error', 'You must get rid of the non-ascii characters at the first charcter of this string %s ; you may have to retype the string. ' % sub ))
    return messages


def question_validate_xmltree(question):
    if question.get("key") is None or question.get("type") is None:
        return False
    return True


def exercise_xmltree_from_xml(xml):
    root = etree.fromstring(xml)
    return root


def exercise_xmltree(path, usermacros={}):
    os.path.join(path, paths.EXERCISE_XML)
    parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
    try:
        xml = exercise_xml(path)
        root = etree.fromstring(xml, parser=parser)
        if not usermacros == {}:
            root = apply_macros_to_exercise(root, usermacros)
        return root
    except etree.XMLSyntaxError as e:
        # logger.debug("PARSING: exercise_xmltree failed: %s", xml )
        raise ExerciseParseError(e)


def question_xmltree_get(exercise_xmltree, question_key, usermacros={}):
    return global_and_question_xmltree_get(exercise_xmltree, question_key, usermacros)[1]


def question_json_get(path, question_key, usermacros={},db=None):
    usermacros["@call"] = "QUESTION_JSON_GET"
    raw_json = exercise_json(path, True)
    exercise_key = exercise_key_get(path)
    return question_json_get_from_raw_json(raw_json, exercise_key, question_key, usermacros,db)


def question_json_get_from_raw_json(raw_json, exercise_key, question_key, usermacros={},db=None):
    questions = deep_get(raw_json, "exercise", "question")
    user_id = usermacros['@userpk'];
    is_staff = usermacros['@is_staff']
    exercise_key = usermacros['@exercise_key'];
    question_key = usermacros['@question_key'];
    from exercises.question import get_other_answers
    other_answers = get_other_answers(question_key, user_id, exercise_key,db); 

    found = list(
        filter(
            lambda q: ("@attr" in q and "key" in q["@attr"] and q["@attr"]["key"] == question_key),
            questions,
        )
    )
    if len(found) == 1:
        global_data = deep_get(raw_json, "exercise", "global")
        if global_data:  # and 'type' in found[0]['@attr']:
            if not isinstance(global_data, list):
                global_data = [global_data]
            global_for_type = list(
                filter(
                    lambda g: (
                        ("@attr" not in g)
                        or ("@attr" in g and "type" in g["@attr"] and g["@attr"]["type"] == found[0]["@attr"]["type"])
                    ),
                    global_data,
                )
            )
            if len(global_for_type) == 1:
                found[0].update({"global": global_for_type[0]})
        found[0]["question_key"] = question_key;
        found[0]["exercise_key"] = exercise_key;
        found[0]["other_answers"] = other_answers;
        found[0]["is_staff"] = is_staff
        found[0]['db'] = db
        return found[0]
    else:
        return "{}"


def exercise_check_thumbnail(xmltree, path):
    messages = []
    p = path + "/thumbnail-*.png"
    thumbs = glob.glob(p)
    if len(thumbs) > 0:
        thumb = thumbs[-1].split("/")[-1]
    else:
        thumb = "thumbnail.png"
    thumbnail_path = os.path.join(path, thumb)
    figure = xmltree.xpath("/exercise//figure")
    try:
        figurepath = figure[0].text.strip()
    except (IndexError, NameError, AttributeError):
        return messages
    full_figurepath = os.path.join(path, figurepath)
    if os.path.exists(thumbnail_path):
        thumbnail_time = os.path.getmtime(thumbnail_path)
    else:
        if not os.path.exists(full_figurepath):
            messages = ("warning", "Thumbnail {path} does not exist:")
            return messages
        else:
            thumbnail_time = os.path.getmtime(full_figurepath) - 1
    if (
        os.path.exists(full_figurepath)
        and not settings.RUNTESTS
        and thumbnail_time < os.path.getmtime(full_figurepath) + 10
    ):
        _, ext = os.path.splitext(figurepath)
        h = (hashlib.md5(open(full_figurepath, "rb").read()).hexdigest())[0:7]
        for thumb in thumbs:
            os.remove(thumb)
        thumbnail_path = path + f"/thumbnail-{h}.png"
        iext = ext.lower()
        size = (100, 100)
        if iext == ".pdf":
            messages.append(("info", "Trying to create thumbnail from pdf..."))
            try:
                check_output(["convert", "-thumbnail", "100x100", full_figurepath, thumbnail_path])
            except (CalledProcessError, IOError) as e:
                messages.append(("warning", "Thumbnail creation failed for pdf"))
                messages.append(("warning", str(e)))
                return Response(response_from_messages(messages))
        else:
            try:
                image = Image.open(full_figurepath)
            except IOError:
                messages.append(("error", "Could not open figure"))
                return messages
            image.thumbnail(size, Image.Resampling.LANCZOS)
            background = Image.new("RGBA", size, (255, 255, 255, 0))
            background.paste(image, (round((size[0] - image.size[0]) / 2), round((size[1] - image.size[1]) / 2)))
            background.save(thumbnail_path)
            os.chmod(thumbnail_path,0o755) # 
        messages.append(("warning", "Created thumbnail"))
    return messages


# def add_text(imgfile ):
#    from PIL import ImageDraw, ImageFont
#    img = Image.open(imgfile)
#    txt = ( imgfile.split('/')[-2] ).split('-')[0]
#    ttf_file = '/tmp/futura.ttf'
#    font = ImageFont.truetype(ttf_file , 24 )
#    ImageDraw.Draw( img).text( (0, 0),  txt ,  (0, 0, 0) , font=font )
#    # font = ImageFont.truetype(<font-file>, <font-size>)
#    #font = ImageFont.truetype("sans-serif.ttf", 16)
#    # draw.text((x, y),"Sample Text",(r,g,b))
#    #draw.text((0, 0),"Sample Text",(255,255,255) )
#    logger.debug("DREW %s on %s " % ( txt , imgfile) )
#    img.save(imgfile)


def exercise_add(folder, name):
    import shutil

    fname = slugify(name) + "-" + str(random.randint(111111, 999999))
    full_path = os.path.join(folder, fname)
    template_path = os.path.join(TEMPLATE_EXERCISE_PATH, "exercise.xml")
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    if os.path.isdir(full_path):
        return {"error": "There is already a folder in the file tree with this name."}
    if is_exercise(full_path):
        return {"error": "There is already an exercise with that name in the file tree"}
    # os.makedirs(full_path, exist_ok=True)
    shutil.copytree(TEMPLATE_EXERCISE_PATH, full_path)
    # add_text( os.path.join(full_path, "examplefig.png" ) )
    xml_path = os.path.join(full_path, paths.EXERCISE_XML)
    template_data = "<exercise>\n\t<exercisename>\n\t\t{name}\n\t</exercisename>\n</exercise>".format(name=name)
    try:
        with open(template_path, "r") as file:
            template_data = file.read().replace("__exercise_name__", name)
    except IOError:
        pass
    try:
        with open(xml_path, "w") as file:
            file.write(template_data)
    except IOError:
        return {"error": "Could not write exercise xml file."}
    return {"success": True, "path": os.path.join(folder, fname)}


def exercise_delete(course_path, path):
    exercise_folder_name = os.path.basename(os.path.normpath(path))
    date_now = "{:%Y%m%d_%H:%M:%S_%f}".format(now())
    deleted_relative_path = os.path.join(TRASH_PATH, exercise_folder_name + "." + date_now)
    deleted_path = os.path.join(course_path, deleted_relative_path)
    if not os.path.isdir(path):
        return {"error": "There is no such exercise folder!"}
    if not is_exercise(path):
        return {"error": "The folder does not seem to be an exercise"}
    try:
        os.renames(path, deleted_path)
    except OSError:
        return {"error": "Could not rename exercise to deleted spec."}
    return {"success": True, "path": deleted_relative_path}


def exercise_move(path, new_path):
    date_now = "{:_%Y%m%d_%H:%M:%S_%f}".format(now())

    if path == new_path:
        return {"error": "Same folder"}
    if not os.path.isdir(path):
        return {"error": "There is no such exercise folder!"}
    if not is_exercise(path):
        return {"error": "The folder does not seem to be an exercise"}
    if os.path.isdir(new_path):
        new_path += "." + date_now
    try:
        os.renames(path, new_path)
    except OSError as e:
        return {"error": "Could not move exercise folder: {}".format(str(e))}
    return {"success": True, "path": new_path}


def patch_path(path):
    subdirs = path.split("/")
    subdirs = [x.strip() for x in subdirs]
    current_path = ""
    while len(subdirs) > 1:
        current_path = current_path + subdirs[0] + "/"
        glob_string = current_path + subdirs[1]
        glob_current_path = glob.glob(glob_string)
        glob_string2 = current_path + "*:*" + subdirs[1]
        glob_current_path = glob_current_path + glob.glob(glob_string2)
        subdirs = subdirs[1:]
        if not subdirs[0] == "..":
            if glob_current_path == []:
                break
            else:
                glob_current_path_save = glob_current_path[0]
    new_path = glob_current_path_save + "/" + "/".join(subdirs)
    return new_path


def exercises_move_folder(old_path, new_path, db):
    new_path = os.path.normpath(new_path)
    os.makedirs(new_path, exist_ok=True)
    messages = []
    if os.path.isdir(new_path):
        dirlist = os.listdir(new_path)
        if len(dirlist) == 0:
            os.rmdir(new_path)
        else:
            return {"error": "Folder already exists; perhaps it is hidden if some exercises are filtered out"}
    if not os.path.isdir(old_path):
        return {"error": "Original folder does not exist."}
    try:
        os.rename(old_path, new_path)
        exercises = list_exercises_in_folder(new_path)
    except OSError:
        if old_path == new_path:
            messages.append(("error", "OSError: Could not move folder to itself "))
        else:
            messages.append(("error", "OSError: Could not move folder "))
        return {"error": "Could not move folder"}
    return {"success": True, "exercises": exercises}


def list_history(path):
    backup_path = os.path.join(path, EXERCISE_HISTORY)
    history = []
    if not os.path.isdir(backup_path):
        return []
    content = os.listdir(backup_path)
    for entry in content:
        fullpath = os.path.join(backup_path, entry)
        if os.path.isfile(fullpath) and entry.endswith(".xml"):
            mtime = os.stat(fullpath).st_mtime
            dtime = time.time() - mtime
            history.append({"filename": entry, "modified": mtime, "delta_time": dtime})
    return history


def exercise_xml_history(path, name):
    backup_path = os.path.join(path, EXERCISE_HISTORY)
    fullpath = os.path.join(backup_path, name)
    if not os.path.isfile(fullpath):
        return {"error": "No such file."}
    xml = exercise_xml(fullpath)
    # with open(fullpath, mode='rb') as fil:
    #    xml = fil.read()
    # xmlfile = open(fullpath)
    # xml = xmlfile.read()
    #print(f"GET HISTORY FILE {xml}")
    return {"success": "Ok", "xml": xml}


def exercise_json_history(path, name):
    res = exercise_xml_history(path, name)
    if "error" in res:
        return res
    return exercise_xml_to_json(res["xml"])

#def get_full_text(element):
#    return ''.join(element.itertext())

#def insert_text_before_close(element, text_to_insert):
#    if len(element):  # Check if the element has child elements
#        # Append text to the tail of the last child element
#        element[-1].tail = (element[-1].tail or '') + text_to_insert
#    else:
#        # Append text to the element's own text
#        element.text = (element.text or '') + text_to_insert

def flatten_text(xml) :
    rhs = xml.decode('utf-8')
    rhs = rhs.replace(r" */>","/>").strip()
    lhs = ''
    pat= '<\w+ *[^>/]*>|<\/\w*>'
    r = re.compile(pat)
    levels = {}
    while  r.search(rhs) :
        #print(f"LEVELS = {levels}")
        m = r.search(rhs) 
        mbeg = m.start()
        mend   = m.end()
        tag = m.group()
        tagname = tag.lstrip('<').split(' ' )[0].lstrip('/').rstrip('>')
        isopentag = not "</" in tag 
        #print(f"LEVELS = {levels}")
        #print(f"TAGNAME={tagname} TAG={tag}")
        textlevel = levels.get("text",0)
        if tagname == 'text'   and isopentag and textlevel > 0  : # and not levels.get('global',0) > 0 :
            lhs  += rhs[0:mbeg] 
            rhs = rhs[ mend : len( rhs ) ]
        elif tagname == 'text'   and not isopentag and not textlevel  == 1   : # and not levels.get('global',0) > 0 :
            lhs  += rhs[0:mbeg] 
            rhs = rhs[ mend : len( rhs ) ]
        else :
            lhs  += rhs[0:mend] 
            rhs = rhs[ mend : len( rhs ) ]



        if isopentag :
            levels[tagname] = levels.get(tagname,0) + 1

        if not isopentag :
            levels[tagname] = levels.get(tagname,1) - 1 
            if levels[tagname] == 0 :
                del levels[tagname]

        rhs = rhs.strip()
    #txt =  html.unescape( lhs )
    return lhs



def denest( target ):
    oldtarget = target
    xml = etree.tostring(target)
    try :
        newxml = flatten_text( xml  )
        newtarget = etree.fromstring( newxml)
        target = newtarget
    except Exception as err :
        print(f"DENEST ERROR {str(err)}")
    try : # DO NOT REWRITE THE XML IF THERE ARE ANY ERRORS
        defs = ["global","local","macros"];
        ss = ''
        for d in defs :
            gs = target.xpath(d);
            ii = 0 ;
            for g in gs:
                sn = [];
                for i in  g.xpath("./text") :
                    text_in_global = i.text
                    txt1 = ''
                    txt2 = ''
                    if hasattr(g,"text") :
                        if g.text :
                            txt1 = g.text
                    if i.text :
                        txt2 = i.text
                    p = txt2.split(';')
                    s = ";\n".join([ t.strip() for t in p ])
                    g.remove(i)
                    g[-1].tail = s + ";\n";
                if len(g) > 0 and hasattr(g[-1], "tail") :
                    tail = g[-1].tail;
                    if tail :
                        p = tail.split(';')
                        s = "\n" + ";\n".join([ t.strip() for t in p ]) 
                        g[-1].tail = s 
                #    ii += 1;
                #s = [ i.strip() for i in sn  if i.strip() ]
                #print(f"S = {s}")
                #if s:
                #    ss = ';\n'.join(s)
                #    #print(f"ss = {ss}")
                #if len(g) == 0 :
                #    print(f"ALT1")
                #    g.text = "\n" + ss + "\n";
                #else :
                #    print(f"ALT2")
                #    g.text = None
                #    for child in g :
                #         child.tail = None
                #    #ss = ss.rstrip().rstrip(';')
                #    print(f"SS = {ss}")
                #    g[-1].tail = ss 
                #g[-1].tail = ''
        #print(f"PATHS = {paths}")
        #print(f"{paths.EXERCISE_XSD}")
        xmlschema = etree.XMLSchema(etree.parse(paths.EXERCISE_XSD))
        parser = etree.XMLParser(recover=True)
        s = xmlschema.validate(target)
        #print(f"S = {s}")
        if s  :
            etree.indent(target, "  ")
        else :
            target = oldtarget
    except Exception as e :
        formatted_lines = traceback.format_exc()
        logger.info(f"ERROR DENESTING {type(e).__name__} {str(e)}")
        logger.info(f"FORMATTED_LINES {formatted_lines}")
        return oldtarget
    return target






def get_translations(xml):
    """Find translation subtags.

    Returns a dict with the translations corresponding to
    the <alt lang=".."> tags.
    """
    ret_langs = dict()
    alt_langs = xml.xpath("./alt[@lang]")
    for lang in alt_langs:
        ret_langs[lang.get("lang")] = lang.text
    return ret_langs


def getkey(stringin):
    key = re.sub(r"\s+", "", stringin)
    return key


def get_questionkeys_from_xml(xml):
    qnodes = (etree.fromstring(xml)).findall("./question")
    questionlist = []
    for qnode in qnodes:
        questionlist.append(qnode.attrib["key"])
    return questionlist


def global_xmltree_get(exercise_xmltree, question_key, usermacros={}):
    return global_and_question_xmltree_get(exercise_xmltree, question_key, usermacros)[0]


def global_and_question_xmltree_get(exercise_xmltree, question_key, usermacros={}):
    xml = etree.tostring(exercise_xmltree)
    root = etree.fromstring(xml)
    root = apply_macros_to_exercise(root, usermacros)
    global_xpath = '/exercise/global[@type="{type}"] | /exercise/global[not(@type)] | /exercise/global'
    global_xmltree = (root.xpath(global_xpath) or [None])[0]
    question_xmltree = root.xpath('/exercise/question[@key="{key}"]'.format(key=question_key))[0]
    return [global_xmltree, question_xmltree]
