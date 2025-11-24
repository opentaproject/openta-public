# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import glob
import re
import json
import logging
import os
import pickle
import time 

import workqueue.util as workqueue
from exercises.models import Answer, Exercise, Question
from exercises.question import _question_check
from exercises.answer_class import answer_class
from messages import embed_messages, error
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from utils import get_subdomain_and_db
from workqueue.exceptions import WorkQueueError
from workqueue.models import AnalyzeTask

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def analyze_dir(exercise_key):
    path = f"{settings.REGRADE_DIR}/{str(exercise_key)}"
    os.makedirs(path, exist_ok=True)
    return path


def analyze_results_async_pipeline(task, *args, **kwargs):  # o exercise_key, question_key):
    exercise_key = kwargs["exercise_key"]
    question_key = kwargs["question_key"]
    p = analyze_dir(exercise_key)
    #print(f"TASK-SUBDOMAIN = {task.subdomain}")
    resultsfile = p + "/results.pkl"
    old_analyze_exists = os.path.isfile(resultsfile)
    result = analyze_students_results(task, exercise_key, question_key)
    task.done = True
    task.status = "Done"
    task.progress = 100
    task.save(using='default')
    return result


@permission_required("exercises.view_statistics")
@api_view(["GET"])
def get_analyze_results_async(request, exercise, question_key=None):
    subdomain, db = get_subdomain_and_db( request);
    exercise_key = exercise
    p = analyze_dir(exercise)
    pklfile = p + "/analyze_items.pkl"
    resultsfile = p + "/results.pkl"
    subdomain = settings.DB_NAME
    #print(f"PKL_FILE = {pklfile} resultsfile={resultsfile} subdomain={subdomain}")
    try:
        analyze_task = AnalyzeTask.objects.using('default').get(exercise_key=exercise_key)
        #logger.error("REGRADE TASK RETURNED")
        task_id = analyze_task.task_id
        messages = embed_messages([error("Task %s is still incomplete" % str(task_id))])
        return Response({"task_id": task_id})
    except Exception as e:  # AnalyzeTask.DoesNotExist:
        logger.debug("REGRADE  TASK GET FAILED  %s %s" % (type(e).__name__, str(e)))
        try:
            dbexercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
        except Exercise.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            #logger.error("REGRADE TASK ENQUEUE STARTS")
            task_id = workqueue.enqueue_task(
                "analyze_results", analyze_results_async_pipeline, exercise_key=exercise_key, question_key=question_key
            )
            #logger.error("CREATE REGRADE TASK OBJECT")
            #logger.error("%s ;  %s ; %s ; %s " % (exercise_key, task_id, resultsfile, pklfile))
            analyze_task = AnalyzeTask.objects.using('default').create(
                exercise_key=exercise_key,
                task_id=task_id,
                resultsfile=resultsfile,
                pklfile=pklfile,
                status="Waiting",
                subdomain=subdomain,
            )
            #logger.error("REGRADE TASK OPJECT CREATED")
            return Response({"task_id": task_id})
        except WorkQueueError as e:
            messages = embed_messages([error(str(e))])
            return Response(messages)


def cleanup_orphaned_tasks(exercise_key, ntasks=1):
    #logger.error("CLEANUP ORPANS %s " % exercise_key)
    analyze_tasks = AnalyzeTask.objects.using('default').filter(exercise_key=exercise_key)
    if len(analyze_tasks) > ntasks:
        i = 0
        for analyze_task in analyze_tasks:
            if i > 0:
                analyze_task.delete()
            i = i + 1
    #logger.error("DONE CLEANUP")


def tprint(s, exercise_key):
    logger.error(f"TPRINT")
    filn = analyze_dir(exercise_key) + "/log.txt"
    s = re.sub(r"\s+", " ", s)
    try:
        with open(filn, "a") as fp:
            fp.write("%s\n" % str(s))
    except Exception as e:
        logger.error(f"CANNOT WRITE {s} TO file {filn} ")
    return ""


