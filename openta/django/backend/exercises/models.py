# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import datetime 
from datetime import timezone
import hashlib
from django.conf import settings
if settings.USE_CHATGPT  :
    from django_ragamuffin.models import Assistant, VectorStore, ModeChoice, Mode, Thread, Message, OpenAIFile
from django.db import transaction
import html
import sys
import json
from backend.user_utilities import send_email_object
import json as JSON
from django.core.mail import EmailMessage
import logging
import os
from pathlib import Path
import importlib.util
from utils import db_info_var
from backend.user_utilities import dynamic_import
import random
import re
import shutil
import traceback
import uuid
from functools import reduce
from zoneinfo import ZoneInfo
from django.utils.timezone import make_aware

import aggregation
from course.models import Course, pytztimezone, tzlocalize
from exercises.parsing import (
    ExerciseNotFound,
    ExerciseParseError,
    exercise_check_thumbnail,
    exercise_key_get,
    exercise_key_get_or_create,
    exercise_xml,
    exercise_xmltree,
    get_translations,
    is_exercise,
    question_validate_xmltree,
)
import xmltodict
from lxml import etree
from exercises.util import nested_print
from image_utils import compress_pil_image_timestamp
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from model_utils import FieldTracker
from utils import touch_

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import caches
from exercises.util import  get_hash_from_string
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import Signal, receiver
from django.forms import ValidationError
from django.template.defaultfilters import slugify
from django.utils.timezone import now
from django.utils.translation import gettext as _
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter,A4
from reportlab.lib import colors


import io

# from utils import chown # FIXME stub left in code for CHOWN

logger = logging.getLogger(__name__)


upload_storage = FileSystemStorage(location=settings.VOLUME, base_url="/")



BIN_LENGTH = settings.BIN_LENGTH

logger = logging.getLogger(__name__)


# https://coderwall.com/p/ktdb3g/django-signals-an-extremely-simplified-explanation-for-beginners
#
# LISTEN TO ALL RELEVANT SIGNALS
#

import xml.etree.ElementTree as ET

