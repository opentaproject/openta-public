from django.shortcuts import render
import json
import io
import fcntl
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import PermissionDenied
from exercises.models import Exercise, Question, Answer, ImageAnswer, AuditExercise
from exercises.serializers import ExerciseSerializer, AnswerSerializer, ImageAnswerSerializer
from exercises.serializers import AuditExerciseSerializer
from exercises import parsing
#from exercises.parsing import xml_to_translationdict, update_translationdict_keys
import exercises.question as question_module
from exercises.modelhelpers import serialize_exercise_with_question_data
from exercises.folder_structure.modelhelpers import exercise_folder_structure
from exercises.modelhelpers import  exercise_test
from exercises.views.file_handling import serve_file
from exercises.time import before_deadline
from course.models import patch_credential_string
from exercises.util import deep_get
from utils import response_from_messages
from django.utils.translation import ugettext as _
from django.http import StreamingHttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import permission_required
from django.template.response import TemplateResponse
from django.template import loader
from django.utils.timezone import now
from django.db import transaction
from django.db.models import Prefetch
from ratelimit.decorators import ratelimit
from django.views.decorators.cache import never_cache
from PIL import Image
import datetime
import PyPDF2
import logging
import backend.settings as settings
import json
import exercises.paths as paths

from lxml import etree
from course.models import Course
import lxml.html
from xml.etree.ElementTree import fromstring, ParseError, tostring
from io import StringIO, BytesIO
import html
from django.conf import settings
import re
from xml.dom import minidom
from xml.dom.minidom import parseString
import os.path
from django.conf import settings
from xmljson import badgerfish as bf
from json import dumps
import copy


from google.cloud import translate_v2 as translate
from google.oauth2 import service_account


import os
import os.path

logger = logging.getLogger(__name__)

translatable_tags = ['exercisename', './/text', './/choice', './/comment']


def dprint(*args, **kwargs):
    print(*args, **kwargs)


@permission_required('exercises.edit_exercise')
@api_view(['POST'])
def exercise_translate(request, exercise, language):
    dprint("EXERCISE_TRANSLATE")
    messages = []
    dbexercise = Exercise.objects.get(exercise_key=exercise)
    course_pk = dbexercise.course.pk
    dbcourse = Course.objects.get(pk=course_pk)
    usetranslations = dbcourse.use_auto_translation
    print("API: course_pk = ", course_pk,' usetranslations = ',usetranslations)
    if usetranslations:
        backup_name = "{:%Y%m%d_%H:%M:%S_%f_}".format(now()) + request.user.username + ".xml"
        action = request.path.split('/')[-2]
        try:
            # print("API: TRANSLATE",action, language)
            messages += exercise_translate_language(
                dbexercise.get_full_path(), request.data['xml'], language, action, course_pk
            )
        except IOError as e:
            messages.append(('error', str(e)))
        try:
            messages += Exercise.objects.add_exercise(dbexercise.path, dbexercise.course)
        except parsing.ExerciseParseError as e:
            messages.append(('warning', str(e)))
    else:
        messages.append(('warning', 'auto-translation has been disabled'))
    result = response_from_messages(messages)
    return Response(result)

def xml_to_translationdict(xml):
    try:
        # print("TRANSLATIONS xml = ", xml )
        root = fromString(xml)
        # print("ROOT = ", etree.tostring(root, encoding=str) )
        texts = root.findall('.//text')
        newdict = {}
        for elem in texts:
            alts = elem.findall('alt')
            newt = {}
            for alt in alts:
                lang = alt.attrib['lang']
                newtxt = etree.tostring(alt, encoding=str)
                newtxt = re.sub(r'<alt lang="' + lang + '">', '', newtxt)
                newtxt = re.sub(r'</alt>', '', newtxt)
                newt[lang] = newtxt.strip()
            key = getkey(elem.text)
            newdict[key] = newt
        root = fromString(xml)
        return newdict
    except Exception as XMLSyntaxError:
        return {}
    #    print("ERROR IN xml_to_translations ", e.__class__.__name__,  str(e) )
    #    return {}
    # except Exception as e :
    #    print("ERROR IN xml_to_translations ", str(e) )
    #    return {}


