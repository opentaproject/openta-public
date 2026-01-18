# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import json
import logging
import os
import random
from django.conf import settings
import re
from datetime import datetime
import time
import traceback
from utils import get_subdomain, get_subdomain_and_db
from django.core.cache import caches
if settings.USE_CHATGPT :
    from django_ragamuffin.models import Message
    from django_ragamuffin.utils import mathfix
from django.utils.safestring import mark_safe





from django_ratelimit.core import is_ratelimited
from exercises.models import Answer, Exercise, Question
from exercises.parsing import (
    exercise_xmltree,
    get_questionkeys_from_xml,
    get_translations,
    global_and_question_xmltree_get,
    question_json_get,
    question_xmltree_get,
)
from exercises.serializers import AnswerSerializer
from exercises.util import deep_get
from exercises.views.asset import _dispatch_asset_path
from exercises.xmljson import BadgerFish
from lxml import etree

from backend.middleware import check_connection
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import translation
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)

question_check_dispatch = {}
answer_class_dispatch = {};
validate_question_dispatch = {};
question_json_hooks = {}
sensitive_tags = {}
sensitive_attrs = {}
bf = BadgerFish(xml_fromstring=False)


class QuestionError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def parsehints(question_xmltree, global_xmltree, answer_data):
    answer_data = re.sub(r"\s+", " ", answer_data, re.M)
    lang = translation.get_language()
    xmllist = [question_xmltree, global_xmltree]
    result = {}
    hints = []
    #for hinttype in ["necessary", "required", "forbidden", "discouraged", "encouraged", "allowed"]:
    for xmlentry in xmllist:
            #if xmlentry is not None:
            #hints = hints + xmlentry.findall(f'.//regex[@present="{hinttype}"]...')
            #else :
            hints = hints + xmlentry.findall(f'.//hint')
    if hints:
        try:
            for item in hints:
                # print("HINT iTEM = ", item )
                regex = item.find("regex").text
                reply = item.find("comment").text
                # alts = item.find('comment').findall('alt')
                # alts2  = get_translations( item.find('comment'))
                # print('alt2 = ', alts2)
                # print('translation', alts2.get(lang, reply) )
                tdict = get_translations(item.find("comment"))
                reply = tdict.get(lang, reply)
                # print("newreply = ", newreply)
                # if alts:
                #    #print("alts = ", alts)
                #    for alt in alts:
                #        #print("alt.get lang", alt.get('lang') )
                #        if alt.get('lang') == lang :
                #            reply = alt.text
                presence = "forbidden"
                # print("p attrib = ", item.find('regex').attrib  )
                attributedict = item.find("regex").attrib
                if attributedict:
                    presence = attributedict.get("present")
                    # print('presence = ', presence )
                if regex and reply:
                    # found = re.search(regex, answer_data)
                    from exercises.utils.string_formatting import insert_implicit_multiply
                    regex = regex.strip()
                    s = insert_implicit_multiply( answer_data )
                    #print(f"TEST S = {s}")
                    found = re.search(
                        r"{}".format(regex), s
                    )  # Allow for special chars in regex hint i.ie. <regex> (\[|\]) </regex>
                    found = False if found is None else True
                    # print("REGEX FOUND AS WELL AS REPLY found = ", found)
                    # print("PRESCENCE = ", presence )
                    if presence == "forbidden" and found:
                        result["correct"] = False
                        result["status"] = "incorrect"
                        result["comment"] = reply
                        result["dict"] = tdict
                        # return result
                        break
                    elif presence == "required" and not found:
                        result["status"] = "incorrect"
                        result["correct"] = False
                        result["comment"] = reply
                        result["dict"] = tdict
                        # return result
                        break
                    elif presence == "necessary" and not found:
                        result["status"] = "incorrect"
                        result["correct"] = False
                        result["comment"] = reply
                        result["dict"] = tdict
                        # return result
                        break
                    elif presence == "allowed" and found:
                        result["comment"] = reply
                        result["dict"] = tdict
                        # return result
                        break
                    elif presence == "encouraged" and not found:
                        result["comment"] = reply
                        result["dict"] = tdict
                        # return result
                        break
                    elif presence == "discouraged" and found:
                        result["comment"] = reply
                        result["dict"] = tdict
                        # return result
                        break
            return result
            # print("QSON ITEM regex",  item.get('regex') )
            # print("QSON ITEM comment",  item.get('comment') )
        except:
            # print("SHOULD NOT GET HERE ANY MORE; qjson is not a list; see parsehints")
            result["correct"] = False
            result["comment"] = "PROGRAMMING ERROR; please inform admin HINT TAGS ARE WRONG"

    #
    # print(f"RETURN PARSEHINTS RESULT = {result}")
    return result


