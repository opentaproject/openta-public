# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import glob
import re
import json
import logging
import os
import pickle

import workqueue.util as workqueue
from exercises.models import Answer, Exercise, Question
from exercises.question import _question_check
from messages import embed_messages, error
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from utils import get_subdomain_and_db
from workqueue.exceptions import WorkQueueError
from workqueue.models import RegradeTask

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def regrade_dir(exercise_key):
    path = f"{settings.REGRADE_DIR}/{str(exercise_key)}"
    os.makedirs(path, exist_ok=True)
    return path


def regrade_results_async_pipeline(task, *args, **kwargs):  # o exercise_key, question_key):
    exercise_key = kwargs["exercise_key"]
    question_key = kwargs["question_key"]
    p = regrade_dir(exercise_key)
    resultsfile = p + "/results.pkl"
    old_regrade_exists = os.path.isfile(resultsfile)
    result = regrade_students_results(task, exercise_key, question_key)
    task.done = True
    task.status = "Done"
    task.progress = 100
    task.save(using='default')
    return result


@permission_required("exercises.view_statistics")
@api_view(["GET"])
def get_regrade_results_async(request, exercise, question_key=None):
    subdomain, db = get_subdomain_and_db( request);
    exercise_key = exercise
    p = regrade_dir(exercise)
    pklfile = p + "/regrade_items.pkl"
    resultsfile = p + "/results.pkl"
    subdomain = settings.DB_NAME
    print(f"PKL_FILE = {pklfile} resultsfile={resultsfile} subdomain={subdomain}")
    try:
        logger.error(f"TRY A")
        regrade_task = RegradeTask.objects.using('default').get(exercise_key=exercise_key)
        logger.error(f"TRY B")
        logger.error("REGRADE TASK RETURNED")
        task_id = regrade_task.task_id
        messages = embed_messages([error("Task %s is still incomplete" % str(task_id))])
        return Response({"task_id": task_id})
    except Exception as e:  # RegradeTask.DoesNotExist:
        logger.debug("REGRADE  TASK GET FAILED  %s %s" % (type(e).__name__, str(e)))
        try:
            dbexercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
        except Exercise.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            #logger.error("REGRADE TASK ENQUEUE STARTS")
            task_id = workqueue.enqueue_task(
                "regrade_results", regrade_results_async_pipeline, exercise_key=exercise_key, question_key=question_key
            )
            #logger.error("CREATE REGRADE TASK OBJECT")
            #logger.error("%s ;  %s ; %s ; %s " % (exercise_key, task_id, resultsfile, pklfile))
            regrade_task = RegradeTask.objects.using('default').create(
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
    logger.error(f"CLEANUP ORPANS  {exercise_key} NTASKS = {ntasks}")
    regrade_tasks = RegradeTask.objects.using('default').filter(exercise_key=exercise_key).all().order_by('-id');
    if regrade_tasks :
        i = 0
        for regrade_task in regrade_tasks:
            print(f"REGRADE+TASK = {regrade_task}")
            if i > 0 :
                try :
                    regrade_task.delete()
                except Exception as err :
                    print(f"REGRADE TASK DELETION OF {regrade_task} failed")
            i = i + 1
    else :
        print(f"NO REGRADE TASKS")
    #logger.error("DONE CLEANUP")


def tprint(s, exercise_key):
    logger.error(f"TPRINT")
    filn = regrade_dir(exercise_key) + "/log.txt"
    s = re.sub(r"\s+", " ", s)
    try:
        with open(filn, "a") as fp:
            fp.write("%s\n" % str(s))
    except Exception as e:
        logger.error(f"CANNOT WRITE {s} TO file {filn} ")
    return ""


def regrade_students_results(task, exercise_key, question_key):
    txt_merge = ""
    print("REGRADE_STUDENTS_RESULTS")
    if settings.MULTICOURSE:
        from backend.middleware import verify_or_create_database_connection
        settings.DB_NAME = task.subdomain
        settings.SUBDOMAIN = task.subdomain
        verify_or_create_database_connection(task.subdomain)
    db = settings.DB_NAME
    print(f"A1")
    cleanup_orphaned_tasks(exercise_key)
    print(f"A2")
    results = {}
    try:
        dbexercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
    except Exercise.DoesNotExist:
        return Response({}, status=status.HTTP_404_NOT_FOUND)
    if question_key == None:
        questions = Question.objects.using(db).filter(exercise=dbexercise)
    else:
        questions = Question.objects.using(db).filter(exercise=dbexercise, question_key=question_key)
    questions = questions.exclude(type='aibased')
    print(f"A3")
    all_answers = Answer.objects.using(db).filter(question__in=questions).exclude(answer__regex=r'^\s*\?').order_by("-date")
    all_answer_pks = set(list(all_answers.values_list("pk", flat=True)))
    print(f"ALL_ANSWSER_PKS = {all_answer_pks}")
    p = regrade_dir(exercise_key)
    showall = False
    print("A9")
    whitelist_file = p + "/" + "whitelist.txt"
    if os.path.exists(whitelist_file):
        allpks = []
        showall = True
        with open(whitelist_file) as fp:
            for line in fp:
                pk = int(line.split(" ")[0])
                allpks.append(pk)
        all_answers = all_answers.filter(pk__in=allpks)
        # print("LEN ALL_ANSWERS = ", len( all_answers) )
    elif os.path.exists(p):
        allpks = []
        filenames = glob.glob("%s/[0-9]*.??" % p)
        allpks = [(item.split("/")[-1]).split(".")[0] for item in filenames]
        if len(allpks) > 0:
            all_answers = all_answers.filter(pk__in=allpks)
            showall = True
    else:
        showall = False
    for question in questions:
        question_key = question.question_key
        results[question_key] = []
    n_answers = len(all_answers)
    txt = "OK"
    regrade_items = []
    try :
        regrade_task = RegradeTask.objects.using('default').get(exercise_key=exercise_key)
    except Exception as err :
        print(f"REGRADE TASK DOES NOT EXIST {str(err)}")
        return
    resultsfile = regrade_task.resultsfile
    pklfile = regrade_task.pklfile
    if regrade_task.status == "Waiting":
        regrade_task.status = "Running"
        regrade_task.save(using='default')
    old_regrade_exists = os.path.isfile(resultsfile)
    if old_regrade_exists:
        results = pickle.load(open(resultsfile, "rb"))
    n_answers = len(all_answers)
    n_same = 0
    n_different = 0
    print(f"B")
    for index, answer in enumerate(all_answers):
        if old_regrade_exists:
            task.status = "Old regrade exists"
            task.progress = 100
            task.save(using='default')
        else:
            if answer.question:
                try:
                    regrade_task = RegradeTask.objects.using('default').get(exercise_key=exercise_key)
                except Exception as e:
                    return {"error": "task no longer exists"}
                old_grader_response = ''
                if regrade_task.status == "Running":
                    try:
                        grader_response_string = answer.grader_response
                        grader_response = json.loads(answer.grader_response)
                        old_error = grader_response.get("error", "")
                        old_grader_response = grader_response

                    except:
                        grader_response = {"error": "Unidentfied", "correct": False}
                    user_agent = answer.user_agent
                    answer_data = answer.answer
                    old_correct = answer.correct
                    hijacked = False
                    view_solution_permission = True
                    dbuser = answer.user
                    question = answer.question
                    exercise_key = question.exercise.exercise_key
                    question_key = question.question_key
                    txt_list = (txt_merge[-180:]).splitlines()
                    txt_status = ""
                    if len(txt_list) > 0:
                        txt_status = "\n".join(txt_list[1:])
                    if task is not None:
                        task.status = f"Running\n{n_answers}=tot {n_same}=same {n_different}=changed\n{txt_status}"
                        task.progress = round(((index + 1) / n_answers) * 100)
                        task.save(using='default')
                check_error = False
                try:
                    (result, new_correct) = _question_check(
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
                    if not (old_correct == new_correct):
                        user = dbuser
                        student_answer = answer_data
                        correct_answer = answer
                        logger.error(f"USER = {user}")
                        logger.error(f"FOUND OLD_CORRECT = {old_correct}  NEW_CORRECT = {new_correct}")
                        logger.error(f"STUDENT_ANSWER = {student_answer}")
                        logger.error(f"CORRECT_ANSWER = {correct_answer}")
                        logger.error(f"OLD_GRADER_RESPONSE = {old_grader_response}")
                        logger.error(f"NEW GRADER_RESPONSE = {result}")
                        n_different = n_different + 1
                        grader_response = result
                        error = result.get("error", "")
                        txt = f"CHECK {str(dbuser)} {str(old_correct)}=>{str(new_correct)}  {answer_data} \n";
                        txtjson = json.dumps(
                            {
                                "question_key": question_key,
                                "user": str(dbuser),
                                "old_correct": str(old_correct),
                                "new_correct": str(new_correct),
                                "new_error_message": error,
                                "student_answer": str(answer_data),
                                "correct_answer": result.get("expression", ""),
                                "old_error_message": old_error,
                            }
                        )
                        tprint(txtjson, exercise_key)
                        txt_merge = txt_merge + txt
                    else:
                        n_same = n_same + 1
                        txt = ""
                    maxerror = result.get("maxerror", "N")
                    result_error = result.get("error", "")
                    answer_grader_response = json.dumps(result)
                    answer_correct = new_correct
                    error = (result.get("error", maxerror),)
                except Exception as e:
                    txt = "FAILURE: " + str(dbuser) + " " + answer_data + ": " + str(old_correct) + "\n"
                    #logger.error(f"{txt}  vars={vars(answer)}")
                    new_correct = None
                    check_error = True
                    result_error = " regrade_fail "
                    maxerror = ""
                    answer_grader_response = {"error": "unknown"}
                    answer_correct = new_correct
                    error = maxerror

                if showall or not (old_correct == new_correct) or check_error:
                    # print("RESULT = ", result )
                    if new_correct:
                        txt = "Correct: " + answer_data
                    else:
                        txt = "Incorrect: " + answer_data + result_error
                    answer.grader_response = answer_grader_response
                    answer.correct = answer_correct
                    # answer.save()
                    regrade_items.append(
                        dict(
                            pk=answer.pk,
                            grader_response=answer.grader_response,
                            correct=answer.correct,
                            error=error,
                            maxerror=maxerror,
                        )
                    )
                    results[question.question_key].append(
                        dict(
                            username=dbuser.username,
                            key=answer.pk,
                            date=answer.date,
                            answer=answer_data,
                            old=old_correct,
                            new=new_correct,
                            error=error,
                            maxerror=maxerror,
                        )
                    )
    print(f"C")
    regrade_task = RegradeTask.objects.using('default').get(exercise_key=exercise_key)
    if regrade_task.status == "Running":
        regrade_task.status = "Finished"
    #logger.error("RESULTS DONE ")
    regrade_task.save(using='default')
    #logger.error("RESULTS DONE REGRAD_TASK SAVE ")
    pklfile = regrade_task.pklfile
    #logger.error("RESULTS DONE PKL_FILE %s " % pklfile)
    resultsfile = regrade_task.resultsfile
    #logger.error("RSULTSFILE %s " % resultsfile)
    os.makedirs(os.path.dirname(pklfile), exist_ok=True)
    print(f"D")
    pickle.dump(regrade_items, open(pklfile, "wb"))
    print(f"F")
    pickle.dump(results, open(resultsfile, "wb"))
    print(f"G")
    return results


@permission_required("exercises.view_statistics")
@api_view(["GET"])
def accept_regrade(request, exercise, yesno="no"):
    # #logger.error("ACCEPT REGRADE")
    subdomain, db = get_subdomain_and_db(request)
    dbexercise = Exercise.objects.using(db).get(pk=exercise)
    exercise_key = str(dbexercise.exercise_key)
    # print(f"db={db} exercise_key={exercise_key}" )
    tasks = RegradeTask.objects.using('default').filter(exercise_key=exercise_key)
    # for task in tasks :
    #    print(f"TASK =  {task} exercise_key={task.exercise_key} ")
    # #logger.error("ACCEPT A %s" % yesno)
    try:
        regrade_task = RegradeTask.objects.using('default').get(exercise_key=exercise_key)
        if yesno == "yes":
            pklfile = regrade_task.pklfile
            regrade_items = pickle.load(open(pklfile, "rb"))
            for item in regrade_items:
                answer = Answer.objects.using(db).get(pk=item["pk"])
                # print("SAVE ANSWER", answer)
                answer.correct = item["correct"]
                answer.grader_response = item["grader_response"]
                answer.save()
            p = regrade_dir(exercise_key)
            try:
                filenames = glob.glob("%s/[0-9]*.??" % p)
                [os.remove(filn) for filn in filenames]
                os.remove("%s/errors" % p)
            except:
                pass
            regrade_task.delete()
        elif yesno == "no":
            regrade_task.delete()
        elif yesno == "cancel":
            regrade_task.status = "Cancelled"
            regrade_task.save(using='default')
        elif yesno == "reset":
            try:
                regrade_task.delete()
                cleanup_orphaned_tasks(exercise, 0)
            except Exception as e:
                logger.error(f"REGRADE TASK CLEANUP FAIL {str(e).__name__}")
        regrade_task.delete()
        cleanup_orphaned_tasks(exercise, 0)
    except Exception as e:
        logger.error("ERROR IN ACCEPT %s " % str(e))

    #logger.error(f"ACCEPT D and REDIRECT {yesno} path={request.get_full_path() }  ")
    return JsonResponse({"progress": "finished"})  # NOT USED IN FRONTEND!
