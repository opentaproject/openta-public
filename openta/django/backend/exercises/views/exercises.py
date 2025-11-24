# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import logging
from django.http import FileResponse
import exercises.paths as paths
from django.views.decorators.csrf import csrf_exempt
import json
import os
import random
import re
import urllib3
import shutil
from django.http import HttpResponse
import xml.etree.ElementTree
from django.contrib.auth.models import User
from backend.middleware import check_connection
import exercises.parsing as parsing
from course.models import Course
from exercises.models import Exercise, ExerciseMeta, Answer, Question
from exercises.parsing import list_history
from exercises.paths import EXERCISE_XML
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from slugify import slugify
from utils import get_subdomain_and_db

from django.conf import settings
from django.http import QueryDict
from django.contrib.auth.decorators import permission_required
from django.core.cache import caches
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import  AllowAny
import base64



logger = logging.getLogger(__name__)


#@csrf_exempt
#def webwork_post_forward(request):
#    querystring = request.META['QUERY_STRING'] 
#    logger.error(f"RAW_QUERYSTRING = {querystring}")
#    fields = querystring.split('&')
#    payload = {} ;
#    for f in fields:
#        [key,value] = f.split('=',1)
#        payload[key] = value;
#        print(f"{key} => {value}")
#    logger.error(f"payload = {payload}")
#    querystring = f"http://{settings.RENDERER_HOST}:3000/render-api?{request.META['QUERY_STRING']}"
#    logger.debug(f"WEBWORK_FORWARD A querystring= {querystring}")
#    http = urllib3.PoolManager()
#    logger.debug(f"WEBWORK_FORWARD http={http}")
#    html = http.request("POST",   f"http://{settings.RENDERER_HOST}:3000/render-api", fields=payload)
#    logger.debug(f"B {html}")
#    res = HttpResponse( html.data )
#    #logger.debug(f"WEBWORK_FORWARD DATA = {html.data}")
#    res.status_code =  200;
#    return res
#


