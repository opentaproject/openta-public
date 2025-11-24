# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import copy
from django.views.decorators.http import condition, etag
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError
from django.core.cache import caches
import html
import io
import json
import logging
import os
import os.path
import pickle
import re
import traceback
from xml.dom import minidom

from django.conf import settings
import exercises.paths as paths
 

# from exercises.parsing import xml_to_translationdict, update_translationdict_keys
from course.models import Course, patch_credential_string
from django.conf import settings
from utils import get_subdomain_and_db
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now
from exercises import parsing
from exercises.models import Exercise
from exercises.parsing import exercise_save, exercise_xml
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from lxml import etree
from rest_framework.decorators import api_view
from rest_framework.response import Response
from utils import response_from_messages

from translations.models import Translation

logger = logging.getLogger(__name__)

translatable_tags = ["./exercisename", ".//text", ".//comment"]


# def #print(*args, **kwargs):
#    pass
#    # #print(*args, **kwargs)

CACHE = "translations"


@permission_required("exercises.edit_exercise")
@api_view(["POST"])
def exercise_translate(request, exercise, language):
    # print("EXERCISE_TRANSLATE exercise=%s " % exercise )
    subdomain, db = get_subdomain_and_db(request)
    messages = []
    dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
    course_pk = dbexercise.course.pk
    dbcourse = Course.objects.get(pk=course_pk)
    usetranslations = dbcourse.use_auto_translation and not caches["default"].get("temporarily_block_translations")
    # print("API: course_pk = ", course_pk,' usetranslations = ',usetranslations)
    if usetranslations:
        backup_name = "{:%Y%m%d_%H:%M:%S_%f_}".format(now()) + request.user.username + ".xml"
        path = dbexercise.get_full_path()
        xml = exercise_xml(path)
        exercise_save(path, xml, backup_name)
        action = request.path.split("/")[-2]
        try:
            # print("API: TRANSLATE",action, language)
            messages += exercise_translate_language(dbexercise, request.data["xml"], language, action, course_pk)
        except IOError as e:
            messages.append(("error", str(e)))
        try:
            messages += Exercise.objects.add_exercise(dbexercise.path, dbexercise.course, db=db)
        except parsing.ExerciseParseError as e:
            messages.append(("warning", str(e)))
    else:
        messages.append(("warning", "auto-translation has been disabled"))
    result = response_from_messages(messages)
    return Response(result)


@api_view(["GET", "POST"])
def notifymissingstring(request, course_pk, language=None):  # LEAVE THIS UNUSED ARG FOR LEGACY  FRONTEND
    # logger.error(f"NOTIFY MISSING cache={ caches['default'].get('temporarily_block_translations')} setting={settings.ENABLE_AUTO_TRANSLATE }")
    if caches["default"].get("temporarily_block_translations"):
        return Response([])
    if not settings.ENABLE_AUTO_TRANSLATE:
        return Response([])
    subdomain, db = get_subdomain_and_db(request)
    if not request.user.is_staff:
        return Response([])
    data = request.data
    # print(f"DATA = {data}")
    missingstring = data["string_"]
    if isinstance(missingstring, (bytes, bytearray)):
        missingstring = data["string_"].decode("utf-8")
    # print(f"MISSING = {missingstring}")
    try:
        altkey = data["altkey"]
        dbcourse = Course.objects.filter(pk=course_pk)
        if len(dbcourse) > 1:
            logger.debug(f"COURSE PK {course_pk}  occurs several times")
            for course in dbcourse:
                logger.debug(f" COURSE IS {course}")
        dbcourse = dbcourse[0]
        languages = dbcourse.get_languages()
        # print("MISSING_STRING = {missingstring} languages = {languages}")
        if dbcourse.use_auto_translation and not caches["default"].get("temporarily_block_translations"):
            # print(f"DO A TRANSLATION of {missingstring} ")
            for lang in languages:
                if google_translate_strings([missingstring], lang, course_pk, altkey):
                    # print("MISSINGSTRING = ", missingstring)
                    cache = caches[CACHE]
                    cachekey = f"{settings.SUBDOMAIN}{course_pk}{lang}"
                    cache.delete(cachekey)
        else:
            print(
                f" SKIP TRANSLATION {missingstring} since  use={dbcourse.use_auto_translation}  and  cache={ caches['default'].get('temporarily_block_translations')} "
            )
    except Exception as e:
        logger.error(
            f"Unknown Exception in NOTIFYMISSINGSTRING {type(e).__name__} subdomain={subdomain} user={request.user} data={data} "
        )
        settings.ENABLE_AUTO_TRANSLATE = False
    return Response([])


