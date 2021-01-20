import os
from django.conf import settings

TEMPLATE_EXERCISE_PATH = "../../exercise_templates"
TRASH_PATH = "z:Trash"
STUDENT_ASSETS_PATH = "/srv/multicourse/media/studentassets"
STUDENT_ASSET_PATH = "/srv/multicourse/media/studentassets"
#STUDENT_ANSWERIMAGES_PATH = "/srv/multicourse/media/answerimages"
EXERCISE_XML = 'exercise.xml'
EXERCISE_XSD = './exercises/exercise.xsd'
EXERCISES_PATH = settings.EXERCISES_PATH  #  '../../exercises'
LIVE_TRANSLATION_DICT_XML = 'locale/translationdict.xml'
DEFAULT_TRANSLATION_DICT_XML = 'translations/translationdict.xml'
EXERCISE_KEY = 'exercisekey'
EXERCISE_HISTORY = 'history'
EXERCISE_THUMBNAIL = 'thumbnail.png'


def get_student_asset_path(user, exercise):
    course_key = exercise.course.course_key
    return os.path.join(STUDENT_ASSETS_PATH,  str( course_key) , user.username, exercise.pk)

def get_exercise_asset_path(user, exercise):
    course_key = exercise.course.course_key
    return exercise.get_full_path() 