def element_string_value(elem):
    """Recreate XPath string(.) for stdlib: gather text recursively."""
    parts = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        parts.append(element_string_value(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)

def extract_text_blocks_from_xml_string(xml_string):
    """
    Parse an XML string, collect the recursive text content of every <text> element
    (namespace-agnostic), and return a single string with a newline after each block.
    """
    root = ET.fromstring(xml_string)

    def is_text(elem):
        # Namespace-agnostic: '{ns}text' or 'text'
        return elem.tag == "text" or elem.tag.endswith("}text")

    blocks = []
    for el in root.iter():
        if is_text(el):
            s = element_string_value(el).rstrip()
            blocks.append(s)

    # Ensure exactly one newline after each <text> block
    return "".join(block + "\n" for block in blocks)


def print_my_stack(s=''):
    import sys,os,traceback
    stdlib = os.path.dirname(os.__file__)
    sitepkgs = next(p for p in sys.path if "site-packages" in p)
    stack = traceback.extract_stack()
    for frame in stack:
        f = os.path.abspath(frame.filename)
        if not f.startswith(stdlib) and not f.startswith(sitepkgs):
            logger.error(f"STACK {s}  {frame.filename}:{frame.lineno} in {frame.name}")

def create_text_pdf(text,idname,x0,y0):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    can.setFillColor(colors.red)
    xr = random.randint(1,10)
    yr = random.randint(1,10)
    can.drawString(x0 + xr , y0 - yr  , text)  # Adjust position (x, y) as needed
    can.drawString(x0 + xr , y0 - yr - 10 , f"id={idname}" )
    can.save()
    packet.seek(0)
    return packet



@receiver([post_save, post_delete])
def signal_handler(sender, *args, **kwargs):
    for signal in ["post_save", "post_delete"]:
        if hasattr(sender, signal):
            getattr(sender, signal)(sender, *args, **kwargs)


answer_received = Signal()  # Signal(providing_args=["course", "user", "exercise"])
exercise_saved = Signal()  # Signal(providing_args=["course", "user", "exercise"])
exercise_options_saved = Signal()
exercise_saved_translation = Signal()  # Signal(providing_args=["course", "user", "exercise"])



def validate_question_xml(  db , exercise_key, question_key, username, xml ):

    if not settings.RUNTESTS :
        user = User.objects.using(db).get(username=username)
    else :
        user = 1
    subdomain = db;
    before_date = None;
    from exercises.question import get_usermacros
    usermacros = get_usermacros(user, exercise_key, question_key=question_key, before_date=before_date, db=db)
    #xmltree = exercise_xmltree(exercise.get_full_path(), {})
    xmltree = etree.fromstring( xml )

    tag = "ignore"
    for tag1 in xmltree.findall(f".//{tag}"):
        if any(tag1.iter(tag)):
            for nested in list(tag1.iter(tag))[1:]:
                parent = nested.getparent()
                parent.remove(nested)




    #hiddens = xmltree.xpath('//hidden')
    #for hidden in hiddens :
    #    xmltree.remove( hidden)
    global_xmltree = xmltree.xpath('/exercise/global')
    if len( global_xmltree) == 0 :
        global_xmltree = etree.fromstring("<global/>")
    else :
        global_xmltree = global_xmltree[0];
    question_xmltree = xmltree.xpath('/exercise/question[@key="{key}"]'.format(key=question_key))[0] 
    varhash =  get_hash_from_string(etree.tostring( question_xmltree) )
    cache = caches["default"]
    msg = None
    if  settings.DO_CACHE  :
        msg = cache.get(varhash )
    if not msg == None :
        return (('success', msg))
    if not question_xmltree  == None :
        return(('error' , 'Skipped initial validation on key change'))
    do_validate = question_xmltree.attrib.get('validate','true') == 'true'
    if not do_validate :
        return (('success' , 'skipped validation'))
    exerciseassetpath = usermacros['@exerciseassetpath']
    question_xmltree.set("exerciseassetpath", exerciseassetpath)  ## NEED THIS
    question_xmltree.set("subdomain", subdomain)  ## NEED THIS
    if not settings.RUNTESTS :
        question_xmltree.set("user", str( user.pk ))  ## NEED THIS
    else :
        question_xmltree.set("user", b"1" )  ## NEED THIS

    question_xmltree.set("username", username ) ## NEED THIS
    question_xmltree.set("exercise_key", str( exercise_key ))  ## NEED THIS
    path = exerciseassetpath # THIS IS BEING RUN AS SUPER SO PATH IS THE SAME exercise.get_full_path()
    xml = etree.tostring( global_xmltree).decode('utf-8')
    qxml = etree.tostring( question_xmltree).decode('utf-8')
    if  '@' in xml  or '@' in qxml :
        from exercises.applymacros import apply_macros_to_exercise
        path =  exerciseassetpath
        root = exercise_xmltree( path, usermacros)
        root = apply_macros_to_exercise(root, usermacros)
        global_xpath = '/exercise/global'
        try :
            global_xmltree = (root.xpath(global_xpath) or [None])[0]
        except :
            global_xmltree = None;
        question_xpath = f'/exercise/question[@key=\"{question_key}\"]'
        question_xmltree = root.xpath(question_xpath)[0]
        newxml = etree.tostring(root ).decode('utf-8')
        if 'fileread' in newxml :
            cache.set('varhash', 'Skipped validation', settings.CACHE_LIFETIME)
            return (('success' , 'Skipped validation'))
    question_xml = etree.tostring( question_xmltree).decode('utf-8');
    global_xml = etree.tostring( global_xmltree).decode('utf-8')
    from exercises.parsing import question_json_get
    question_json = question_json_get(path, question_key, usermacros,db)


    def get_expressions_from_xml( question_json, xmltree ):
        others = question_json.get('other_answers',None)
        if others :
            for key in others.keys() :
                oldval = others[key]
                qroots = xmltree.xpath('/exercise/question[@key="{key}"]/expression'.format(key=key))
                for qroot in qroots :
                    txt = qroot.text.strip() 
                    question_json['other_answers'][key] = txt # FIXME
        return question_json 

    question_json = get_expressions_from_xml( question_json, xmltree ) 


    from exercises.question import validate_question_dispatch, question_check_dispatch
    #if not qtype :
    #    qtype = settings.DEFAULT_QUESTION_TYPE
    src = 'validate_question_xml'
    qtype = get_qtype_from_xml(   global_xml , question_xml , exercise_key ,src )
    f = validate_question_dispatch[qtype]
    question_json['is_staff'] = True # VALIDATE QUESITON IN THE CONTEXT OF STAFF
    expressions = global_xmltree.xpath('//expression')
    if global_xmltree == None :
        global_xmltree = etree.fromstring("<global/>")
    try :
        res = f( question_json, question_xmltree, global_xmltree)
    except Exception as e :
        logger.error(f"ERROR IN VALIDATE_QUESTION_XML {str(e)}")
        print_my_stack('ERROR_IN_VALIDATE_QUESTION_XML')
        raise e
    if res :
        (k,v) = res
        if k == 'error' :
            assert False, v 
        else :
            pass
    else :
        res = (('success' , 'skipped validation'))
    if res[0] == 'success' :
        cache.set(varhash, res[1] , settings.CACHE_LIFETIME)
    return res


def get_qtype_from_xml(   global_xml , question_xml , exercise_key ,src ) :
    qtype = 'default'
    try :
        if '</choice>' in question_xml :
            qtype = "multipleChoice"
            return qtype
        varhash =  get_hash_from_string( str( exercise_key ) +  str(  question_xml )  + str( global_xml) + 'get-qtype')
        cache = caches["default"]
        qtype = cache.get(varhash )
        if  not qtype == None  and not qtype == 'default' and settings.DO_CACHE : # CACHING qtype
                return qtype
        nqxmls = ''
        db = settings.SUBDOMAIN if settings.RUNTESTS else db_info_var.get(None)
        assert not db == None , "XXX GET_QTYPE DID NOT GET A PROPER DB = {db}"
        #print(f"GLOBAL_XML = {global_xml}")
        #print(f"QUESTION_XML = {question_xml}")
        question_xmltree  = etree.fromstring( question_xml )
        attribs =  question_xmltree.attrib 
        if attribs.get('type',None) == 'aibased' :
            return 'aibased'


        if '@' in question_xml  or '@' in global_xml :
            try:
                dbexercise = Exercise.objects.using(db).get(exercise_key=exercise_key);
                from exercises.applymacros import apply_macros_to_node, apply_macros_to_exercise
                from exercises.parsing import exercise_xml
                from exercises.question import get_usermacros
                global_xmltree  = etree.fromstring( global_xml )
                xml = exercise_xml(dbexercise.get_full_path())
                question_key = question_xmltree.attrib['key']
                username='super'
                user = User.objects.using(db).get(username=username)
                usermacros = get_usermacros(user, exercise_key, question_key=question_key, before_date=None, db=db)
                #print(f"USERMACROS = {usermacros}")
                root = etree.fromstring(xml)
                root = apply_macros_to_exercise( root , usermacros)
                global_xmltree = root.findall('./global')[0]
                global_xml = etree.tostring(global_xmltree).decode('utf-8')
                question_xmltree =  root.xpath('/exercise/question[@key="{key}"]'.format(key=question_key))[0]
                question_xml = etree.tostring(question_xmltree).decode('utf-8')
            except Exception as e :
                logger.error(f" SAVE ERROR {type(e).__name__} {str(e)}")
    
        if '@' in question_xml  or '@' in global_xml :
            logger.error(f"MACROS STILL NOT RESOLVED from {src}")
    
        qtype = 'default'
        attribs =  question_xmltree.attrib 
        if not ( attribs.get('type','default')   == 'default' ) :
            qtype = attribs['type']
        elif 'function' in attribs :
            qtype = 'pythonic'
        elif re.search(r'FiniteBosonFockSpace', global_xml )  or  re.search(r'FiniteBosonFockSpace', question_xml )  :
            qtype = 'qm'
        elif '[' in question_xml or '[' in global_xml  or '[' in nqxmls :
            qtype = 'matrix'
        else :
            qtype = 'basic'
    
        if '</choice>' in question_xml :
            qtype = "multipleChoice"
        try :
            cache.set(varhash, qtype , settings.CACHE_LIFETIME )
        except Exception as e :
            logger.error(f" CANNOT SET QTYPE {str(e)}")
    except :
        qtype = 'default'
    return qtype 


def reconnect_exercise_to_path( path,course, db ):


    exercises = Exercise.objects.using(db).filter(path=path)
    if exercises.count() > 1 :
        assert False , "Several exercises with that key";
    else :
        exercise = exercises[0];
    keys = [];
    paths = {};
    base = course.get_exercises_path(db)
    baselen = len(base)
    for root, dirs, files in os.walk(base , topdown=False):
        for path_ in dirs:
            keyfile=  os.path.join( root, path_ , 'exercisekey' ) 
            if os.path.exists( keyfile) :
                key = open(keyfile,"r").read()
                keys.append(key)
                path_ = path_.strip();
                paths[key] = f"{root}/{path_}"
                #print(f"PATH={path_} KEY={key}") 
    if not len(keys) == len( set( keys) ) :
        assert False , "KEYS IS DUPLICATED"
    exercise_key = exercise.exercise_key
    path = path.lstrip('/')
    folder = exercise.folder 
    full_path = os.path.join(course.get_exercises_path(db), path)
    res = False
    if not exercise_key in paths :
        dbexercise = Exercise.objects.using(db).filter(pk=exercise_key)[0]
        dbexercise.delete()
        return (('error' , 'DELETED NONEXISTENT EXERCISE IN DATABASE'))
    if not is_exercise( full_path ) :
        path_found = paths[exercise_key];
        issame = ( path_found == full_path )
        logger.error(f" {issame} PATH ACTUALLY  FOUND IS {path_found}")
        logger.error(f" {issame} PATH ACCORDING TO DB IS {full_path}")
        path_in_dir = path_found[baselen + 1:];
        folder_in_dir = '/'.join( path_in_dir.split('/')[0:-1])
        logger.error(f" PATH IN DATABASE  =   {exercise.path}")
        logger.error(f" PATH FOUND IN DIR =   {path_in_dir}")
        logger.error(f" FOLDER IN DATABASE = {exercise.folder}")
        logger.error(f" FOLDER FOUND IN DIR = {folder_in_dir}")
        exercise.path = path_in_dir;
        exercise.folder = folder_in_dir;
        pk = exercise.pk;
        Exercise.objects.using(db).filter(pk=pk).update(path=path_in_dir, folder=folder_in_dir)
        res = path_in_dir
    return path




class ExerciseManager(models.Manager):

    def add_exercise_full_path(self, path, course, db=settings.DB_NAME):
        """Add exercise from full path.

        Verifies that the folder structure corresponds to the specified course.

        Args:
            path (str): Full path to exercise.
            course (Course): Course model object.

        """
        exercises = self.model.objects.filter(path=path)
        if exercises.count() == 0 : # ADD A COMPLETELY NEW EXERCISE
            course_path = course.get_exercises_path(db)
            if not path.startswith(course_path):
                raise ExerciseParseError("Exercise does not reside in the specified course")
            relative_path = path[len(course_path) :]
            if relative_path.startswith("/"):
                relative_path = relative_path[1:]
            return self.add_exercise(relative_path, course, db=db)
        keys = [];
        paths = {};
        base = course.get_exercises_path(db)
        baselen = len(base)
        path = path.lstrip('/')
        #full_path = os.path.join(course.get_exercises_path(db), path)
        #if not is_exercise( full_path )  and not settings.RUNTESTS :
        #    path = reconnect_exercise_to_path(path,course,db)
        return self.add_exercise(path , course, db=db)

    def add_exercise(self, exercise_path, course, db=settings.DB_NAME):
        """Add exercise by relative path.

        Args:
            exercise_path (str): Path relative to course base.
            course (Course): Course model object.

        """
        progress = []
        translation_name = {}
        if exercise_path.startswith("/"):
            exercise_path = exercise_path[1:]
        full_path = os.path.join(course.get_exercises_path(db), exercise_path)
        if not is_exercise(full_path):
            logger.error(f"ADD EXERCISE FULL_PATH = FAILS WITH FULL_PATH = {full_path}" )
            logger.error(f"ADD EXERCISE EXERCISE_PATH = {exercise_path}")
            logger.error(f"REFUSED TO SAVE")
            return (("warning" , "REFUSED TO SAVE"))
            #assert False, f"FULL_PATH {full_path} DOES NOT EXIST"
            #raise ExerciseNotFound(full_path)
        exercisetree = exercise_xmltree(os.path.join(course.get_exercises_path(db), exercise_path))
        #logger.error(f"EXERCISE_TREE={exercisetree}")F*(bx-ax)
        exercisename_xml = exercisetree.xpath("/exercise/exercisename")
        #logger.error(f"XML = {exercisename_xml}")
        if exercisename_xml:
            translation_name = get_translations(exercisename_xml[0])
        name = (exercisetree.xpath("/exercise/exercisename/text()") or ["No name"])[0]
        key = exercise_key_get_or_create(os.path.join(course.get_exercises_path(db), exercise_path))
        key = str(key);
        #logger.error(f"KEY = {key}")
        #logger.error(f"COURSE = {course}")
        #translated_name=JSON.dumps(translation_name)
        path=exercise_path
        folder=os.path.dirname(exercise_path)
        exercise_key=key
        try :
            dbexercise, created = Exercise.objects.using(db).get_or_create(course=course,exercise_key=key,name=name,path=exercise_path,folder=folder)
            dbexercises = Exercise.objects.using(db).filter(exercise_key=key,course=course)
            if dbexercises :
                dbexercise = dbexercises[0]
            else :
                dbexercise = Exercise.objects(course=course,exercise_key=key)
            dbexercise.name = name
            dbexercise.path = path
            dbexercise.folder = folder
            dbexercise.translated_name = json.dumps( translation_name )
            dbexercise.translated_name = json.dumps( translation_name )
            dbexercise.save();
        except Exception as e :
            defaults = dict(
                name=name,
                translated_name=JSON.dumps(translation_name),
                path=exercise_path,
                folder=os.path.dirname(exercise_path),
            )
            dbexercise, created = self.update_or_create(exercise_key=key, course=course, defaults=defaults)
        defaults_meta = {"sort_key":  name} # os.path.basename(exercise_path)}
        dbmeta, created_meta = ExerciseMeta.objects.get_or_create(exercise=dbexercise, defaults=defaults_meta)
        # if os.path.exists(jsonfile) :
        #    print(f"jsonfile = {jsonfile} exists ")
        #    with open(jsonfile,"r") as f :
        #        s= f.read()
        #    j = json.loads(s)
        #    print(f"j = {j}")
        #    for key in ['difficulty','required','image','allow_pdf','bonus','published','locked','sort_key','feedback' ] :
        #        jm = getattr(dbmeta,key)
        #        print(f"KEY={key} {j[key]} {jm}")
        #        setattr(dbmeta,key,j[key])
        #    print(f" META = {dbmeta}")
        #    dbmeta.save()F*(bx-ax)
        #    #os.path.remove(jsonfile)
        if created_meta:
            progress.append(("success", _("Added exercise ") + exercise_path))
            # logger.debug('Adding ' + exercise_path + '/' + name + ' to database.')
        else:
            pass
            # progress.append(("info", _("Updated exercise ") + exercise_path))
            # logger.debug('Updated ' + exercise_path + '/' + name)
        questions = exercisetree.xpath("/exercise/question")
        keys = [x.get("key") for x in questions]
        if len(keys) > len(set(keys)):
            raise ExerciseParseError("Duplicate question keys!")
        for question in questions:
            question_key = question.get('key')
            #if qtype == "none"  or qtype == 'default':
            #    global_xmltrees = exercisetree.xpath('/exercise/global')
            #    global_xml = ''
            #    for global_xmltree in global_xmltrees :
            #        global_xml = etree.tostring( global_xmltree).decode('utf-8')
            #    question_xpath = f'/exercise/question[@key=\"{question_key}\"]'
            #    question_xmltree = exercisetree.xpath(question_xpath)[0]
            #    question_xml = etree.tostring( question_xmltree).decode('utf-8');
            #    qtype = get_qtype(  global_xml , question_xml , exercise_key, src='MODELS')
            #    #print(f"GLOBAL_XML = {global_xml}")
            #    #print(f"QUESTION_XML = {question_xml}")

            #    #print(f"QTYPE = {qtype}")
            #if not question_validate_xmltree(question):
            #    logger.debug(exercise_path + " contains invalid question: ")
            #    nested_print(question)
            #    raise ExerciseParseError("Invalid question in " + name)
            #print(f"NOW UPDATE QTYPE = ", qtype )
            #print(f"CREATE THE QUESTION  {question_key}")
            dbquestion, created = Question.objects.update_or_create(
                exercise=dbexercise,
                question_key=question.get("key"),
                defaults={"type": 'default'},
            )
            qtype = dbquestion.type
            if not settings.RUNTESTS :
                qtype = dbquestion.qtype()
                dbquestion.type = qtype
                dbquestion.save(using=db) 
            if created:
                logger.debug(name + ": Adding question " + question.get("key") + f" of type {qtype} "  )
            #print(f"CHECK QTYPES DB: {qtypecheck} SET TO {qtype}")
            #print(f"QTYPECHECK = {qtypecheck}")
            # else:
            #    logger.debug(
            #        (
            #            name
            #            + ': Updating question '
            #            + question.get('key')
            #            + ' of type '
            #            + question.get('type')
            #        )
            #    )
        questions_with_key = exercisetree.xpath("/exercise/question[@key]")
        for question in Question.objects.using(db).filter(exercise=dbexercise).all() :
            bool_list = map(lambda q: q.get("key") == question.question_key, questions_with_key)
            exists = reduce(lambda a, b: a or b, bool_list, False)
            if not exists:
                try :
                    question.delete(using=db)
                except  Exception as err :
                    logger.error(f"DELETION EXCEPTION {str(err)}")


        progress.extend(
            exercise_check_thumbnail(exercisetree, os.path.join(course.get_exercises_path(db), exercise_path))
        )
        # if os.path.exists(jsonfile) :
        #    os.path.remove(jsonfile)
        # path = dbexercise.get_full_path()
        # jsonfile = os.path.join(path,'meta.json')
        # if os.path.exists(jsonfile) :
        #    print(f"jsonfile = {jsonfile} exists ")
        #    with open(jsonfile,"r") as f :
        #        s= f.read()
        #    j = json.loads(s)
        #    print(f"j = {j}")
        #    for key in ['difficulty','required','image','allow_pdf','bonus','published','locked','sort_key','feedback' ] :
        #        jm = getattr(dbmeta,key)
        #        print(f"KEY={key} {j[key]} {jm}")
        #        setattr(dbmeta,key,j[key])
        #    print(f" META = {dbmeta}")
        #    dbmeta.save()
        #    dbexercise.save()
        #    #os.path.remove(jsonfile)

        return progress

    def validate_all(self, course, i_am_sure=True, db=settings.DB_NAME):
        subdomain = db
        logger.error(f"VALIDATGE_ALL DB={db}")
        need_to_be_sure = False
        progress = [("success", _("Checking status of file tree..."))]
        exercises = Exercise.objects.using(db).filter(meta__published=True)
        char_limit = 60
        n = len( exercises)
        nerr = 0
        for exercise in exercises :
            key = exercise.exercise_key
            name = f"<a href=\"exercise/{key}/\"> {exercise.name} </a>"
            ename = exercise.name
            key = exercise.exercise_key
            name = f"<a onClick={{(ev) => onExerciseClick({key}, {subdomain})}}> <div> {name} </div> </a>"
            name = str( key )
            #print(f"NAME = {nname}")
            try :
                res = dict( exercise.validate() )
                if 'error' in res :
                    msg = html.unescape( res['error'] )
                    msg = f" :<em>{msg}</em>"
                    #msg = '<em>' +  ename + ' </em> : ' + (msg[:char_limit] + "...") if char_limit<len(msg) else msg
                    res = (key , msg )
                    nerr = nerr + 1
                else :
                    res = ('success', exercise.name + ' :  OK ')
                    res = ( key , 'success' )
                    res = None
            except Exception as e :
                nerr = nerr + 1
                msg = f" : <em> {str(e) } </em>"
                msg =  ename  + msg 
                res = ( key , msg )
            if res :
                progress.append(res)
        progress.append(("success", _(f"Finished validating {n} published exercises and {nerr} has errors .")))
        yield progress



    def sync_with_disc(self, course, i_am_sure=False, db=settings.DB_NAME):
        subdomain = db
        db = course.opentasite
        logger.error(f"SYNC_WITH_DISC DB={db}")
        if not settings.RUNNING_DEVSERVER:
            caches["default"].set("temporarily_block_translations", True, 35)
        need_to_be_sure = False
        prevent_reload = False
        logger.debug("Starting sync with disc of exercises.")
        progress = [("success", _("Checking status of file tree..."))]
        exerciselist = []
        exercises_without_keys = []
        keys = {}
        other_courses_keys = self.exclude(course=course).values_list("exercise_key", flat=True)
        exercises_path = course.get_exercises_path(db)
        # chown( exercises_path ) # unimplemented CHOWN  funcionality
        if not settings.RUNTESTS :
            trashdir = os.path.join(exercises_path, "z:Trash")
            invisible = os.path.join( trashdir, 'invisible')
            os.makedirs(invisible, exist_ok=True)
            exercisexml = os.path.join(invisible, 'exercise.xml')
            if not os.path.exists(exercisexml ):
                f = open(exercisexml,'w')
                f.write("<exercise> <exercisename>invisible</exercisename> </exercise>\n")
                f.close
                f = open( os.path.join(invisible,'exercisekey') ,"w")
                f.write('abcdefagasdfa')
                f.close

        for root, dirs, files in os.walk(exercises_path, topdown=False):
            for dir in dirs:
                newDir = os.path.join(root, dir)
                if len(os.listdir(newDir)) == 0:
                    os.rmdir(newDir)
                strip_dir = dir.strip()
                strip_dir = re.sub("\s+", " ", strip_dir)
                if not dir == strip_dir:
                    try:
                        os.rename(
                            os.path.join(root, dir),
                            os.path.join(root, strip_dir).encode(encoding="UTF-8", errors="replace"),
                        )
                    except OSError:
                        logger.error(f"Directory {strip_dir} is not empty and was not overwritten")

        for root, directories, filenames in os.walk(course.get_exercises_path(db), followlinks=True):
            for filename in filenames:
                # print("FULLFILE = %s " %   os.path.os.path.join( root, filename) )
                # os.path.os.path.join( root, filename)
                # os.chmod(root,0755)
                # os.chmod( os.path.os.path.join( root, filename), 0755 )
                try:
                    if filename == "exercise.xml":
                        name = os.path.basename(os.path.normpath(root))
                        if settings.FIX_XML:
                            xmlpath = os.path.os.path.join(root, filename)
                            xml = exercise_xml(xmlpath)
                            logger.debug("XMLPATH= %s " % xmlpath)
                            logger.debug("COURSE EXERCISES PATH = %s " % course.get_exercises_path(db))
                            path = (str(xmlpath.replace(course.get_exercises_path(db), ""))).split("/")
                            logger.debug("PATH = %s " % path)
                            path.pop(0)
                            path.pop()
                            logger.debug("PATH = %s " % path)
                            path = "/".join(path)
                            exercise = Exercise.objects.get(path=path, course=course)
                            #print(f"EXERCISE = {exercise}")
                            xml_link = exercise.exercise_asset_file_url("exercise.xml.txt")
                            logger.debug("xml_link = %s " % xml_link)
                            (newxml, changed) = fix_xml(xml, xml_link)
                            if changed and not settings.RUNTESTS:
                                txtfile = str(xmlpath) + ".txt"
                                if not os.path.exists(txtfile):
                                    shutil.copy(xmlpath, str(xmlpath) + ".txt")
                                    shutil.copy(
                                        xmlpath, str(xmlpath) + "-" + str(random.randint(11111, 99999)) + ".txt"
                                    )
                                    f = open(xmlpath, "w")
                                    f.write(newxml)
                                    f.close()
                            if not changed:
                                txtfile = str(xmlpath) + ".txt"
                                logger.debug("NOT CHANGED SO TRY TO REMOVE %s " % txtfile)
                                logger.debug("NOT CHANGED SO TRY TO REMOVE %s " % txtfile)
                                if os.path.exists(txtfile):
                                    logger.debug("DO REMOVE %s " % txtfile)
                                    os.remove(txtfile)

                        relpath = root[len(exercises_path) :]
                        splitname = name.rsplit(".problem", 1)
                        if not slugify(splitname[0]) == splitname[0]:
                            splitname[0] = slugify(splitname[0]) + "-" + str(random.randint(11111, 99999))
                            new_name = ".problem".join(splitname)
                            new_root = "/".join(root.split("/")[:-1] + [new_name])
                            os.rename(root, new_root)
                except ObjectDoesNotExist as e:
                    logger.info(f"FILE DOES NOT EXIST SYNC ERROR 1622 in exercise {name} { str( type(e).__name__ ) } ")
                except Exception as e:
                    logger.debug(f"FILE SYNC ERROR 1623 in exercise {name} { str( type(e).__name__ ) } ")
                    logger.error(traceback.format_exc())

        progress.append(("success", "Checking in" + exercises_path))

        for root, directories, filenames in os.walk(course.get_exercises_path(db), followlinks=True):
            for filename in filenames:
                if filename == "exercise.xml":
                    name = os.path.basename(os.path.normpath(root))
                    relpath = root[len(exercises_path) :]
                    # THE NEXT COMMAND CAUSED SYNC TO CRASH WHEN exercise.xml mistakenly is put in root dir
                    if not relpath == "":  # GET RID OF EDGE CASE WHEN exercise.xml mistakenly is put in root dir
                        exerciselist.append((name, relpath))

        for name, path in exerciselist:
            try:
                key = exercise_key_get(os.path.join(exercises_path, path))
                if key in other_courses_keys:
                    duplicate_exercise = self.get(exercise_key=key)
                    progress.append(("error", _("Duplicate exercise keys!")))
                    progress.append(
                        (
                            "error",
                            _("Exercise at [")
                            + path
                            + _("] has the same key as exercise in other course:" + str(duplicate_exercise)),
                        )
                    )
                    progress.append(
                        (
                            "warning",
                            _(
                                (
                                    "You will need to fix this before a reload is possible."
                                    "(Perhaps you copied an exercise? Then please remove the"
                                    " key file from the new exercise to generate a new one on reload)"
                                )
                            ),
                        )
                    )
                    prevent_reload = True
                elif key in keys:
                    progress.append(("error", _("Duplicate exercise keys!")))
                    progress.append(
                        (
                            "error",
                            _("Exercise at [") + path + _("] has the same key as exercise at [") + keys[key] + "]",
                        )
                    )
                    progress.append(
                        (
                            "warning",
                            _(
                                (
                                    "You will need to fix this before a reload is possible."
                                    "(Perhaps you copied an exercise? Then please remove the"
                                    " key file from the new exercise to generate a new one on reload)"
                                )
                            ),
                        )
                    )
                    keys.pop(key)
                    prevent_reload = True
                else:
                    keys[key] = path
            except IOError:
                exercises_without_keys.append(path)

        existing_exercises = set(self.filter(course=course).values_list("pk", flat=True))
        file_tree_exercises = set(keys.keys())
        new_exercises = file_tree_exercises - existing_exercises
        for new_exercise in new_exercises:
            progress.append(("success", "A reload would add the exercise at " + keys[new_exercise]))
        for exercise_path in exercises_without_keys:
            progress.append(("success", "A reload would add the exercise at " + exercise_path))

        for exercise in self.filter(course=course):
            if not is_exercise(exercise.get_full_path(use_path_cache=False)):
                if exercise.exercise_key in keys:
                    progress.append(
                        (
                            "info",
                            _("The exercise with path ")
                            + exercise.path
                            + _(" seems to have been moved to ")
                            + keys[exercise.exercise_key],
                        )
                    )
                else:
                    progress.append(
                        (
                            "warning",
                            _("The exercise with path ")
                            + exercise.path
                            + _(" does no longer contain an exercise.xml file and will be deleted."),
                        )
                    )

        for name, path in exerciselist:
            try:
                dbexercise = Exercise.objects.get(path=path)
                try:
                    key = exercise_key_get(os.path.join(exercises_path, path))
                except IOError:
                    key = None
                if dbexercise.exercise_key != key:
                    need_to_be_sure = True
                    progress.append(
                        (
                            "warning",
                            _("The exercise with path ")
                            + path
                            + _(
                                " changed exercise key, this will result in a new exercise "
                                "being added and the old one deleted."
                            ),
                        )
                    )
                    progress.append(("info", "Old key:  " + dbexercise.exercise_key))
                    if key is not None:
                        progress.append(("info", "New key: " + key))
                    else:
                        progress.append(("info", "New key: Empty, a new one will be generated."))
            except Exercise.DoesNotExist:
                pass

        if prevent_reload:
            progress.append(
                (
                    "error",
                    _("Something will prevent a reload from being carried out, " "please review messages above."),
                )
            )
            yield progress
            return
        if need_to_be_sure and not i_am_sure:
            progress.append(("error", _("Are you sure you want to do these actions?")))
            yield progress
            return
        if not need_to_be_sure and not i_am_sure:
            progress.append(
                (
                    "info",
                    _(
                        "Do you want to do a reload? This will update all existing exercises and perform "
                        "any additional actions listed above."
                    ),
                )
            )
            yield progress
            return
        progress.append(("info", "Ok, starting reload..."))
        for name, path in exerciselist:
            try:
                msgs = self.add_exercise(path, course, db=db)
                progress.extend(msgs)
                yield progress
                progress.clear()
            except (ExerciseParseError, IOError) as e:
                progress.append(("warning", "Failed to add " + path + " because " + str(e)))
                yield progress
                progress.clear()
        for exercise in self.filter(course=course):
            exercise.path + "/exercise.xml"
            if not is_exercise(exercise.get_full_path(use_path_cache=False)):
                exercise.delete()
                progress.append(
                    (
                        "warning",
                        _("Deleted ") + exercise.path + _(" since it is not present on disc anymore"),
                    )
                )
            else:
                key = exercise_key_get_or_create(os.path.join(exercises_path, exercise.path))
                if key != exercise.exercise_key:
                    exercise.delete()
                    progress.append(
                        (
                            "warning",
                            _("Deleted an entry for ")
                            + exercise.path
                            + _(
                                " since the stored exercise key did not correspond to the " "exercisekey in the folder."
                            ),
                        )
                    )
        progress.append(("success", _("Finished syncing exercises.")))
        yield progress

class Exercise(models.Model):
    exercise_key = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=255, default="")
    translated_name = models.CharField(max_length=512, default="{}")
    path = models.TextField()
    folder = models.TextField(default="")
    course = models.ForeignKey(Course, related_name="exercises", null=True, on_delete=models.CASCADE)
    objects = ExerciseManager()

    class Meta:
        permissions = (
            ("reload_exercise", "Can reload exercises from disk"),
            ("edit_exercise", "Can edit exercises in frontend"),
            ("create_exercise", "Can create exercises in frontend"),
            ("administer_exercise", "Can administer exercise options"),
            ("view_solution", "Can view exercise solution (even if not published)"),
            ("view_statistics", "Can view student progress statistics"),
            ("view_student_id", "Can view student identity"),
            ("view_unpublished", "Can view unpublished exercises"),
            ("view_xml", "Can view exercise XML"),
        )

    def __str__(self):
        return self.name + ": " + self.path

    def db( self ):
        if settings.RUNTESTS :
            db = 'default'
        else :
            db = self.course.opentasite

    def isbonus(self):
        db = self.course.opentasite
        meta = ExerciseMeta.objects.using(db).get(exercise__pk=self.pk)
        if meta.bonus:
            ret = "bonus"
        elif meta.required:
            ret = "required"
        else:
            ret = "optional"
        # cache.set(cachekey, ret , 20 )
        return ret

    def exercise_asset_file_url(self, filename):
        return "/exercise/%s/asset/%s" % (str(self.exercise_key), filename)

    def exercise_asset_accel_xpath(self, filename):  # the public url
        db = self.course.opentasite
        return f"/{settings.SUBDOMAIN}/exercises/{self.course.course_key}/{self.path}/{filename}"
        # return '/exercise/%s/asset/%s' % ( str( self.exercise_key) , filename )

    def exercise_asset_devpath(self, filename):  # the file path relative to /subdomain-data/SUBDOMAIN
        db = self.course.opentasite
        return "%s/%s/%s" % (self.course.get_exercises_path(db), str(self.path), filename)

    def deadline(self):
        try :
            deadline_time = datetime.time(23, 59, 59)
            course = self.course
            if course is not None and course.deadline_time is not None:
                deadline_time = course.deadline_time
            try:
                deadline_date = self.meta.deadline_date
            except:
                deadline_date = None
            if deadline_date is not None:
                #deadline_date_time = tz.localize(datetime.datetime.combine(deadline_date, deadline_time))
                #deadline_date_time = make_aware(datetime.datetime.combine(deadline_date, deadline_time), tz )
                deadline_date_time = tzlocalize(datetime.datetime.combine(deadline_date, deadline_time))
            else:
                deadline_date_time = None
            return deadline_date_time
        except Exception as err :
            return None

    def uses_exerciseseed(self, *args, **kwargs):
        xmltree = exercise_xmltree(self.get_full_path(), {})
        uses = xmltree.xpath("/exercise/macros")
        if len(uses) == 0:
            return False
        else:
            return True

    def subdomain(self, *args, **kwargs):
        return self.course.opentasite

    def old_validate(self) :

        exercise = self
        db = self.course.opentasite
        questions = Question.objects.using(db).filter(exercise=exercise)
        res = []
        for question in questions :
            #print(f"VALIDATE_QUESTION_IN_EXERCISE_CLASS_DEF {question}")
            res.append(  question.validate_xml() )
        res = dict( res )
        #print(f"RES-OK= {res}")
        return res
            
        

    def validate( self ):
        from exercises.views.api import validate_exercise_xml 
        from exercises.parsing import exercise_xml
        exercise = self
        db = self.course.opentasite
        name = exercise.name
        xml = exercise_xml(exercise.get_full_path())
        user = User.objects.using(db).get(username='super')
        res = validate_exercise_xml( xml, user,  self.exercise_key,db)
        res = dict( res )
        #if 'error' in res :
        #    raise SyntaxError( res['error'] ) 
        return res



    #def old_validate( self ):
    #    print(f"VALIDATE_EXERCISE_IN_CLASS_DEF")
    #    from exercises.views.api import validate_exercise_xml 
    #    from exercises.parsing import exercise_xml
    #    exercise = self
    #    db = self.course.opentasite
    #    name = exercise.name
    #    xml = exercise_xml(exercise.get_full_path())
    #    user = User.objects.using(db).get(username='super')
    #    res = validate_exercise_xml( xml, user,  self.exercise_key)
    #    print(f"XML_VALIDATION IN EXERCCISE_CLASS RES = {res}")
    #    res = dict( res )
    #    return res



    def get_full_path(self, use_path_cache=True):
        course = self.course
        course_key = course.course_key
        dbcheck =  self._state.db 
        db = self.course.opentasite
        if settings.RUNTESTS:
            db = settings.DB_NAME

        try :
            if use_path_cache and not settings.RUNTESTS :
                pathkey = f"{str(db)}-{self.exercise_key}"
                cache = caches["default"]
                path0 = cache.get(pathkey)
                if not None == path0 and use_path_cache and settings.DO_CACHE :
                    if os.path.isdir(path0):
                        return path0
        except Exception as err :
            logger.error(f"{str(err)}")
        path0 = os.path.join(course.get_exercises_path(db), *self.path.split("/"))
        if not os.path.isdir( path0 ) and not settings.RUNTESTS :
            if not db == dbcheck :
                db = dbcheck
                course = Course.objects.using(db).first()
                course_key = str( course.course_key)
                path0 = os.path.join(course.get_exercises_path(db), *self.path.split("/"))
            else :
                exercise_key = self.exercise_key
                path = self.path
                newpath = reconnect_exercise_to_path( path,course, db )
                path = newpath
                folder = self.folder
                logger.error(f"ERROR FOR SUBDOMAIN {db} EXERCISE {exercise_key} folder {folder} PATH {path} FULL_PATH {path0}  JUST DOES NOT EXIST")
        if not settings.RUNTESTS:
            if not os.path.isdir(path0):

                logger.error(f"ERROR IN GET_FULL_PATH {path0} is not a directory db={db} dbcheck={dbcheck} ") # TRY TO UNDERERSTAND DB ERRORS
        if use_path_cache and os.path.isdir(path0) and not settings.RUNTESTS :
            pathkey = f"{str(db)}-{self.exercise_key}"
            cache.set(pathkey, path0, settings.CACHE_LIFETIME )
        return path0

    def questionlist_is_empty( self ):
        questions = Question.objects.filter(exercise=self)
        is_empty = True
        for question in questions:
            if question.points() != '0' :
                is_empty = False
                break;
        return is_empty




    def old_user_is_correct(self, user):
        allcorrect = True
        questions = Question.objects.filter(exercise=self)
        for question in questions:
            try:
                answer = Answer.objects.filter(user=user, question=question).latest("date")
                if not answer.correct:
                    allcorrect = False
            except ObjectDoesNotExist:
                allcorrect = False
        return allcorrect

    def user_is_correct(self, user):
        try:
            user_is_correct = aggregation.models.Aggregation.objects.get(user=user, exercise=self).user_is_correct
        except:
            user_is_correct = False
        return user_is_correct

    def user_tried_all(self, user):
        try:
            tried_all = aggregation.models.Aggregation.objects.get(user=user, exercise=self).user_tried_all
        except:
            tried_all = False
        return tried_all

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        touchfile = "last_admin_activity"
        subdomain = self.course.opentasite
        fname = os.path.join(settings.VOLUME, subdomain, touchfile)
        if not settings.RUNTESTS :
            os.utime( os.path.join(settings.VOLUME, subdomain) )
            if os.path.exists(fname):
                os.utime(fname, None)




        if self.course.use_auto_translation:
            from aggregation.models import t_cache_and_key

            try:
                # dbexercise = Exercise.objects.get(exercise_key=self.exercise_key)
                dbexercise = self
                (cache, cachekey) = t_cache_and_key(dbexercise.course, dbexercise)
                if cache.has_key(cachekey):
                    # logger.debug("DELETING CACHEKEY %s " % cachekey )
                    cache.delete(cachekey)
            except ObjectDoesNotExist:
                pass

    def post_save(self, *args, **kwargs):
        #print("POST_SAVE EXERCISE")
        instance = kwargs["instance"]
        db = kwargs['using']
        try:
            course = instance.course
            subdomain = instance.course.opentasite
            db = subdomain,
            exercise = instance
            exercise_saved.send(
                sender=self.__class__,
                user=None,
                username=None,
                exercise=exercise,
                course=course,
                date=None,
                db=db,
                subdomain=subdomain,
                src="models_Exercise1"
            )
        except ObjectDoesNotExist as e:
            return
        except Exception as e:
            logger.error(f"POST_SAVE ERROR {type(e).__name__} {str(e)}")
            return
        touch_(course.opentasite)
        answer_received.send(
                sender=self.__class__, 
                user=None, 
                username=None,
                exercise=exercise, 
                course=course, 
                date=None, 
                subdomain=subdomain, 
                db=db,  
                src="models_Exercise"
            )