def get_translation_etag(request, course_pk, language=None):
    cachekey = f"{settings.SUBDOMAIN}{course_pk}{language}"
    etag = cachekey
    cache = caches[CACHE]
    if cache.get(cachekey):
        return etag
    else:
        return None


@api_view(["GET"])
@etag(get_translation_etag)
def translationdict(request, course_pk, language=None):
    subdomain, db = get_subdomain_and_db(request)
    request.session["lang"] = language
    dbcourse = Course.objects.get(pk=course_pk)
    if not language:
        if dbcourse.languages:
            language = (dbcourse.languages).split(",")[0]
        else:
            language = "en"
    request.session["lang"] = language
    cachekey = f"{settings.SUBDOMAIN}{course_pk}{language}"
    cache = caches[CACHE]
    ret = cache.get(cachekey)
    if not ret == None:
        return Response(ret)
    trans = list(
        Translation.objects.filter(exercise__isnull=True, language=language).values_list("altkey", "translated_text")
    )
    ret = {"lang": language, "translations": {item[0]: {language: item[1]} for item in trans}}
    response = Response(ret)
    cache.set(cachekey, ret)
    return response


def exercise_translate_language(dbexercise, xml, language, action, course_pk):
    path = dbexercise.get_full_path()
    dbcourse = Course.objects.get(pk=course_pk)

    if not dbcourse.use_auto_translation and not caches["default"].get("temporarily_block_translations"):
        return []
    messages = []
    if True:
        xml = translate_xml(xml, language, action, course_pk, dbexercise, False)
        xml_path = os.path.join(path, paths.EXERCISE_XML)
        with open(xml_path, "w") as file:
            file.write(xml)
        messages.append(("success", "Saved translated exercise"))
    else:
        messages.append(("warning", "translate_xml failed"))
    return messages


def elem_to_ascii(elem):
    return html_content(xml_stripped_of_tags(elem, "alt"))


 # hashkey removed


