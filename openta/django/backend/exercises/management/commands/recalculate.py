# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import glob
import re
import time
import sys, traceback
import ast
from backend.middleware import verify_or_create_database_connection, create_connection
from exercises.question import _question_check, get_usermacros
from exercises.models import Exercise, Answer, Question
from django.contrib.auth.models import User
from course.models import Course
from django.conf import settings
import os
import json
import pickle
from users.models import OpenTAUser
import exercises
import aggregation as ag
import logging
from exercises.parsing import (
    question_json_get,
    exercise_xmltree,
    question_xmltree_get,
    global_and_question_xmltree_get,
    get_questionkeys_from_xml,
)

from random import shuffle, seed


from course.models import Course

logger = logging.getLogger(__name__)

BIN_LENGTH = settings.BIN_LENGTH
logdir = "tmp"


class Command(BaseCommand):

    help = "recalculate answers"

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("--whitelist", type=str, help="List of exercises to recalculate")
        parser.add_argument("--accept", type=str, help="Choose to accept results in results.pkl")
        parser.add_argument("--exercise", default=None, type=str, help="filter by exercise")
        parser.add_argument("--suffix", type=str, default=None, help="filter by suffix")
        parser.add_argument("--answerpks", type=str, default="", help="filter by answerpks")
        parser.add_argument("--subdomain",  dest="subdomain" , type=str, default="", help="filter by answerpks")

    def handle(self, *args, **kwargs):
        #print(f"A")
        subdomain = kwargs.get("subdomain")
        verify_or_create_database_connection(subdomain)
        settings.DB_NAME = subdomain
        settings.SUBDOMAIN = subdomain
        create_connection(subdomain)
        verify_or_create_database_connection( subdomain )
        results_directory = f"/tmp/{settings.SUBDOMAIN}/regrade"
        #print(f"B")
        answers = Answer.objects.using(settings.SUBDOMAIN).all()
        nobjects = answers.count()
        whitelist_filename = kwargs.get("whitelist", None)
        # print("KWARGS = ", kwargs)
        accept = kwargs.get("accept", "False")
        accept = 'rue' in accept;
        exercise = kwargs.get("exercise")
        suffix = kwargs.get("suffix")
        answerpks = []
        if not exercise == None:
            # print("EXERCISE SPECIFIED " , exercise)
            answerpks = []
            for filn in os.listdir(os.path.join(results_directory, exercise)):
                suffix = kwargs.get("suffix", ".yn")
                if suffix in filn:
                    pk = filn.split(".")[0]
                    answerpks.append(pk)
        if (not kwargs.get("answerpks") == "") and len(answerpks) == 0:
            answerpks = (kwargs.get("answerpks")).split(",")
        #print(f"WHITELIST FILENAME = {whitelist_filename}")
        if whitelist_filename:
            whitelist = []
            with open(whitelist_filename) as fp:
                for line in fp:
                    questions = list(Question.objects.using(settings.SUBDOMAIN).filter(exercise__exercise_key=line.strip()).exclude(type='aibased') )
                    whitelist = whitelist + questions
            # print("whitelist = ", whitelist )
            answers = list(answers.filter(question__in=whitelist))
        #print("answerpkks = ", answerpks)
        if not answerpks == []:
            answers = list(answers.filter(pk__in=answerpks).exclude(answer__regex=r'^\s*\?') )
        else:
            answers = get_new_answers()
        print("NUMBER OF  ANSWERS = ", len( answers ) )
        #print("ACCEPT = ", accept )
        #print("ANSWERS = ", answers)
        answers = list(answers)
        redo(answers, accept)


def dotask(npks=20, seed=None, accept_new=False, course_key=None):
    print("DOTASK ACCEPT_NEW = ", accept_new)
    answers = get_new_answers(npks, seed, course_key)
    return redo(answers, accept_new)


