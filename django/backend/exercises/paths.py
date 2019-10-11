import os
from django.conf import settings

TEMPLATE_EXERCISE_PATH = "../../exercise_templates"
TRASH_PATH = "z:Trash"
STUDENT_ASSETS_PATH = "media/studentassets"
STUDENT_ANSWERIMAGES_PATH = "media/answerimages"
EXERCISE_XML = 'exercise.xml'
EXERCISE_XSD = './exercises/exercise.xsd'
EXERCISES_PATH = settings.EXERCISES_PATH  #  '../../exercises'


def get_student_asset_path(user, exercise):
    """Get path to asset folder.
>>>>>>> Fix login if two courses exist with same name

    Args:
        user (User): Django user object.
        exercise (Exercise): Exercise model object.

    Returns:
        str: Full path to asset folder

    """
    return os.path.join(STUDENT_ASSETS_PATH, user.username, exercise.pk)


#
#
# def get_student_assets_path(user, exercise):
#    """Get path to asset folder.
#
#    Args:
#        user (User): Django user object.
#        exercise (Exercise): Exercise model object.
#
#    Returns:
#        str: Full path to asset folder
#
#    """
#    return os.path.join(STUDENT_ASSETS_PATH, user.username, exercise.pk)
#
#
# def get_student_answerimages_path(user, exercise):
#    """Get path to asset folder.
#
#    Args:
#        user (User): Django user object.
#        exercise (Exercise): Exercise model object.
#
#    Returns:
#        str: Full path to asset folder
#
#    """
#    return os.path.join(STUDENT_ANSWERIMAGES_PATH, user.username, exercise.pk)