def google_translate_strings(txts, lang, course_pk=None, altkey=None, exercise=None):
    # print(f"STRINGS {settings.ENABLE_AUTO_TRANSLATE}")
    ca = caches["default"].get("temporarily_block_translations")
    # print(f" CA IN GOOGLE {ca}")
    if caches["default"].get("temporarily_block_translations"):
        # print("blocked")
        return None
    # else :
    #    print("not blocked")
    if not settings.ENABLE_AUTO_TRANSLATE:
        return None
    use_auto_translation = Course.objects.get(pk=course_pk).use_auto_translation
    if not use_auto_translation:
        return None
    # print(f"USE_AUTO_TRANSLATION={use_auto_translation}")
    donttranslatetags = ["qmath", "asciimath", "right", "figure", "code"]
    translate_client = None
    print(f"TXTS = {txts}")
    try:
        lhtag = "<span class='notranslate'>"
        rhtag = "</span>"
        txtsin = []
        origtxts = []
        for txt in txts:
            txt = txt.strip()
            if not Translation.objects.filter(original_text=txt, language=lang, exercise=exercise).exists():
                # logger.error(f"FRESH TRANSLATION OF {txt}")
                # logger.info("RETRANSLATE hsh = %s lang=%s ", hsh, lang)
                if translate_client is None:
                    pklfile = os.path.join(settings.BASE_DIR, "backend", "service_account.pkl")
                    course = Course.objects.get(pk=course_pk)
                    cfile = f"{settings.VOLUME}/auth/google_auth_string.txt"
                    if os.path.exists(cfile):
                        f = open(f"{settings.VOLUME}/auth/google_auth_string.txt", "r+")
                        credential_string = f.read()
                        credentialstring = patch_credential_string(credential_string)
                        f.close()
                    else:
                        credential_string = course.google_auth_string
                        credentialstring = patch_credential_string(course.google_auth_string)
                    if settings.VALIDATE_GOOGLE_AUTH_STRING:
                        service_account_info = json.load(io.StringIO(credentialstring))
                    elif os.path.isfile(pklfile):
                        service_account_info = pickle.load(open(pklfile, "rb"))
                    else:
                        service_account_info = json.load(io.StringIO(credentialstring))
                    credentials = service_account.Credentials.from_service_account_info(service_account_info)
                    translate_client = translate.Client(credentials=credentials)
                origtxt = txt
                for tag in donttranslatetags:
                    ltag = "<" + tag + ">"
                    rtag = "</" + tag + ">"
                    txt = re.sub(ltag, lhtag + ltag, txt)
                    txt = re.sub(rtag, rtag + rhtag, txt)
                txt = re.sub(r"(\$[^\$]*\$)", lhtag + "\\1" + rhtag, txt, flags=re.MULTILINE)  # DONT TRANSLATE MATH
                # txt = re.sub(r"(\\\[.*\\\])", lhtag + "\\1" + rhtag, txt,  flags=re.MULTILINE )  # DONT TRANSLATE MATH
                txt = re.sub(r"(\\\[)", lhtag + "\\1", txt, flags=re.MULTILINE)  # DONT TRANSLATE MATH
                txt = re.sub(r"(\\\])", "\\1" + rhtag, txt, flags=re.MULTILINE)  # DONT TRANSLATE MATH
                txt = re.sub(r"(@\w+)", lhtag + "\\1" + rhtag, txt)  # DONT TRANSLATE MACRO VARIABLES
                txt = re.sub(r"&amp;", "AmPeRsAnD", txt)
                txt = re.sub(r"&", "AmPeRsAnD", txt)
                txt = re.sub("<p/>", "##", txt)
                txt = re.sub("<table>", "BeGiNTaBlE", txt)
                txt = re.sub("</table>", "EnDTaBlE", txt)
                txt = "{}".format(txt)
                txtsin = txtsin + [txt]
                origtxts.append(origtxt)
            else:
                pass
                # tr = Translation.objects.get(hashkey=hsh,language=lang,exercise=exercise)
                # #logger.info("SKIP hsh =  %s lang=%s %s %s ",(hsh, lang, txt, tr.translated_text) )
        if len(txtsin) > 0:
            logger.error(f"RETRANSLATE : subdomain={settings.SUBDOMAIN}  to {lang} txt={txtsin}")
            translations = translate_client.translate(txtsin, target_language=lang, format_="html")
        else:
            translations = []
        txtsout = []
        # #print("translations = ", translations)
        for translation in translations:
            translated_text = "{}".format(translation["translatedText"])
            # #print("TRANSLATIONS translated_text = ", translated_text)
            translated_text = html.unescape(translated_text)
            # #print("TRANSLATIONS unescaped translated_text = ", translated_text)
            translated_text = re.sub(lhtag, "", translated_text)
            translated_text = re.sub(rhtag, "", translated_text)
            translated_text = re.sub("##", "<p/>", translated_text)
            translated_text = re.sub("@ ", "@", translated_text)
            translated_text = re.sub(r"(<[^\/])", "\n\\1", translated_text)
            translated_text = re.sub(r"AmPeRsAnD", "&", translated_text)
            translated_text = re.sub(r"BeGiNTaBlE", "<table/>", translated_text)
            translated_text = re.sub(r"EnDTaBlE", "</table>", translated_text)
            # translated_text = re.sub(r"\\ ", r'\\', translated_text)
            # translated_text = re.sub(r"begin {", r'begin{', translated_text)
            # translated_text = re.sub(r"end {", r'end{', translated_text)
            txtsout = txtsout + [translated_text]
        # #print("txtsout = ", txtsout )
        zipped = zip(origtxts, txtsout)
        for (txtin, txtout) in zipped:
            trs = Translation.objects.filter(original_text=txtin, language=lang, exercise=exercise)
            while trs.count() > 1:
                trs[0].delete()
                trs = Translation.objects.filter(original_text=txtin, language=lang, exercise=exercise)
            tr, _ = Translation.objects.get_or_create(original_text=txtin, language=lang, exercise=exercise)
            tr.original_text = txtin
            tr.translated_text = txtout
            tr.exercise = exercise
            if not altkey is None:
                tr.altkey = altkey
            tr.save()
        txtsout = []
        for orig in origtxts:
            if altkey is None:
                tr = Translation.objects.filter(original_text=orig, language=lang, exercise=exercise)
                # logger.info("TR STRINGS  = %s ", tr)
            else:
                tr = Translation.objects.filter(original_text=orig, language=lang, altkey=altkey, exercise=None)
            try:
                tr = tr[0]
                txtsout.append(tr.translated_text)
            except Exception as e:
                logger.error(
                    "UNTRANSLATED %s FOR UNKNOWN REASON  %s %s " % (tr.original_text, type(e).__name__, str(e))
                )
                txtsout.append("UNTRANSLATED")

        # logger.info("RETURN txtout = %s ", txtsout)
        return txtsout

    except FileNotFoundError as e:
        pass
    # except ValueError as e :
    #    return None
    # except IntegrityError as e :
    #    return None
    # except AttributeError as e :
    #    return None
    except MultipleObjectsReturned as e:
        logger.error(f"MULT OBJECTS: ERROR in  google_translate_strings { type(e).__name__} {str(e)  }")
    except Exception as e:
        logger.error(f"TRANSLATIONS: ERROR in  google_translate_strings { type(e).__name__} {str(e)  }")
        return None
    if translate_client == None:
        raise FileNotFoundError("No valid translation credentials found")
    else:
        raise RuntimeError("Unknown error in google translate; check credentials")


