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
from workqueue.models import QueueTask
import workqueue.util as workqueue
from messages import error, embed_messages
from workqueue.exceptions import WorkQueueError
import os
import rq
import redis
import redis
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
    if old_regrade_exists:
        task.status = 'Old Regrade'
    r = redis.Redis()
    r.get(str(task.pk))
    if not r.get(str(task.pk)):
        task.status = 'Cancelled'
    task.save()
    return result


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_regrade_results_async(request, exercise):
    r = redis.Redis()
    if r.get(exercise):
        task_id = r.get(exercise)
        messages = embed_messages([error('Task %s is still incomplete' % str(task_id))])
        return Response({'task_id': task_id})
    else:
        try:
            dbexercise = Exercise.objects.get(pk=exercise)
        except Exercise.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        try:
            task_id = workqueue.enqueue_task(
                "regrade_results", regrade_results_async_pipeline, exercise=dbexercise
            )
            return Response({'task_id': task_id})
        except WorkQueueError as e:
            messages = embed_messages([error(str(e))])
            return Response(messages)


def regrade_students_results(task=None, exercise=None):
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
    r = redis.Redis()
    regrade_items = []
    p = '/tmp/regrade/%s' % exercise_key
    pklfile = p + '/regrade_items.pkl'
    resultsfile = p + '/results.pkl'
    old_regrade_exists = os.path.isfile(resultsfile)
    r = redis.Redis()
    r.set(str(exercise_key), task.pk)
    r.set(task.pk, str(exercise_key))

    if old_regrade_exists:
        results = pickle.load(open(resultsfile, 'rb'))
    for index, answer in enumerate(all_answers):
        if old_regrade_exists:
            task.status = "Old regrade exists"
            task.progress = 100
            task.save
        else:
            if r.get(str(task.pk)) or index == 0:
                # THIS ALWAYS FAILS SINCE PERHAAPS FILE
                # CREAED IN model.save IS NOT CREATED FAST ENOUGH
                #
                # if ( r.get(str(task.pk) )  == None   ) :
                #    break
                # if (  index > 0 and not os.path.isfile("/tmp/%s" % task.pk)  ):
                #    break
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
                    # task.status =  task.status + "\n" + str( answer_data )
                    # task.status = task.status + str(i) + ","
                    task.status = (task.status + txt)[-245:]
                    task.progress = round(((index + 1) / n_answers) * 100)
                    task.save()
                if r.get(str(task.pk)):
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
                else:
                    new_correct = old_correct
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
        # else :
        #    yield None
    p = '/tmp/regrade/%s' % exercise_key
    # if old_regrade_exists:
    #    results['msg'] = 'Old regrades'
    # else :
    #    results['msg'] = 'New regrades'
    os.makedirs(p, exist_ok=True)
    pickle.dump(regrade_items, open(p + '/regrade_items.pkl', 'wb'))
    pickle.dump(results, open(p + '/results.pkl', 'wb'))
    return results


@permission_required('exercises.view_statistics')
@api_view(['GET'])
def accept_regrade(request, exercise, yesno='no'):
    p = '/tmp/regrade/%s' % exercise
    pklfile = p + '/regrade_items.pkl'
    resultsfile = p + '/results.pkl'
    if yesno == 'yes':
        regrade_items = pickle.load(open(pklfile, 'rb'))
        for item in regrade_items:
            answer = Answer.objects.get(pk=item['pk'])
            answer.correct = item['correct']
            answer.grader_response = item['grader_response']
            answer.save()
        os.remove(pklfile)
        os.remove(resultsfile)
        r = redis.Redis()
        r.delete(exercise)
    elif yesno == 'no':
        os.remove(pklfile)
        os.remove(resultsfile)
        r = redis.Redis()
        r.delete(exercise)
    elif yesno == 'cancel':
        r = redis.Redis()
        pk = r.get(exercise)
        r.delete(pk)
        tasks = QueueTask.objects.filter(pk=pk)
        if len(tasks) == 1:
            tasks[0].delete()
    return redirect("../")
    # return redirect("/" + settings.SUBPATH)