def function_qtype( subdomain, exercise_key, question_key ):
    # Pick the DB alias. In tests, prefer the configured default alias.
    db = subdomain
    if settings.RUNTESTS:
        db = getattr(settings, "DB_NAME", None) or "default"
    cache = caches["default"]
    varhash = get_hash_from_string( f'qtype-{subdomain}-{exercise_key}-{question_key}' )
    qtype = cache.get(varhash )
    src = 'function qtype'
    if  not qtype == None  and not qtype == 'default' and settings.DO_CACHE : # CACHING qtype
            #print(f"GRABBED QTYPE {varhash}")
            return qtype
    try:
        exercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
    except Exercise.DoesNotExist:
        # During tests, database routing/ordering can briefly hide the exercise; default safely.
        if settings.RUNTESTS:
            logger.warning(f"QTYPE: Exercise {exercise_key} not found in DB '{db}' during tests; defaulting to 'basic'")
            return "basic"
        raise
    try:
        xmltree = exercise_xmltree(exercise.get_full_path(), {})
        question_xmltree = xmltree.xpath(f'/exercise/question[@key="{question_key}"]' )
        if question_xmltree   :
            question_xmltree = question_xmltree[0]
        else :
            return 'basic'
        global_xmltrees = xmltree.xpath('/exercise/global')
        global_xml = ''
        for global_xmltree in global_xmltrees:
            global_xml = global_xml + etree.tostring(global_xmltree).decode('utf-8')
        question_xml = etree.tostring(question_xmltree).decode('utf-8')
        qtype = get_qtype_from_xml(global_xml, question_xml, exercise_key, src)
    except Exception as e:
        # In tests there may be no exercise files on disk; fall back to a sane default.
        if settings.RUNTESTS:
            logger.warning(f"QTYPE fallback: {type(e).__name__}: {e}; returning 'basic'")
            qtype = "basic"
        else:
            raise
    cache.set(varhash, qtype, settings.CACHE_LIFETIME)
    #print(f"FUNCTION_QTYPE IS SETTING TO {qtype}")
    return qtype