def get_new_answers(npks=1000, iseed=None, course_key=None):
    donepks = []
    if course_key:
        course = Course.objects.using(settings.SUBDOMAIN).get(course_key=course_key)
        exercises = Exercise.objects.using(settings.SUBDOMAIN).filter(course=course)
        questions = Question.objects.using(settings.SUBDOMAIN).filter(exercise__in=exercises).exclude(type='aibased')
        answers = Answer.objects.using(settings.SUBDOMAIN).filter(question__in=questions).exclude(answer__regex=r'^\s*\?') 
    else:
        answers = Answer.objects.using(settings.SUBDOMAIN).exclude(answer__regex=r'^\s*\?').all()
    if os.path.exists(f"/tmp/{settings.SUBDOMAIN}/whitelist.txt"):
        allpks = []
        with open(f"/tmp/{settings.SUBDOMAIN}/whitelist.txt") as fp:
            for line in fp:
                pk = int(line.split(" ")[0])
                allpks.append(pk)
        answers = answers.filter(pk__in=allpks)
    print("LEN ANSWERS = ", len(answers))
    allpks = [item.pk for item in answers]
    if os.path.exists(f"/tmp/{settings.SUBDOMAIN}/recalculated.txt"):
        with open(f"/tmp/{settings.SUBDOMAIN}/recalculated.txt") as fp:
            for line in fp:
                donepks.append(int(line.rstrip("\n")))
    else:
        donepks = []
    # if iseed :
    #    allpks = list( filter( lambda x : x % 8 == iseed , allpks ) )
    if os.path.exists(f"/{logdir}/{settings.SUBDOMAIN}/nok.txt") :
        ffp = open(f"/{logdir}/{settings.SUBDOMAIN}/nok.txt","r")
        allpks = [];
        for line in ffp:
            allpks.append(line.strip());
        ffp.close();
        allpks = list( set( allpks) );
        print(f"ALLPKS = {allpks}")
    answerpks = list((set(allpks)).difference(set(donepks)))
    #print("ANSWERPKS = ", len( answerpks) )
    if len(answerpks) == 0:
        return []
    if seed:
        seed(iseed)
    # if  not os.path.exists("/tmp/whitelist.txt") :
    #    shuffle( answerpks )
    answerpks = answerpks[0:max( npks, len( answerpks) ) ]
    answers = list(answers.filter(pk__in=answerpks))
    #print(f"LENGTH OF ANSWERS { len(answers)}")
    return answers


