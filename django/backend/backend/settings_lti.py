from backend.settings_subpath import *

# Override needed settings here

INSTALLED_APPS.append('opentalti')
TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'opentalti', 'templates'))
AUTHENTICATION_BACKENDS = ['opentalti.apps.LTIAuth', 'django.contrib.auth.backends.ModelBackend']
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
TIME_ZONE = 'Europe/Copenhagen'

# THE NEXT FLAG FORCES ALL NON-STUDENT Roles to Student
# THIS IS IMPORTANT SAFETY FEATURE SO THAT LOCAL MISCONFIGURATIONS
# DO NOT ACCIDENTALL COMPROMISE OpenTA
FORCE_ROLE_TO_STUDENT = True 

# ROLES ALLOWED
VALID_ROLES = ['ContentDeveloper', 'Learner', 'Student', 'Instructor', 'Observer','TeachingAssistant']
