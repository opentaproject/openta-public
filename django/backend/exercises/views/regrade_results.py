from rest_framework import status
from rest_framework.decorators import api_view
from django.conf import settings
from django.shortcuts import redirect
from django.conf import settings
from exercises.models import Exercise, Question, Answer
from exercises.question import question_check, _question_check
from utils import response_from_messages
from django.contrib.auth.models import User
import glob
import json
from rest_framework.decorators import api_view
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from django.http import HttpResponse
from aggregation.models import Aggregation,  STATISTICS_CACHE_TIMEOUT
from workqueue.models import RegradeTask
import workqueue.util as workqueue
from messages import error, embed_messages
import shutil
from workqueue.exceptions import WorkQueueError
import os
import rq
import pickle
import logging
logger = logging.getLogger(__name__)



def regrade_results_async_pipeline(task, exercise_key):
    logger.info("PIPELINE STARRTED TASK = %s " %  task )
    p = '/tmp/regrade/%s' % exercise_key
    resultsfile = p + '/results.pkl'
    old_regrade_exists = os.path.isfile(resultsfile)
    logger.info("START REGRADE_STUDENTS_RESULTS %s " % exercise_key)
    result = regrade_students_results(task, exercise_key)
    logger.info("REGRADE_STUDENTS_RESULTS RETURNED")
    logger.info("REGRADE_STUDENTS_RESULTS RETURNED RESULT = %s " % result )
    task.done = True
    task.status = "Done"
    task.progress = 100
    task.save()
    logger.info("REGRADE_STUDENTS_RESULTS TASK SAVED %s " % task )
    logger.info("REGRADE_STUDENTS_RESULTS TASK SAVED %s " % task.done )
    logger.info("REGRADE_STUDENTS_RESULTS TASK SAVED %s " % task.status )
    logger.info("REGRADE_STUDENTS_RESULTS TASK SAVED %s " % task.progress )
    logger.info("REGRADE_STUDENTS_RESULTS TASK RETURN RESULT %s " % result )
    return result


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_regrade_results_async(request, exercise):
    exercise_key = exercise
    p = '/tmp/regrade/%s' % exercise
    pklfile = p + '/regrade_items.pkl'
    resultsfile = p + '/results.pkl'
    subdomain = settings.DB_NAME
    logger.info("EXERCISE IN GET_REGRADE_RESULTS ASYNC = %s " % exercise)
    try:
        regrade_task = RegradeTask.objects.get(exercise_key=exercise_key)
        logger.info("REGRADE TASK RETURNED" )
        task_id = regrade_task.task_id
        messages = embed_messages([error('Task %s is still incomplete' % str(task_id))])
        return Response({'task_id': task_id})
    except Exception as e : # RegradeTask.DoesNotExist:
        logger.debug("REGRADE  TASK GET FAILED  %s %s" % ( type(e).__name__ , str(e) ) )
        try:
            dbexercise = Exercise.objects.get(exercise_key=exercise_key)
        except Exercise.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            logger.info("REGRADE TASK ENQUEUE STARTS")
            task_id = workqueue.enqueue_task(
                "regrade_results", regrade_results_async_pipeline, exercise_key=exercise_key
            )
            logger.info("CREATE REGRADE TASK OBJECT")
            logger.info("%s ;  %s ; %s ; %s " % ( exercise_key , task_id, resultsfile, pklfile) )
            regrade_task = RegradeTask.objects.create(
                exercise_key=exercise_key,
                task_id=task_id,
                resultsfile=resultsfile,
                pklfile=pklfile,
                status='Waiting',
                subdomain=subdomain
                )
            logger.info("REGRADE TASK OPJECT CREATED")
            return Response({'task_id': task_id})
        except WorkQueueError as e:
            messages = embed_messages([error(str(e))])
            return Response(messages)


def cleanup_orphaned_tasks(exercise_key,ntasks=1):
    logger.info("CLEANUP ORPANS %s " % exercise_key)
    regrade_tasks = RegradeTask.objects.filter(exercise_key=exercise_key)
    if len(regrade_tasks) > ntasks:
        i = 0
        for regrade_task in regrade_tasks:
            if i > 0:
                regrade_task.delete()
            i = i + 1
    logger.info("DONE CLEANUP")