# def translate_string(txt, lang):
#    return google_translate_strings([txt], lang)[0]


def makepretty(xml):
    xmlout = xml
    xmlout = re.sub(r"\s+", " ", xmlout)
    xmlout = minidom.parseString(xmlout).toprettyxml()
    xmlout = re.sub(r"\s*\n\s*\n", "\n", xmlout)
    xmlout = re.sub(r"&quot;", '"', xmlout)
    return xmlout


def translate_xml(xml, lang, action, course_pk, dbexercise, domakepretty):
    logger.info("TRANSLATE XML action %s , lang= %s ", action, lang)
    course = Course.objects.get(pk=course_pk)
    if not course.use_auto_translation and not caches["default"].get("temporarily_block_translations"):
        return xml
    if "translate" in action:
        # logger.info("TRANSLATION translate_xml to %s ", lang)
        newxml = translate_xml_language(xml, [lang], course_pk, dbexercise, domakepretty)
    elif "remove" in action:
        try:
            newxml = remove_language(xml, lang, course_pk)
        except Exception as e:
            formatted_lines = traceback.format_exc()
            logger.error("TRANSLATIONS ERROR IN remove %s , %s ", (str(e), formatted_lines))
            raise ValueError("Removal of language " + lang + " failed")
    elif "changedefaultlanguage" in action:
        try:
            newxml = change_default_language(xml, lang, course_pk)
        except Exception as e:
            formatted_lines = traceback.format_exc()
            logger.error(
                "TRANSLATIONS ERROR IN change_default_language %s , %s ",
                (str(e), formatted_lines),
            )
            raise ValueError("Change default of language " + lang + " failed")
    else:
        logger.error("Action " + action + " and lang = " + lang + " failed")
        raise ValueError("Action " + action + " and lang = " + lang + " failed")
    return newxml


def xml_stripped_of_tags(elem, tag):
    # #print("STRIP TAG ", tag )
    elemstripped = copy.deepcopy(elem)
    etree.strip_attributes(elemstripped)
    otheralts = elemstripped.findall(tag)
    for otheralt in otheralts:
        elemstripped.remove(otheralt)
    xml = etree.tostring(elemstripped, encoding=str)
    # #print("STRIPPED= ", xml )
    return xml


def html_content(txt):
    # #print("COMPARISON2 = ",  lxml.html.tostring( etree.fromstring(txt) ,encoding=str) )
    txt = re.sub(r"^\s*<[^>]+>", "", txt)
    txt = re.sub(r"</[^>]+>\s*$", "", txt)
    txt = txt.strip()
    # #print("HTML CONTENT = ",txt)
    return txt


def fromString(xml):
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml, parser=parser)
    return root


# def patch_credential_string(value):
#    return value.strip().lstrip('r').strip("'")


def translatable_texts(root):
    elems_to_be_translated = []
    for tag in translatable_tags:
        elems_to_be_translated = elems_to_be_translated + root.findall(tag)
    return elems_to_be_translated


