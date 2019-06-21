"""Asset file handling."""
import os
import zipfile
import tarfile
import tempfile
from course.models import Course
from exercises.models import Exercise, ExerciseMeta
from django.core.exceptions import ObjectDoesNotExist
import logging
from image_utils import compress_pil_image_timestamp



LOGGER = logging.getLogger(__file__)


def list_assets(path, types):
    all_files = os.listdir(path)
    assets = [{'filename': asset} for asset in all_files if asset.lower().endswith(types)]
    return assets


def has_asset(path, asset):
    file_path = os.path.join(path, asset)
    return os.path.isfile(file_path)


def extract_exercise_archive(path, asset_file, types, course_key):
    extension = asset_file.name.split('.')[-1]
    contains_exercise_xml = False
    if 'zip' in extension:
        try:
            filelist = ''
            with zipfile.ZipFile(asset_file) as myzip:
                for member in myzip.namelist():
                    if member in ['exercise.xml']:
                        contains_exercise_xml = True
                    if member not in ['exercisekey']:
                        myzip.extract(member, path)
                        filelist = filelist + str(member) + ', '
        except zipfile.BadZipFile as e:
            LOGGER.error('zip extract error: ' + asset_file.name + ' ' + str(e))
            return {'error': 'Error extracting  zipfile : ' + asset_file.name}

    elif 'gz' in extension:
        try:
            temp_file_path = asset_file.temporary_file_path()
            filelist = ''
            with tarfile.open(temp_file_path) as mytar:
                for member in mytar.getmembers():
                    if member in ['exercise.xml']:
                        contains_exercise_xml = True
                    if member not in ['exercisekey']:
                        mytar.extract(member, path)
                        filelist = filelist + member.name + ', '
                    else:
                        pass
        except tarfile.TarError as e:
            LOGGER.error('tar extract error: ' + asset_file.name + ' ' + str(e))
            return {'error': 'Error extracting  tarfile : ' + asset_file.name}

    if contains_exercise_xml:
        try:
            dbcourse = Course.objects.get(course_key=course_key)
            Exercise.objects.add_exercise_full_path(path, dbcourse)
        except ObjectDoesNotExist as e:
            LOGGER.error("UNABLE TO RECREATE EXERCISE " + str(e))
            return {'error': 'Unable to create exercise. Perhaps exercise.xml is missing'}

    return {'success': 'Extracted: ' + filelist}


def add_asset(path, asset_file, types, course_key):
    """Create asset from uploaded file.

    Args:
        path (str): Path where asset is to be saved.
        asset_file (UploadedFile): Django uploaded file object.
        types (list(str)): List of approved file endings.

    Returns:
        dict: ::

            error (str): Error message
            success (str): Success message

    """
    file_path = os.path.join(path, asset_file.name)
    if not asset_file.name.lower().endswith(types):
        return {'error': 'File type not allowed, valid filetypes are: ' + ', '.join(types)}
    if os.path.isfile(file_path):
        return {'error': 'File already exists.'}
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)
    extension = asset_file.name.split('.')[-1]
    if extension in ('zip', 'gz'):
        return extract_exercise_archive(path, asset_file, types, course_key)
    else:
        try:
            with open(file_path, 'wb') as asset:
                for chunk in asset_file.chunks():
                    asset.write(chunk)
        except IOError:
            return {'error': "Couldn't write to asset file " + file_path}
    if  extension.lower()  in ('jpg','png','jpeg') :
            compress_pil_image_timestamp(file_path)
    return {'success': 'Wrote file'}


def delete_asset(path, asset_filename):
    file_path = os.path.join(path, asset_filename)
    if not os.path.isfile(file_path):
        return {'error': 'No such file!'}
    try:
        os.remove(file_path)
    except IOError:
        return {'error': "Couldn't delete asset file " + file_path}
    if os.path.isfile(file_path):
        return {'error': "Couldn't delete asset file " + file_path}

    return {'success': 'Deleted file'}