def function_question_xmltree( subdomain, exercise_key, question_key ):
    # Pick the DB alias. In tests, prefer the configured default alias.
    db = subdomain
    if settings.RUNTESTS:
        db = getattr(settings, "DB_NAME", None) or "default"
    cache = caches["default"]
    varhash = get_hash_from_string( f'xmltree-{subdomain}-{exercise_key}-{question_key}' )
    xml = cache.get(varhash)
    if xml :
        return etree.fromstring( xml )
    try:
        exercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
    except Exercise.DoesNotExist:
        # During tests, database routing/ordering can briefly hide the exercise; default safely.
        if settings.RUNTESTS:
            logger.warning(f"QTYPE: Exercise {exercise_key} not found in DB '{db}' during tests; defaulting to 'basic'")
            return "basic"
        raise
    try:
        xmltree = exercise_xmltree(exercise.get_full_path(), {})
        question_xmltree = xmltree.xpath(f'/exercise/question[@key="{question_key}"]')
    except Exception as e:
        # In tests there may be no exercise files on disk; fall back to a sane default.
        if settings.RUNTESTS:
            logger.warning(f"QTYPE fallback: {type(e).__name__}: {e}; returning 'basic'")
        else:
            raise
    #print(f"FUNCTION_QTYPE IS SETTING TO {qtype}")
    if isinstance( question_xmltree, list ):
        question_xmltree = question_xmltree[0]
    try :
        xml = etree.tostring( question_xmltree)
        cache.set(varhash, xml, settings.CACHE_LIFETIME)
    except :
        pass
    return question_xmltree




