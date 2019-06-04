import os

EXERCISES_PATH = "../../exercises"
TEMPLATE_EXERCISE_PATH = "../../exercise_templates"
TRASH_PATH = "z:Trash"
STUDENT_ASSETS_PATH = "media/studentassets"
EXERCISE_XML = 'exercise.xml'
EXERCISE_XSD = './exercises/exercise.xsd'


def get_student_asset_path(user, exercise):
    """Get path to asset folder.

    Args:
        user (User): Django user object.
        exercise (Exercise): Exercise model object.

    Returns:
        str: Full path to asset folder

    """
    return os.path.join(STUDENT_ASSETS_PATH, user.username, exercise.pk)
