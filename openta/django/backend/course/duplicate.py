# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import datetime
import json
from django.core.cache import caches
import glob
import logging
import os
import re
import shutil
import subprocess
import time
import uuid
import zipfile
from collections import OrderedDict
from pathlib import Path
from backend.middleware import verify_or_create_database_connection

from course.export_import import (
    OpenTAUserResource,
    UserResource,
    export_course_exercises,
)
from course.models import Course
from exercises.models import Exercise, ExerciseMeta
from course.views import upload_zip_core

from django.conf import settings

logger = logging.getLogger(__name__)


def file_get_contents(filename):
    with open(filename) as f:
        return f.read()


# resource_lookup =  OrderedDict( { 'OpenTAUser': OpenTAUserResource() , 'User' : UserResource() } )
resource_lookup = OrderedDict({"OpenTAUser": OpenTAUserResource(), "User": UserResource()})


def duplicate_course(course: Course, *args, **kwargs):
    csv_data = {}
    messages = []
    print(f"DUPLICATE course {course}")
    c = 0
    if settings.MULTICOURSE:
        subdomain = str(course.opentasite)
        settings.SUBDOMAIN = subdomain
        settings.DB_NAME = subdomain
    else:
        subdomain = settings.SUBDOMAIN
    print(f"DUPLICATE2 SUBDMAIN = {subdomain}")
    #for resource_name in list(resource_lookup.keys()):
    #    resource = resource_lookup[resource_name]
    #    dataset = resource.export()
    #    csv_data[resource_name] = dataset.csv
    data = kwargs["data"]
    action = data.get("action")
    print(f" DATA = {data}")
    user = data.get("user", "nonuser")
    email = data.get("email", user.username + "@example.com")
    valid_email = not re.match(r"[\w\.-]+@[\w\.-]+(?:\.[\w]+)+", email) is None
    if not valid_email and not user.username == "super":
        print(f"STOP DUPLCATION, {valid_email} {email} ")
        raise NameError(f"Invalid_email email for ={user} with email={email}")
        yield "STOPPED", 1
    if not valid_email:
        email = f"{user}@localhost"
    print(f"CONTINUE DATA = {data}")
    password = data.get("password", "nopassword")
    print(f"user={user} password={password} email={email}")
    newname = data.get("newname", subdomain)
    valid_subdomain = not os.path.isdir(f"/subdomain-data/{newname}")
    print(f"ACTION = {action}")
    if action == "modify":
        alter_meta(course, data)
        return course
    if not valid_subdomain:
        print(f"STOP DUPLCATION, {valid_subdomain} {newname} ")
        raise NameError(f"Invalid subdomain {newname} already exists")
        yield "STOPPED", 1
    print(f"NEWNAME = {newname} oldname = {course.course_name}")
    if action == "duplicate":
        tbeg = time.time()
        c = c + 1
        yield (f"{c} Creating course ; takes about 30 seconds", 0.1)
        process = subprocess.Popen(["./db_createcourse", newname, email], stdout=subprocess.PIPE)
        # subprocess.run(['./osx_db_createcourse',newname,email] )
        for line in process.stdout:
            c = c + 1
            dt = ((time.time() - tbeg)) / 20.0
            pline = "" if not settings.DEBUG else line[0:30]
            yield (f"{c} Create blank course ; can take two minutes {pline}", dt)
        globber = glob.glob(f"/subdomain-data/{newname}/exercises/*")
        dest = glob.glob(f"/subdomain-data/{newname}/exercises/*")[0]
        verify_or_create_database_connection(newname)
        yield (f"{c} Zipping old exercises", 0.2)
        for i in export_course_exercises(course, dest):
            c = c + 1
            yield (f"{c} Zipping old exercises ", 0.2)
            tt = list(i)[1]
        zip_path = glob.glob(f"{dest}/*.zip")[-1]
        server_zip = zipfile.ZipFile(zip_path, "r")
        namelist = server_zip.namelist()
        logger.info(f"zip_path= {zip_path}")
        yield "Unzipping  exercises to new course ", 0.2
        upload_zip_core( course.pk, zip_path, newname )
        os.remove(zip_path)
        readme = f"{dest}/README"
        if os.path.exists(readme) :
            os.remove( readme) 
        exercises = Exercise.objects.using(newname).all()
        for exercise in exercises:
            ca = caches["default"].get("temporarily_block_translations")
            # logger.info(f"CA = {ca}" )
            # print(f"EXERCIS IN IMPORT {exercise}")
            meta = exercise.meta
            fullpath = exercise.get_full_path()
            jsonfile = os.path.join(fullpath, "meta.json")
            for f in ['display.html','README'] :
                ff = os.path.join(fullpath, f )
                if os.path.exists( ff ):
                    os.remove( ff )
            if os.path.exists(jsonfile):
                # print(f"jsonfile = {jsonfile} exists ")
                with open(jsonfile, "r") as f:
                    s = f.read()
                j = json.loads(s)
                # print(f"j = {j}")
                for key in [
                    "difficulty",
                    "required",
                    "image",
                    "allow_pdf",
                    "bonus",
                    "published",
                    "locked",
                    "sort_key",
                    "feedback",
                    "deadline_date",
                ]:
                    jm = getattr(meta, key)
                    # print(f"KEY={key} {j[key]} {jm}")
                    setattr(meta, key, j[key])
                # print(f" META = {meta}")
                meta.save()
                exercise.meta = meta
                exercise.save()
                os.remove(jsonfile)
        
        #
        #ntot = float(len(namelist))
        #nc = 0
        #for index, member in enumerate(namelist):
        #    c = c + 1
        #    server_zip.extract(member, path=dest)
        #    prog = index / max(ntot, 1)
        #    if "exercise.xml" in member:
        #        nc = nc + 1
        #    yield f"{c} Unzipping new exercises ", prog
        #yield "Unzip done   ", float(0.6)
        #for resource_name in csv_data.keys():
        #    with open(f"{dest}/{resource_name}.csv", "w") as output_file:
        #        output_file.write(csv_data[resource_name])
        #os.remove(zip_path)
        #c = c + 1
        #yield (f"{c} Syncing exercises : can silently take two minutes", 0.9)
        #process = subprocess.Popen(["./db_sync_exercises", newname], stdout=subprocess.PIPE)
        #i = 0
        #den = max(float(nc) * 1.1, 1)
        #for line in iter(process.stdout.readline, b""):
        #    i = i + 1
        #    c = c + 1
        #    print(f" FLOAT = {i} { den } { float(i)/den }")
        #    pline = "" if not settings.DEBUG else line[0:30]
        #    yield (f"{c} Syncing exercises : can silently take two minutes {pline} ", float(i) / den)
        #logger.info(f"DEST = {dest}")
        #process = subprocess.Popen(["./db_load_users", newname], stdout=subprocess.PIPE)
        #for line in process.stdout:
        #    c = c + 1
        #    logger.info(f"LINE = {line}")
        #    dt = ((time.time() - tbeg)) / 10.0
        #    yield (f"{c} Fixing up users", 0.9)

        #shutil.rmtree(f"{dest}/xsl")
    #process = subprocess.Popen(["./db_backup", newname], stdout=subprocess.PIPE)
    #for line in process.stdout:
    #    c = c + 1
    #    logger.info(f"LINE = {line}")
    #    dt = ((time.time() - tbeg)) / 10.0
    #    yield (f"{c} Making a backup of the course", 0.95)
    #opentasites = OpenTASite.objects.filter(subdomain=newname)
    #
    # MONKEYPATCHED ERRONEOUS CREATE OF AN OPENTASITE WITH BLANK COURSE_KEY
    #
    #for opentasite in opentasites:
    #    if not opentasite.course_key:
    #        opentasite.delete()
    #    else:
    #        now = datetime.datetime.now()
    #        t = now.strftime("%Y-%m-%d %H:%M:%S")
    #        opentasite.db_label = f"Created from {subdomain} on {t} "
    #        print(f"NOW SETTING EMAIL {email}")
    #        opentasite.creator = email
    #        opentasite.data = {"creation_date": t, "creator": email}
    #        opentasite.save()

    yield ("Done", 1)


