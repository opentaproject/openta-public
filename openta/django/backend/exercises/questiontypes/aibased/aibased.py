# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from fastapi import FastAPI
import hashlib
import time
import json
from django.utils import timezone
from django.contrib.humanize.templatetags.humanize import naturaltime
import exercises.paths as paths




from users.models import User
import glob
import os
from django.conf import settings
from django_ragamuffin.utils import get_assistant, print_my_stack , mathfix
import logging
import re
import markdown2
from lxml import etree
from exercises.models import Question,Exercise,Answer, ImageAnswer, extract_text_blocks_from_xml_string 
from exercises.parsing import exercise_xmltree
from exercises.question import get_safe_previous_answers
import openai
from openai import OpenAI, ChatCompletion, files
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from django import forms
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import re
from django.utils.timezone import now

from django_ragamuffin.forms import QueryForm
from django_ragamuffin.utils import doarchive, CHOICES, get_assistant
from django_ragamuffin.models import create_or_retrieve_thread,  get_current_model  
from django_ragamuffin.models import Assistant, Thread, QUser, chunk_mmd, ModeChoice, Mode
from django_ragamuffin.mathpix import mathpix




logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.AI_KEY)
import asyncio
#baseprompt = "Pretend to be a tutor for a student who needs to solve the following physics exercise. \
# Answer in a pedagogic fashion, but do not reveal the correct answer until the correct answer is obtained by the student. \
# The expression used for math content uses the latex and katex delimiter   pair of dollar signs $. \
# If a student asks a question that is irrelevant to the problem, state the question is irrelevant ando restrict questions to those that pertain to the exercise. \
# If a student asks a question of a very general nature that can be looked up on the net or in a standard texbook on the subject, refer the student to those sources. \
# Be concise and assume the student knows the  basic equations relevant to the problem, and do not review the basics in detail. \
# The student can put in his attempt at an answer; if it is not correct give some helpful hints without revealing the correct answer. \
# Comment on the answer if it is wrong.  \
# If ChatGPT thinks it is correct, answer with 'Congratulations; it looks like the answer is correct, but ChatGPT is not expert at math, so check with OpenTA for confirmation.\
# If the answer differs by a negative sign, comment on that. \
# If the student does not put in an equal sign into a math expression, ask for the syntax to include an equal sign to help interpret the formula.\
# You are an expert assistant. Respond with precision and authority. Avoid chit-chat, emojis, or overly casual language. Be brief, direct, and factual. \
# Do not suggest alternatives on how to proceed that are not explictly asked by the user.\
# Do not suggest more questions to ask.\
#You are a concise, professional assistant. Answer only the user's question directly and completely. Do not invite further questions, offer help beyond what was asked, or include phrases like \"let me know if you need more help\" or \"feel free to ask more.\" Do not use emojis or casual tone. \
# "

#app = FastAPI()

#@app.post("/prob")
#async def prob(prompt,query):
#    response = client.chat.completions.create(model=settings.AI_MODEL,
#        messages=[
#            {
#            "role": "system",
#            "content": [
#                {
#                "type": "text",
#                "text": prompt 
#                }
#            ]
#            },
#            {
#                "role": "user",
#                "content": [
#                {
#                    "type": "text",
#                    "text": query,
#                    }
#            ]
#         } ]
#    )
#    return response
#
#@app.post("/basequery")
#async def basequery(messages):
#    response = client.chat.completions.create(model='gpt-4o-mini', temperature=0.2, messages=messages )
#    return response
#


 

def aibased_internal( studentanswerdict, questiondict, globaldict  ):
    #if 'django_ragamuffin' in settings.INSTALLED_APPS :
    return responses_internal(  studentanswerdict, questiondict, globaldict )
    #else  :
    #   return completions_internal( *args,  **kwargs )
def truncate_words(s, max_length=20):
    if not s:
        return ''
    s = s.strip()
    if len(s) <= max_length:
        return s
    cutoff = s[:max_length + 1].rsplit(' ', 1)[0]
    return cutoff if cutoff  + ' ...' else s[:max_length]