def getkey(stringin):
    key = re.sub(r'\s+', '', stringin)
    return key


def update_translationdict_keys(xml, stringin, lang):
    # print("PARSING MISSING", stringin, lang )
    newxml = xml
    try:
        root = fromString(xml)
        texts = root.findall('.//text')
        key = getkey(stringin)
        # print("PARSING key = ", key )
        for elem in texts:
            if getkey(elem.text) == key:
                return xml
        newelem = etree.Element("text")
        newelem.text = stringin
        root.append(newelem)
        newxml = etree.tostring(root, encoding=str)
        # try:
        #    newxml = translate_xml_language( newxml, lang )
        # except:
        # print("PARSING NEWXML = ", newxml)
    except:
        pass
    return newxml



@api_view(['GET', 'POST'])
def notifymissingstring(request, course_pk, language):
    dprint("NOTIFY")
    messages = []
    data = request.data
    # print("API data for notifymissingstring= ", data )
    missingstring = data['string_']
    dprint("MISSING STRING", missingstring)
    language = data['language']
    xml_path = paths.LIVE_TRANSLATION_DICT_XML
    dbcourse = Course.objects.get(pk=course_pk)
    usetranslation = dbcourse.use_auto_translation
    # print("API: notify usetranslation  = ", usetranslation)
    # print("API: notify course_pk = ", course_pk )
    # print("API: notify language = ", language)
    try:
        xmlfile = open(xml_path)
        xml = xmlfile.read()
        xmlfile.close()
        newxml = update_translationdict_keys(xml, missingstring, language)
        safe_replace_translationdict(newxml)
        open(xml_path + ".notified", 'a').close()
        # with open(xml_path, 'w') as file:
        #     file.write(newxml)
    except FileNotFoundError as e:
        messages.append(('write error of ' + xml_path, str(e)))
    result = response_from_messages(messages)
    return Response(result)


