# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import copy
from django.db import transaction
from django.db.models import F, Func, Value
from django.db.models.functions import Lower, LTrim
from django.db.models import Case, When, Value, IntegerField
import hashlib
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
from utils import db_info_var

import deepl
import exercises.paths as paths

# from exercises.parsing import xml_to_translationdict, update_translationdict_keys
from course.models import Course, patch_credential_string
from exercises import parsing
from exercises.models import Exercise
from exercises.parsing import exercise_save, exercise_xml
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from lxml import etree
from rest_framework.decorators import api_view
from rest_framework.response import Response
from translations.models import Translation
from django.shortcuts import render, redirect
from django.forms import modelformset_factory, ModelForm, Textarea
from django.contrib.auth.decorators import permission_required
from utils import get_subdomain_and_db, response_from_messages

from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.utils.timezone import now
from django.views.decorators.http import etag
from contextvars import ContextVar
#db_info_var = ContextVar('db_info')
#user_info_var = ContextVar('user_info')


logger = logging.getLogger(__name__)

translatable_tags = ["./exercisename", ".//text", ".//comment"]


# def #print(*args, **kwargs):
#    pass
#    # #print(*args, **kwargs)

CACHE = "translations"

def exercise_translate_raw(subdomain, dbexercise, language ,action ):
    #print(f"EXERCISE_TRANSLATE_RAW")
    dbcourse = dbexercise.course
    course_pk = dbcourse.pk
    backup_name = "{:%Y%m%d_%H:%M:%S_%f_}".format(now()) + ".exercise.xml"
    name = dbexercise.name 
    path = dbexercise.get_full_path()
    xml = exercise_xml(path)
    exercise_save(path, xml, backup_name, 'super')
    # 'translate','remove','changedefaultlanguage'
    caches["default"].set("force_translate",True)
    messages =  exercise_translate_language(dbexercise, xml, language, action, course_pk)
    #print(f"Exercise {name} : {messages}")
    return messages





@permission_required("exercises.edit_exercise")
def edit_translation(request,course_pk):
    """Bulk edit/delete Translation entries.

    - Displays only original_text, language, translated_text.
    - Save applies edits and deletions to all rows.
    """
    subdomain, db = get_subdomain_and_db(request)

    class TranslationEditForm(ModelForm):
        class Meta:
            model = Translation
            # Only translated_text is editable in the formset
            fields = ["language","original_text","translated_text"]
            widgets = {
                "translated_text": Textarea(attrs={"rows": 2, "cols": 80}),
            }

    TranslationFormSet = modelformset_factory(
        Translation,
        form=TranslationEditForm,
        can_delete=True,
        extra=0,
    )

    #qs = Translation.objects.using(db).annotate(sort_key=Lower(LTrim(F("original_text")))).order_by("-language","sort_key")
    #qs = ( Translation.objects.using(db) .annotate( lang_sort=Case( When(language="sv", then=Value(1)), When(language="en", then=Value(0)),
    #        default=Value(2), output_field=IntegerField(),), text_sort=Lower(Func(F("original_text"), function="LTRIM")),) .order_by("lang_sort", "text_sort"))
    qs = Translation.objects.using(db).order_by("-language","original_text")


    #print(f"METHOD = {request.method}")
    if request.method == "POST":
        formset = TranslationFormSet(request.POST, queryset=qs)
        if formset.is_valid():
            #print(f"FORMSET IS VALID")
            # Save changes and handle deletions using the correct DB alias
            instances = formset.save(commit=False)
            # Deletions
            for obj in formset.deleted_objects:
                obj.delete(using=db)
            # Updates
            for inst in instances:
                inst.save(using=db)
            # Redirect to avoid resubmission
            from django.urls import reverse
            return redirect(request.path) 
    else:
        formset = TranslationFormSet(queryset=qs)

    context = {
        "formset": formset,
        # Render-only fields accessed via form.instance
    }
    return render(request, "edit_translation.html", context)