#def function_qtype( subdomain, exercise_key, question_key ):
#    db = subdomain
#    cache = caches["default"]
#    varhash = get_hash_from_string( f'qtype-{subdomain}-{exercise_key}-{question_key}' )
#    qtype = cache.get(varhash )
#    src = 'function qtype'
#    if  not qtype == None  and not qtype == 'default' and settings.DO_CACHE : # CACHING qtype
#            #print(f"GRABBED QTYPE {varhash}")
#            return qtype
#    exercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
#    xmltree = exercise_xmltree(exercise.get_full_path(), {})
#    question_xmltree = xmltree.xpath('/exercise/question[@key="{key}"]'.format(key=question_key))[0]
#    global_xmltrees = xmltree.xpath('/exercise/global')
#    global_xml = ''
#    for global_xmltree in global_xmltrees: 
#        global_xml = global_xml + etree.tostring( global_xmltree).decode('utf-8')
#    question_xml = etree.tostring( question_xmltree).decode('utf-8')
#    qtype = get_qtype_from_xml(   global_xml , question_xml , exercise_key ,src ) 
#    cache.set(varhash, qtype,settings.CACHE_LIFETIME)
#    #print(f"FUNCTION_QTYPE IS SETTING TO {qtype}")
#    return qtype
#


class Question(models.Model):
    class Meta:
        unique_together = ("question_key", "exercise")
        permissions = (("log_question", "Answers are logged"),)

    question_key = models.CharField(max_length=255)
    exercise = models.ForeignKey(Exercise, related_name="question", on_delete=models.CASCADE)
    type = models.CharField(max_length=255, default="none")
    tracker = FieldTracker()

    def __str__(self):
        try:
            return self.exercise.name + ": " + self.question_key
        except Exception as e:
            # DEBUG_PLUS
            return "MISSING SELF.EXERCISE.NAME " + str(e).__name__ + ": " + self.question_key

    #def save(self, *args, **kwargs):
    #    logger.error(f"QUESTION_SAVE ")
    #    super().save(*args, **kwargs)


    def get_ai_messages( self ):
        assistant_name = self.assistant_name();
        try :
            threads = Thread.objects.filter(assistant__name=assistant_name)
            messages = Message.objects.filter(thread__in=threads)
        except Exception as err : # ObjectDoesNotExist as err :
            messages = Message.objects.none()
        return messages


    def qtype( self ):
        src = 'qtype'
        exercise = self.exercise;
        subdomain = exercise.course.opentasite
        exercise_key = str( exercise.exercise_key )
        question_key = self.question_key
        qtype =  function_qtype( subdomain, exercise_key, question_key )
        return qtype

    def get_xmltree(self):
        exercise = self.exercise;
        subdomain = exercise.course.opentasite
        exercise_key = str( exercise.exercise_key )
        question_key = self.question_key
        #xmltree = exercise_xmltree(self.exercise.get_full_path(), {})
        #question_xmltree = xmltree.xpath('/exercise/question[@key="{key}"]'.format(key=self.question_key))[0]
        question_xmltree = function_question_xmltree( subdomain, exercise_key, question_key)
        return question_xmltree





    def validate_xml(self,xml):
        # HAVE TO ACCOMODATE UNSAVED XML TO VALIDATE
        exercise = self.exercise;
        exercise_key = exercise.exercise_key
        question_key = self.question_key
        course = exercise.course;
        db = course.opentasite;
        username = "super"
        ret = validate_question_xml( db, exercise_key, question_key, username, xml )
        return ret



    def points(self, *args, **kwargs):
        xmltree = exercise_xmltree(self.exercise.get_full_path(), {})
        question_xmltrees = xmltree.xpath('/exercise/question[@key="{key}"]'.format(key=self.question_key))
        if question_xmltrees :
            points =  question_xmltrees[0].get("points", None)
        else :
            points =  1
        return points

    def uses_questionseed(self, *args, **kwargs):
        xmltree = exercise_xmltree(self.exercise.get_full_path(), {})
        uses = xmltree.xpath('/exercise/question[@key="{key}"]/macros'.format(key=self.question_key))
        return len(uses) > 0
        # if len( uses ) == 0 :
        #    return False
        # else :
        #    return True

    def assistant_name(self ) :
        exercise = self.exercise
        exercise_key = exercise.exercise_key 
        question_key = self.question_key
        question_xmltree = self.get_xmltree();
        xml = etree.tostring( question_xmltree )
        questiondict = (xmltodict.parse(etree.tostring(question_xmltree)))
        questiondict = dict( questiondict)["question"]
        qtype = questiondict.get('@type', None )
        assistant_name = exercise.course.opentasite
        subpath = questiondict.get('querypath' ,None)
        #print(f"SUBPATH = {subpath}")
        if subpath == None :
            subpath = exercise.course.opentasite
            subpath = re.sub(r"^(\S+)-(\d+)",r"\1",subpath)
        segments = subpath.split('/')
        xt = str( exercise_key )[0:7] + str(question_key)
        segments.append(xt)
        assistant_name = ( '.'.join( segments ) ).rstrip('.')
        #print(f"ASSISTANT_NAME = {assistant_name}")
        return assistant_name








    def post_save(self, *args, **kwargs):
        instance = kwargs["instance"]
        question_key_has_changed = instance.tracker.has_changed("question_key")
        exercise = kwargs["instance"].exercise
        exercise_key = exercise.exercise_key 
        question_key = instance.question_key 
        qtype = 'basic'
        full_path = instance.exercise.get_full_path();
        #xmltree = exercise_xmltree(full_path, {})
        #xml = etree.tostring( xmltree )
        course = exercise.course
        subdomain = course.opentasite
        qtype = instance.qtype();


        if  settings.USE_CHATGPT :

            def make_text_file_from_exercise(exercise):
                xmltree = exercise_xmltree(exercise.get_full_path(), {})
                xml = etree.tostring( xmltree ).decode()
                txt = extract_text_blocks_from_xml_string(xml)
                outfile = os.path.join( exercise.get_full_path(), f'{question_key}.txt')
                fp = open( outfile, "w")
                fp.write(txt)
                fp.close();
                return txt


            def save_aibased(full_path) :
                xmltree = exercise_xmltree(full_path, {})
                xml = etree.tostring( xmltree )
                course = exercise.course
                subdomain = course.opentasite
                question_xmltree = xmltree.xpath(f"/exercise/question[@key=\"{question_key}\"]")
                if question_xmltree :
                    question_xmltree = question_xmltree[0]
                questiondict = dict((xmltodict.parse(etree.tostring(question_xmltree)))["question"])

                #subpath = questiondict.get('querypath')
                #segments = subpath.split('/')
                #xt = str( exercise_key )[0:7] + str(question_key)
                #segments.append(xt)
                #assistant_name = ( '.'.join( segments ) ).rstrip('.')
                assistant_name = instance.assistant_name();
                assistant, created = Assistant.objects.get_or_create(name=assistant_name)
                #if True or not assistant.mode_choice :
                #    mode_choice = ModeChoice.objects.get(key='assistant')
                #    assistant.mode_choice = mode_choice
                #    assistant.save(update_fields=['mode_choice'] )
                resources = questiondict.get('resources','')
                mode_choice = questiondict.get('@mode',None)
                instructions = questiondict.get('instructions',None)
                querypath = questiondict.get('querypath',None)
                if resources :
                    filenames_ = [ item.strip() for item in resources.split(',') ]
                else :
                    filenames_ = []
                #print(f"FILENAMES_ = {filenames_}")
                filenames = [s for s in filenames_ if s.strip()]
                #print(f"FILENAMES = {filenames}")
                #filenames.append(f'{question_key}.txt')
                exercise_path = exercise.get_full_path();
                #print(f"ASSISTANT LOCAL_FILES = {assistant.local_files()}")
                local_files = set( [ item[1] for item in assistant.local_files() ] )
                local_pks = list( set( [ item[0] for item in assistant.local_files() ] ) )
                #print(f"LOCAL_PKS = {local_pks}")
                #local_old_dates = [ OpenAIFile.objects.get(pk=f).date for f in local_pks ]
                #print(f"LOCAL_OLD_DATES = {local_old_dates}")
                deletions = list( local_files - set( filenames ) )
                #print(f"DELETIONS = {deletions}")
                if deletions :
                    for  o in assistant.local_files() :
                        (oldpk, oldname, oldcksum, olddir ) = o;
                        #print(f"OLDPK = {oldpk} OLDNMAME = {oldname}  ")
                        if oldname in deletions :
                            #print(f" OLDNAME = {oldname} in DELETEIONS ")
                            assistant.delete_file(oldpk)
                #additions = list( set(filenames) - local_files )
                #print(f"ADDITIONS = {additions}")
                #for file in filenames :
                #    filepath = os.path.join( exercise_path , file)
                #    print(f"FILEPATH = {filepath}")
                #    if os.path.exists( filepath ) :
                #        ts = os.path.getmtime(filepath)
                #        new_date = datetime.fromtimestamp(ts, tz=timezone.utc)
                #        print(f"NEW_DATES = {new_date}")
                #        old_date =  OpenAIFile.objects.get(name=file).date 
                #        print(f"OLD_DATE = {old_date}")
                #        is_new = new_date > old_date
                #        print(f"ISNEW = {is_new}")
                #        if is_new : 
                #            deletions.append( file )
                #            additions.append( file )
                #print(f" NOW DELETIONS = {deletions} ADDITIONS = {additions}")
                #vss = VectorStore.objects.filter(name=assistant_name).all();
                #if vss :
                #    for vs in vss :
                #        ff = vs.file_names() 
                #        print(f"OLD VS = {vs} {ff}")



                #if len( deletions ) > 0 :
                #    for d in deletions :
                #        pk = OpenAIFile.objects.get(name=d).pk
                #        print(f"DELETE {d} pk={pk} ")
                #        assistant.delete_file(pk)
                if instructions:
                    assistant.instructions = instructions
                    assistant.save(update_fields=['instructions'] )
                if mode_choice :
                    mode_choice = ModeChoice.objects.get(key=mode_choice)
                    assistant.mode_choice = mode_choice
                    assistant.save(update_fields=['mode_choice'] )
                for file in filenames :
                    filepath = os.path.join( exercise_path , file)
                    #print(f"FILEPATH = {filepath}")
                    assert os.path.exists( filepath ) , f"path to {file} is not found"
                    #print(f"NOW ADD FILE")
                    assistant.add_file_by_name( filepath )
                    #print(f"FILE ADDED")
            try :
                save_aibased(full_path);
            except Exception as err :
                print(f"ERROR IN SAVING AIBASED {type(err)} {str(err)}")
                

        if not settings.RUNTESTS :
            os.utime( os.path.join(settings.VOLUME, subdomain) )
        if question_key_has_changed:
            exercise = kwargs["instance"].exercise
            course = exercise.course
            subdomain = course.opentasite
            if not settings.RUNTESTS :
                os.utime( os.path.join(settings.VOLUME, subdomain) )
            answer_received.send(
                sender=self.__class__,
                user=None,
                username=None,
                exercise=exercise,
                course=course,
                db=subdomain,
                date=None,
                subdomain=subdomain,
                src="models_Question_post_save",
            )

        cache = caches["default"]
        varhash = get_hash_from_string( f'qtype-{subdomain}-{exercise_key}-{question_key}' )
        #print(f"DELETE qtype-{subdomain}-{exercise_key}-{question_key}" )
        if cache.get(varhash ) :
            cache.delete( varhash )

    def post_delete(self, *args, **kwargs):
        instance = kwargs["instance"]
        exercise = kwargs["instance"].exercise
        course = exercise.course
        subdomain = course.opentasite
        if not settings.RUNTESTS :
            os.utime( os.path.join(settings.VOLUME, subdomain) )
        question_key_has_changed = instance.tracker.has_changed("question_key")
        exercise = kwargs["instance"].exercise
        exercise_key = exercise.exercise_key 
        question_key = instance.question_key
        course = exercise.course
        if question_key_has_changed:
            answer_received.send(
                sender=self.__class__,
                user=None,
                username=None,
                exercise=exercise,
                course=course,
                date=None,
                subdomain=subdomain,
                db = subdomain,
                src="models_Question_delete",
            )
        varhash = get_hash_from_string( f'qtype-{subdomain}-{exercise_key}-{question_key}' )
        #print(f"DELETE {varhash}")
        cache = caches['default']
        if cache.get(varhash ) :
            cache.delete( varhash )