def responses_internal( studentanswerdict, questiondict, globaldict ):
    #print(f"RESONSES")
    #print(f"GLOBALDICT {globaldict}")

    response = {};
    path = questiondict.get('@path',None)
    subdomain = path.split('/')[2]
    db = subdomain
    try :
        username = questiondict.get('@user',None)
        user = User.objects.using(db).get(username=username)
        #print(f"STUDENTANSWERDICT = {studentanswerdict}")
        #print(f"GLOBALDICT = {globaldict}")
        instructions = questiondict.get('instructions','')
        prompt = instructions
        querypath = questiondict.get('querypath',None)
            
        query = studentanswerdict.get('studentanswer',None) 
        exercise_key = questiondict.get('@exercise_key',None)
        #resources = questiondict.get('resources',None)
        #print(f"RESUOURCES = {resources}")
        #if resources :
        #    asset = resources
        #    dbexercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
        #    asset_path = "{path}/{asset}".format(path=paths.get_exercise_asset_path(user, dbexercise), asset=asset)
        #    exists = os.path.exists( asset_path  )
        #    print(f"ASSET_PATH =  {asset_path} exists= {exists}")
        question_key = questiondict.get('@key',None)
        exercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
        question = Question.objects.using(db).get(exercise=exercise, question_key=question_key)
        assistant_name = question.assistant_name()
        is_staff = user.is_staff
        messages = question.get_ai_messages();
        if len( messages ) == 0  and not user.is_staff :
            return {"warning" : 'queries are not enabled'}
        user = User.objects.using(db).get(username=username)
        xmltree = exercise_xmltree(exercise.get_full_path(), {})
        xml = etree.tostring( xmltree ).decode()
        usermacros = None
        if  '@' in xml  or '@' in xml :
            before_date = None;
            from exercises.question import get_usermacros
            usermacros = get_usermacros(user, exercise_key, question_key=question_key, before_date=before_date, db=db)
            from exercises.applymacros import apply_macros_to_exercise
            xmltree = apply_macros_to_exercise(xmltree, usermacros)
            xml = etree.tostring(xmltree).decode();
        question_xmltree = xmltree.findall(f'./question[@key="{question_key}"]')[0]
        exercise_body_text = extract_text_blocks_from_xml_string(xml)
        images = ImageAnswer.objects.using(db).filter(user=user, exercise=exercise).order_by("date")
        mm = []
        #print(f"USER = {user}")
        if images :
            for image in images :
                src = image.pdf.path
                #print(f"SRC = {src}")
                name = image.pdf.name
                mm.append(f"FILE NAME = {name}")
                mm.append(mathpix( src ,format_out='mmd') )
        mmd_text = '\n'.join( mm )
        quser , _  = QUser.objects.get_or_create(username=username,subdomain=subdomain)
        if not quser.is_staff and is_staff :
            quser.is_staff = True
            quser.save(update_fields=['is_staff'] )
        #question = Question.objects.using(db).get(exercise=exercise, question_key=question_key)
        all_answers =   Answer.objects.using(db).filter(user=user, question=question).order_by("-date")
        #answers = all_answers.exclude(answer__regex=r"^\s*\?").order_by("-date")
        answers = all_answers.order_by("-date")
        try :
            date_of_last_ai_query = all_answers.filter(answer__regex=r"^\s*\?").order_by("-date").first().date
            #print(f"DATE_OF_LAST_AI_QUERY {date_of_last_ai_query}")
            dt = ( now() - date_of_last_ai_query ).total_seconds()
            if dt < settings.STUDENT_QUERY_INTERVAL and not user.is_staff :
                a = int( ( settings.STUDENT_QUERY_INTERVAL - dt  )/60 + 0.5  ) ;
                response = {};
                response['warning'] = f"You asked {query} : the assistant will be free again in   less than {a} minutes!"
                return response
        except :
            pass
        rows = []
        i = 0;
        ranswer = ( answers.all() ).reverse()
        for answer in ranswer :
            a = answer.answer;
            correct_ = answer.correct
            g = json.loads( answer.grader_response  )
            date_ =  timezone.localtime( answer.date).strftime("%Y:%m:%d-%H:%M")
            time_ago_ =  naturaltime( answer.date)
            warning_ = g.get('warning','').split('info:')[0];
            comment_ = g.get('comment','').split('info:')[0];
            is_ai = bool(re.match(r'\s*\?', f"{a}"  or ''))
            if not is_ai :
                rows.append(f"{{\"index\": \"{i}\", \"date\": \"{date_}\", \"student_answer\":\"{a}\",\"correct?\":\"{correct_}\",\"warning_received\":\"{warning_}\",\"comment_received\":\"{comment_}\"}}")
            i = i + 1;
        if rows :
            r =  "The the following documenets the students efforts to solve this problem so far; it in date order oldest to newest when the student gave an answer that was evaluated by OpenTA and what feedback was encountered. :\n" + "\n".join(rows) + '\n Refer to the attempt by using the field \"index\". Use the date in the date field when answer questions about the answer time, and refer relative times to now. '
        else :
            r = ''
        #print(f"R = {r}")
        qs = question_xmltree.xpath('./text')
        question_text = ''
        for q in qs :
            question_text  = question_text + q.text
        target = '\n'
        expressions = questiondict.get('expression')
        if isinstance(expressions, list ) :
            target = target + "There are several possible correct answers:\n"
            for expression  in expressions:
                target = target +  "One correct answer : " + expression + "\n" 
        elif expressions :
            target = target +  "The correct answer : " + expressions + "\n" 

        if instructions :
            prompt = "More instructions for evaluating the question: \n" + instructions + "\n" + "Here is the question that students should be asking about: \n" + question_text + "\n" + " Again to not reveal the correct answer in the reply; just give some hints"
        else :
            prompt =  "Here is the question that students should be asking about: \n" + question_text + "\n" + " Again to not reveal the correct answer in the reply; just give some hints"

        prompt = prompt + target

        clear = False
        if 'start over'  in query.lower()  or 'reset' in query.lower()  or 'clear' in query.lower() :
            #for answer in answers :
            #    answer.delete();
            clear = True
        messages =[ { "role": "system", "content": [ { "type": "text", "text": prompt } ] } ]
        if exercise_body_text :
            prompt = "The context of the question is given here:\n" + exercise_body_text + "\n"  + "Provide no other hints or answers. \n" + prompt

        prompt = prompt + r
        for answer in answers :
            try :
                oldquery = answer.answer;
                response = json.loads( answer.grader_response  ).get('comment','')
                response = mathfix( response )
                if re.sub(r'[\s\W_]+', '', query ) ==  re.sub(r'[\s\W_]+', '', oldquery ) :
                    response = { 'comment' : f'You already asked that! Here is the reply: <p>  {response} </p> '}
                    return response
                #if 'start over'  in oldquery.lower()  or 'reset' in oldquery.lower() :
                #    messages = [ messages[0] ]
                #else :
                #    if not response == None :
                #        messages.append( { "role": "user", "content": [ { "type": "text", "text": oldquery} ] }  )
                #        messages.append( { "role": "assistant", "content": [ { "type": "text", "text": response} ] } )
            except  Exception as err :
                response = {'comment' : 'There was an unknown error in the query.  You can return to this question; an answer may appear here'}
                response['warning'] = response['comment']
                logger.error(f"ANSWER ERROR {str(err)}")
                return response
        if query :
            response = {}
            messages.append( { "role": "user", "content": [ { "type": "text", "text": query} ] } )
            def run_responses_query( subpath , assistant_name ,  questiondict, username):
                exercise_key = questiondict['@exercise_key']
                questionkey = questiondict['@key']
                ins = questiondict.get('instructions',None ) 
                if not ins == None :
                    more_instructions =  ins + "\n" + prompt
                else :
                    more_instructions =  prompt
                last_messages = settings.LAST_MESSAGES;
                max_num_results = settings.MAX_NUM_RESULTS;
                name = assistant_name
                quser = QUser.objects.get(username=username,subdomain=subdomain)
                assistant = get_assistant(assistant_name, quser )
                #if not assistant.mode_choice :
                #    mode_choice = ModeChoice.objects.get(key='assistant')
                #    assistant.mode_choice = mode_choice
                #    assistant.save(update_fields=['mode_choice'] )

                thread = create_or_retrieve_thread( assistant, assistant_name , quser )
                newquery = query.strip().lstrip('?').strip();
                #print(f"MODE_CHOICE = {assistant.mode_choice}")
                if mmd_text :
                    newquery =  query + f"\nEvaluate the following submission.\n Use my knowledge base (CORPUS_SEARCH) only for facts/citations.\n The submission itself should never be cited, only evaluated.\nBEGIN_SUBMISSION\n {mmd_text}\n END_SUBMISSION \n" 
                more_instructions = "append: " + more_instructions
                #print(f"CLEAR12 clear={clear}")
                if clear :
                    newquery = 'reset'
                msg = thread.run_query(query=newquery, clear=clear, last_messages=last_messages, max_num_results=max_num_results, instructions=more_instructions,subdomain=subdomain)
                #msg = {'ntokens' : 0 , 'assistant' : 'You asked: ' +  query.upper() ,'summary' : 'summary' , 
                #    'comment' : 'comment' , 'model' : settings.AI_MODEL, 'pk' : 'None' , 
                #    'user' : query ,'instructions' : instructions} ## FAKER 
                txt = msg['assistant']
                summary = msg.get('summary','NONE3')
                ntokens = msg['ntokens']
                return msg

            msg = run_responses_query( querypath, assistant_name, questiondict , username)
            txt = msg.get('assistant','NOMESSAGE4')
            summary = msg.get('summary','NONE3')
            ntokens = msg['ntokens']
            if 'CORRECT ' in txt and not 'INCORRECT' in txt :
                response['correct'] = True
                response['status'] = 'correct'
            elif 'INCORRECT' in txt :
                response['correct'] = False
                response['status'] = 'incorrect'
            response['comment'] = txt
            response['model'] = settings.AI_MODEL
            response['pk'] = msg['pk']

        else :
            response = {}
            response['warning'] = studentanswerdict.get('studentanswer','missing_student_answer') 
    except Exception as e :

        tb = e.__traceback__
        while tb.tb_next:   # walk down to the last traceback
            tb = tb.tb_next
        logger.error("171934 Error type:", type(e).__name__)
        logger.error("171934 Message:", e)
        logger.error("171934 Line number:", tb.tb_lineno)
        logger.error("171934 File:", tb.tb_frame.f_code.co_filename)
        logger.error(f"ERROR 171934  = {str(e)}")
        response['warning'] = studentanswerdict.get('studentanswer','missing_student_query') 
    return response