@permission_required("exercises.edit_exercise")
@api_view(["POST"])
def exercise_translate(request, exercise, language):
    #    print("EXERCISE_TRANSLATE exercise=%s " % exercise )
    subdomain, db = get_subdomain_and_db(request)
    messages = []
    dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
    dbcourse = dbexercise.course
    course_pk = dbcourse.pk
    usetranslations = dbcourse.use_auto_translation and not caches["default"].get("temporarily_block_translations")or False 
    # print("API: course_pk = ", course_pk,' usetranslations = ',usetranslations)
    if usetranslations:
        backup_name = "{:%Y%m%d_%H:%M:%S_%f_}".format(now()) + request.user.username + ".xml"
        path = dbexercise.get_full_path()
        xml = exercise_xml(path)
        exercise_save(path, xml, backup_name, request.user.username)
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
    subdomain,db = get_subdomain_and_db( request)
    data = request.data
    altkey = data.get("altkey", None)
    missingstring = data["string_"]
    dbcourse = Course.objects.using(db).get(pk=course_pk)
    languages = dbcourse.get_languages()
    #if isinstance(missingstring, (bytes, bytearray)):
    if not isinstance( missingstring, str ):
        missingstring = missingstring.decode("utf-8")
    missingstring = f"{missingstring}"
    #new = False
    old = Translation.objects.using(db).filter(language=language, altkey=altkey).exists() 
    #print(f"MISSING = {missingstring} data={data}")
    #for lang in languages : 
    #    ts =  Translation.objects.using(db).filter(original_text=missingstring,language=lang,altkey=altkey).all()
    #    while len( ts ) > 0 :
    #        for t in ts :
    #            t.delete(using=db);
    #        ts =  Translation.objects.using(db).filter(original_text=missingstring,language=lang ,altkey=altkey)
    #    if len( ts ) ==  0 :
    #        new = True
    if old :
        return Response([] )
    else :
        #temporarily_block_translations =  caches["default"].get("temporarily_block_translations" ) or False
        use_auto_translation = dbcourse.use_auto_translation
        #temporarily_blocked =  not use_auto_translation or temporarily_block_translations 
        for lang in languages:
            #print(f"MISSINGSTRING = {missingstring}")
            #print(f"LANG = {lang}")
            #print(f"COURSE_PK = {course_pk}")
            #print(f"ALTKEY = {altkey}")
            txtsout = auto_translate_strings([missingstring], lang, course_pk, altkey)
            #print(f"TXTSOUT = {txtsout}")
            if txtsout  and altkey :
                t, created  = Translation.objects.get_or_create( original_text=missingstring, translated_text=txtsout[0], altkey=altkey, language=lang ) 
                t.save();
            #logger.error(
            #    f" SKIP TRANSLATION {missingstring} since  use={dbcourse.use_auto_translation}  and  cache={ caches['default'].get('temporarily_block_translations')} "
            #)
    #except Exception as e:
    #    print( f"Unknown Exception in NOTIFYMISSINGSTRING {type(e).__name__} subdomain={subdomain}  data={data} ")
    return Response([])


def get_translation_etag(request, course_pk, language=None):
    subdomain, db = get_subdomain_and_db(request)
    cachekey = f"{subdomain}{course_pk}{language}"
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
    dbcourse = Course.objects.using(db).get(pk=course_pk)
    if not language:
        if dbcourse.languages:
            language = (dbcourse.languages).split(",")[0]
        else:
            language = "en"
    request.session["lang"] = language
    cachekey = f"{subdomain}{course_pk}{language}"
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
    dbcourse = dbexercise.course

    if caches["default"].get('force_translate') or False :
        pass 
    elif  not dbcourse.use_auto_translation and not caches["default"].get("temporarily_block_translations") or False :
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


 # hashkey removed; use original_text directly