class Answer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True, related_name="answer")

    answer = models.TextField()
    grader_response = models.TextField(default="")
    correct = models.BooleanField()
    date = models.DateTimeField(default=now)
    user_agent = models.TextField(default="")
    questionseed = models.TextField(default="")
    exerciseseed = models.TextField(default="")

    def __str__(self):
        return (
            self.user.username
            + " answered {"
            + self.answer
            + "} which is "
            + ("correct" if self.correct else "incorrect")
        )

    def post_save(self, *args, **kwargs):
        db = kwargs["using"]
        subdomain = db if not settings.RUNTESTS else 'openta'
        #print(f"SAVE ANSWER")
        if not settings.RUNTESTS :
            os.utime( os.path.join(settings.VOLUME, subdomain) )
        instance = kwargs["instance"]
        #try:
        #    ins = db).select_related("user", "question", "question__exercise", "question__exercise__course").get(pk=instance.pk))
        #except ObjectDoesNotExist as e:
        #    return
        answer = instance.answer
        user = instance.user
        username = user.username
        date = instance.date
        question = instance.question
        try :
            question_key = instance.question.question_key
        except :
            question_key=None
        questionseed = instance.questionseed
        grader_response = instance.grader_response
        try :
            correct = instance.correct
        except Exception as e :
            logger.error(f"{str(e)}")
            correct = False
        try:
            msg = ""
            exercise = question.exercise
            msg = msg + f"{exercise} {question_key}  1"
            exercise_key = exercise.exercise_key
            msg = msg + "2"
            course = exercise.course
            msg = msg + "3"
            course_key = course.course_key
            msg = msg + "4"
            archive = os.path.join(
                settings.VOLUME, db, "json-answer-backups", str(course_key), str(username), str(exercise_key)
            )
            msg = msg + "5"
            filename = os.path.join(archive, str(question_key) + ".json")
            msg = msg + "6"
            os.makedirs(archive, exist_ok=True)
            msg = msg + "7"
            if question.type == 'aibased' :
                path = exercise.get_full_path() 
            save_json = json.dumps(
                {
                    "user": str(username),
                    "answer": str(answer),
                    "correct": str(correct),
                    "date": str(date),
                    "questionseed": str(questionseed),
                    "grader_response": str(grader_response),
                }
            )
            msg = msg + "8"
            sender = self.__class__
            msg = msg + "a"
            open(filename, "w+").write(save_json)
            msg = msg + "9"
            user = User.objects.using(db).get(username=username) # Make sure LazyOpject is not passed

            with transaction.atomic(using=db) :
                logger.info(f"USE ATOMIC TRANSACTION USER={user} pk={user.pk}   exercise={exercise} key={exercise.exercise_key}  course={course} subdomain={subdomain} db={db} username={username} src=models_Answer_post_save")
                answer_received.send(
                    sender=sender,
                    user=user,
                    exercise=exercise,
                    course=course,
                    date=date,
                    subdomain=subdomain,
                    db=db,
                    username=username,
                    src="models_Answer_post_save",
                )






        except Exception as e:
            logger.error(
                f"EXERCISE_SAVE  POST_SAVE FAILED msg={msg} type={type(e).__name__} DB = {db} {username} "
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        (f"ANSWER SAVED {self}")
        user = self.user
        username = user.username
        question = self.question;
        exercise = question.exercise
        subdomain = kwargs.get('using',question.exercise.course.opentasite)
        db = subdomain
        exercise_key = str( exercise.exercise_key )
        cache = caches['default'];
        username_ = username.encode('ascii','ignore').decode('ascii')
        cachekey = f"{username_}:X:{exercise_key}"
        logger.info(f"SET CACHE {cachekey} =  {subdomain}")
        cache.set(cachekey,subdomain)


    #    #print(f" SAVE self = {self}")
    #    db = kwargs['using']
    #    try :
    #        msg = '0'
    #        #if self.pk == None:
    #        #    msg += '1'
    #        #    answers = Answer.objects.using(db).filter(user=self.user, question=self.question)
    #        #    nattempt = 0
    #        #    for answer in answers :
    #        #        g = answer.grader_response
    #        #        if 'correct' in g :
    #        #            nattempt = nattempt + 1
    #        #    nattempt = 1 if answers == None else answers.count()
    #        #    print(f"NATTEMPT = {nattempt}")
    #        #    msg += '3'
    #        #    self.nattempt = nattempt
    #        #    msg += '4'
    #        #msg += '5'
    #        print(f" SUPER SAVED nattempt={self.nattempt}")
    #    except  Exception as e :
    #        logger.error("MODELS ANSSWER SAVE args = %s", args )
    #        logger.error("MODELS ANSWSER KWARGS = %s", kwargs)
    #        logger.error("MODELS INSTANCE = %s", self)
    #        logger.error(f"MODELS ANSWER SAVE FAILED msg={msg} {type(e).__name__} user={self.user} question={self.question}")


def answer_image_filename(instance, filename):
    #logger.error(f"INSTANCE = {dir(instance)}")
    #logger.error(f"FILENAME = {filename}")
    subdomain = instance.exercise.course.opentasite
    ret = "/".join(
        [
            subdomain,
            "media",
            "answerimages",
            str(instance.exercise.course.course_key),
            instance.user.username,
            instance.exercise.exercise_key,
            str(uuid.uuid4()) + os.path.splitext(filename)[1],
        ]
    )
    ret = re.sub(r"^/", "", ret)
    # logger.info(f"TRIGGER ANSWER_IMAGE_FILANAME {ret}")
    return ret


class ImageAnswer(models.Model):
    IMAGE = "IMG"
    PDF = "PDF"
    FILETYPE_CHOICES = ((IMAGE, "Image"), (PDF, "Pdf"))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.SET_NULL, null=True, related_name="imageanswer")
    date = models.DateTimeField(default=now)
    filetype = models.CharField(max_length=3, choices=FILETYPE_CHOICES, default=IMAGE)
    image = models.ImageField(
        default=None,
        blank=True,
        null=True,
        upload_to=answer_image_filename,
        max_length=512,
        storage=upload_storage,
    )
    pdf = models.FileField(
        default=None,
        blank=True,
        null=True,
        upload_to=answer_image_filename,
        max_length=512,
        storage=upload_storage,
    )
    image_thumb = ImageSpecField(
        source="image",
        processors=[ResizeToFill(100, 50)],
        format="JPEG",
        options={"quality": 60},
    )

    def __str__(self):
        try:
            return self.user.username + " image for " + self.exercise.name
        except AttributeError:
            return "__Orphan__"

    def compress(self):
        compress_pil_image_timestamp(self.image.path)

    def remove_file(self):
        try :
            now = time.time()
            if self.image:
                new_path =  str(self.image.path) + ".bak"
                os.rename(self.image.path, new_path )
                os.utime(new_path, (now, now))
            elif self.pdf:
                new_path =  str(self.pdf.path) + ".bak"
                os.rename(self.pdf.path, newPath)
                os.utime(new_path, (now, now))
        except FileNotFoundError as err :
            pass

    def post_save(self, *args, **kwargs):
        instance = kwargs["instance"]
        #print(f"INSTANCE = {instance} {vars(instance)}")
        subdomain = kwargs.get('using', instance.exercise.course.opentasite )
        db = subdomain
        try:
            user = instance.user
            username = user.username
            user = User.objects.using(db).get(username=username) # THIS IS THE ONLY WAY I GOT LAZY OBJECT TO INSTANTIATE
        except User.DoesNotExist:
            return
        pdffile = f"/subdomain-data/{instance.pdf}"
        t = datetime.datetime.now().strftime("%F %T.%f")[:-3]
        subdomain = settings.DB_NAME if settings.RUNTESTS else db
        pypath =  f"/subdomain-data/{subdomain}/urkund.py"

        if os.path.exists( pdffile ) and not os.path.isdir( pdffile ) and  instance.filetype == 'PDF':
            idname = ( pdffile.split('/')[-1].strip('.pdf') ).split('-')[-1]
            existing_pdf = PdfReader(open(pdffile, "rb"))
            output_pdf = PdfWriter()
            first_page = existing_pdf.pages[0]
            height = int( first_page.mediabox.height )
            x0 = 20;
            y0 = height - 10
            text_pdf_stream = create_text_pdf(f"Submitted {t}",idname,x0,y0)
            text_pdf = PdfReader(text_pdf_stream)
            #first_page.merge_page(text_pdf.pages[0])
            #output_pdf.add_page(first_page)
            #for i in range(0, len(existing_pdf.pages)):
            #    output_pdf.add_page(existing_pdf.pages[i])
            extracted_text = ''
            for p in existing_pdf.pages:
                p.merge_page( text_pdf.pages[0] )
                output_pdf.add_page(p)
                extracted_text += p.extract_text();
            textlength = len( extracted_text);
            dirname = os.path.dirname( pdffile )
            output_file = pdffile
            if os.path.exists( output_file ):
                os.remove( output_file )
            with open(output_file ,  "wb") as output_file:
                output_pdf.write(output_file)
            subdomain = dirname.split('/')[2]
            if settings.USE_URKUND :
                pypath =  f"/subdomain-data/{subdomain}/urkund.py"
                module_name = "urkund"
                if os.path.exists(pypath) :
                    try :
                        assert textlength > 430 , "Urkund will not accept this file; the character content is less than 430 characters. Delete and resubmit. Remember, scanned pdf are image and do not contain text."
                        imported_module = dynamic_import(module_name, pypath)
                        email = imported_module.urkund_email( user, instance, pdffile )
                        logger.info(f"EMAIL = {email}")
                        email.send()
                        logger.error(f"URKUND FILE {pdffile} SENT TO URKUND")
                    except Exception as e :
                        logger.error(f":URKUND FILE {pdffile} FAILED TO SEND TO URKUND {str(e)}")
                        raise e


        date = instance.date
        exercise = instance.exercise
        try:
            course = exercise.course

            with transaction.atomic(using=db) :
                logger.info(f"USE ATOMIC TRANSACTION USER={user} pk={user.pk}   exercise={exercise} key={exercise.exercise_key}  course={course} subdomain={subdomain} db={db} username={username} src=models_ImageAnswer_post_save")
                answer_received.send(
                    sender=self.__class__,
                    user=user,
                    exercise=exercise,
                    course=course,
                    date=date,
                    db=db,
                    subdomain=subdomain,
                    username=username,
                    src="models_Image_answer_post_save",
                    )

        except Exception as e :
            logger.error(f"{str(e)} ATOMIC SIGNAL ERROR models_Image_answer_post_save")
            pass


    def post_delete(self, *args, **kwargs):
        #print(f"DELETE ", kwargs )
        instance = kwargs["instance"]
        user = instance.user
        username = instance.user.username
        date = instance.date
        exercise = instance.exercise
        db = kwargs.get('using',exercise.course.opentasite)
        sudomain = db if not settings.RUNTESTS else 'openta'
        try:
            course = exercise.course
            answer_received.send(
                sender=self.__class__,
                user=user,
                exercise=exercise,
                course=course,
                date=date,
                db=db,
                subdomain=subdomain,
                username=username,
                src="models_Image_answer_post_delete",
            )
        except:
            pass