def get_all_answers(dbhooks):  # exercise_key, question_id, user_id ) :
    #print(f"GET_ALL_ANSWERS {dbhooks} ")
    db = settings.DB_NAME
    exercise_key = dbhooks["exercise_key"]
    user_id = dbhooks["user_id"]
    all_answers = {}
    dbexercise = Exercise.objects.get(exercise_key=exercise_key)
    db = dbexercise.course.opentasite
    for question in Question.objects.using(db).filter(exercise=dbexercise):
        try:
            previous_answer = get_previous_answers(question.pk, user_id, 1, False, db )[0]
            all_answers[question.question_key] = previous_answer["answer"]
        except:
            pass
    return all_answers


def get_number_of_attempts(question_id, user_id, before_date=None, db=None):
    """
    Number of attempts by user at question.
    Args:
        question_id: question primary key
        user_id: user primary key
    Returns:
        Number of attempts (int)
    """
    if db == None:
        db = settings.DB_NAME
    answers = Answer.objects.using(db).filter(user__pk=user_id, question__pk=question_id)
    nattempt = 0
    for answer in answers:
        g = answer.grader_response
        if "correct" in g:
            nattempt = nattempt + 1

    return nattempt
    # if answers == None:
    #    return 0
    # last_answer = answers.last()
    # if not None == last_answer:
    #    nattempt = last_answer.nattempt + 1
    # else:
    #    nattempt = 0
    # print("COMPARE ", answers.count(), nattempt)
    # if answers.count() != nattempt:
    #    attemptlist = list(answers.values_list('nattempt', flat=True))
    #    datelist = list(answers.values_list('date', flat=True))
    #    #print("ANSWERLIST = ", attemptlist)
    #    #print("ANSWERLIST = ", attemptlist)
    #    # assert False, "IN QUESTION.py, GET NUMBER OF ATTEMPTS INCORRECT"
    # return nattempt


def get_other_answers(question_key, user_id, exercise_key,db=None):
    all_answers = {}
    if db == None :
        return {}
        #dbexercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
        #questions =  Question.objects.using(db).filter(exercise=dbexercise)
    else :
        dbexercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
        questions =  Question.objects.using(db).filter(exercise=dbexercise)
    for question in questions:
        try:
            if db == None :
                previous_answer = Answer.objects.filter(user__pk=user_id, question=question).latest("date")
            else :
                previous_answer = Answer.objects.using(db).filter(user__pk=user_id, question=question).latest("date")
            all_answers[question.question_key] = previous_answer.answer
        except Answer.DoesNotExist:
            all_answers[question.question_key] = None
    return all_answers


def get_safe_previous_answers(question_id, user_id, n_answers=settings.N_ANSWERS, feedback=False,db=None):
    """Previous attempts (time ordered with most recent first) at the question by user.

    Args:
        question_id: question primary key
        user_id: user primary key
        n_answers: number of attempts to include (default: 10)
    Returns:
        List of serialized answers (see AnswerSerializer for fields)

    """
    if settings.RUNTESTS :
        db = 'default'
    if not db == None :
        answers = Answer.objects.using(db).filter(user__pk=user_id, question__pk=question_id)
        last_answers = answers.order_by("-date")[:n_answers]
        for answer in last_answers:
            if not feedback:
                answer.correct = None
                answer.grader_response = None
        sanswers = AnswerSerializer(last_answers, many=True)
        data = [];
        # PATCH SERIALIZER TO GRAB THE ORIGINAL MESSAGE RESPONSE FOR AIBASED
        for aj in sanswers.data :
            gs = aj.get('grader_response',"{}") 
            if gs == None :
                g = {}
            else :
                g = json.loads(gs)
            pk = g.get('pk',None)
            s = aj
            if  isinstance(pk, int)   and settings.USE_CHATGPT :
                m = Message.objects.filter(pk=pk).first()
                if m :
                    msg =  m.response + f"<p/>msg={pk}" 
                else  :
                    msg = g.get('comment','') + f"<p/>msg={pk} no longer exists"
            else :
                msg = g.get('comment','')
            if settings.USE_CHATGPT :
                g['comment'] = mathfix( mark_safe( msg  ) )
            elif isinstance(pk, int ) :
                g['comment'] = msg
            #g['comment'] = re.sub(r"operatorname","bold",g['comment'] )
            #g['comment'] = re.sub(r"boldsymbol","bold",g['comment'] )
            #g['comment'] = re.sub(r"\$\$(.*?)\$\$", r"<p/><p/>$\1$<p/><p/>", g['comment'], flags=re.S)
            #g['comment'] = re.sub(r"\\dots", r"\\ldots", g['comment'] )
            #g['comment'] = re.sub(r'fileciteturn0file[0-9]+\.', '', g['comment'] )
            gj = json.dumps(g);
            s['grader_response'] = gj
            data.append(s)
        return data
    else :
        return []