#@transaction.atomic
def auto_translate_strings(txts, lang, course_pk=None, altkey=None, exercise=None):
    #print(f"AUTO_TRANSLATE_STRINGS {txts} {lang} {course_pk} {altkey} {exercise}")
    #print(f"AUTO_TRANSLATE STRINGS {settings.ENABLE_AUTO_TRANSLATE} {txts} {lang} pk={course_pk} ")
    #db = 'ffy144-2025'
    #try :
    #    ca = caches["default"].get("temporarily_block_translations") or False
    #except  Exception :
    #    ca = False
    #else:
    #    ca = False if ca is None else ca 
    #hsh = (".").join(txts) + f"{lang}"  # THE SAME SET OF STRINGS ARE SUBMITTED TWICE; JUST USE THE FIRST OCCASION
    #block_hash = (hashlib.md5(hsh.encode("utf-8")).hexdigest())
    #try :
    #    if caches["default"].get("force_translate") or False:
    #        pass
    #except :
    #    return None
    #if caches["default"].get("temporarily_block_translations")  or False:
    #    #print(f"TEMPORARILY BLOCK")
    #    return None
    #else :
    #    pass
    #already_done = caches["default"].get(block_hash) or False
    #if not already_done :
    #    #print(f"NOT BLOCKED by {already_done} {block_hash} {txts} ")
    #    pass
    #else :
    #    #print(f"BLOCKED by {already_done} {block_hash} ")
    ##    return None
    #if not settings.ENABLE_AUTO_TRANSLATE and not caches["default"].get("force_translate"):
    #    #print(f"RETGURNIN NONE")
    #    return None
    #if course_pk == None :
    #    #print(f"PK=None so return None")
    #    return []
    db = db_info_var.get(None)
    #logger.error(f"DB = {db} {exercise} ")
    #print(f"EXERCISE = {exercise}")
    #if not exercise == None :
    #    #print(f"EXERCISE = {exercise}")
    #    dbcourse =  exercise.course
    #else :
    #    dbcourse = Course.objects.using(db).get(pk=course_pk)
    #logger.error(f"DBCOURSE = {dbcourse}")
    dbcourses = Course.objects.using(db).all()
    if dbcourses :
        dbcourse =dbcourses[0]
    else :
        return []
    use_auto_translation = dbcourse.use_auto_translation
    #if caches["default"].get("force_translate",False):
    #    use_auto_translation = True 
    if not use_auto_translation:
        return None
    donttranslatetags = ["qmath", "asciimath", "right", "figure", "code", "solution", "asset"]
    origtxts = []
    deepl_lang = lang.upper()
    if deepl_lang == "EN":
        deepl_lang = "EN-US"
    try :
        if not settings.USE_DEEPL:
            lhtag = "<span class='notranslate'>"
            pklfile = os.path.join(settings.BASE_DIR, "backend", "service_account.pkl")
            course = dbcourse
            cfile = f"{settings.VOLUME}/auth/google_auth_string.txt"
            if os.path.exists(cfile):
                f = open(f"{settings.VOLUME}/auth/google_auth_string.txt", "r+")
                credential_string = f.read()
                credentialstring = patch_credential_string(credential_string)
                f.close()
            else:
                credential_string = course.google_auth_string
                credentialstring = patch_credential_string(course.google_auth_string)
            #print(f"CREDENTIAL_STRING {credential_string}")
            #if settings.VALIDATE_GOOGLE_AUTH_STRING:
            #    service_account_info = json.load(io.StringIO(credentialstring))
            service_account_info = json.load(io.StringIO(credentialstring))
            #print(f"SERVICE_ACCOUNT_INFO {service_account_info}")
            #elif os.path.isfile(pklfile):
            #    service_account_info = pickle.load(open(pklfile, "rb"))
            #else:
            #    service_account_info = json.load(io.StringIO(credentialstring))
            credentials = service_account.Credentials.from_service_account_info(service_account_info)
            #print(f"CREDENTIALS")
        else:
            lhtag = '<span translate="no">'
        rhtag = "</span>"
        txtsin = []
        origtxts = []
        #print(f"TRANSLATE TXTS = {txts} TO {lang} ")
        for txt in txts:
            txt = txt.strip()
            if True: # not Translation.objects.filter(original_text=txt, language=lang, exercise=exercise).exists():
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
                if not origtxt == '' :
                    origtxts.append(origtxt)
            else:
                pass
            # tr = Translation.objects.get(hashkey=hsh,language=lang,exercise=exercise)
            # #logger.info("SKIP hsh =  %s lang=%s %s %s ",(hsh, lang, txt, tr.translated_text) )
        #print(f"TXTSIN = {txtsin} {lang}")
        #print(f"ORIGTXTS = {origtxts} {lang}")
        if len(txtsin) > 0:
            if not settings.USE_DEEPL:
                translate_client = translate.Client(credentials=credentials)
                translations = translate_client.translate(txtsin, target_language=lang, format_="html")
            else:
                logger.info(f"NEW DEEPL TRANSLATION TXTSIN = {lang} {txtsin}")
                #translator = deepl.Translator(settings.DEEPL_AUTH_KEY)
                auth_key = settings.DEEPL_AUTH_KEY
                translator = deepl.DeepLClient(auth_key)
                translations = translator.translate_text(
                    txtsin, target_lang=deepl_lang, split_sentences="nonewlines", tag_handling="html"
                )
        else:
            translations = []
        txtsout = []
        for translation in translations:
            if settings.USE_DEEPL:
                translated_text = "{}".format(translation.text)
            else:
                translated_text = "{}".format(translation["translatedText"])
            translated_text = html.unescape(translated_text)
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
        return txtsout 
        zipped = zip(origtxts, txtsout)
        for txtin, txtout in zipped:
            trs = Translation.objects.filter(original_text=txtin, language=lang, exercise=exercise)
            while trs.count() > 1:
                trs[0].delete()
                trs = Translation.objects.filter(original_text=txtin, language=lang, exercise=exercise)
            tr, _ = Translation.objects.using(db).get_or_create(original_text=txtin, language=lang, exercise=exercise)
            tr.original_text = txtin
            tr.translated_text = txtout
            tr.exercise = exercise
            if not altkey == None :
                tr.altkey = altkey
            tr.save()
        txtsout = []
        for orig in origtxts:
            if altkey is None:
                tr = Translation.objects.select_related("exercise").filter(
                    original_text=orig, language=lang, exercise=exercise
                )
            else:
                tr = Translation.objects.select_related("exercise").filter(
                    original_text=orig, language=lang, altkey=altkey, exercise=None
                )
            try:
                if len(tr) > 0 :
                    tr = tr[0]
                    txtsout.append(tr.translated_text)
            except Exception as e:
                logger.error(
                    "UNTRANSLATED  FOR UNKNOWN REASON  %s %s " % ( type(e).__name__, str(e))
                )
                txtsout.append("UNTRANSLATED")

        # logger.info("RETURN txtout = %s ", txtsout)
        #caches["default"].set(block_hash, True, 10) # Prevent recursion
        return txtsout

    except ValueError as e :
        return None
    except IntegrityError as e :
        return None
    except AttributeError as e :
        return None
    except MultipleObjectsReturned as e:
        logger.error(f"MULT OBJECTS: ERROR in  auto_translate_strings { type(e).__name__} {str(e)  }")
    except Exception as e:
        logger.error(f"TRANSLATIONS: ERROR in  auto_translate_strings { type(e).__name__} {str(e)  }")
        return None
    if translate_client == None:
        raise FileNotFoundError("No valid translation credentials found")
    else:
        raise RuntimeError("Unknown error in google translate; check credentials")