def redo(answers, accept=False):
    accept_new = accept
    #print(f"ACCEPT_NEW={accept_new}")
    #print("RED ACCEPT_NEW = ", accept_new)
    db = settings.SUBDOMAIN
    if answers == []:
        return None
    ind = 0
    n = 0
    results_directory = f"/tmp/{settings.SUBDOMAIN}/regrade"
    os.makedirs(f"/tmp/{settings.SUBDOMAIN}",exist_ok=True)
    if os.path.exists( f"/tmp/{settings.SUBDOMAIN}/recalculated.txt" ) :
        fp = open(f"/tmp/{settings.SUBDOMAIN}/recalculated.txt", "a")
    else :
        fp = open(f"/tmp/{settings.SUBDOMAIN}/recalculated.txt", "w")
    for answer in answers:
        fp.write("%s\n" % str(answer.pk))
    fp.flush()
    fp.close()
    done_answers = []
    for answer in answers:
        print(f"NEXT = {answer}")
        ind = ind + 1
        if not answer.question == None and not answer.question.qtype() == 'pythonic' and not answer == None:  # not str( answer.pk )  in done_answers:
            error_message = None
            did = True
            time_beg = time.time()
            if True :
                s1 = "n"
                s2 = "n"
                if answer.question:
                    exercise = answer.question.exercise
                    time_beg = time.time()
                    question_key = answer.question.question_key
                    user = answer.user
                    course = exercise.course
                    try:
                        grader_response = json.loads(answer.grader_response, strict=False)
                    except:
                        # grader_response_string =  answer.grader_response
                        # grader_response_string =  grader_response_string.replace('true' , 'True') ;
                        # grader_response_string =  grader_response_string.replace('false' , 'False') ;
                        # grader_response_string =  grader_response_string.replace('true' , 'True') ;
                        # grader_response_string =  grader_response_string.replace('false' , 'False') ;
                        # grader_response_string =  grader_response_string.replace('\'','\"' )
                        # try :
                        #    grader_response = eval(grader_response_string)
                        # except:
                        grader_response = {"error": "Unidentfied error in %s " % answer.pk, "correct": False}
                    user_agent = answer.user_agent
                    answer_data = answer.answer
                    try:
                        old_correct = answer.correct
                    except:
                        old_correct = grader_response.get("correct", False)
                    hijacked = False
                    view_solution_permission = True
                    dbuser = answer.user
                    question = answer.question
                    question_type = question.type
                    exercise_key = question.exercise.exercise_key
                    db = settings.SUBDOMAIN
                    usermacros = get_usermacros(user, exercise_key, question_key, None,  db)
                    question_key = question.question_key
                    # old_correct = grader_response.get('correct', False)
                    full_path = exercise.get_full_path()
                    name = exercise.name.replace("\n", "")
                    print(f"DO USER={dbuser} ekey={exercise_key} qkey={question_key} answer_data={answer_data} answer={answer}")
                    if os.path.exists(full_path):

                        # print("RECALCULATE.PY QUESITON CHECK ARGUMENTS")
                        # print("ANSWER_DATA", answer_data)
                        # print("ANSWER", answer )
                        (result, new_correct ) = _question_check(
                            hijacked,
                            view_solution_permission,
                            dbuser,
                            user_agent,
                            exercise_key,
                            question_key,
                            answer_data,
                            answer,
                            db,
                        )
                        did = True
                        if "error" in result:
                            error_log_directory = os.path.join(results_directory, exercise.exercise_key)
                            os.makedirs(error_log_directory,exist_ok=True)
                            fp = open(os.path.join(error_log_directory, "errors"), "a")
                            fp.write(
                                '{%s : { user: %s,name: %s ,type: %s,answer:  "%s",old_correct: %s, new_correct %s  },  error : "%s"} }\n'
                                % (
                                    answer.pk,
                                    dbuser,
                                    name,
                                    question_type,
                                    answer_data,
                                    old_correct,
                                    new_correct,
                                    result,
                                )
                            )
                            fp.close
                        if accept_new  :
                            pk = answer.pk
                            print("%s %s  %s SAVE " % (str(pk), str(exercise_key), str(question_key)))
                            answer.correct = new_correct
                            answer.grader_response = json.dumps(result)
                            answer.save()
                        else:
                            pass
                    else:
                        answer.delete()
                        # print("FILE ", full_path ," HAS BEEN REMOVED")
                pass
                # if (ind % interval) == 0:
                #    print("\nX\n", end='', flush=True)
                #    error_message = None
            #except Exception as e:
            #    did = False
            #    print("UNCAUGHT EXCEPTION IN SCRIPT %s %s " % (type(e), str(e)))
            #    # print("JSON = ", grader_response_string)
            #    # print("keys = %s ", exercise_key,  question_key)
            #    # print("ANSWER_DATA ", answer.answer)
            #    # print("PATH = ",  exercise.get_full_path)
            #    error_message = str(e)
            if did:
                try :  # ( not  (old_correct == new_correct ) ) :
                    error_log_directory = os.path.join(results_directory, exercise.exercise_key)
                    s = "1";
                    os.makedirs(error_log_directory,exist_ok=True)
                    summary = dict(
                        pk=answer.pk,
                        user=dbuser.username,
                        name=name,
                        answer=answer_data,
                        old_correct=old_correct,
                        new_correct=new_correct,
                        correct=new_correct,
                        grader_response=result,
                    )
                    s1 = "y"
                    s2 = "n"
                    s = "2";
                    if True :
                        s1 = "y" if old_correct else "n"
                        s2 = "y" if new_correct else "n"
                        txt = json.dumps(summary) + "\n"
                        s = "3"
                        answer_data = re.sub(r"\s+", " ", answer_data)
                        tdiff = int((time.time() - time_beg) * 1000)
                        s = "4"
                        if not (old_correct == new_correct) and (not new_correct):
                            s = "5"
                            print(
                                "%s NOK %s%s " % (str(answer.pk), s1, s2),
                                user,
                                ind,
                                tdiff,
                                old_correct,
                                new_correct,
                                "[",
                                name,
                                question_key,
                                "]",
                                answer_data,
                                result.get("error", ""),
                                result.get("warning",""),
                            )
                            s = "6"
                            ffp = open(f"/{logdir}/{settings.SUBDOMAIN}/nok.txt","a+")
                            ffp.write(str( answer.pk) + "\n" )
                            ffp.close()
                            s = "7"

                        else:
                            s = "8"
                            print("%s OK %s%s " % (str(answer.pk), s1, s2), ind, tdiff, name, question_key, answer_data)
                        s = "9"
                        fils = glob.glob(os.path.join(error_log_directory, str(answer.pk)) + ".*")
                        for fil in fils:
                            if os.path.isfile(fil):
                                os.unlink(fil)
                        s = "10"
                        if not (s1 == s2):
                            fp = open(os.path.join(error_log_directory, str(answer.pk)) + "." + s1 + s2, "a")
                            fp.write(txt)
                            fp.close()
                        #    if ( old_correct ==  new_correct ) :
                        #        answer.grader_response = json.dumps(result)
                        #        answer.save()
                    else:
                        did = False
                    n = n + 1
                except Exception as err  :
                   print(f"ERR {s} = {str(err)}")
                   done_answers.append(str(answer.pk))
                   print(ind, "NOK -error %s %s%s " % (s,s1,s2), answer.pk )
                   ffp = open(f"/{logdir}/{settings.SUBDOMAIN}/nok.txt","a+")
                   ffp.write(str( answer.pk)  + "\n")
                   ffp.close()

            else:
                tdiff = int((time.time() - time_beg) * 1000)
                try:
                    print(
                        "%s NOK %s%s" % (str(answer.pk), s1, s2),
                        ind,
                        tdiff,
                        old_correct,
                        new_correct,
                        name,
                        question_key,
                        answer_data,
                        "RESULT FAILED",
                    )
                    ffp = open(f"/{logdir}/{settings.SUBDOMAIN}/nok.txt","a+")
                    ffp.write(str( answer.pk)  + "\n")
                    ffp.close()

                except:
                    print("%s NOK FAILED COMPLETETLY " % (str(answer.pk)))
                    ffp = open(f"/{logdir}/{settings.SUBDOMAIN}/nok.txt","a+")
                    ffp.write(str( answer.pk) + "\n" )
                    ffp.close()

            # if ind % 100 == 0 :
            #    fp = open(pklfile,'wb')
            #    pickle.dump( done_answers, fp)
            #    fp.close()

        else:
            print("OLD %s " % str(answer.pk))
    return answers