def get_previous_answers(question_id, user_id, n_answers=settings.N_ANSWERS, feedback=False,db=None):
    #print(f"GET_PREVIOUS_ANSWERS feedback={feedback} DB={db} ")
    return get_safe_previous_answers(question_id, user_id, n_answers=n_answers, feedback=feedback,db=db)
    """ Previous attempts (time ordered with most recent first) at the question by user.

    Args:
        question_id: question primary key
        user_id: user primary key
        n_answers: number of attempts to include (default: 10)
    Returns:
        List of serialized answers (see AnswerSerializer for fields)

    """
    # answers = Answer.objects.filter(user__pk=user_id, question__pk=question_id)
    # last_answers = answers.order_by('-date')[:n_answers]
    # sanswers = AnswerSerializer(last_answers, many=True)
    # return sanswers.data

def default_validate_question(question_json, *arg,**kwargs):
    qtype = question_json['@attr'].get('type',"undefined") ;
    key   = question_json['@attr']['key'] ;
    return (("warning" , f"a validation of {qtype} in {key} was not done"))

def register_question_class(obj):
    try :
        register_question_type(obj.name, obj.local_question_check,  obj.answer_class , obj.validate_question, obj.json_hook, obj.hide_tags)
    except :
        register_question_type(obj.name, obj.local_question_check,  obj.answer_class , default_validate_question, obj.json_hook, obj.hide_tags )


def register_question_type(
    question_type,
    grading_function,
    answer_class_function,
    validation_function,
    json_hook=lambda safe_json, full_json, q_id, u_id, e_id: safe_json,
    hide_tags=[],
    hide_attrs=[],
):
    question_check_dispatch[question_type] = grading_function
    answer_class_dispatch[question_type] = answer_class_function
    validate_question_dispatch[question_type] = validation_function
    question_json_hooks[question_type] = json_hook
    sensitive_tags[question_type] = hide_tags
    sensitive_attrs[question_type] = hide_attrs