# def translate_string(txt, lang):
#    return auto_translate_strings([txt], lang)[0]


def makepretty(xml):
    xmlout = xml
    xmlout = re.sub(r"\s+", " ", xmlout)
    xmlout = minidom.parseString(xmlout).toprettyxml()
    xmlout = re.sub(r"\s*\n\s*\n", "\n", xmlout)
    xmlout = re.sub(r"&quot;", '"', xmlout)
    return xmlout


def translate_xml(xml, lang, action, course_pk, dbexercise, domakepretty):
    course = dbexercise.course
    if caches["default"].get("force_translate", False ):
        pass 
    elif not course.use_auto_translation and not caches["default"].get("temporarily_block_translations"):
        return xml
    if "translate" in action:
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
    elemstripped = copy.deepcopy(elem)
    etree.strip_attributes(elemstripped)
    otheralts = elemstripped.findall(tag)
    for otheralt in otheralts:
        elemstripped.remove(otheralt)
    xml = etree.tostring(elemstripped, encoding=str)
    return xml


def html_content(txt):
    txt = re.sub(r"^\s*<[^>]+>", "", txt)
    txt = re.sub(r"</[^>]+>\s*$", "", txt)
    txt = txt.strip()
    return txt


def fromString(xml):
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml, parser=parser)
    return root


# def patch_credential_string(value):
#    return value.strip().lstrip('r').strip("'")


def translatable_texts(root,lang):
    elems_to_be_translated = []
    pskip = [ elem.getparent().getparent() for elem in  root.xpath("//alt[@lang='" + lang + "']")]
    for tag in translatable_tags:
        elems_to_be_translated = elems_to_be_translated + root.findall(tag)
    all_elems = list( set( elems_to_be_translated) - set( pskip) )
    return all_elems
    #print(f"ELEMEMS_TO_BE_TRANSLATED {elems_to_be_translated} {lang}")
    #all_elems = [];
    #for elem in elems_to_be_translated :
    #    exists = any( child.get("lang") == lang for child in elem)
    #    if not exists :
    #        print(f"APPEND {elem} {elem.text.strip() } ")
    #        all_elems.append( elem )
    #    else :
    #        print(f"{elem} {elem.text.strip() }  EXISTS")
    #for elem in all_elems :
    #    print(f"DO_TRANSLATATE {elem.text.strip() } into {lang}")
    #return all_elems