def tprint(s) :
    try:
        with open( "/tmp/regrade_log.txt","a") as fp:
            fp.write("%s\n" % str(s) )
    except: 
        pass
    return ''


def regrade_students_results(task, exercise_key):
    logger.info("TASK = %s " % task.subdomain)
    settings.DB_NAME = task.subdomain
    logger.info("REGRADE_STUDENTS_RESULTS CALLED exercise_key = %s " % exercise_key)
    cleanup_orphaned_tasks(exercise_key)
    results = {}
    logger.info("REGRADE STUDENTS_RESULTS DB_NAME = %s " % settings.DB_NAME)
    try:
        dbexercise = Exercise.objects.get(exercise_key=exercise_key)
        logger.info("REGRADE STUDENTS_RESULTS DBEXERCISE %s " % dbexercise)
    except Exercise.DoesNotExist:
        logger.info("REGRADE STUDENTS_RESULTS DBEXERCISE FAILED  %s " % settings.DB_NAME)
        return Response({}, status=status.HTTP_404_NOT_FOUND)
    questions = Question.objects.filter(exercise=dbexercise)

    logger.info("QUESTIONS = %s " % str(  questions) )
    #WHY DOES THIS MISS SOME! 
    all_answers = Answer.objects.filter(question__in=questions).order_by('-date')
    all_answer_pks =  set( list( all_answers.values_list('pk',flat=True) )  )
    logger.info("ALL_FILTERED = %s  " % all_answer_pks.intersection( set([3021,3024,3025,2677])))
    #all_answers = Answer.objects.all()
    p = '/tmp/regrade/%s' % exercise_key
    showall = False
    if  os.path.exists("/tmp/whitelist.txt") :
        allpks = []
        showall = True
        with open("/tmp/whitelist.txt") as fp:
                for line in fp:
                    pk = int( line.split(' ')[0] )
                    print("PK = ", pk )
                    allpks.append(pk)
        print("ALLPKS = ", allpks )
        all_answers = all_answers.filter(pk__in=allpks)
        print("LEN ALL_ANSWERS = ", len( all_answers) )
    elif os.path.exists(p) :
        allpks = []
        filenames = glob.glob('%s/[0-9]*.??' % p)
        allpks = [ (item.split('/')[-1] ).split('.')[0] for item in filenames ]
        logger.info("ALLPKS TO DO = %s " % allpks)
        if len(allpks) > 0 :
            all_answers = all_answers.filter(pk__in=allpks)
            showall = True
    else:
        logger.info("PATH %s does not exist " % p )
        showall = False
    for question in questions:
        question_key = question.question_key
        results[question_key] = []
    n_answers = len(all_answers)
    logger.info("n_answerfs = %s " % n_answers)
    txt = "OK"
    regrade_items = []
    regrade_task = RegradeTask.objects.get(exercise_key=exercise_key)
    resultsfile = regrade_task.resultsfile
    pklfile = regrade_task.pklfile
    if regrade_task.status == 'Waiting':
        regrade_task.status = 'Running'
        regrade_task.save()
    old_regrade_exists = os.path.isfile(resultsfile)
    if old_regrade_exists:
        results = pickle.load(open(resultsfile, 'rb'))
    logger.info("ALL_ANSWERS = %s " % len(all_answers) )
    for index, answer in enumerate(all_answers):
        if old_regrade_exists:
            task.status = "Old regrade exists"
            task.progress = 100
            task.save
        else:
            #if index > 3 :
            #    break
            if answer.question :
                tprint("CHECK %s " % answer.question)
                regrade_task = RegradeTask.objects.get(exercise_key=exercise_key)
                tprint("REGRADE TASK STATUS =  %s " % regrade_task.status)
                if regrade_task.status == 'Running':
                    try:
                        grader_response_string =  answer.grader_response
                        grader_response = json.loads( answer.grader_response) 
                        tprint("GRADER_RESPONSE = %s " % str( grader_response) )

                    except:
                        tprint("GRADER_RESPONSE_STRING ERROR  " )
                        grader_response = {"error" : "Unidentfied" , "correct" : False}
                    user_agent = answer.user_agent
                    answer_data = answer.answer
                    old_correct = answer.correct
                    hijacked = False
                    view_solution_permission = True
                    dbuser = answer.user
                    question = answer.question
                    exercise_key = question.exercise.exercise_key
                    question_key = question.question_key
                    #old_correct = grader_response.get('correct', False)
                    print("ANSWER_DATE = ", answer.date)
                    if task is not None:
                        task.status = (task.status + txt)[-245:]
                        task.progress = round(((index + 1) / n_answers) * 100)
                        task.save()
                    if True : # or 'stellan.ostlund@physics.gu.se'  == dbuser.username :
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
                            )
                            if True or not (old_correct == new_correct):
                               print("DID ", index, answer.pk)
                               txt = ( str(dbuser) + ' ' + answer_data + ': ' + str(old_correct) + ' => ' + str(new_correct) + "\n")
                               print("TXT ", txt)
                            else :
                                pass 
                            if showall or not ( old_correct == new_correct ):
                                print("RESULT = ", result )
                                maxerror = result.get('maxerror','N')
                                if new_correct:
                                    txt = "Correct: " + answer_data
                                else:
                                    txt = "Incorrect: " + answer_data + result.get('error','')
                                answer.grader_response = json.dumps(result)
                                answer.correct = new_correct
                                # answer.save()
                                regrade_items.append(
                                    dict(
                                        pk=answer.pk,
                                        grader_response=answer.grader_response,
                                        correct=answer.correct,
                                        error=result.get('maxerror','Z'),
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
                                        error=result.get('error',maxerror),
                                        maxerror=maxerror
                                    )
                                )
                        except:
                                pass
    regrade_task = RegradeTask.objects.get(exercise_key=exercise_key)
    if regrade_task.status == 'Running':
        regrade_task.status = 'Finished'
    logger.info("RESULTS DONE ")
    regrade_task.save()
    logger.info("RESULTS DONE REGRAD_TASK SAVE ")
    pklfile = regrade_task.pklfile
    logger.info("RESULTS DONE PKL_FILE %s " % pklfile  )
    resultsfile = regrade_task.resultsfile
    logger.info("RSULTSFILE %s " % resultsfile)
    os.makedirs(os.path.dirname(pklfile), exist_ok=True)
    pickle.dump(regrade_items, open(pklfile, 'wb'))
    pickle.dump(results, open(resultsfile, 'wb'))
    return results


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def accept_regrade(request, exercise, yesno='no'):
    logger.info("ACCEPT REGRADE")
    dbexercise = Exercise.objects.get(pk=exercise)
    exercise_key = dbexercise.exercise_key
    regrade_task = RegradeTask.objects.get(exercise_key=exercise_key)
    logger.info("ACCEPT A %s" % yesno)
    try:
        if yesno == 'yes':
            pklfile = regrade_task.pklfile
            regrade_items = pickle.load(open(pklfile, 'rb'))
            for item in regrade_items:
                answer = Answer.objects.get(pk=item['pk'])
                print("SAVE ANSWER", answer)
                answer.correct = item['correct']
                answer.grader_response = item['grader_response']
                answer.save()
            p = '/tmp/regrade/%s' % exercise
            try :
                filenames = glob.glob('%s/[0-9]*.??' % p)
                [ os.remove(filn) for filn in filenames ]
                os.remove("%s/errors" % p )
            except:
                pass
            regrade_task.delete()
        elif yesno == 'no':
            regrade_task.delete()
        elif yesno == 'cancel':
            regrade_task.status = 'Cancelled'
            regrade_task.save()
        elif yesno == 'reset':
            try :
                regrade_task.delete()
                cleanup_orphaned_tasks(exercise,0)
            except :
                pass
    except Exception as e :
        logger.info("ERROR IN ACCEPT %s " % str(e) )

    logger.info("ACCEPT D and REDIRECT")
    return redirect("../")