def question_check(request, db, user, user_agent, exercise_key, question_key, answer_data, old_answer_object=None):
    subdomain = db
    dbexercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
    hijacked = request.session.get("hijacked", False)
    view_solution_permission = user.has_perm("exercises.view_solution")
    _dispatch_asset_path(user, dbexercise)
    cache = caches['default'];      
    username_ = request.user.username.encode('ascii','ignore').decode('ascii')
    cache.set(f"{username_}:X:{exercise_key}",subdomain,604800) # THIS IS A MONKEYPATCH TO GET SUBDMOMAIN IN AGGREGATION POST_SAVE
    ms = str( time.time() ).split(".")[1]
    path = '/subdomain-data/auth/templogs'
    os.makedirs(path , exist_ok=True)
    current_time = time.time()
    ft = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") 
    formatted_time = f"{subdomain}-{ft}-{ms}"
    fname = os.path.join( path , formatted_time)
    fp = open( fname, "w")
    fp.write(f"{request.user}\n")
    p = str( request.get_full_path() )
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if os.path.isfile(file_path):
            file_mod_time = os.path.getmtime(file_path)
            window = int( settings.ACTIVITY_WINDOW )
            if current_time - file_mod_time > window :
                os.remove(file_path)


    
    # print("OLD_ANSWER_OBJECT = ", old_answer_object)
    # print("STUDENTASSETPATH = ", studentassetpath)
    try:
        get_usermacros(user, exercise_key, question_key=question_key, before_date=None, db=db)
        str(user)
        # print("USERMACROS = ", usermacros)
    except ObjectDoesNotExist:
        return {
            "error": "Invalid question",
            "author_error": (
                "You must save the exercise (save " "button in toolbar) before the question " "can be evaluated."
            ),
        }
    # xmltree = exercise_xmltree(dbexercise.get_full_path(), usermacros)
    # question_xmltree = xmltree.xpath('/exercise/question[@key="{key}"]'.format(key=question_key))[0]
    # rate_limit = (question_xmltree.xpath('//rate') or [None])[0]
    rate_limit = None
    # print("RATE_LIMIT = ", rate_limit)
    if (
        (not settings.RUNNING_DEVSERVER and not settings.RUNTESTS)
        and rate_limit is not None
        and rate_limit.text is not None
        and not user.is_staff
    ):
        rate = rate_limit.text.strip()
        if (not settings.RUNNING_DEVSERVER) and is_ratelimited(
            request, group="question_custom_rate", key="user", rate=rate, increment=True
        ):
            error_msg = _("Answer rate exceeded, " "please wait before trying again. (Rate: ")
            return {"error": error_msg + rate + ")"}
    ret = _question_check(
        hijacked,
        view_solution_permission,
        user,
        user_agent,
        exercise_key,
        question_key,
        answer_data,
        old_answer_object=old_answer_object,
        db=db,
    )
    comment = ret.get('comment','none')
    return ret

def answer_class(  hijacked, view_solution_permission, user, user_agent, exercise_key, question_key, answer_data, old_answer_object=None, db=None,):
    return _question_check( hijacked, view_solution_permission, user, user_agent, exercise_key, question_key, answer_data, old_answer_object=old_answer_object, db=db, answer_class="answer_class" )