def translate_xml_language(xml, langs, course_pk, dbexercise, domakepretty):
    # print("TRANSLATE_XML_LANGUAGE LANGS = %s " % langs )
    if caches["default"].get("temporarily_block_translations"):
        return xml
    xmlin = xml
    if langs[0] == "none":
        xml = makepretty(xml)
        return xml
    root = fromString(xml)
    elems_already_translated = root.findall(".//alt")
    for elem in elems_already_translated:
        lang = elem.attrib.get("lang")
        if not lang:
            continue
        parent = elem.getparent()
        if parent is None:
            continue
        original_txt = elem_to_ascii(parent)
        objs = Translation.objects.filter(language=lang, original_text=original_txt, exercise=dbexercise).union(
            Translation.objects.filter(language=lang, original_text=original_txt, exercise__isnull=True)
        )

        if objs.exists():
            for obj in objs:
                obj.translated_text = elem.text or ""
                obj.save()
        else:
            obj, _ = Translation.objects.get_or_create(
                language=lang,
                original_text=original_txt,
                exercise=dbexercise,
                defaults={"translated_text": elem.text or ""},
            )

    for lang in langs:
        if xml == "":
            return ""
        txtsin = []
        root = fromString(xml)
        elems = []
        elems_to_be_translated = translatable_texts(root)
        # print("ELEMS = %s " % elems_to_be_translated)
        originals_in_xml = set([elem_to_ascii(elem) for elem in elems_to_be_translated])
        originals_in_database = set(
            Translation.objects.filter(language=lang, exercise=dbexercise).values_list("original_text", flat=True)
        )
        deleted_originals = list(originals_in_database.difference(originals_in_xml))
        for orig in deleted_originals:
            trs = Translation.objects.filter(original_text=orig, exercise=dbexercise)
            for tr in trs:
                tr.delete()

        # texts = root.findall('.//text') + root.findall('.//exercisename') + root.findall('.//choice')
        for elem in elems_to_be_translated:
            if not "notranslate" in elem.attrib:
                elem.findall("alt")
                if len(elem.findall("alt[@lang='" + lang + "']")) == 0:
                    txt = elem_to_ascii(elem)
                    txtsin = txtsin + [txt]
                    elems = elems + [elem]
        if len(txtsin) == 0:
            return xmlin
        txtsout = google_translate_strings(txtsin, lang, course_pk, None, dbexercise)
        if txtsout:
            zipped = zip(elems, txtsout)
            for (elem, txtout) in zipped:
                xmlout = "<alt>" + txtout + "</alt>"
                original_txt = elem_to_ascii(elem)
                tr, _ = Translation.objects.get_or_create(original_text=original_txt, language=lang, exercise=dbexercise)
                tr.original_text = original_txt
                tr.translated_text = txtout
                tr.save()
                newelem = fromString(xmlout)
                newelem.set("lang", lang)
                elem.append(newelem)
            xml = etree.tostring(root, encoding=str)
            if domakepretty:
                xml = makepretty(xml)
        else:
            xml = xmlin
    return xml


def change_default_language(xml, lang, course_pk):
    # #print("MAKE DEFAULT lang = ", lang )
    if lang == "none":
        return xml
    try:
        xmlorig = xml
        root = fromString(xml)
        # texts = root.findall('.//text')  + root.findall('.//exercisename') +  root.findall('.//choice')
        elems_to_be_translated = translatable_texts(root)
        # texts = root.findall('.//text')  + root.findall('.//exercisename') +  root.findall('.//choice')
        xml_altered = False
        for elem in elems_to_be_translated:
            # #print("T1")
            parent = elem.getparent()
            alts = elem.findall("alt")
            newalt = copy.deepcopy(elem.find("alt[@lang='" + lang + "']"))
            if elem is not None and newalt is not None:
                newalt.tag = elem.tag
                newalt.attrib.pop("lang", None)
                attribs = elem.attrib
                etree.strip_attributes(newalt)
                for key, val in attribs.items():
                    newalt.set(key, val)
                for alt_ in alts:
                    newalt.append(alt_)
                # elem = copy.deepcopy(newalt)
                parent.replace(elem, newalt)
                xml_altered = True
        if xml_altered is not None:
            xml = etree.tostring(root, encoding=str)
        return xml
    except Exception as e:
        formatted_lines = traceback.format_exc()
        logger.error(
            "TRANSLATIONS ERROR IN change_default_language %s , %s ",
            (str(e), formatted_lines),
        )

        # #print("TRANSLATIONS: ERROR in change_default_language", str(e))
        return xmlorig


def remove_language(xml, lang, course_pk):
    # #print("REMOVE lang = ", lang)
    if lang == "none":
        return xml
    try:
        xmlorig = xml
        root = fromString(xml)
        # texts = root.findall('.//text') + root.findall('exercisename') + root.findall('choice')
        elems_to_be_translated = translatable_texts(root)
        # texts = root.findall('.//text') + root.findall('exercisename') + root.findall('.//choice')
        for elem in elems_to_be_translated:
            # #print("REMOVE FOUND text ")
            elem.findall("alt")
            for alt_ in elem.findall("alt[@lang='" + lang + "']"):
                # #print("FOUND")
                elem.remove(alt_)
        xml = etree.tostring(root, encoding=str)
        return xml
    except Exception as e:
        # #print("TRANSLATIONS: ERROR in remove_language", str(e))
        formatted_lines = traceback.format_exc()
        logger.error("TRANSLATIONS ERROR IN remove_language %s , %s ", (str(e), formatted_lines))
        return xmlorig