class ImageAnswerManager(models.Model):
    def course_key(self):
        return self.exercise.course.course_key


class ExerciseMeta(models.Model):
    exercise = models.OneToOneField(Exercise, related_name="meta", on_delete=models.CASCADE)
    deadline_date = models.DateField(default=None, null=True, blank=True)
    solution = models.BooleanField(
        default=False,
        verbose_name="Publish solution",
        help_text="Select to allow students to see the solutions listed in the solution tag.",
    )
    difficulty = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        default=None,
        help_text="Optional tag for the exercise that can be edited in course options.",
    )
    required = models.BooleanField(default=False, verbose_name="Obligatory", help_text="Flag exercise as obligatory")
    # student_assets = models.BooleanField(default=False, verbose_name="Student assets")
    # image = models.BooleanField(default=False, verbose_name="Image upload")
    student_assets = models.BooleanField(
        default=False,
        verbose_name="Enable student assets",
        help_text="Select to allow student to upload arbitrary files into asset directory.",
    )
    image = models.BooleanField(
        default=False,
        verbose_name="Require student upload of image or pdf",
        help_text="Select to allow student upload of pdf or png. pdf will be converted to png unless overridden. ",
    )

    allow_pdf = models.BooleanField(
        default=False,
        verbose_name="Do not convert pdf to png.",
        help_text="Select to not automatically convert pdf to png."
        # default=False, verbose_name="Allow pdf as image upload"
    )
    bonus = models.BooleanField(default=False, help_text="Flag exercise as bonus.")
    server_reply_time = models.DurationField(default=None, null=True, blank=True)
    published = models.BooleanField(default=False)
    allow_ai = models.BooleanField(default=False,
        verbose_name="Allow openai queries",
        help_text="Select to allow students to make openai queries")
    # locked = models.BooleanField(default=False)
    locked = models.BooleanField(
        default=False, help_text="Select to lock the question so student can no longer submit answers or images.  "
    )
    sort_key = models.CharField(
        max_length=255,
        default="",
        verbose_name="Sort order key.",
        help_text="An invisible field to order the exercises in a folder."
        # max_length=255, default="", verbose_name="Sort order key"
    )
    # feedback = models.BooleanField(default=True, verbose_name="Feedback to student")
    feedback = models.BooleanField(
        default=True,
        verbose_name="Feedback to student",
        help_text='Unselect to choose "Exam mode" i.e.  students will not find out if the answer is right or wrong',
    )

    def clean(self):
        if self.required and self.bonus:
            raise ValidationError("BONUS AND REQUIRED CANNOT BOTH BE TRUE")
        try :
            res = ( self.validate_exercise_meta() )
        except Exception as e :
            msg = html.unescape( str(e) );
            if self.published  :
                raise ValidationError( msg  + ": Fix before publishing!")
        #if not 'success' in res :
        #    msg = html.unescape( res.get('error','Unknown error') )
        #    raise ValidationError( msg  + ": Fix before saving!")
    
    def __str__(self):
        return self.exercise.name

    def validate_exercise_meta( self ):
        exercise = self.exercise
        res = exercise.validate()
        if not settings.USE_CHATGPT and self.allow_ai :
            raise ValidationError("you cannot allow openai if USE_CHATGPT is false")
        #db = exercise.course.opentasite
        #questions = Question.objects.using(db).filter(exercise=exercise)
        #res = []
        #for question in questions :
        #    print(f"VALIDATE_QUESTION {question}")
        #    res.append(  question.validate_xml() )
        #res = dict( res )
        return res



    def post_save(self, *args, **kwargs):
        instance = kwargs["instance"]
        exercise = instance.exercise
        course = exercise.course
        subdomain = course.opentasite
        touchfile = "last_admin_activity"
        fname = os.path.join(settings.VOLUME, subdomain, touchfile)
        if not settings.RUNTESTS :
            os.utime( os.path.join(settings.VOLUME, subdomain) )
        if os.path.exists(fname):
            os.utime(fname, None)
        # from exercises.serializers import ExerciseMetaSerializer as exerciseMetaSerializer
        # serializer = exerciseMetaSerializer(exercise.meta)
        # data = JSON.dumps( serializer.data )
        # print(f"META SERIALIZER IN META SAVE = {data}")
        # p = os.path.join( exercise.get_full_path() , "meta.json")
        # if os.path.exists(p) :
        #    f = open(p,'w')
        #    f.write(data)
        #    f.close()
        db = course.opentasite
        cache = caches["aggregation"]
        cachekey = f"{db}:{exercise.exercise_key}:cat"
        # print(f"IN POST SAVE DELETE {cachekey}")
        cache.delete(cachekey)

        exercise_options_saved.send(
            sender=self.__class__,
            user=None,
            exercise=exercise,
            course=course,
            date=None,
        )

    #def get_languages(self):
    #    return "ABCDEFG"