def _question_check(
    hijacked,
    view_solution_permission,
    user,
    user_agent,
    exercise_key,
    question_key,
    answer_data,
    old_answer_object=None,
    db=None,
    answer_class=None,
):
    # print(f"VIEW_SOLUTION_PERMSSION = {view_solution_permission}")
    assert db != None, "_QUESTION_CHECKE DB=None"
    # print("QUESTION CHECK ANSER_DATA = ", answer_data)
    questioncheckdata = {
        "hijacked": hijacked,
        "view_solution_permission": view_solution_permission,
        "user": user,
        "user_agent": user_agent,
        "exercise_key": exercise_key,
        "question_key": question_key,
        "answer_data": answer_data,
    }
    if  len( answer_data) > 0   :
        force_aibased = ( answer_data[0].lstrip()[:1] ) == '?'
    else :
        force_aibased = False
    before_date = None
    if old_answer_object:
        before_date = old_answer_object.date
    check_connection(db)
    dbquestion = (
        Question.objects.using(db)
        .select_related("exercise", "exercise__meta", "exercise__course")
        .get(exercise__exercise_key=exercise_key, question_key=question_key)
    )
    #try :
    #    qcheck = dbquestion.qtype()
    #except Exception as e:
    #    logger.error(traceback.format_exc())
    #    logger.error(f"DBQUESTION = {dbquestion}")
    #    logger.error(f"ERROR QTYPE {str(e)}")
    qtype =  'aibased' if force_aibased else  dbquestion.qtype()
    dbexercise = dbquestion.exercise
    meta = dbexercise.meta
    course = dbexercise.course
    feedback = dbexercise.meta.feedback
    # print(f"FEEDBACK = {feedback}")
    studentassetpath = _dispatch_asset_path(user, dbexercise)
    try:
        # dbquestion = Question.objects.using(db).get(exercise=dbexercise, question_key=question_key)
        usermacros = get_usermacros(user, exercise_key, question_key=question_key, before_date=before_date, db=db)
        str(user)
        # print("USERMACROS = ", usermacros)
    except ObjectDoesNotExist:
        return {
            "error": "Invalid question",
            "author_error": (
                "You must save the exercise (save " "button in toolbar) before the question " "can be evaluated."
            ),
        }

    usermacros["@call"] = "question_check"
    usermacros["@is_staff"] = user.is_staff
    tbeg = time.time()
    tbeg = time.time()
    ######
    if not settings.RUNTESTS and settings.DEBUG_PLUS:
        course_key = course.course_key
        exercise_path = dbexercise.path
        alternative_full_path = os.path.join(settings.VOLUME, db, "exercises", str(course_key), exercise_path)
        if not dbexercise.get_full_path() == alternative_full_path:
            logger.error(f"QUESTION_CHECK {dbexercise.get_full_path()} alternative_full_path={alternative_full_path} ")
    #######
    question_json = question_json_get(dbexercise.get_full_path(), question_key, usermacros,db)

    try:
        expression = question_json.get("expression").get("$")
    except Exception as e:
        expression = ""
    # print("TIME1 = ",  ( time.time() - tbeg ) *1000 )
    # print("CALL HOOK USERMACROS=", usermacros)
    #logger.error(f"DB={db} QTYPE={qtype}")
    if not settings.USE_CHATGPT and qtype == 'aibased' :
        #print("WARNING THAT QTYPE=AIBASED")
        return {"comment": "No grading function for question type " + qtype,'warning' : 'aibased queries are not implemented.'}

    if qtype in question_json_hooks:
        question_json = question_json_hooks[qtype](
            question_json, question_json, dbquestion.pk, user.pk, exercise_key, feedback, db=db
        )
    # print("TIME2 = ",  ( time.time() - tbeg ) *1000 )
    xmltree = exercise_xmltree(dbexercise.get_full_path(), usermacros)
    # print("TIME3 = ",  ( time.time() - tbeg ) *1000 )
    question_xmltree = xmltree.xpath('/exercise/question[@key="{key}"]'.format(key=question_key))[0]
    if question_xmltree.xpath("macros") and settings.REFRESH_SEED_ON_CORRECT_ANSWER:
        refreshable_macros = True
    else:
        refreshable_macros = False
    [global_xmltree, question_xmltree] = global_and_question_xmltree_get(xmltree, question_key, usermacros)
    # THESE AREA ADDED FOR USE IN  IN MACROS IN PYTHONIC
    question_xmltree.append(etree.fromstring("<exercisekey>" + exercise_key + "</exercisekey>"))
    question_xmltree.set("exerciseseed", usermacros["@exerciseseed"])
    question_xmltree.set("questionseed", usermacros["@questionseed"])
    question_xmltree.set("exercise_key", exercise_key)
    question_xmltree.set("path", os.path.join(course.get_exercises_path(db), dbexercise.path))
    question_xmltree.set("user", str(user))

    studentassetpath = _dispatch_asset_path(user, dbexercise)
    exerciseassetpath = os.path.join(course.get_exercises_path(db), dbexercise.path)  ## NEED THIS
    question_xmltree.set("studentassetpath", studentassetpath)  ## NEED THIS
    question_xmltree.set("exerciseassetpath", exerciseassetpath)  ## NEED THIS
    global_xpath = '/exercise/global'
    try :
        global_xmltree = (xmltree.xpath(global_xpath))[0]
    except IndexError as e :
        global_xmltree = etree.fromstring("<global/>")
    runtime_element = etree.Element("runtime")
    runtime_element.append(etree.fromstring("<exercisekey>" + exercise_key + "</exercisekey>"))
    runtime_element.set("exercise_key", exercise_key)
    runtime_element.set("path", os.path.join(course.get_exercises_path(db), dbexercise.path))
    runtime_element.set("user", str(user))
    exerciseassetpath = os.path.join(course.get_exercises_path(db), dbexercise.path)
    runtime_element.set("studentassetpath", studentassetpath)
    runtime_element.set("exerciseassetpath", exerciseassetpath)
    question_xmltree.append(runtime_element)
    asciok = True
    try:
        if qtype != 'aibased' :
            answer_data.encode("ascii")
        else :
            answer_data.encode("utf-8")
    except UnicodeEncodeError:
        asciok = False
    if not asciok:
        return {
            "error": "non-asci possibly unseen character in the answer. Retype the entire answer; don't just paste."
        }
    if qtype in question_check_dispatch:
        result = {}
        try:
            result = question_check_dispatch[qtype]( question_json, question_xmltree, answer_data, global_xmltree)
            if user.username == "super":
                result["expression"] = expression
                result["debug"] = str(int((time.time() - tbeg) * 1000)) + " ms" + result.get("debug", "")
        except AssertionError as e :
            return {"correct": False, "error": str(e) }
        except Exception as e:
            logger.error(f"QUESTION_CHECK_ERROR E520193 : { type(e).__name__} data={questioncheckdata}")
            logger.error(traceback.format_exc())
            return {"error": f"QUESTION_CHECK_ERROR E520193 : { type(e).__name__}", "correct": False}
        result["type"] =  qtype
        hints = parsehints(question_xmltree, global_xmltree, answer_data)
        result.update(hints)
        if "comment" in hints.keys():
            result["warning"] = hints["comment"]
        if "zerodivision" in result:
            logger.error(["zerodivision", dbexercise.name, question_key])
        # print("Q3")
        correct = False
        # print("RESULT IN QUESTION = ", result)
        if "correct" in result:
            correct = result["correct"]
            if correct and refreshable_macros:
                result["comment"] = " Note that a new random question is now presented. "
        if settings.DEBUG_PLUS and user.groups.filter(name="Author").exists() and result.get("debug", False):
            result["warning"] = result.get("warning", "") + "info:  " + result.get("debug")

        else:
            result.pop("debug", None)

        # #print("RESULT AFTER UPDATE  = ", result )
        new = not settings.IGNORE_NOFEEDBACK  # WHEN REGRADING FLAG NEW = False to ignor no_feedback
        if old_answer_object == None:
            questionseed = usermacros["@questionseed"]
            exerciseseed = usermacros["@exerciseseed"]
            #print(f"RESULT = {result}")
            grader_response = json.dumps(result)
            answer_data = re.sub(
                r"\s+", " ", answer_data, re.M
            )  # Avoid error when answer data is hidden due to many returns
            fails = True
            for retries in [0, 1]:
                if fails:  # and user.has_perm("exercises.log_question"):
                    try:
                        new = True
                        fails = True
                        check_connection(db)
                        answer_data = answer_data
                        a = Answer(
                            user=user,
                            # question=dbquestion,
                            answer=answer_data,
                            grader_response=grader_response,
                            correct=correct,
                            user_agent=user_agent,
                            questionseed=questionseed,
                            exerciseseed=exerciseseed,
                            question=dbquestion,
                        )
                        a.save(using=db)
                        # print(f"QUESTION_SAVED OK! SAVED {answer_data} ")
                        fails = False
                    except Exception as e:
                        logger.error(
                            f"{type(e).__name__} ERROR E991962 QUESTION.py db={db} user={user} answer={answer_data}  retries={retries}  CANNOT CREATE ANSWER DATABASE OBJECT"
                        )
                        time.sleep(0.5)
        else:
            return (result, correct)
        usermacros = get_usermacros(user, exercise_key, question_key=question_key, before_date=before_date, db=db)
        previous_answers = get_safe_previous_answers(dbquestion.pk, user.pk, n_answers=settings.N_ANSWERS, feedback=feedback,db=db)
        result["previous_answers"] = previous_answers
        result["n_attempts"] = usermacros["@nattempts"]
        result["status"] = None
        if fails:
            yesorno = "correct" if correct else "incorrect"
            result["warning"] = f"Your answer {answer_data} is {yesorno} but there was an error saving ; try again."
        usermacros["@call"] = "question_check"
        # print("USERMACROS = ", usermacros)
        xmltree = exercise_xmltree(dbexercise.get_full_path())
        # NOTE MUST KEEP THIS IN CASE random is updated
        question_xmltree = question_xmltree_get(xmltree, question_key, usermacros)
        if not view_solution_permission:
            question_xmltree = hide_sensitive_tags_in_question(question_xmltree,qtype)
        bfdata = bf.data(question_xmltree)
        result["question"] = bfdata["question"]
        if not meta.feedback and new:
            result["correct"] = None
        comment = result.get('comment')
        if 'comment' in result and qtype == 'aibased' :
            result['error'] = result['comment']
        #print(f"RETURN RESULT {json.dumps(result, indent=4)}")
        return result
    else:
        return {"error": "No grading function for question type " + qtype}