def safe_replace_translationdict(newxml):
    # print("SAFE REPLACE")
    parser = etree.XMLParser(recover=True)
    try:
        if len(newxml) == 0:
            dprint("NEWXML is blank")
            return False
        newxml = makepretty(newxml)
        root = etree.fromstring(newxml, parser=parser)
    except Exception as e:
        return False
    # print("OK NEWXML IS  LOADED")
    try:
        live_xml_path = paths.LIVE_TRANSLATION_DICT_XML
        if not os.path.isfile(live_xml_path):
            directory = os.path.dirname(paths.LIVE_TRANSLATION_DICT_XML)
            if not os.path.exists(directory):
                os.makedirs(directory)
            # print("NO EXISTS SO WRITE", live_xml_path)
            file_ = open(live_xml_path, 'w+')
            fcntl.flock(file_, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with file_ as file:
                file.write(newxml)
            return True
        live_xmlfile = open(live_xml_path)
        oldxml = live_xmlfile.read()
        if len(re.sub(r'[\s\n\t\r]+', '', newxml)) < len(re.sub(r'[\s\n\t\r]+', '', oldxml)):
            return False
        with open(live_xml_path, 'w+') as file:
            # print("WRITE THE NEW XML")
            file.write(newxml)
    except etree.XMLSyntaxError as e:
        return False
    return True


@api_view(['GET', 'POST'])
def translationdict(request, course_pk):
    dprint("TRANSLATIONDICT")
    messages = []
    dbcourse = Course.objects.get(pk=course_pk)
    usetranslation = dbcourse.use_auto_translation
    xml_path = paths.LIVE_TRANSLATION_DICT_XML
    try:
        # print("TRY OPENING ", xml_path )
        xmlfile = open(xml_path)
        xml = xmlfile.read()
        xmlfile.close()
    except Exception as e:
        # print("ERROR = ", str(e) )
        default_xml_path = paths.DEFAULT_TRANSLATION_DICT_XML  #   "exercises/translationdict.xml"
        dprint("INSTEAD TRY OPENING ", default_xml_path)
        xmlfile = open(default_xml_path)
        dprint("OPENED THE FILE")
        xml = xmlfile.read()
        dprint("READ THE FILE")
        xmlfile.close()
        dprint("CLOSED THE FILE")
        safe_replace_translationdict(xml)
        # if not os.path.isfile( xml_path ):
        #    with open( xml_path,'w+')  as file :
        #        file.write( xml )

        # print("translationdict written ", xml_path )
        # print("API: request.path = ", request.path)
        # result = xml_to_translationdict(xml)
        # print("API: translationdict : " )
        # print("API: translationdict : course_pk =  ", course_pk )
        # print("API request.data = ", request.data )
    result = xml_to_translationdict(xml)
    return Response(result)


@api_view(['GET', 'POST'])
def updatetranslationdict(request, course_pk):
    dprint("UPDATE TRANSLATION_DICT")
    messages = []
    notifyfile = paths.LIVE_TRANSLATION_DICT_XML + ".notified"
    if not os.path.isfile(notifyfile):
        dprint("UPDATE NOT NECESSARY")
        result = response_from_messages(messages)
        return Response(result)
    else:
        dprint("UPDATE live file")
    # print("API updatetranslationdict")
    # print("API: updatetranslationdict : course_pk =  ", course_pk )
    # print("API request.data = ", request.data )
    dbcourse = Course.objects.get(pk=course_pk)
    languages = dbcourse.languages
    usetranslation = dbcourse.use_auto_translation
    # print("VIEWS: updatetranslationdict= ", usetranslation)
    # print("languages = ", languages )
    try:
        languages = (dbcourse.languages).split(',')
        xml_path = paths.LIVE_TRANSLATION_DICT_XML
        xmlfile = open(xml_path)
        newxml = xmlfile.read()
        for lang in languages:
            # print("API lang = ", lang.strip() )
            newxml = translate_xml_language(newxml, lang, course_pk, domakepretty=False)
        # print("API: newxml = ", newxml )
        safe_replace_translationdict(newxml)
        # with open(xml_path, 'w') as file:
        #     file.write(newxml)
    except:
        messages.append(('warning', 'no language specified'))
        pass
    result = response_from_messages(messages)
    os.remove(notifyfile)
    return Response(result)


def exercise_translate_language(path, xml, language, action, course_pk):
    dprint("EXERCISE TRANSLATE LANGUAGE")
    print("TRANSLATIONS: exercise_translate",path,language,action,course_pk)
    dbcourse = Course.objects.get(pk=course_pk)
    usetranslation = dbcourse.use_auto_translation
    print("TRANSLATIONS: exercise_translation_language usetranslation = ", usetranslation)
    messages = []
    # try:
    #    settings.GOOGLE_TRANSLATE_CLIENT
    # except:
    #    messages.append(
    #        (
    #            'warning',
    #            "use_auto_translation is set but GOOGLE_TRANSLATE_CLIENT not defined; Either turn off use_auto_translation in course options, or install GOOGLE_TRANSLATE_CLIENT and enable the INSTALLED_APP translations ",
    #        )
    #    )
    #    return messages
    try:
        print("OLD_XML", xml )
        xml = translate_xml(xml, language, action, course_pk)
        print("NEW XML", xml )
        xml_path = os.path.join(path, paths.EXERCISE_XML)
        with open(xml_path, 'w') as file:
            file.write(xml)
        messages.append(('success', 'Saved exercise'))
    except:
        messages.append(('warning', "translate_xml failed"))

    return messages


def translate_strings(txts, lang, translate_client):
    dprint("TRANSLATE STRINGS")
    dprint("TRANSLATIONS.py translate_strings, txts = ", txts)
    donttranslatetags = ['qmath', 'asciimath']
    try:
        lhtag = '<span class=\'notranslate\'>'
        rhtag = '</span>'
        txtsin = []
        # print("txts = ", txts)
        for txt in txts:
            for tag in donttranslatetags:
                ltag = '<' + tag + '>'
                rtag = '</' + tag + '>'
                txt = re.sub(ltag, lhtag + ltag, txt)
                txt = re.sub(rtag, rtag + rhtag, txt)
            txt = re.sub(r'(\$[^\$]*\$)', lhtag + '\\1' + rhtag, txt)  # DONT TRANSLATE MATH
            txt = re.sub(r'(\\\[.*\\\])', lhtag + '\\1' + rhtag, txt)  # DONT TRANSLATE MATH
            txt = re.sub(r'(@\w+)', lhtag + '\\1' + rhtag, txt)  # DONT TRANSLATE MACRO VARIABLES
            txt = re.sub(r'&amp;', 'AmPeRsAnD', txt)
            txt = re.sub(r'&', 'AmPeRsAnD', txt)
            txt = u'{}'.format(txt)
            txtsin = txtsin + [txt]
        translations = translate_client.translate(txtsin, target_language=lang, format_='html')
        txtsout = []
        # print("translations = ", translations)
        for translation in translations:
            translated_text = u'{}'.format(translation['translatedText'])
            # print("TRANSLATIONS translated_text = ", translated_text)
            translated_text = html.unescape(translated_text)
            # print("TRANSLATIONS unescaped translated_text = ", translated_text)
            translated_text = re.sub(lhtag, '', translated_text)
            translated_text = re.sub(rhtag, '', translated_text)
            translated_text = re.sub('##', '<p/>', translated_text)
            translated_text = re.sub('@ ', '@', translated_text)
            translated_text = re.sub(r'(<[^\/])', '\n\\1', translated_text)
            translated_text = re.sub(r'AmPeRsAnD', '&', translated_text)
            txtsout = txtsout + [translated_text]
        # print("txtsout = ", txtsout )
        return txtsout
    except Exception as e:
        # print("TRANSLATIONS: ERROR in  translate_strings", str(e) )
        return txts


def translate_string(txt, lang):
    return translate_strings([txt], lang)[0]


def makepretty(xml):
    xmlout = xml
    xmlout = re.sub(r'\s+', ' ', xmlout)
    xmlout = minidom.parseString(xmlout).toprettyxml()
    xmlout = re.sub(r'\s*\n\s*\n', '\n', xmlout)
    xmlout = re.sub(r'&quot;', '\"', xmlout)
    return xmlout


def translate_xml(xml, lang, action, course_pk, domakepretty=True):
    print("TRANSLATE XML action %s , lang= %s " % ( action, lang )  )
    if 'translate' in action:
        # print("TRANSLATION translate_xml to ", lang )
        try:
            newxml = translate_xml_language(xml, lang, course_pk, domakepretty)
        except:
            raise ValueError('Translation of xml into ' + lang + ' failed.')
    elif 'remove' in action:
        try:
            newxml = remove_language(xml, lang, course_pk)
        except:
            raise ValueError('Removal of language ' + lang + ' failed')
    elif 'changedefaultlanguage':
        try:
            newxml = change_default_language(xml, lang, course_pk)
        except:
            raise ValueError('Change default of language ' + lang + ' failed')
    else:
        raise ValueError('Action ' + action + " and lang = " + lang + ' failed')
    return newxml


def xml_stripped_of_tags(elem, tag):
    # print("STRIP TAG ", tag )
    elemstripped = copy.deepcopy(elem)
    etree.strip_attributes(elemstripped)
    otheralts = elemstripped.findall(tag)
    for otheralt in otheralts:
        elemstripped.remove(otheralt)
    xml = etree.tostring(elemstripped, encoding=str)
    # print("STRIPPED= ", xml )
    return xml


def html_content(txt):
    # print("COMPARISON2 = ",  lxml.html.tostring( etree.fromstring(txt) ,encoding=str) )
    txt = re.sub(r'^\s*<[^>]+>', '', txt)
    txt = re.sub(r'</[^>]+>\s*$', '', txt)
    txt = txt.strip()
    # print("HTML CONTENT = ",txt)
    return txt


def fromString(xml):
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml, parser=parser)
    return root


