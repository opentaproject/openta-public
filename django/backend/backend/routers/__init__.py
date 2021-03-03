from django.conf import settings
from aggregation.models import Aggregation
from course.models import Course
from django.contrib.auth.models import Group, User
from exercises.models import Answer, AuditExercise, ImageAnswer, Question, Answer, ExerciseMeta, Exercise
from django.contrib.sessions.models import Session
from users.models import OpenTAUser
import logging
logger = logging.getLogger(__file__)



#dbmodels = [ Aggregation, Course, Group, Answer, AuditExercise, Exercise, ExerciseMeta,  \
#    ImageAnswer, Question, OpenTAUser, User, Aggregation,  ExerciseMeta, Subpath]
#
## django.core.cache.backends.db.BaseDatabaseCache.__init__.<locals>.CacheEntry,\
#class AuthRouter:
#    """
#    A router to control all database operations on models in the
#    auth and contenttypes applications.
#    """
#    route_app_labels = {'auth', 'contenttypes','users','course','backend','opentalti'}
#
#
#    def db_for_read(self, model=None, **hints):
#        """
#        Attempts to read auth and contenttypes models go to default.
#        """
#        #print("SELF = ", self)
#        #if not model  == None:
#        #    #print("model read = ", model)
#        #else :
#        #    #print("model read = None")
#        #if model == None :
#        #    return settings.DB_NAME
#        if model in dbmodels:
#            try: 
#                #print("READ MODEL FOUND", model, "HINTS" , hints)
#            except:
#                #print("READ MODEL FOUND", "NO HINTS\n")
#            return settings.DB_NAME
#        else:
#            return 'default'
#
#    def db_for_write(self, model=None, **hints):
#        """
#        Attempts to write auth and contenttypes models go to default.
#        """
#        #print("SELF = ", self )
#        #if not model  == None:
#        #    #print("model write = ", model)
#        #else :
#        #    #print("model write = None")
#        if model in dbmodels:
#            
#            try: 
#                #print("WRITE MODEL FOUND", model, "HINTS" , hints )
#            except:
#                #print("WRITE READ MODEL FOUND", model )
#            return settings.DB_NAME
#        else:
#            return 'default'
#
#    def allow_relation(self, obj1, obj2, **hints):
#        """
#        Allow relations if a model in the auth or contenttypes apps is
#        involved.
#        """
#        #print("ALLOW RELATION")
#        return True
#
#    def allow_migrate(self, db, app_label, model_name=None, **hints):
#        """
#        Make sure the auth and contenttypes apps only appear in the
#        settings.DB_NAME database.
#        """
#        #print("APP_LABEL = ", app_label)
#        #print("ALLOW MIGRATE")
#        #print("MIGRATE model ", model_name)
#        
#        #if  hints == {} :
#        #   return 'default'
#        return settings.DB_NAME
#
# FROM class CacheRouter in django project

default_models = ['django_cache','workqueue','sites','opentasites']
site_models = []

class AuthRouter:
    """A router to control all database cache operations; see CacheRouter in djangoproject """

    def db_for_read(self, model, **hints):
        "All cache read operations go to the replica"
        #logger.info("READ MODEL label = %s " %  model._meta.app_label)
        if settings.RUNTESTS or model._meta.app_label in default_models :
            return 'default'
        elif model._meta.app_label in site_models :
            #print("RETURN DB READ SITES")
            return 'sites'
        #try: 
        #    #print("READ MODEL FOUND", model, "HINTS" , hints['instance'] )
        #except:
        #    #print("READ READ MODEL FOUND NO HINT", model )
        #print("RETURNING ", settings.DB_NAME)
        return settings.DB_NAME

    def db_for_write(self, model, **hints):
        #logger.info("WRIT MODEL label = %s  %s " %  ( model._meta.app_label, settings.DB_NAME ) )
        if settings.RUNTESTS or model._meta.app_label in default_models :
            return 'default'
        elif model._meta.app_label in site_models :
            #print("RETURN DB WRITE SITES")
            return 'sites'
        #try: 
        #    #print("WRITE MODEL FOUND", model, "HINTS" , hints['instance'] )
        #except:
        #    #print("WRITE READ MODEL FOUND NO HINT", model )
        #print("DB_WRITE DB_NAME = ", settings.DB_NAME )
        return settings.DB_NAME

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        "Only install the cache model on primary"
        #print("MIGRATE app_label ", app_label , " MODEL NAME = ", model_name )
        if settings.RUNTESTS or app_label == 'django_cache':
            return db == 'default'
        return True

    def allow_relation( self, bj1, obj2 , **hints):
        return True