def question_json_hook(safe_question, full_question, question_id, user_id, exercise_key, feedback,db=None):
    type = deep_get(safe_question, "@attr", "type")
    #logger.error(f"QUESTION_JSON_HOOK db={db} ")
    # precision =  deep_get(safe_question, "@attr", "precision")
    # print(f"PRECISION = {precision}" )
    if type is not None and type in question_json_hooks:
        safe_question = question_json_hooks[type](
            safe_question, full_question, question_id, user_id, exercise_key, feedback, db=db
        )
    return safe_question


def get_sensitive_tags():
    return sensitive_tags


def get_sensitive_attrs():
    return sensitive_attrs


def get_combined_usermacros(exercise, xml, user, before_date=None, db=None):
    assert db != None, "GET_COMBINED_USERMACROS DB=None"
    dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
    usermacros = {}
    question_keys = get_questionkeys_from_xml(xml)
    for question_key in question_keys:
        # question_key =   str( question['@attr']['key'] )
        #print(f"GET_COMBINED_USERMACROS_QUESTION_KEY_TO_TEST = {question_key}")
        usermacros[question_key] = {}
        try :
            dbquestion = Question.objects.using(db).get(exercise=dbexercise, question_key=question_key)
            n_attempts = get_number_of_attempts(dbquestion.pk, user.pk, before_date, db=db)
            n_correct = get_number_of_correct_attempts(dbquestion.pk, user.pk, before_date, db=db)
            usermacros[question_key]["@questionseed"] = get_seed( user.pk, dbexercise, dbquestion=dbquestion, before_date=before_date, db=db)
        except Exception as e :
            n_attempts = 0;
            n_correct = 0;
            usermacros[question_key]["@questionseed"] = get_seed( user.pk, dbexercise, None , before_date=before_date, db=db)
        username = str(user)
        #n_attempts = get_number_of_attempts(dbquestion.pk, user.pk, before_date, db=db)
        #n_correct = get_number_of_correct_attempts(dbquestion.pk, user.pk, before_date, db=db)
        usermacros[question_key]["@definedby"] = "get_combined_usermacros"
        usermacros[question_key]["@nattempts"] = str(n_attempts)
        usermacros[question_key]["@ncorrect"] = str(n_correct)
        usermacros[question_key]["@user"] = username
        usermacros[question_key]["@exercise_key"] = str(exercise)
        usermacros[question_key]["@question_key"] = question_key
        usermacros[question_key]["@exerciseseed"] = get_seed( user.pk, dbexercise, dbquestion=None, before_date=None, db=db)
        usermacros[question_key]["@userpk"] = str(user.pk)
    return usermacros