@csrf_exempt
@permission_classes([AllowAny])
def webwork_htdocs(request,exercise):
    subdomain,db = get_subdomain_and_db(request)
    r = request.get_full_path()
    htdoc = settings.HTDOCS_TMP + r.split('htdocs')[-1]
    htdoc2 =  os.path.join(settings.VOLUME,"htdocs","tmp","renderer","images",htdoc.split('/')[-1] );
    if os.path.exists(htdoc) :
        img = open(htdoc, 'rb')
    elif os.path.exists(htdoc2) :
        img = open(htdoc2,'rb')
    else :
        img = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\x00\x00 \x08\x02\x00\x00\x00\xfc\x18\xed\xa3\x00\x00\x00\xd0IDATx\x9c\xad\xd6\xc1\x16\x830\x08DQ\xc2\xff\xffs\xbaR\x1b\xc2\xc0\x90\xe0J\x17\xbe\xdbc\x8ceLy\x8e\xf9\x9d\xf6\x1cc\x88\x88\x9a\xeb\xde\xfa\n4\x1a\x7f\x1d\xb5O\xe6\xdeX\x0b*\xb2=\xfd\x1b\xc3\xdc;\xa7\xbeg\r\xc6V\x97e\r.\r\xaf.v\x91\x8f\rP\xdf\x803\x03\xd7=\xa0j\x84u\x00\xf0FV\xc7\x00c\x10\xf5\x10\x88\r\xae\x9e\x01\xc8\xa0\xeb\x04\x80\x0c\xae\xce\x01A\x85\xf8\xc2s\x80\xdb\xe2\xfe?h }\x8b\xae\x00r\x1f\x1c\x02\xf1\xaafF\x06\xb8\xf5\x8a\x11\x02\xc1o\xa7\r\x0c\xa4\xef;g\x00\x80\xdcM\x84\xe1\x01\xa5\xbd\x9a\x19\x1bP\xfc\x12\xa4F8\x17\xf1\xb3\x1e6\xf0dW\x9d$\x81\xa1\xe6\xfa\xb0\x8e\rm\xab\x03c\xd8X\xcb\x8c\xed\xafAW}\xed\xfc\x00\x96\njCw\x82\xc7\x9c\x00\x00\x00\x00IEND\xaeB`\x82'
        return HttpResponse( img, content_type="image/png")
    response = FileResponse(img)
    return response



@csrf_exempt
@permission_classes([AllowAny])
def webwork_forward(request, course_pk=None):
    subdomain,db = get_subdomain_and_db(request)
    #print(f"WEBWORK_FORWARD {request.get_full_path()}")
    if request.method == 'POST' :
        fields=  request.POST.copy()
        #jsonarray = json.loads(request.body)
        #rint(f"JSONARRAY_IN_FORWARD = {jsonarray}")
        #[http,subdomain_check,server,port,coursekey,userpk,exercise_key,question_key,exercise_seed,outputFormat] = full_identifier.split(':')
        #print(f"OUTPUT_FORMAT = {outputFormat}")
        #print(f"FIELDS = {fields}")
        identifier = fields.get('identifier');
        outputFormat = fields.get('outputFormat');
        full_identifier = base64.b64decode( identifier  ).decode('utf-8');
        #print(f"POST WEBWORK_FORWARD FULL IDENTIFIER ={full_identifier}")
        #print(f'POST WEBWORK_FORWARD outputFORMAT = {outputFormat}');
        [http,subdomain_check,server,port,coursekey,userpk,exercise_key,question_key,exercise_seed,outputFormat] = full_identifier.split(':')
        dbexercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
        #user = User.objects.using(db).get(pk=userpk)
        #print(f"USER = ", user )
        #student_asset_path =  paths.get_student_asset_path(user, dbexercise)
        #print(f"STUDENT_ASSET_PATH = {student_asset_path}")
        #indexhtml = os.path.join(student_asset_path, 'index.html')
        #if os.path.exists( indexhtml ) :
        #    f = open( indexhtml,'r')
        #    for line in f :
        #        if 'identifier' in line :
        #            identifier = line.split("\"")[-2]
        #            print(f"IDENTIFIER = {identifier}")
        #            old_full_identifier = base64.b64decode( identifier  ).decode('utf-8');
        #    f.close;
        show_solution = dbexercise.meta.solution
        #print(f"SHOW_SOLUTION = {show_solution}")
        #print(f"OLD_FULL_IDENTIFIER {old_full_identifier} ")
        if show_solution:
            outputFormat = 'simple'
        else :
            outputFormat = 'single'
        #decoded_identifier = f"{http}:{subdomain}:{server}:{port}:{coursekey}:{userpk}:{exercise_key}:{question_key}:{exercise_seed}:{outputFormat}" 
        #encoded_identifier = base64.b64encode( decoded_identifier.encode()  );
        #print(f"INDEXHTML = {indexhtml}")
        #print(f"OLD IDENTIFIER = {full_identifier}")
        #print(f"NEW IDENTIFIER = {decoded_identifier}")
        #if os.path.exists( indexhtml ) :
        #    f = open( indexhtml,'rb' )
        #    html = f.read();
        #print(f"outputFormat = {outputFormat}")
        #fields['identifier'] = [encoded_identifier]
        #fields['ouputFormat'] = [outputFormat ];
        j = fields.urlencode();
        j = j + f'&outputFormat={outputFormat}'
        http = urllib3.PoolManager()
        html = http.request("GET",   f"http://{settings.RENDERER_HOST}:3000/render-api?{j}", headers={
            "Referrer-Policy": "origin-when-cross-origin"
            })
        #html = http.request("POST",   f"http://{settings.RENDERER_HOST}:3000/render-api",fields=fields)
        data = html.data;
        return HttpResponse(data)
    if request.method == 'GET' :
        querystring = request.META['QUERY_STRING'] 
        querystring = f"http://{settings.RENDERER_HOST}:3000/render-api?{querystring}"
        print(f"GET WEBWORK_FORWARD QUERYSTRING ={querystring}")
        http = urllib3.PoolManager()
        html = http.request("GET", querystring)
        res = HttpResponse( html.data )
        res.status_code =  200;
        return res




@csrf_exempt
@api_view(["POST","GET"])
@permission_classes([AllowAny])
def webwork_save_result(request,identifier):
    subdomain,db = get_subdomain_and_db( request );
    #if len( identifier ) > 8 :
    #print(f"IDENTIFIER IN WEBWORK {identifier}")
    full_identifier = base64.b64decode( identifier  ).decode('utf-8');
    #print(f"WEBWORK SAVE_RESULT {full_identifier}")
    if settings.VALIDATE_IDENTIFIER and settings.DO_CACHE : # ADD CHECK TO MAKE SURE HTML IS NOT SENT INAPPROPRIATELY 
        icache = caches['default'];
        nfull_identifier = icache.get(identifier)
        assert full_identifier == nfull_identifier , 'FULL IDENTIFIER NOT PRESENT IN CACHE';
        #print(f"CHECK FULL IDENTIFIER IN WEBWORK = {full_identifier} {nfull_identifier} ")
    jsonarray = json.loads(request.body)
    #print(f"JSONARRAY = {jsonarray}")
    #logger.error(f" FULL_IDENTIFIER IN EXERCISES {full_identifier}")
    [http,subdomain_check,server,port,coursekey,userpk,exercise_key,question_key,exercise_seed,outputFormat] = full_identifier.split(':')
    # decoded_identifier = f"{http}:{subdomain}:{server}:{port}:{course.course_key}:{user.pk}:{exercise.exercise_key}:{question.question_key}:{exercise_seed}" 

    #assert userpk == request.user.pk, "USER IS NOT CORRECT";
    #print(f"JSONARRAY = {jsonarray}")
    #res = [];
    #for j in jsonarray :
    #    res.append(  json.loads(j) );
    #print( f"res = {res}")
    check_connection(db)
    try :
        res = json.loads( jsonarray[0] );
    except :
        res = jsonarray
    #print(f" RES = {res}")
    if '1' == res['submitted'] :
        #print(f"SUBMITTED")
        dbquestion = (
            Question.objects.using(db)
            .get(exercise__exercise_key=exercise_key, question_key=question_key)
            )
        #print(f"DBQUSTION = {dbquestion}")
        user = User.objects.using(db).get(pk=userpk);
        answer_data = res['ans'];
        grader_response = { 'correct' : not ( res['correct'] == 0 ) , 'status' : 'incorrect' if res['correct'] == 0  else 'correct',
                           'type' : "webworks", 'expression' : answer_data }
        correct = not( res['correct']  == 0 );
        user_agent = '';
        questionseed = res['seed'];
        exerciseseed = res['seed'];
        a = Answer(
            user=user,
            question=dbquestion,
            answer=answer_data,
            grader_response=grader_response,
            correct=correct,
            user_agent=user_agent,
            questionseed=questionseed,
            exerciseseed=exerciseseed,
            )
        a.save(using=db)

    return Response({"success": "graded exercise", "messages": 'grade recorded'})
    


@api_view(["POST"])
@permission_required("exercises.edit_exercise")
def exercises_add(request):
    _, db = get_subdomain_and_db(request)
    try:
        course_pk = request.data.get("course_pk")
        dbcourse = Course.objects.using(db).get(pk=course_pk)
    except Course.DoesNotExist:
        logger.debug("Requested course does not exist pk: %d", course_pk)
        return Response({"error": "Invalid course"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    path = os.path.join(*request.data.get("path").split("/"))
    name = request.data.get("name")
    # name = re.sub('[^\w]', '', name)  # MAKE SURE ONLY SIMPLY PARSED FILENAMES ARE CREATED
    res = parsing.exercise_add(os.path.join(dbcourse.get_exercises_path(db), path), name)
    if "error" in res:
        return Response(res, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    msg = Exercise.objects.add_exercise_full_path(res["path"], dbcourse,db)
    logger.error("MSG Added exercise at " + res["path"])
    logger.error(f"MSG {msg}")
    return Response({"success": "Added exercise", "messages": msg})


@api_view(["DELETE"])
@permission_required("exercises.edit_exercise")
def exercise_delete(request, exercise):
    _, db = get_subdomain_and_db(request)
    try:
        dbexercise = Exercise.objects.using(db).get(pk=exercise)
    except Exercise.DoesNotExist:
        logger.debug("Tried to delete invalid exercise " + exercise)
        return Response({"error": "Invalid exercise"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    res = parsing.exercise_delete(dbexercise.course.get_exercises_path(), dbexercise.get_full_path())
    ExerciseMeta.objects.using(db).filter(exercise=dbexercise).update(published=False)
    if "error" in res:
        return Response(res, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    logger.info("Deleted exercise at " + dbexercise.name)
    Exercise.objects.add_exercise("/" + res["path"], dbexercise.course)
    return Response({"success": "Deleted exercise"})


@api_view(["POST"])
@permission_required("exercises.edit_exercise")
def exercise_handle(request):
    #logger.error("EXERCISE_HANDLE")
    _, db = get_subdomain_and_db(request)
    exercises = request.data.get("exercises")
    path = request.data.get("path")
    action = request.data.get("action")
    # new_folder = re.sub('[^\w\ :]', '', new_folder)
    if action == "clone":
        return Response(exercise_clone(exercises, db))
    for exercise in exercises:
        # print("Action %s DO %s " % (action, exercise) )
        try:
            dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)

        except Exercise.DoesNotExist:
            logger.debug("Tried to move invalid exercise " + exercise)
    return Response({"error": "Unknown action %s" % action})


@api_view(["POST"])
@permission_required("exercises.edit_exercise")
def folder_handle(request):
    #logger.error("FOLDER_HANDLE")
    _, db = get_subdomain_and_db(request)
    path = request.data.get("path")
    action = request.data.get("action")
    coursePk = request.data.get("coursePk")
    caches["default"].set("temporarily_block_translations", True, 15)
    #print(f" ACTION = {action}")
    if action == "emptyTrash":
        # print(f"emptyTrash")
        course = Course.objects.using(db).get(pk=coursePk)
        course_path = course.get_exercises_path()
        trashdir = os.path.join(course_path, "z:Trash")
        if os.path.isdir(trashdir):
            npaths = []
            for root, subdirs, files in os.walk(trashdir):
                for file in files:
                    if file == "exercise.xml":
                        path = root.split("z:Trash")[1]
                        npaths = npaths + [path]
            for path in npaths:
                epath = f"z:Trash{path}"
                try:
                    exercise = Exercise.objects.using(db).get(path=epath)
                    if not '/invisible'  == path :
                        exercise.delete()
                        shutil.rmtree(os.path.join(course_path, epath))
                except Exception as e:
                    logger.debug(f"ERROR DELETING TRASH {type(e).__name__} {str(e)} ")

        


    return Response({"success in folderHandle ": "Action %s" % action})


def exercise_clone(exercises, db):
    for exercise in exercises:
        dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
        path = dbexercise.path
        full_path = dbexercise.get_full_path()
        Exercise.objects.add_exercise(dbexercise.path, dbexercise.course)
        postfix = "-" + str(random.randint(11111, 99999))
        new_path = settings.NEW_FOLDER + "/" + slugify(dbexercise.name) + postfix
        new_full_path = os.path.join(dbexercise.course.get_exercises_path(), new_path)
        shutil.copytree(full_path, new_full_path)
        history_dir = os.path.join(new_full_path, "history")
        if os.path.isdir(history_dir):
            shutil.rmtree(history_dir)
        os.remove(os.path.join(new_full_path, "exercisekey"))
        xml_file = os.path.join(new_full_path, EXERCISE_XML)
        et = xml.etree.ElementTree.parse(xml_file)
        root = et.getroot()
        tag = root.findall(".//exercisename")[0]
        name = tag.text.strip()
        tag.text = name + "-copy"
        et.write(xml_file)
        Exercise.objects.add_exercise(new_path, dbexercise.course)


@api_view(["POST"])
@permission_required("exercises.edit_exercise")
def exercise_move(request):
    #print(f"EXERCISE_MOVE")
    _, db = get_subdomain_and_db(request)
    # print(f"EXERCISE_MOVE_REQUEST ")
    exercises = request.data.get("exercises")
    new_folder = request.data.get("new_folder")
    # new_folder = re.sub('[^\w\ :]', '', new_folder)
    for exercise in exercises:
        # print("DO %s " % exercise)
        try:
            dbexercise = Exercise.objects.using(db).get(exercise_key=exercise)
        except Exercise.DoesNotExist:
            logger.debug("Tried to move invalid exercise " + exercise)
        new_name = slugify(dbexercise.name) + "-" + str(random.randint(111111, 999999))
        # print("COMPARISON %s %s " % ( dbexercise.name, new_name) )
        relative_path = os.path.normpath(os.path.join("/1/2/3/4/5/6", *new_folder.split("/"), new_name))
        # print("relative_path = %s " % relative_path )
        if not "/6/" in relative_path:
            # print("MOVED ATTEMPTED OUTSIDE TREE")
            return Response({"error": "Move outside tree attempted"})
        new_full_path = os.path.join(dbexercise.course.get_exercises_path(), *new_folder.split("/"), new_name)
        res = parsing.exercise_move(dbexercise.get_full_path(), new_full_path)
        if "error" in res:
            return Response(res, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        dbexercise.path = os.path.join(*new_folder.split("/"), new_name)
        dbexercise.save(using=db)
        logger.info("Moved exercise " + dbexercise.name + " to " + res["path"])
    return Response({"success": "Moved exercise"})


@api_view(["POST"])
@permission_required("exercises.edit_exercise")
def exercises_move_folder(request):
    _, db = get_subdomain_and_db(request)
    # print("START EXERCISES _MOVE FOLDER ")
    # print("EXERCISE_MOVE_FOLDER REQUEST = %s " % request.data)
    caches["default"].set("temporarily_block_translations", True, 15)
    old_folder = request.data.get("old_folder")
    new_folder = request.data.get("new_folder")
    course_pk = request.data.get("course_pk")
    dbcourse = Course.objects.using(db).get(pk=course_pk)
    course_path = dbcourse.get_exercises_path()
    res = _exercises_move_folder(old_folder, new_folder, course_path, db)
    caches["default"].delete("temporarily_block_translations")
    # print("FINISH EXERCISES _MOVE FOLDER ")
    return res


def path_is_outside(path):
    path = re.sub(r"/\./", "/", path)
    normpath = os.path.normpath(path)
    ndoubledots = len(path.split(".."))
    ndirsorig = len(path.split("/"))
    ndirsnew = len(normpath.split("/"))
    # print("%s + %s = %s " % ( ndirsnew , ndoubledots , ndirsorig) )


def _exercises_move_folder(old_folder, new_folder, course_path, db):
    #print("BEGIN _EXERCISES_MOVE_FOLDER")
    # new_folder = re.sub('[^\w\ :]', '', new_folder)
    # print("_EXERCISES_MOVE_FOLDER %s to %s " % ( old_folder, new_folder) )
    # print("_EXERCISES_MOVE_FOLDER PATH %s " %  course_path  )
    # dbexercises = Exercise.objects.filter(folder=old_folder)  \
    #    | Exercise.objects.filter( folder__startswith=old_folder + '/')  \
    #    | Exercise.objects.filter( folder__startswith='/' + old_folder )
    # if dbexercises.count() == 0:
    #    #print("DBEXERCISES DO NOT EXIST")
    #    return Response(
    #        {'error': 'There are no exercises in that folder'},
    #        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #    )
    path_is_outside(new_folder)
    # course_path = dbexercises[0].course.get_exercises_path()
    # print("COURSE PATH = %s " % course_path)
    # print("OLD_FOLDER1 IS %s " % old_folder )
    # print("NEW_FOLDER1 IS %s " % new_folder )
    old_folder = os.path.normpath(old_folder)
    new_folder = os.path.normpath(new_folder)
    # if not new_folder[0] == '/' :
    #        new_folder = os.path.join( old_folder, '../',new_folder )
    #        #print("NEW_FOLDER IS %s " % new_folder )
    # print("courspath is %s " % course_path)
    # print("NORM: OLD_FOLDER1 IS %s " % old_folder )
    # print("NORM NEW_FOLDER1 IS %s " % new_folder )
    if new_folder[0] == "/":
        new_folder = new_folder[1:]
    # if not course_path in new_folder :
    #    #print("TACK ON COURSE PATH")
    #    new_folder = course_path +  new_folder
    #    #print(" NEW_FOLDER BECAME %s " % new_folder)
    if ".." in new_folder:
        # print("CANNOT GO OUTSIDE TREE")
        return Response({"error": "Cannot go outside tree"})
    old_full_path = os.path.join(course_path, old_folder)
    new_full_path = os.path.join(course_path, new_folder)
    # print("OLD_FULL_PATH %s " % old_full_path)
    # print("NEW_FULL_PATH %s " % new_full_path)
    # print(f"PARSING TEMP {caches['default'].get('temporarily_block_translations')}")
    res = parsing.exercises_move_folder(old_full_path, new_full_path, db)
    # print("RES FROM PARSING EXERCISES_MOVE_FOLDER %s " %  res )
    if res.get("success", False):
        entries = res.get("exercises", [])
        for entry in entries:
            name = entry.get("name")
            path = entry.get("path")
            f = open(os.path.join(path, "exercisekey"), "r+")
            exercise_key = f.read()
            f.close
            # print("exercise_key = ", exercise_key)
            dbexercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
            # print("OLD EXERCISE PATH = %s " % dbexercise.path)
            dbexercise.path = (path.split(course_path)[1]).lstrip("/")
            # print("NEW EXERCISE_PATH = %s " % dbexercise.path)
            dbexercise.save(using=db)
            # print("NAME = %s PATH = %s " % (name, path) )
    # print("FINISH _EXERCISES_MOVE_FOLDER")
    if "error" in res:
        return Response(res)
    # for exercise_data in res['exercises']:
    #    Exercise.objects.add_exercise_full_path(exercise_data['path'], dbexercises[0].course)
    #    logger.info('Moved exercise ' + exercise_data['name'] + " to " + exercise_data['path'])
    return Response(res)


#@api_view(["POST"])
#@permission_required("exercises.edit_exercise")
#def noexercises_rename_folder(request, exercise):
#    print("EXERCSISE RENAME FOLDER")
#    caches["default"].set("temporarily_block_translations", True, 15)
#    _, db = get_subdomain_and_db(request)
#    old_folder = request.data.get("old_folder")
#    # print("OLD_FOLDER %s " % old_folder )
#    new_name = request.data.get("new_name").strip()
#    # print("NEW_NAME %s " % new_name )
#
#    if new_name[0] == "/":
#        new_folder_list = new_name.split("/")
#    else:
#        new_folder_list = old_folder.split("/")[:-1] + [new_name]
#    new_folder = "/".join(new_folder_list)
#    # print("NEW_FOLDER = %s " % new_folder)
#    dbexercises = Exercise.objects.using(db).filter(folder=old_folder) | Exercise.objects.using(db).filter(
#        folder__startswith=old_folder + "/"
#    )
#
#    # if dbexercises.count() == 0:
#    #    return Response(
#    #        {'error': 'There are no exercises in that folder'},
#    #        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#    #    )
#
#    course_path = dbexercises[0].course.get_exercises_path()
#    old_full_path = os.path.join(course_path, old_folder)
#    base_path = (old_full_path.split(old_folder)[0]).rstrip("/")
#    # print("BASE_PATH = %s " % base_path )
#    # print("NEW_FOLDER %s " % new_folder)
#    new_full_path = base_path + "/" + new_folder.lstrip("/")
#    # print("FULL PATH MOVE %s TO %s " % ( old_full_path, new_full_path) )
#    res = parsing.exercises_move_folder(old_full_path, new_full_path, db)
#    if "error" in res:
#        return Response(res, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#    course = dbexercises[0].course
#    for exercise_data in res["exercises"]:
#        newpath = exercises_data["path"]
#        Exercise.objects.using(db).update(path=newpath)
#        #Exercise.objects.add_exercise_full_path(exercise_data["path"], dbexercises[0].course)
#        logger.error("Moved exercise " + exercise_data["name"] + " to " + exercise_data["path"])
#    caches["default"].delete("temporarily_block_translations")
#    return Response({"success": "Moved exercise"})


@api_view(["GET"])
@permission_required("exercises.edit_exercise")
def exercise_history(request, exercise):
    _, db = get_subdomain_and_db(request)
    try:
        dbexercise = Exercise.objects.using(db).get(pk=exercise)
    except Exercise.DoesNotExist:
        logger.debug("Tried to access history for invalid exercise " + exercise)
        return Response({"error": "Invalid exercise"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(list_history(dbexercise.get_full_path()))


@api_view(["GET"])
@permission_required("exercises.edit_exercise")
def exercise_xml_history(request, exercise, name):
    _, db = get_subdomain_and_db(request)
    try:
        dbexercise = Exercise.objects.using(db).get(pk=exercise)
    except Exercise.DoesNotExist:
        logger.debug("Tried to access history for invalid exercise " + exercise)
        return Response({"error": "Invalid exercise"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(parsing.exercise_xml_history(dbexercise.get_full_path(), name))


@api_view(["GET"])
@permission_required("exercises.edit_exercise")
def exercise_json_history(request, exercise, name):
    _, db = get_subdomain_and_db(request)
    try:
        dbexercise = Exercise.objects.using(db).get(pk=exercise)
    except Exercise.DoesNotExist:
        logger.debug("Tried to access history for invalid exercise " + exercise)
        return Response({"error": "Invalid exercise"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(parsing.exercise_json_history(dbexercise.get_full_path(), name))