def accept_changes(accept):
    if accept:
        subdirs = os.listdir(error_log_directory)
        ind = 0
        accept_list = []
        for subdir in subdirs:
            # if ind > 4 :
            #    break
            bigstring = ""
            if os.path.isdir(os.path.join(error_log_directory, subdir)):
                # print("SUBDIR = ", subdir)
                for pk in os.listdir(os.path.join(error_log_directory, subdir)):
                    if re.match(r"[0-9]+\.(y|n)(y|n)$", pk):
                        # print("pk = ", pk)
                        fullpath = os.path.join(error_log_directory, subdir, pk)
                        with open(os.path.join(error_log_directory, subdir, pk)) as fp:
                            for line in fp:
                                try:
                                    js = json.loads(line)
                                    js["path"] = fullpath
                                    # print("JS = ", js )
                                except:
                                    print("ERROR", line)
                                    exit()
                            accept_list.append(js)
                            ind = ind + 1
                # print("bigstring = ", bigstring)
                # lines = bigstring.split("\n")
        print(" FILES HANDLED = ", ind)
        total = ind
        ind = 0
        for new in accept_list:
            ind = ind + 1
            pk = new.get("pk")
            old = Answer.objects.using(settings.SUBDOMAIN).get(pk=pk)
            correct = new.get("correct")
            fullpath = new.get("path")
            grader_response = new.get("grader_response")
            try:
                # print("SAVE", pk, old.correct, correct, grader_response, fullpath)
                old.correct = correct
                old.grader_response = grader_response
                old.save()
                os.rename(fullpath, fullpath + ".done")
            except:
                print("ERROR ", pk, old.correct, correct, grader_response, fullpath)
            if (ind % 100) == 0:
                print("DONE ", ind, " of ", total)

        print("NUMBER OF UPDATES", ind)