def get_usermacros(user, exercise_key, question_key=None, before_date=None, db=None):
    exercise_key =str( exercise_key) 
    assert db != None, "GET_USERMACROS DB=None"
    try :
        dbexercise = Exercise.objects.using(db).select_related("course").get(exercise_key=exercise_key)
        course = dbexercise.course
        exerciseassetpath = os.path.join(course.get_exercises_path(db), dbexercise.path)
        usermacros = {}
        username = str(user)
        usermacros["@definedby"] = "get_usermacros"
        usermacros['@is_staff'] = user.is_staff
        usermacros["@user"] = username
        usermacros["@exercise_key"] = str(exercise_key)
        usermacros["@exerciseseed"] = get_seed(user.pk, dbexercise=dbexercise, dbquestion=None, before_date=None, db=db)
        usermacros["@userpk"] = str(user.pk)
        usermacros["@exerciseassetpath"] = exerciseassetpath
        # studentassetpath = paths.get_student_asset_path(user, dbexercise)
        studentassetpath = _dispatch_asset_path(user, dbexercise)
        usermacros["@studentassetpath"] = studentassetpath
        if question_key:
            dbquestion = Question.objects.using(db).get(exercise=dbexercise, question_key=question_key)
            n_attempts = get_number_of_attempts(dbquestion.pk, user.pk, before_date, db=db)
            n_correct = get_number_of_correct_attempts(dbquestion.pk, user.pk, before_date=before_date, db=db)
            usermacros["@exerciseassetpath"] = exerciseassetpath
            usermacros["@nattempts"] = str(n_attempts)
            usermacros["@ncorrect"] = str(n_correct)
            usermacros["@question_key"] = dbquestion.question_key
            usermacros["@questionseed"] = get_seed(
                user.pk, dbexercise=dbexercise, dbquestion=dbquestion, before_date=before_date, db=db)
        return usermacros 
    except  Exception as e : 
        usermacros = {}
        username = str(user)
        exerciseassetpath = '.'
        usermacros["@definedby"] = "get_usermacros"
        usermacros['@is_staff'] = True
        usermacros["@user"] = 'super'
        usermacros["@exercise_key"] = str(exercise_key)
        usermacros["@exerciseseed"] = '123'
        usermacros["@userpk"] = 1
        usermacros["@exerciseassetpath"] = None
        studentassetpath = None
        usermacros["@studentassetpath"] = studentassetpath
        if question_key:
            n_attempts = 0
            n_correct =  0
            usermacros["@exerciseassetpath"] = exerciseassetpath
            usermacros["@nattempts"] = str(n_attempts)
            usermacros["@ncorrect"] = str(n_correct)
            usermacros["@question_key"] = question_key
            usermacros["@questionseed"] = '123'


    #print(f"GET_USERMACROS_OUT")
    return usermacros