def alter_meta(course: Course, data):
    print(f"ALTER META data = {data}")
    days = data["days"]
    db = course.opentasite
    print(f"DB = {db}")
    exercises = list(Exercise.objects.using(db).filter(course=course))
    for exercise in exercises:
        print(f"EXERCISE = {exercise}")
        meta_date_names = ["deadline_date"]
        for name in meta_date_names:
            print(f"NAME = {name}")
            olddate = getattr(exercise.meta, name)
            if not olddate == None:
                newdate = getattr(exercise.meta, name) + datetime.timedelta(days=int(days))
            else:
                newdate = None
            setattr(exercise.meta, str(name), newdate)
        for name, val in data.items():
            if (type(val) == bool) and (not val):
                getattr(exercise.meta, str(name))
                default = ExerciseMeta._meta.get_field(name).get_default()
                setattr(exercise.meta, str(name), default)
        exercise.meta.save()


def old_duplicate_course(course: Course, *args, **kwargs):
    # This is the old routine that
    # clones the course as a subpath
    # It is saved here as archive
    # It is replacement compatible with the new
    # which creates an entirely new server
    print(f"DUPLICATE course {course}")
    if settings.MULTICOURSE:
        subdomain = str(course.opentasite)
        settings.SUBDOMAIN = subdomain
        settings.DB_NAME = subdomain
    else:
        subdomain = settings.SUBDOMAIN
    db = subdomain
    print(f"DUPLICATE SUBDMAIN = {subdomain}")
    data = kwargs["data"]
    newname = data.get("newname", course.course_name)
    data.get("days", "0")
    yield ("Beginning", 0)
    if not newname == course.course_name:
        n_exercises = Exercise.objects.using(db).filter(course=course).count()
        old_exercises = Exercise.objects.using(db).filter(course=course)
        old_uuid = str(course.course_key)
        old_exercises_path = course.get_exercises_path()
        course.pk = None
        course.course_key = uuid.uuid4()
        new_uuid = str(course.course_key)
        course.lti_secret = uuid.uuid4()
        course.lti_key = uuid.uuid4()
        course.course_name = newname
        course.published = False
        try:
            course.save()
        except Exception as e:
            logger.error("SAVE ERROR = %s " % str(e))
        course.save()
        new_exercises_path = re.sub("sites", subdomain, course.get_exercises_path())
        yield ("Copying exercises file tree, this could take some time...", 0)
        shutil.copytree(old_exercises_path, new_exercises_path)
        for key_file in Path(new_exercises_path).glob("**/exercisekey"):
            key_file.unlink()
        print("ENUMERATE")
        for index, _ in enumerate(Exercise.objects.using(db).sync_with_disc(course, i_am_sure=True)):
            if index % (n_exercises // 20 + 1) == 0:
                yield ("Populationg exercises ...", index / max(n_exercises, 1))
        print("DONE YIELD")
        new_exercises = Exercise.objects.using(db).filter(course=course)
        exercises_path = new_exercises_path
        exerciselist = []
        print(f"EXERCISES_PATH {exercises_path}")
        print(f"NEW_EXERCISES {new_exercises}")
        for root, directories, filenames in os.walk(exercises_path, followlinks=True):
            for filename in filenames:
                if filename == "exercise.xml":
                    name = os.path.basename(os.path.normpath(root))
                    relpath = root[len(exercises_path) :]
                    if not relpath == "":  # GET RID OF EDGE CASE WHEN exercise.xml mistakenly is put in root dir
                        exerciselist.append((name, relpath))
        nocopy = ["id", "_state", "exercise_id"]
        subdomaindata = f"{settings.VOLUME}/"
        print(f"EXERCISELIST = {exerciselist}")
        for _, key_file in exerciselist:
            try:
                oldkey = file_get_contents(
                    subdomaindata + subdomain + "/exercises" + "/" + str(old_uuid) + str(key_file) + "/" + "exercisekey"
                )
                print(f"OLDKEY = {oldkey}")
                newkey = file_get_contents(
                    subdomaindata + subdomain + "/exercises" + "/" + new_uuid + str(key_file) + "/" + "exercisekey"
                )
                print(f"NEWWKYE = {newkey}")
                old_exercise = Exercise.objects.using(db).get(exercise_key=oldkey)
                new_exercise = Exercise.objects.using(db).get(exercise_key=newkey)
                meta_names = list(old_exercise.meta.__dict__.keys())
                print(f"META NAMES = {meta_names}")
                for name in meta_names:
                    if not name in nocopy:
                        setattr(
                            new_exercise.meta,
                            str(name),
                            getattr(old_exercise.meta, str(name)),
                        )
                new_exercise.meta.save()
            except Exception as e:
                yield ("Duplication error  for  %s " % str("new_exercise"), 0)
    yield ("Modify Meta", 0)
    alter_meta(course, data)
    return course
