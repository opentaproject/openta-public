from rest_framework import status
from rest_framework.decorators import api_view
from django.shortcuts import redirect
from django.conf import settings
from exercises.models import Exercise, Question, Answer
from exercises.question import question_check, _question_check
from utils import response_from_messages
from django.contrib.auth.models import User
import json
from rest_framework.decorators import api_view
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from django.http import HttpResponse
from aggregation.models import Aggregation, get_cache_and_key, STATISTICS_CACHE_TIMEOUT
from workqueue.models import  RegradeTask
import workqueue.util as workqueue
from messages import error, embed_messages
from workqueue.exceptions import WorkQueueError
import os
import rq
import pickle


def regrade_results_async_pipeline(task, exercise):
    exercise_key = exercise.exercise_key
    p = '/tmp/regrade/%s' % exercise_key
    resultsfile = p + '/results.pkl'
    old_regrade_exists = os.path.isfile(resultsfile)
    result = regrade_students_results(task=task, exercise=exercise)
    task.done = True
    task.status = "Done"
    task.progress = 100
    task.save()
    return result


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_regrade_results_async(request, exercise):
    p = '/tmp/regrade/%s' % exercise
    pklfile = p + '/regrade_items.pkl'
    resultsfile = p +'/results.pkl' 
    try: 
        regrade_task  = RegradeTask.objects.get(exercise=exercise)
        task_id = regrade_task.task_id
        messages = embed_messages([error('Task %s is still incomplete' % str(task_id))])
        return Response({'task_id': task_id})
    except RegradeTask.DoesNotExist :
        try:
            dbexercise = Exercise.objects.get(pk=exercise)
        except Exercise.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            task_id = workqueue.enqueue_task(
                "regrade_results", regrade_results_async_pipeline, exercise=dbexercise
            )
            regrade_task = RegradeTask.objects.create(exercise=dbexercise,task_id=task_id,resultsfile=resultsfile,pklfile=pklfile,status='Waiting')
            return Response({'task_id': task_id})
        except WorkQueueError as e:
            messages = embed_messages([error(str(e))])
            return Response(messages)

def cleanup_orphaned_tasks(exercise):
    regrade_tasks = RegradeTask.objects.filter(exercise=exercise)
    if len( regrade_tasks) > 1 :
        i = 0
        for regrade_task in regrade_tasks:
            if i > 0 :
                regrade_task.delete()
            i = i + 1
            
        


def regrade_students_results(task, exercise):
    cleanup_orphaned_tasks(exercise)
    results = {}
    try:
        dbexercise = Exercise.objects.get(pk=exercise.pk)
    except Exercise.DoesNotExist:
        return Response({}, status=status.HTTP_404_NOT_FOUND)
    questions = Question.objects.filter(exercise=dbexercise)
    exercise_key = dbexercise.exercise_key
    all_answers = Answer.objects.filter(question__in=questions).order_by('-date')
    for question in questions:
        question_key = question.question_key
        results[question_key] = []
    n_answers = len(all_answers)
    txt = "OK"
    regrade_items = []
    regrade_task = RegradeTask.objects.get(exercise=exercise_key)
    resultsfile = regrade_task.resultsfile
    pklfile = regrade_task.pklfile
    if regrade_task.status == 'Waiting':
        regrade_task.status = 'Running'
        regrade_task.save()
    old_regrade_exists = os.path.isfile(resultsfile)
    if old_regrade_exists:
        results = pickle.load(open(resultsfile, 'rb'))
    for index, answer in enumerate(all_answers):
        if old_regrade_exists:
            task.status = "Old regrade exists"
            task.progress = 100
            task.save
        else:
            regrade_task = RegradeTask.objects.get(exercise=dbexercise)
            if  regrade_task.status == 'Running' :
                grader_response = json.loads(answer.grader_response)
                user_agent = answer.user_agent
                answer_data = answer.answer
                old_correct = grader_response.get('correct', False)
                hijacked = False
                view_solution_permission = True
                dbuser = answer.user
                question = answer.question
                exercise_key = question.exercise.exercise_key
                question_key = question.question_key
                old_correct = grader_response.get('correct', False)
                if task is not None:
                    task.status = (task.status + txt)[-245:]
                    task.progress = round(((index + 1) / n_answers) * 100)
                    task.save()
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
                txt = (
                    str(dbuser)
                    + ' '
                    + answer_data
                    + ': '
                    + str(old_correct)
                    + ' => '
                    + str(new_correct)
                    + "\n"
                )
                if not (old_correct == new_correct):
                    if new_correct:
                        txt = "Correct: " + answer_data
                    else:
                        txt = "Incorrect: " + answer_data
                    answer.grader_response = json.dumps(result)
                    answer.correct = new_correct
                    # answer.save()
                    regrade_items.append(
                        dict(
                            pk=answer.pk,
                            grader_response=answer.grader_response,
                            correct=answer.correct,
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
                        )
                    )
    try: 
        regrade_task = RegradeTask.objects.get(exercise=exercise_key)
        if regrade_task.status == 'Running' :
            regrade_task.status = 'Finished'
        regrade_task.save()
        pklfile = regrade_task.pklfile
        resultsfile = regrade_task.resultsfile
        os.makedirs(os.path.dirname(pklfile), exist_ok=True)
        pickle.dump(regrade_items, open(pklfile, 'wb'))
        pickle.dump(results, open(resultsfile, 'wb'))
    except RegradeTask.DoesNotExist:
        pass
    return results


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def accept_regrade(request, exercise, yesno='no'):
    p = '/tmp/regrade/%s' % exercise
    dbexercise = Exercise.objects.get(pk=exercise)
    regrade_task = RegradeTask.objects.get(exercise=dbexercise)
    if yesno == 'yes':
        pklfile =  regrade_task.pklfile
        regrade_items = pickle.load(open(pklfile, 'rb'))
        for item in regrade_items:
            answer = Answer.objects.get(pk=item['pk'])
            answer.correct = item['correct']
            answer.grader_response = item['grader_response']
            answer.save()
        regrade_task.delete() 
    elif yesno == 'no':
         regrade_task.delete() 
    elif yesno == 'cancel':
         regrade_task.status = 'Cancelled'
         regrade_task.save()
    return redirect("../")