def get_number_of_correct_attempts(question_id, user_id, before_date=None, db=None):
    """
    Number of attempts by user at question.
    Args:
        question_id: question primary key
        user_id: user primary key
    Returns:
        Number of attempts (int)
    """
    assert db != None, "GET_NUMBER_OF_CORRECT_ATTEMTPS DB=None"
    if before_date:
        answers = Answer.objects.using(db).filter(
            user__pk=user_id, question__pk=question_id, correct=True, date__lt=before_date
        )
    else:
        answers = Answer.objects.using(db).filter(user__pk=user_id, question__pk=question_id, correct=True)
    ncorrect = answers.count()
    return ncorrect


def get_seed(user_id, dbexercise=None, dbquestion=None, before_date=None, db=None):
    # print("GET_SEED")
    assert db != None, "GET_SEED DB=None"

    """
    Number of attempts by user at question.
    Args:
        question_id: question primary key
        user_id: user primary key
    Returns:
        Number of attempts (int)
    """
    # print("GET_SEED before_date=", before_date)
    exercise_key = dbexercise.exercise_key
    if dbquestion:
        question_id = dbquestion.pk
        random.seed(exercise_key + str(question_id))
    else:
        random.seed(exercise_key)
    r = random.randrange(123, 55321, 1)
    # print("QUESTION_ID = ", question_id)
    # uses_questionseed =  dbquestion.uses_questionseed()
    # dbexercise = Exercise.objects.get(exercise_key=exercise_key)
    # ret_seed = ''
    # if dbexercise.uses_exerciseseed() :
    ret_seed = str(r + user_id)
    if settings.REFRESH_SEED_ON_CORRECT_ANSWER and dbquestion:
        # dbquestion = Question.objects.using(db).get(pk=question_id)
        xmltree = exercise_xmltree(dbexercise.get_full_path(), {})
        uses = xmltree.xpath('/exercise/question[@key="{key}"]/macros'.format(key=question_id))
        uses_questionseed = not (uses == 0)
        if uses_questionseed:
            try:
                # answer = Answer.objects.using(db).get(user=user_id,question=dbquestion )
                # ret_seed = answer.questionseed
                # if ret_seed  == '' :
                ret_seed = str(
                    r + get_number_of_correct_attempts(dbquestion.id, user_id, before_date=before_date, db=db) + user_id
                )
            except Exception as e:
                logger.error(f"{type(e).__name__} GET_SEED THIS SHOULD BE DEAD CODE")
                # THIS SHOULD BE  DEAD CODE
                # ret_seed = str(r + get_number_of_correct_attempts(question_id, user_id,before_date=before_date,db=db) + user_id)
    # print(f"RET_SEED = {ret_seed}")
    return ret_seed


def hide_sensitive_tags_in_question(root,qtype):
    hide_tags = get_sensitive_tags()
    hide_attrs = get_sensitive_attrs()
    question_type = qtype
    tags_to_hide = hide_tags[question_type]
    for tag in tags_to_hide:
        nodes = root.findall(".//" + tag)
        for node in nodes:
            parent = node.getparent()
            parent.remove(node)
    attr_to_hide = hide_attrs[question_type]
    for attr in attr_to_hide:
        nodes = root.findall("./*/[@" + attr + "]")
        for node in nodes:
            node.attrib.pop(attr, None)
    return root