def analyze_students_results(task, exercise_key, question_key):
    txt_merge = ""
    if settings.MULTICOURSE:
        from backend.middleware import verify_or_create_database_connection
        settings.DB_NAME = task.subdomain
        settings.SUBDOMAIN = task.subdomain
        verify_or_create_database_connection(task.subdomain)
    db = settings.DB_NAME
    cleanup_orphaned_tasks(exercise_key)
    results = {}
    try:
        dbexercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
    except Exercise.DoesNotExist:
        return Response({}, status=status.HTTP_404_NOT_FOUND)
        questions = Question.objects.using(db).filter(exercise=dbexercise, question_key=question_key)
    question =  Question.objects.using(db).get(exercise=dbexercise, question_key=question_key)
    all_answers = Answer.objects.using(db).filter(question=question)
    #for a in all_answers :
    #    print(f"A = {a.user}  {a.answer} {a.grader_response}")
    all_answer_pks = set(list(all_answers.values_list("pk", flat=True)))
    analyze_items = []
    analyze_task = AnalyzeTask.objects.using('default').get(exercise_key=exercise_key)
    #print(f"ALL_ANSWER_PKS = {all_answer_pks}")
    nanswers = len( all_answer_pks)
    if analyze_task.status == "Waiting":
        analyze_task.status = "Running"
        analyze_task.save(using='default')
    results = {}
    diff = []
    cum = {};
    kk = 0;
    for index, answer in enumerate(all_answers):
        try:
            analyze_task = AnalyzeTask.objects.using('default').get(exercise_key=exercise_key)
        except Exception as e:
            return {"error": "task no longer exists"}
        #print(f"ANALYZE_TASK = {analyze_task} {analyze_task.status }")
        if analyze_task.status == "Running":
            #print(f"RUNNING")
            try:
                grader_response_string = answer.grader_response
                grader_response = json.loads(answer.grader_response)
            except:
                grader_response = {"error": "Unidentfied", "correct": False}
            answer_data = answer.answer
            dbuser = answer.user
            question = answer.question
            exercise_key = question.exercise.exercise_key
            question_key = question.question_key
            txt_list = (txt_merge[-180:]).splitlines()
            txt_status = ""
            if task is not None:
                task.status = f"Running index={index} tot={nanswers}"
                task.progress = round(((index + 1) / nanswers) * 100)
                task.save(using='default')


            check_error = False
            hijacked = False
            view_solution_permission = True
            user_agent = answer.user_agent
            txtjson = json.dumps(
                {
                    "question_key": question_key,
                    "user": str(dbuser),
                    "student_answer": str(answer_data),
                }
            )
            #print(f"TXTJSON = {txtjson}")
            #old_grader_response = grader_response
            #grader_response = result
            r =  {'user' : str( dbuser) , 'data' : str( answer_data ) , 'grader_response' : grader_response }
            a  = str( answer_data )
            iscorrect = grader_response.get('correct',None)
            username = f"{dbuser}".split('@')[0]
            if iscorrect == None :
                cum['none'] = cum.get('none',0) + 1
            elif iscorrect :
                cum['correct'] = cum.get('correct',0) + 1
                #print(f" CORRECT  ATTEMPT = {str( answer_data)} ")
            else :
                cum['incorrect'] = cum.get('incorrect',0) + 1
                warning = grader_response.get('warning','')
                #print(f"WARNING = {warning}")
                if warning == ''  or warning in ['Units OK']  or 'rational' in warning or 'info' in warning:
                    c  = answer_class( hijacked, view_solution_permission, dbuser, user_agent, exercise_key, question_key, answer_data, answer, db,)
                    try : 
                        warning = grader_response.get('warning','')
                        qtype = grader_response.get('type','notype');
                        results[kk] =  {'c' : f"{c}", 'user' : str( dbuser) , 'qtype' : qtype,  'answer_data' : str( answer_data) , 'data' : f"{qtype}  : "  +   str( answer_data ) ,  'grader_response' : grader_response }
                        kk = kk + 1 
                    except :
                        pass

            txt_merge = txt_merge + txtjson
    #print(f"CUM = {cum}")
    analyze_task = AnalyzeTask.objects.using('default').get(exercise_key=exercise_key)
    if analyze_task.status == "Running":
        analyze_task.status = "Finished"
    analyze_task.save(using='default')
    resultsfile = analyze_task.resultsfile
    resultlist = [ results[k]  for k in results ]
    resultlist.sort( key=lambda x:  x.get("c",-299)) 
    rnew = {};
    k = 0;
    rnew['000'] = {'c' : "99" , 'data' : f"{cum}"}
    cold = -1000;
    acc = 0;
    n = 1;
    mincount = 1000
    ad = ''
    mold = resultlist.pop();
    mold['count'] = 1;
    admin = mold['answer_data']
    for m in resultlist:
        #print(f"M = {m}")
        cnew = m['c']
        ind = str( k ).zfill(3) 
        m['count'] = n # f"[{n}] " 
        if float( cnew ) - float( cold ) > 1.e-5 :
            rnew[ ind ] =  mold;
            k = k + 1;
            ind = str( k ).zfill(3) 
            n = 0;
            mold = m
        n = n + 1;
        cold = cnew
        m['count'] = n
        if len( mold['answer_data']) < len( m['answer_data'] ) :
            m['answer_data'] = mold['answer_data'] 
        mold = m
    rnew[ ind ] =  mold ;
    rr = list( rnew.values() )
    rr.sort( key=lambda x: x['count'] , reverse=True)
    n = 1
    rp = {};
    rp['000'] = {'c' : "99" , 'answer_data' : f"{cum}"}
    for m in rr :
        ind = str(n).zfill(3);
        rp[ind] = m;
        n = n + 1;

    return rp


