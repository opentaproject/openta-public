import os
from exercises.models import Exercise, Answer, Question
from course.models import Course
from datetime import timedelta
from django.contrib.auth.models import User
import shutil
from pathlib import Path
import re
import datetime
import uuid
import logging
from opentasites.models import OpenTASite


logger = logging.getLogger(__name__)

def file_get_contents(filename):
    with open(filename) as f:
        return f.read()


def duplicate_course(course: Course,  *args, **kwargs):
    subdomain = str( course.opentasite.db_name )
    logger.info("SUBDOMAIN OBTAINED %s " % subdomain )
    data = kwargs['data']
    newname = data.get('newname', course.course_name)
    days = data.get('days', '0')
    logger.info("BEGGING DUPLICATE")
    logger.info("SUBDOMAIN = %s " % subdomain)
    yield ("Beginning", 0)
    if not newname == course.course_name:
        logger.info("BEGIN = %s " % subdomain)
        old_course = course
        n_exercises = Exercise.objects.filter(course=course).count()
        old_exercises = Exercise.objects.filter(course=course)
        old_uuid = str(course.course_key)
        old_exercises_path = course.get_exercises_path()
        course.pk = None
        course.course_key = uuid.uuid4()
        new_uuid = str(course.course_key)
        course.lti_secret = uuid.uuid4()
        course.lti_key = uuid.uuid4()
        # if newname == None :
        #   newname = "{old}-copy".format(old=course.course_name)
        course.course_name = newname
        course.published = False
        logger.info("TRY TO SAVE COURSE" )
        try: 
            course.save()
        except Exception as e:
            logger.info("SAVE ERROR = %s " % str(e) )
        course.save()
        new_exercises_path = re.sub('sites',subdomain,  course.get_exercises_path() )
        logger.info("SUCCEEDED IN SAVING THE COURSE")
        logger.info("EXERCISES PATH OLD AND NEW %s %s " % ( old_exercises_path, new_exercises_path) )
        yield ("Copying exercises file tree, this could take some time...", 0)
        shutil.copytree(old_exercises_path, new_exercises_path)
        for key_file in Path(new_exercises_path).glob("**/exercisekey"):
            key_file.unlink()
        for index, _ in enumerate(Exercise.objects.sync_with_disc(course, i_am_sure=True)):
            if index % (n_exercises // 20 + 1) == 0:
                yield ("Populationg exercises ...", index / n_exercises)
        logger.debug("UPDATED EXERCISES")
        new_exercises = Exercise.objects.filter(course=course)
        exercises_path = new_exercises_path
        logger.debug("EXERCISES-PATH = %s " % exercises_path)
        exerciselist = []
        for root, directories, filenames in os.walk(exercises_path, followlinks=True):
            for filename in filenames:
                if filename == 'exercise.xml':
                    name = os.path.basename(os.path.normpath(root))
                    relpath = root[len(exercises_path) :]
                    # THE NEXT COMMAND CAUSED SYNC TO CRASH WHEN exercise.xml mistakenly is put in root dir
                    if (
                        not relpath == ''
                    ):  # GET RID OF EDGE CASE WHEN exercise.xml mistakenly is put in root dir
                        exerciselist.append((name, relpath))
        logger.debug("FINSHED COPYYING OVER EXERCISES")
        nocopy = ['id', '_state', 'exercise_id']
        for (_, key_file) in exerciselist:
            try:
                oldkey = file_get_contents(
                    '/subdomain-data/' + subdomain + '/exercises' + '/' + old_uuid + '/' + str(key_file) + '/' + 'exercisekey'
                )
                newkey = file_get_contents(
                    '/subdomain-data/' + subdomain + '/exercises' + '/' + new_uuid + '/' + str(key_file) + '/' + 'exercisekey'
                )
                #newkey = file_get_contents(
                #    '../../exercises/' + new_uuid + '/' + str(key_file) + '/' + 'exercisekey'
                #)
                old_exercise = Exercise.objects.get(exercise_key=oldkey)
                new_exercise = Exercise.objects.get(exercise_key=newkey)
                meta_names = list(old_exercise.meta.__dict__.keys())
                for name in meta_names:
                    if not name in nocopy:
                        setattr(new_exercise.meta, str(name), getattr(old_exercise.meta, str(name)))
                new_exercise.meta.save()
            except Exception as e :
                logger.error("FAILURE TO COPY META FOR =  %s %s %s" % (  str( 'new_exercise') , str( newkey) , str( meta_names)) )
                logger.error("Error is  %s " % str(e) )
                yield("Duplication error  for  %s " % str('new_exercise') , 0)
                pass
    yield("Modify Meta",0)
    alter_meta(course, data)
    return course


def alter_meta(course: Course, data):
    days = data['days']
    exercises = list(Exercise.objects.filter(course=course))
    for exercise in exercises:
        meta_date_names = ['deadline_date']
        for name in meta_date_names:
            olddate = getattr(exercise.meta, name)
            print("OLDDATE = ", olddate)
            if not olddate == None:
                newdate = getattr(exercise.meta, name) + datetime.timedelta(days=int(days))
            else:
                newdate = None
            print("NEWDATE = ", newdate)
            setattr(exercise.meta, str(name), newdate)
        for name, val in data.items():
            if (type(val) == bool) and ( not val ):
                oldvalue = getattr(exercise.meta, str(name))
                default = ExerciseMeta._meta.get_field(name).get_default()
                setattr(exercise.meta, str(name), default)
        exercise.meta.save()
