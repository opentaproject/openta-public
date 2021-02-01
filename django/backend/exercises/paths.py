import os
from django.conf import settings

TEMPLATE_EXERCISE_PATH = "../../exercise_templates"
TRASH_PATH = "z:Trash"
STUDENT_ASSETS_PATH = settings.VOLUME + '/'  + settings.DB_NAME + '/media/studentassets'
#STUDENT_ASSETS_PATH = settings.MEDIA_ROOT + '/studentassets'
STUDENT_ASSET_PATH = STUDENT_ASSETS_PATH
STUDENT_ANSWERIMAGES_PATH = settings.VOLUME + '/' + settings.SUBDOMAIN +  "/media/answerimages"
STUDENT_ANSWERIMAGES_PATH = settings.MEDIA_ROOT + "/answerimages"
EXERCISE_XML = 'exercise.xml'
EXERCISE_XSD = './exercises/exercise.xsd'
EXERCISES_PATH = settings.VOLUME + '/' + settings.DB_NAME +  '/exercises' 
LIVE_TRANSLATION_DICT_XML = 'locale/translationdict.xml'
DEFAULT_TRANSLATION_DICT_XML = 'translations/translationdict.xml'
EXERCISE_KEY = 'exercisekey'
EXERCISE_HISTORY = 'history'
EXERCISE_THUMBNAIL = 'thumbnail.png'

def _subpath(**kwargs):
    #subpath = settings.SUBPATH
    if settings.SUBPATH == '/'  or settings.SUBPATH == '' : # don't parse subpaths if there is none
        return ''
    if not settings.SUBPATH_REGEX  :
        return settings.SUBPATH
    #try: 
    #    for key, value in kwargs.items(): 
    #        print ("%s == %s" %(key, value)) 
    #        if key == 'session' :
    #            print("SESSON KEYS = ", value.keys() )
    #            subpath = value['subpath'] + '/'
    try:
        subpath = kwargs['uri'].split('/')[1] + '/'
    except:
        subpath = '/'
    #if subpath in ['login/','1/','logout/','favicon.ico/','','2/','3/','exercise/'] :
    #    subpath = settings.SUBPATH
    #if subpath == '' :
    #    subpath = settings.SUBPATH
    print("PATHS: subpath = ",  '>' + subpath + '<')
    return  subpath
    #return settings.SUBPATH


def get_student_asset_path(user, exercise):
    course_key = exercise.course.course_key
    print("STUDENT_ASSETS_PATH = ", STUDENT_ASSETS_PATH)
    print("settings.SUBDOMAIN = ", settings.SUBDOMAIN)
    multipath = settings.VOLUME + '/'  + settings.DB_NAME + '/media/studentassets'
    return os.path.join(multipath ,  str( course_key) , user.username, exercise.pk)

def get_exercise_asset_path(user, exercise):
    course_key = exercise.course.course_key
    return exercise.get_full_path() 
