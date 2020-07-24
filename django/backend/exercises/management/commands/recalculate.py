from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import glob
import re
import time
import sys, traceback
import ast
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

from random import shuffle




from course.models import Course

logger = logging.getLogger(__name__)

BIN_LENGTH = settings.BIN_LENGTH


class Command(BaseCommand):

    help = 'recalculate answers'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('--whitelist',  type=str, help='List of exercises to recalculate' )
        parser.add_argument('--accept',  type=str, help='Choose to accept results in results.pkl' )
        parser.add_argument('--exercise',  default=None, type=str , help='filter by exercise' )
        parser.add_argument('--suffix',  type=str , default='.yn' , help='filter by suffix' )
        parser.add_argument('--answerpks',  type=str , default='' , help='filter by answerpks' )


    def handle(self, *args, **kwargs):
        error_log_directory ='/tmp/answer_errors/'
        answers =  Answer.objects.all() 
        nobjects = answers.count()
        whitelist_filename = kwargs.get('whitelist',None)
        #print("RUNNING_DEVSERVVER = ", settings.RUNNING_DEVSERVER)
        #print("BLACKLIST = ", whitelist_filename)
        print("KWARGS = ", kwargs)
        accept = kwargs.get('accept', False)
        exercise = kwargs.get('exercise')
        suffix = kwargs.get('suffix')
            
        if not exercise  == None :
            print("EXERCISE SPECIFIED " , exercise)
            answerpks = []
            for filn in os.listdir(os.path.join(error_log_directory, exercise) ) :
                if suffix  in filn :
                    pk = filn.split('.')[0]
                    answerpks.append(pk)
        if not kwargs.get('answerpks') == '' :
            answerpks =  ( kwargs.get('answerpks') ).split(',')
        else :
            exercises = os.listdir(os.path.join(error_log_directory ) )
            answerpks = []
            for  exercise in exercises :
                fullpath = os.path.join(error_log_directory, exercise )
                if os.path.isdir(fullpath) :
                    for filn in os.listdir(fullpath)  :
                        if suffix  in filn :
                            pk = filn.split('.')[0]
                            answerpks.append(pk)
        if whitelist_filename :
            whitelist = []
            with open(whitelist_filename) as fp:
                for line in fp:
                    questions = list( Question.objects.filter(exercise__exercise_key=line.strip() ) )
                    whitelist = whitelist + questions
            #print("whitelist = ", whitelist )
            answers = list( answers.filter( question__in=whitelist) )
        print("answerpkks = ", answerpks)
        #answerpks = [17865,22207,23825]
        if not answerpks == [] :
            answers = list( answers.filter( pk__in=answerpks) )
        print("NUMBER OF  ANSWERS = ", len( answers ) )
        print("ACCEPT = ", accept )
        #print("ANSWERS = ", answers)
        ind = 0
        #{res : { user: lundand@student.chalmers.se, name: 		 Trig identities		 , type: symbolic, answer:  "|sqrt(90)/40|", old_correct: False,  new_correct :  True   },   error :{ "None"} }
        if accept :
            subdirs = os.listdir( error_log_directory)
            ind = 0
            accept_list = []
            for subdir in subdirs :
                #if ind > 4 :
                #    break 
                bigstring = ""
                if os.path.isdir(  os.path.join(error_log_directory, subdir) ) :
                    #print("SUBDIR = ", subdir)
                    for pk in os.listdir(os.path.join(error_log_directory, subdir) ) :
                        if re.match(r'[0-9]+\.(y|n)(y|n)$',pk) :
                            #print("pk = ", pk)
                            fullpath = os.path.join(error_log_directory, subdir, pk )
                            with open(os.path.join(error_log_directory, subdir, pk )) as fp :
                                for line in fp:
                                    try: 
                                        js = json.loads(line)
                                        js['path'] =  fullpath
                                        #print("JS = ", js )
                                    except:
                                        print("ERROR", line)
                                        exit()
                                accept_list.append(js)
                                ind = ind + 1
                    #print("bigstring = ", bigstring)
                    #lines = bigstring.split("\n")
            print(" FILES HANDLED = ", ind )
            total = ind
            ind = 0
            for new in accept_list:
                ind = ind + 1
                pk = new.get("pk")
                old = Answer.objects.get(pk=pk)
                correct = new.get("correct")
                fullpath = new.get("path")
                grader_response = new.get("grader_response")
                try: 
                        #print("SAVE", pk, old.correct, correct, grader_response, fullpath)
                        old.correct = correct
                        old.grader_response = grader_response
                        old.save()
                        os.rename( fullpath, fullpath + ".done")
                except:
                        print("ERROR ", pk, old.correct, correct, grader_response, fullpath)
                if ( ind % 100 ) == 0 :
                        print("DONE ", ind , " of " , total)
                        
            print("NUMBER OF UPDATES", ind)        
            exit()
        ind = 0
        interval = 4
        #print("NUMBER OF DISTINCT ANSWERS = ", nobjects)
        answers = list(answers)
        shuffle( answers)
        n = 0
        pklfile = "/tmp/answer_errors/done.pkl"
        if not os.path.exists(pklfile) :
            done_answers = []
        else :
            done_answers = pickle.load( open(pklfile,'rb') )
        #print("ALREADY DONE ARE ", len( done_answers) )
        for answer in answers:
            ind = ind + 1
            if True or not str( answer.pk )  in done_answers:
                error_message = None
                did = False
                try:
                    if answer.question:
                        time_beg = time.time()
                        exercise = answer.question.exercise
                        question_key = answer.question.question_key
                        user = answer.user
                        course = exercise.course
                        grader_response_string =  answer.grader_response
                        grader_response_string =     grader_response_string.replace('true' , 'True') ;
                        grader_response_string =     grader_response_string.replace('false' , 'False') ;
                        try:
                            grader_response_string =  answer.grader_response
                            grader_response_string =     grader_response_string.replace('true' , 'True') ;
                            grader_response_string =     grader_response_string.replace('false' , 'False') ;
                            grader_response_string =    grader_response_string.replace('\'','\"' )
                            grader_response = eval(grader_response_string)
                        except:
                            grader_response = {"error" : "Unidentfied" , "correct" : False }
                        user_agent = answer.user_agent
                        answer_data = answer.answer
                        old_correct = grader_response.get('correct', False)
                        hijacked = False
                        view_solution_permission = True
                        dbuser = answer.user
                        question = answer.question
                        question_type = question.type
                        exercise_key = question.exercise.exercise_key
                        usermacros = get_usermacros(user, exercise_key, question_key)
                        question_key = question.question_key
                        old_correct = grader_response.get('correct', False)
                        full_path = exercise.get_full_path()
                        name = exercise.name.replace("\n","")
                        if os.path.exists(full_path ):
                            question_json = question_json_get(exercise.get_full_path(), question_key, usermacros)
                            (result, new_correct) = _question_check( hijacked, view_solution_permission, dbuser, user_agent, exercise_key, question_key, answer_data, answer,)
                            did = True
                            if 'error' in result :
                                error_log_directory ='/tmp/answer_errors/%s' % exercise.exercise_key
                                if not os.path.exists( error_log_directory ) :
                                    os.mkdir( error_log_directory)
                                fp =  open( os.path.join( error_log_directory, 'errors') , 'a')
                                fp.write( '{%s : { user: %s,name: %s ,type: %s,answer:  \"%s\",old_correct: %s, new_correct %s  },  error : \"%s\"} }\n' %
                                                (answer.pk, dbuser,name,question_type, answer_data, old_correct, new_correct ,result  )  )
                                fp.close
                        else :
                            answer.delete()
                            print("FILE ", full_path ," HAS BEEN REMOVED")
                    pass
                    #if (ind % interval) == 0:
                    #    print("\nX\n", end='', flush=True)
                    #    error_message = None
                except Exception as e :
                    print("UNCAUGHT EXCEPTION IN SCRIPT %s %s " % ( type(e), str(e) ))
                    print("JSON = ", grader_response_string)
                    error_message = str(e)
                    traceback.print_exc(file=sys.stdout) 
                if did:
                    if True : # ( not  (old_correct == new_correct ) ) :
                        error_log_directory ='/tmp/answer_errors/%s' % exercise.exercise_key
                        if not os.path.exists( error_log_directory ) :
                             os.mkdir( error_log_directory)
                        summary = dict(pk= answer.pk,
                                        user=dbuser.username,
                                        name=name,
                                        answer=answer_data,
                                        old_correct=old_correct,
                                        new_correct=new_correct,
                                        correct = new_correct,
                                        grader_response=result
                                    )
                        if True or not question_type == 'symbolic' :
                            s1 =  'y' if old_correct else 'n'
                            s2 =  'y' if new_correct else 'n'
                            txt = json.dumps(summary) + '\n'
                            answer_data = re.sub(r'\s+',' ',answer_data)
                            tdiff = int( ( time.time() - time_beg ) *1000 )
                            if not ( old_correct == new_correct )  and  ( not new_correct) :
                                print( "NOK %s%s " % (s1,s2) ,ind,tdiff,old_correct,new_correct, '[' , name, question_key, ']', answer_data, result.get('error','') )
                            else:
                                print( "OK %s%s " % (s1,s2) , ind, tdiff ,name,question_key,answer_data)
                            fils = glob.glob(  os.path.join( error_log_directory, str( answer.pk ) ) + '.*'  )
                            for fil in fils :
                                if os.path.isfile(  fil ) :
                                    os.unlink( fil )
                            fp = open(os.path.join( error_log_directory, str( answer.pk ) ) + "." + s1 + s2   ,"a")
                            fp.write( txt)
                            fp.close()
                            if ( old_correct ==  new_correct ) :
                                answer.grader_response = json.dumps(result) 
                                answer.save()
                        else :
                            did = False
                        n = n + 1
                    else :
                        done_answers.append(str(answer.pk))
                        print(ind, "OK %s%s " % (s1,s2), name )
                else:
                    print( "NOK %s%s" % (s1,s2) ,ind,tdiff,old_correct,new_correct, name, question_key, answer_data, "RESULT FAILED")
                if ind % 100 == 0 :
                    fp = open(pklfile,'wb')
                    pickle.dump( done_answers, fp)
                    fp.close()
            if ind > 100000:
                break