# def patch_credential_string(value):
#    return value.strip().lstrip('r').strip("'")


def translate_xml_language(xml, lang, course_pk, domakepretty=True):
    print("TRANSLATIONS translate_xml_language lang = ", lang)
    xmlin = xml
    if "none" == lang:
        xml = makepretty(xml)
        return xml
    try:
        txtsin = []
        elems = []
        xmlorig = xml
        root = fromString(xml)
        texts = []
        for tag in translatable_tags:
            texts = texts + root.findall(tag)
        # print("TEXTS  = ", texts)
        # texts = root.findall('.//text') + root.findall('.//exercisename') + root.findall('.//choice')
        for elem in texts:
            tag = elem.tag
            # print("HANDLE tag = ", tag )
            if not "notranslate" in elem.attrib:
                alts = elem.findall('alt')
                # elemstripped = elem
                if len(elem.findall("alt[@lang=\'" + lang + "\']")) == 0:
                    txt = html_content(xml_stripped_of_tags(elem, 'alt'))
                    # print("ALT STRIPPED TXT: TRANSLATION: txt = ", txt )
                    txtsin = txtsin + [txt]
                    elems = elems + [elem]
        if len(txtsin) == 0:
            return xmlin
        course = Course.objects.get(pk=course_pk)
        credentialstring = patch_credential_string(course.google_auth_string)
        service_account_info = json.load(io.StringIO(credentialstring))
        credentials = service_account.Credentials.from_service_account_info(service_account_info)
        translate_client = translate.Client(credentials=credentials)
        try:
            english = translate_client.detect_language('This is a statement in english')['language']
        except:
            english = "failed"
        txtsout = translate_strings(txtsin, lang, translate_client)
        zipped = zip(elems, txtsout)
        for (elem, txtout) in zipped:
            # print("TRANSLATION txtout = ", txtout )
            xmlout = "<alt>" + txtout + "</alt>"
            newelem = fromString(xmlout)
            newelem.set('lang', lang)
            elem.append(newelem)
        xml = etree.tostring(root, encoding=str)
        if domakepretty:
            xml = makepretty(xml)
        return xml
    except:
        return xmlin