class AuditManager(models.Manager):
    def get_force_passed_exercises_pk(self, user):
        exercises = self.filter(student=user, force_passed=True).values_list("exercise__pk", flat=True)
        return exercises


def audit_fileresponse_filename(instance, filename):
    return "/".join(
        [
            "audit_fileresponses",
            instance.student.username,
            instance.exercise.exercise_key,
            str(uuid.uuid4()) + os.path.splitext(filename)[1],
        ]
    )


class AuditExercise(models.Model):
    student = models.ForeignKey(User, related_name="audits", on_delete=models.CASCADE)
    auditor = models.ForeignKey(User, related_name="studentaudits", on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.SET_NULL, null=True, related_name="audits")
    subject = models.CharField(max_length=255, default="", blank=True)
    message = models.TextField(default="", blank=True)
    published = models.BooleanField(default=False)  # Audit shown to student
    force_passed = models.BooleanField(default=False)
    date = models.DateTimeField(default=now)
    sent = models.BooleanField(default=False)
    revision_needed = models.BooleanField(null=True)
    updated = models.BooleanField(default=False)
    updated_date = models.DateTimeField(null=True, blank=True, default=None)
    modified = models.DateTimeField(auto_now=True)
    points = models.TextField(default="", blank=True)

    tracker = FieldTracker()

    objects = AuditManager()

    class Meta:
        unique_together = (("student", "exercise"),)  # Only one audit per student and exercise

    def save(self, *args, **kwargs):
        logger.info(f"SAVE AUDIT {self} args={args} kwargs={kwargs} POINTS={self.points}")
        if self.points == '' :
            #print(f"POINTS WAS blank")
            if self.revision_needed :
                self.points =  '0'
            elif self.force_passed :
                self.points = '1'
            else :
                self.points = '1'
            super().save(*args, **kwargs)

        if self.tracker.changed():
            return super().save(*args, **kwargs)
        else:
            pass

    def answer_date(self):
        ags = aggregation.models.Aggregation.objects.filter(user=self.student, exercise=self.exercise)
        if len(ags) > 0:
            ag = ags[0]
            if ag.all_complete:
                return ag.date_complete
            elif ag.image_date:
                return ag.image_date
            elif ag.answer_date:
                return ag.answer_date
        return None

    def post_save(self, *args, **kwargs):
        t = datetime.datetime.now().strftime("%F %T.%f")[:-3]
        instance = kwargs["instance"]
        logger.error(f"POST-SAVE-AUDIT {t} {instance} {args} {kwargs}")
        user = instance.student
        username = user.username
        date = instance.date
        points = instance.points
        exercise = instance.exercise
        course = instance.exercise.course
        subdomain = kwargs.get('using', instance.exercise.course.opentasite )
        db = subdomain

        archive = os.path.join(
            settings.VOLUME,
            subdomain,
            "json-answer-backups",
            str(course.course_key),
            str(user.username),
            str(exercise.exercise_key),
        )
        filename = os.path.join(archive, "audit.json")
        os.makedirs(archive, exist_ok=True)
        if not settings.RUNTESTS :
            os.utime( os.path.join(settings.VOLUME, subdomain) )
        save_json = json.dumps(
            {
                "student": str(user.username),
                "date": str(instance.date),
                "points": str(points),
                "message": str(instance.message),
                "published": str(instance.published),
                "sent": str(instance.sent),
                "revision_needed": str(instance.revision_needed),
                "updated_date": str(instance.updated_date),
                "modified": str(instance.modified),
                "auditor": str(instance.auditor),
                "force_passed": str(instance.force_passed),
            }
        )
        try :
            open(filename, "w+").write(save_json)
        except Exception as err :
            print(f"CANNOT SAVE JSON FILE {filename}")

        try :
            logger.info(f"USE ATOMIC TRANSACTION USER={user} pk={user.pk}   exercise={exercise} key={exercise.exercise_key}  course={course} subdomain={subdomain} db={db} username={username} src=models_Audit_post_save")
            with transaction.atomic(using=db) :
                answer_received.send(
                    sender=self.__class__,
                    user=user,
                    exercise=exercise,
                    course=course,
                    date=date,
                    subdomain=subdomain,
                    db=subdomain,
                    username=username,
                    src="models_Audit_post_save",
                )
    
        except Exception as e :
            logger.error(f"{str(e)} ATOMIC SIGNAL ERROR models_Audit_post_save")


def audit_response_filename(instance, filename):
    return "/".join(
        [
            "auditresponses",
            instance.audit.student.username,
            instance.audit.exercise.exercise_key,
            str(uuid.uuid4()) + os.path.splitext(filename)[1],
        ]
    )


# https://stackoverflow.com/questions/57301789/how-can-i-select-and-update-text-nodes-in-mixed-content-using-lxml


def fix_xml(xml, filename=""):
    taglist = ["question", "exercise", "choice"]
    nowrap = ["var"]
    try:
        root = etree.fromstring(xml)
    except etree.XMLSyntaxError as e:
        logger.debug("ERROR IN XML")
        htmlfilename = html.escape(filename)
        xml = (
            '<exercise><exercisename> BROKEN XML  </exercisename><global/><text>  \
                <h3> Broken xml </h3> The xml file <a href=".%s"> %s </a>  had broken xml. <p/> \
                <p/> The error message was <p/> <em> %s </em> </p> \
                <p/> <em> Click the link above,  copy the contents into live edit and try editing and fix the xml . </em> \
                <p/> Backup copies of the damaged files with hash version numbers are in assets.  \
                <p/> Delete them after you are done recovering your file. </text> </exercise>'
            % (htmlfilename, htmlfilename, html.escape(str(e)))
        )
        return (xml, True)
    globaldefs = root.xpath("./global")
    changed = False
    if len(globaldefs) == 0:
        g = etree.Element("global")
        root.insert(1, g)
        changed = True

    # https://stackoverflow.com/questions/15304229/convert-python-elementtree-to-string
    for text in root.xpath("//text()"):
        parent = text.getparent()
        if text.strip() != "":
            if text.is_tail:
                if parent.tag == "text":
                    changed = True
                    parent.tail = "LeFt" + text.strip() + "RiGhT"
                elif parent.tag in nowrap:
                    parent.tail = text
                else:
                    changed = True
                    parent.tail = "LeFt" + text.strip() + "RiGhT\n"
            elif parent.tag in taglist:
                if text.is_text:
                    changed = True
                    parent.text = "LeFt" + text.strip() + "RiGhT"
                else:
                    parent.text = text
    xml = (etree.tostring(root, encoding="UTF-8")).decode("UTF-8").replace("LeFt", "<text>").replace("RiGhT", "</text>")
    return (xml, changed)


class AuditResponseFile(models.Model):
    IMAGE = "IMG"
    PDF = "PDF"
    FILETYPE_CHOICES = ((IMAGE, "Image"), (PDF, "Pdf"))
    audit = models.ForeignKey(AuditExercise, related_name="responsefiles", on_delete=models.CASCADE)
    auditor = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(default=now)
    filetype = models.CharField(max_length=3, choices=FILETYPE_CHOICES, default=IMAGE)
    image = models.ImageField(default=None, blank=True, null=True, upload_to=audit_response_filename)
    pdf = models.FileField(
        default=None,
        blank=True,
        null=True,
        upload_to=audit_response_filename,
        max_length=512,
        storage=upload_storage,
    )
    image_thumb = ImageSpecField(
        source="image",
        processors=[ResizeToFill(100, 50)],
        format="JPEG",
        options={"quality": 60},
    )
