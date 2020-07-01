from rest_framework import status
from rest_framework.decorators import api_view
from exercises.models import Exercise, Question, Answer
from exercises.question import question_check, _question_check
from django.contrib.auth.models import User
import json
from rest_framework.decorators import api_view
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from django.http import HttpResponse
from aggregation.models import Aggregation, get_cache_and_key, STATISTICS_CACHE_TIMEOUT
from workqueue.models import QueueTask
import workqueue.util as workqueue
from workqueue.exceptions import WorkQueueError
from datetime import datetime



def regrade_results_async_pipeline(task, exercise):
    result = regrade_students_results(task=task, exercise=exercise)
    task.done = True
    task.status = "Working"
    task.progress = 100
    task.save()
    return result



@permission_required('exercises.view_statistics')
@api_view(['GET'])
def get_regrade_results_async(request, exercise):
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
    
    n_answers = len( all_answers)
    txt = "OK"
    for index, answer in enumerate(all_answers):
        grader_response = json.loads( answer.grader_response )
        user_agent = answer.user_agent
        answer_data = answer.answer
        old_correct =  grader_response.get('correct',False)
        hijacked = False
        view_solution_permission = True
        dbuser = answer.user
        question = answer.question
        exercise_key = question.exercise.exercise_key
        question_key = question.question_key
        old_correct =  grader_response.get('correct',False)
        if task is not None:
            #task.status =  task.status + "\n" + str( answer_data )
            #task.status = task.status + str(i) + ","
            task.status = txt
            task.progress = round(((index + 1) / n_answers) * 100)
            task.save()
        ( result,new_correct ) = _question_check(hijacked , view_solution_permission, dbuser, user_agent, exercise_key, question_key, answer_data,answer)
        txt = str( dbuser ) + ' ' + answer_data + ': ' +  str(old_correct) + ' => '  + str( new_correct)  + "\n"
        if not ( old_correct == new_correct ) :
           if new_correct: 
                txt =  "Correkt: " + answer_data
           else :
                txt =  "Incorrect: " + answer_data
           answer.grader_response = json.dumps( result )
           answer.correct = new_correct
           answer.save()
           results[question.question_key].append( dict(
               username=dbuser.username, 
               key=answer.pk , 
               date=answer.date, 
               answer=answer_data, 
               old=old_correct, 
               new=new_correct) )
    return results