@permission_required("exercises.view_statistics")
@api_view(["GET"])
def accept_analyze(request, exercise, yesno="no"):
    # #logger.error("ACCEPT REGRADE")
    subdomain, db = get_subdomain_and_db(request)
    dbexercise = Exercise.objects.using(db).get(pk=exercise)
    exercise_key = str(dbexercise.exercise_key)
    # print(f"db={db} exercise_key={exercise_key}" )
    tasks = AnalyzeTask.objects.using('default').filter(exercise_key=exercise_key)
    # for task in tasks :
    #    print(f"TASK =  {task} exercise_key={task.exercise_key} ")
    # #logger.error("ACCEPT A %s" % yesno)
    try:
        analyze_task = AnalyzeTask.objects.using('default').get(exercise_key=exercise_key)
        if yesno == "yes":
            pklfile = analyze_task.pklfile
            analyze_items = pickle.load(open(pklfile, "rb"))
            for item in analyze_items:
                answer = Answer.objects.using(db).get(pk=item["pk"])
                # print("SAVE ANSWER", answer)
                answer.correct = item["correct"]
                answer.grader_response = item["grader_response"]
                answer.save()
            p = analyze_dir(exercise_key)
            try:
                filenames = glob.glob("%s/[0-9]*.??" % p)
                [os.remove(filn) for filn in filenames]
                os.remove("%s/errors" % p)
            except:
                pass
            analyze_task.delete()
        elif yesno == "no":
            analyze_task.delete()
        elif yesno == "cancel":
            analyze_task.status = "Cancelled"
            analyze_task.save(using='default')
        elif yesno == "reset":
            try:
                analyze_task.delete()
                cleanup_orphaned_tasks(exercise, 0)
            except Exception as e:
                logger.error(f"REGRADE TASK CLEANUP FAIL {str(e).__name__}")
        analyze_task.delete()
        cleanup_orphaned_tasks(exercise, 0)
    except Exception as e:
        logger.error("ERROR IN ACCEPT %s " % str(e))

    #logger.error(f"ACCEPT D and REDIRECT {yesno} path={request.get_full_path() }  ")
    return JsonResponse({"progress": "finished"})  # NOT USED IN FRONTEND!