def change_default_language(xml, lang, course_pk):
    # print("MAKE DEFAULT lang = ", lang )
    if "none" == lang:
        return xml
    try:
        xmlorig = xml
        root = fromString(xml)
        # texts = root.findall('.//text')  + root.findall('.//exercisename') +  root.findall('.//choice')
        texts = []
        for tag in translatable_tags:
            texts = texts + root.findall(tag)
        # texts = root.findall('.//text')  + root.findall('.//exercisename') +  root.findall('.//choice')
        for elem in texts:
            # print("T1")
            parent = elem.getparent()
            alts = elem.findall('alt')
            newalt = copy.deepcopy(elem.find("alt[@lang=\'" + lang + "\']"))
            newalt.tag = elem.tag
            newalt.attrib.pop('lang', None)
            attribs = elem.attrib
            etree.strip_attributes(newalt)
            for key, val in attribs.items():
                newalt.set(key, val)
            for alt_ in alts:
                newalt.append(alt_)
            # elem = copy.deepcopy(newalt)
            parent.replace(elem, newalt)
            # print("ELEM = ", etree.tostring( elem,encoding=str) )

        xml = etree.tostring(root, encoding=str)
        return xml
    except Exception as e:
        print("TRANSLATIONS: ERROR in change_default_language", str(e))
        return xmlorig


def remove_language(xml, lang, course_pk):
    dprint("REMOVE lang = ", lang)
    if "none" == lang:
        return xml
    try:
        xmlorig = xml
        root = fromString(xml)
        # texts = root.findall('.//text') + root.findall('exercisename') + root.findall('choice')
        texts = []
        for tag in translatable_tags:
            texts = texts + root.findall(tag)
        # texts = root.findall('.//text') + root.findall('exercisename') + root.findall('.//choice')
        for elem in texts:
            # print("REMOVE FOUND text ")
            alts = elem.findall('alt')
            for alt_ in elem.findall("alt[@lang=\'" + lang + "\']"):
                # print("FOUND")
                elem.remove(alt_)
        xml = etree.tostring(root, encoding=str)
        return xml
    except Exception as e:
        print("TRANSLATIONS: ERROR in remove_language", str(e))
        return xmlorig