def translate_xml_language(xml, langs, course_pk, dbexercise, domakepretty):
    db = dbexercise.course.opentasite
    #if caches["default"].get("temporarily_block_translations") == 'True':
    #    return xml
    xmlin = xml
    if langs[0] == "none":
        xml = makepretty(xml)
        return xml
    root = fromString(xml)
    #elems_already_translated = root.findall(".//alt")
    #for elem in elems_already_translated:
    #    lang = elem.attrib.get("lang")
    #    if lang :
    #        parent = elem.getparent()
    #        if parent :
    #            original_txt = elem_to_ascii(parent)
    #            objs = Translation.objects.using(db).filter(language=lang, original_text=original_txt, exercise=dbexercise) # .union(
    #                #Translation.objects.using(db).filter(language=lang, original_text=original_txt, exercise__isnull=True))
    #            if objs.exists():
    #                for obj in objs:
    #                    obj.translated_text = elem.text or ""
    #                    obj.save()
    #            else:
    #                obj, _ = Translation.objects.using(db).get_or_create(
    #                    language=lang,
    #                    original_text=original_txt,
    #                    exercise=dbexercise,
    #                    defaults={"translated_text": elem.text or ""},
    #                )

    for lang in langs:
        txtsin = []
        root = fromString(xml)
        elems = []
        elems_to_be_translated = translatable_texts(root,lang)
        originals_in_xml = set([elem_to_ascii(elem) for elem in elems_to_be_translated])
        #originals_in_database = set(
        #    Translation.objects.filter(language=lang, exercise=dbexercise).values_list("original_text", flat=True)
        #)
        #deleted_originals = list(originals_in_database.difference(originals_in_xml))
        #for orig in deleted_originals:
        #    trs = Translation.objects.filter(original_text=orig, exercise=dbexercise)
        #    for tr in trs:
        #        tr.delete()

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
        #print(f"LANG = {lang}")
        #print(f"TXTSIN = {txtsin}")
        txtsout = auto_translate_strings(txtsin, lang, None , None, None )
        #txtsout = [ s.upper() for s in txtsin ]
        #print(f"TXTOUT = {txtsout}")
        if txtsout != None :
            zipped = zip(elems, txtsout)
            for elem, txtout in zipped:
                xmlout = f"\n<alt>" + txtout + "</alt>"
                #original_txt = elem_to_ascii(elem)
                #tr, _ = Translation.objects.get_or_create(
                #    original_text=original_txt, language=lang, exercise=dbexercise
                #)
                #tr.original_text = original_txt
                #tr.translated_text = txtout
                #tr.save()
                newelem = fromString(xmlout)
                newelem.set("lang", lang)
                #print(f"NEWELEM = {newelem.text}")
                elem.append(newelem)
                #print(f"NEW ELEM = {etree.tostring( elem ) }")
            #xml = etree.tostring(root, encoding=str)
            #if domakepretty:
            #    xml = makepretty(xml)
    xml = etree.tostring( root , encoding='utf-8').decode('utf-8');
    #print(f"XML = {xml}")
    return xml


def change_default_language(xml, lang, course_pk):
    #print("MAKE DEFAULT lang = ", lang )
    if lang == "none":
        return xml
    try:
        xmlorig = xml
        root = fromString(xml)
        # texts = root.findall('.//text')  + root.findall('.//exercisename') +  root.findall('.//choice')
        all_elems = []
        for path in translatable_tags:
            all_elems.extend(root.findall(path))
        # texts = root.findall('.//text')  + root.findall('.//exercisename') +  root.findall('.//choice')
        xml_altered = False
        for elem in all_elems :
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
    if lang == "none":
        return xml
    try:
        xmlorig = xml
        root = fromString(xml)
        for elem in root.xpath("//alt[@lang='" + lang + "']"):
            p = elem.getparent()
            p.remove(elem)
        #elems_to_be_translated = translatable_texts(root,lang)
        #for elem in elems_to_be_translated:
        #    # #print("REMOVE FOUND text ")
        #    if lang == 'all' :
        #        for alt_ in elem.findall("alt") :
        #            elem.remove(alt_)
        #    else :
        #        for alt_ in elem.findall("alt[@lang='" + lang + "']"):
        #            elem.remove(alt_)
        # hashkey attribute no longer used; nothing to strip
        xml = etree.tostring(root, encoding=str)
        #xml = makepretty( xml )
        return xml
    except Exception as e:
        # #print("TRANSLATIONS: ERROR in remove_language", str(e))
        formatted_lines = traceback.format_exc()
        logger.error("TRANSLATIONS ERROR IN remove_language %s , %s ", (str(e), formatted_lines))
        return xmlorig
