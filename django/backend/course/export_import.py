import os
from exercises.aggregation import student_statistics_exercises, students_results
from django.db.models import Q
from exercises.models import Exercise, Answer, Question, ExerciseMeta, ImageAnswer, AuditExercise
from course.models import Course
from users.models import OpenTAUser
from django.contrib.auth.models import User, Group
from pprint import pprint

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.widgets import DateTimeWidget
from import_export.widgets import ManyToManyWidget
from import_export.widgets import Widget
from import_export.instance_loaders import BaseInstanceLoader
from django.utils.timezone import localtime, get_current_timezone, make_aware
from django.conf import settings
import pytz
from datetime import datetime
import time
import tablib
import zipfile
from pathlib import Path
from exercises.paths import *

import logging
import tempfile
from django.utils.encoding import smart_text
from workqueue.util import TaskResult

SERVER_EXERCISES_EXPORT_FILENAME = 'exercises.zip'
STUDENT_ASSETS_EXPORT_FILENAME = 'assets.zip'
STUDENT_ANSWERIMAGES_EXPORT_FILENAME = 'answerimages.zip'
SERVER_EXPORT_FILENAME = 'server.zip'
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

LOGGER = logging.getLogger(__file__)


class ExportError(Exception):
    """Export error"""


class ImportError(Exception):
    """Import error"""


class TzDateTimeWidget(DateTimeWidget):
    """Custom datetime handling to ensure timezone correctness.

    The default behaviour of django-export-import DateTimeWidget is to
    export and import in the locally defined timezone, i.e. what is defined
    in settings.py. To be robust against importing in a different timezone this
    class changes the behaviour to always export and import in UTC.

    """

    def render(self, value, obj=None):
        """Render time in UTC."""
        render_value = value
        if settings.USE_TZ:
            render_value = get_current_timezone().normalize(value).astimezone(pytz.utc)
        return super(TzDateTimeWidget, self).render(render_value)

    def clean(self, value, row=None, *args, **kwargs):
        """Override clean to parse time as UTC."""
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        for format in self.formats:
            try:
                dt = datetime.strptime(value, format)
                if settings.USE_TZ:
                    dt = make_aware(dt, pytz.utc)
                return dt
            except (ValueError, TypeError):
                continue
        raise ValueError("Enter a valid date/time.")


class QuestionForeignKeyWidget(ForeignKeyWidget):
    def render(self, value, obj=None):
        """Dummy render.

        The question render is handled explicitly in the Answer resource.

        """
        return ""

    def clean(self, value, row=None, *args, **kwargs):
        try:
            return self.get_queryset(value, row, *args, **kwargs).get(
                question_key__iexact=row["question__question_key"],
                exercise__exercise_key__iexact=row["question__exercise__exercise_key"],
            )
        except Exception as e:
            LOGGER.error(str(e))
            LOGGER.error(str(row))


class CourseResource(resources.ModelResource):
    def __init__(self, *args, **kwargs):
        self._course = None
        if 'course' in kwargs:
            self._course = kwargs.pop('course')
        super().__init__(*args, **kwargs)

    class Meta:
        model = Course
        fields = (
            'course_key',
            'course_name',
            'course_long_name',
            'registration_domains',
            'registration_by_domain',
            'languages',
        )
        exclude = ('id', 'lti_secret', 'lti_key')
        import_id_fields = ('course_key',)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(pk=self._course.pk)
        else:
            return self._meta.model.objects.all()


class ExerciseResource(resources.ModelResource):
    course = fields.Field(
        column_name='course',
        attribute='course',
        widget=ForeignKeyWidget(Course, field='course_key'),
    )

    class Meta:
        model = Exercise
        exclude = ('id',)
        import_id_fields = ('exercise_key',)

    def __init__(self, *args, **kwargs):
        self._course = None
        if 'course' in kwargs:
            self._course = kwargs.pop('course')
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(course=self._course)
        else:
            return self._meta.model.objects.all()


class ExerciseMetaResource(resources.ModelResource):
    exercise = fields.Field(
        column_name='exercise',
        attribute='exercise',
        widget=ForeignKeyWidget(Exercise, field='exercise_key'),
    )

    class Meta:
        model = ExerciseMeta
        newfields = [f.name for f in model._meta.get_fields()]
        newfields.remove('id')
        fields = tuple(newfields)
        LOGGER.debug("fields" + str(fields))
        exclude = ('id',)
        import_id_fields = ('exercise',)
        # COMPUTE META FIELDS TO ADD
        # PLEASE RETAIN THIS COMMENT BLOCK
        #newfields = [f.name for f in model._meta.get_fields()]
        #newfields.remove('id')
        #fields = tuple(newfields)
        

    def __init__(self, *args, **kwargs):
        self._course = None
        if 'course' in kwargs:
            self._course = kwargs.pop('course')
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(exercise__course=self._course)
        else:
            return self._meta.model.objects.all()


class AnswerResource(resources.ModelResource):
    user = fields.Field(
        column_name='user', attribute='user', widget=ForeignKeyWidget(User, field='username')
    )
    question = fields.Field(
        column_name='Question', attribute='question', widget=QuestionForeignKeyWidget(Question)
    )

    date = fields.Field(
        column_name='date', attribute='date', widget=TzDateTimeWidget(format=DATETIME_FORMAT)
    )

    class Meta:
        model = Answer
        fields = (
            'user',
            'question__question_key',
            'answer',
            'grader_response',
            'correct',
            'date',
            'user_agent',
            'question__exercise__exercise_key',
        )
        import_id_fields = ('user', 'date', 'question')
        exclude = ('id', 'question')

    def __init__(self, *args, **kwargs):
        self._course = None
        if 'course' in kwargs:
            self._course = kwargs.pop('course')
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(
                question__exercise__course=self._course,
                # if unenrolled user such as 'student' has answered
                # it breaks import. Therefor the next line
                user__opentauser__courses=self._course,  # if unenrolled user such as 'student' has answered
            ).exclude(question__isnull=True)
        else:
            return self._meta.model.objects.all().exclude(question__isnull=True)


class ImageAnswerResource(resources.ModelResource):
    user = fields.Field(
        column_name='user', attribute='user', widget=ForeignKeyWidget(User, field='username')
    )
    exercise = fields.Field(
        column_name='exercise',
        attribute='exercise',
        widget=ForeignKeyWidget(Exercise, field="exercise_key"),
    )

    date = fields.Field(
        column_name='date', attribute='date', widget=TzDateTimeWidget(format=DATETIME_FORMAT)
    )

    class Meta:
        model = ImageAnswer
        import_id_fields = ('user', 'date', 'exercise')
        newfields = [f.name for f in model._meta.get_fields()]
        newfields.remove('id')
        fields = tuple(newfields)
        LOGGER.debug("fields" + str(fields))
        exclude = ('id',)

    def __init__(self, *args, **kwargs):
        self._course = None
        if 'course' in kwargs:
            self._course = kwargs.pop('course')
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(
                exercise__course=self._course,
                # if unenrolled user such as 'student' has answered
                # it breaks import. Therefor the next line
                user__opentauser__courses=self._course,
            ).exclude(exercise__isnull=True)
        else:
            return self._meta.model.objects.all().exclude(exercise__isnull=True)


class QuestionResource(resources.ModelResource):
    class Meta:
        model = Question
        import_id_fields = ('exercise', 'question_key')
        exclude = ('id',)

    def __init__(self, *args, **kwargs):
        self._course = None
        if 'course' in kwargs:
            self._course = kwargs.pop('course')
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(exercise__course=self._course)
        else:
            return self._meta.model.objects.all()


class UserCoursesWidget(ManyToManyWidget):
    def render(self, value, obj=None):
        ids = [smart_text(obj.course_key) for obj in value.all()]
        print("COURSES IDS = ", ids)
        return self.separator.join(ids)


CAREFUL_IMPORT = True


class OpenTAUserResource(resources.ModelResource):
    def skip_row(self, instance, original):
        try:
            print("SKIP_ROW instance ", instance)
        except:
            print(" THEE WAS NOT INSTANCE ")
        try:
            print("SKIP_ROW original ", original)
        except:
            print("THERE WAS NO ORIGINAL")
        # Add code here
        if CAREFUL_IMPORT:
            return super(OpenTAUserResource, self).skip_row(instance, original)
        else:
            return False

    user = fields.Field(
        column_name='user', attribute='user', widget=ForeignKeyWidget(User, field='username')
    )
    courses = fields.Field(
        column_name='courses',
        attribute='courses',
        widget=UserCoursesWidget(Course, field="course_key"),
    )
    print("USER = ", user, "COURES = ", courses)

    class Meta:
        model = OpenTAUser
        # fields = ('user', 'courses','lti_user_id',
        #    'lis_person_contact_email_primary',
        #    'lti_tool_consumer_instance_guid',
        #    'lti_context_id', 'lti_roles',
        #    'lis_person_name_full',
        #    'lis_person_name_given',
        #    'lis_person_name_family',
        #    'immutable_user_id',)
        import_id_fields = ('user',)
        skip_unchanged = CAREFUL_IMPORT
        newfields = [f.name for f in model._meta.get_fields()]
        newfields.remove('id')
        fields = tuple(newfields)
        exclude = ('id',)
        print(" OPENTA_USER GETTING fields" + str(fields))

    def __init__(self, *args, **kwargs):
        self._course = None
        if 'course' in kwargs:
            self._course = kwargs.pop('course')
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(courses=self._course)
        else:
            return self._meta.model.objects.all()


class UserResource(resources.ModelResource):
    groups = fields.Field(
        column_name='groups', attribute='groups', widget=ManyToManyWidget(Group, field="name")
    )

    class Meta:
        model = User
        exclude = ('id',)
        import_id_fields = ('username',)
        skip_unchanged = CAREFUL_IMPORT

    def __init__(self, *args, **kwargs):
        self._course = None
        if 'course' in kwargs:
            self._course = kwargs.pop('course')
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(opentauser__courses=self._course)
        else:
            return self._meta.model.objects.all()


class AuditExerciseResource(resources.ModelResource):
    student = fields.Field(
        column_name='student', attribute='student', widget=ForeignKeyWidget(User, field='username')
    )
    auditor = fields.Field(
        column_name='auditor', attribute='auditor', widget=ForeignKeyWidget(User, field='username')
    )
    exercise = fields.Field(
        column_name='exercise',
        attribute='exercise',
        widget=ForeignKeyWidget(Exercise, field="exercise_key"),
    )

    class Meta:
        model = AuditExercise
        exclude = ('id',)
        import_id_fields = ('student', 'exercise')

    def __init__(self, *args, **kwargs):
        self._course = None
        if 'course' in kwargs:
            self._course = kwargs.pop('course')
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(exercise__course=self._course)
        else:
            return self._meta.model.objects.all()


def export_server(output_path='export'):
    """Export server to zip file.

    Exports all supported models to a portable CSV format.
    Saves the full exercise file tree for all courses.

    Args:
        output_path (str, optional): Where to save the server export. Defaults to 'export'.

    Yields:
        float: Fraction complete

    """
    subpath = "server"
    full_path = os.path.join(output_path, subpath)
    LOGGER.debug("EXPORT_SERVER")
    for status, progress in _export_databases(full_path):
        yield TaskResult(status=status, progress=progress, result=None)

    exercises_zip_path = os.path.join(full_path, SERVER_EXERCISES_EXPORT_FILENAME)
    for _, progress in _zip_recursively(
        output_filepath=exercises_zip_path, input_path=EXERCISES_PATH
    ):
        yield TaskResult(status="Compressing exercises", progress=progress, result=None)

    assets_zip_path = os.path.join(full_path, STUDENT_ASSETS_EXPORT_FILENAME)
    for _, progress in _zip_recursively(
        output_filepath=assets_zip_path, input_path=STUDENT_ASSETS_PATH
    ):
        yield TaskResult(status="Compressing assets", progress=progress, result=None)

    total_zip_path = os.path.join(output_path, SERVER_EXPORT_FILENAME)
    for _, progress in _zip_recursively(output_filepath=total_zip_path, input_path=full_path):
        yield TaskResult(status="Compiling output", progress=progress, result=total_zip_path)


def export_course(course, output_path='export'):
    LOGGER.debug("EXPORT_COURSE output_path = " + str(output_path))
    LOGGER.debug("EXERCISES_PATH = " + str(EXERCISES_PATH))
    subpath = "server"
    full_path = os.path.join(output_path, subpath)
    for status, progress in _export_databases(full_path, course=course):
        LOGGER.debug("STATUS, PROGRESS" + str(status) + str(progress))
        yield TaskResult(status=status, progress=progress, result=None)

    exercises_zip_path = os.path.join(full_path, SERVER_EXERCISES_EXPORT_FILENAME)
    LOGGER.debug(" A: EXERCISES ZIP_PATH " + str(exercises_zip_path))
    LOGGER.debug(" B: EXERCISES_PATH " + str(EXERCISES_PATH))
    LOGGER.debug(" C: INPUT_PATH " + str(course.get_exercises_path()))
    LOGGER.debug(" D: DIRLIST = " + str(os.listdir(course.get_exercises_path())))
    for _, progress in _zip_recursively(
        output_filepath=exercises_zip_path,
        input_path=course.get_exercises_path(),
        relative_base=EXERCISES_PATH,
    ):
        yield TaskResult(status="Compressing exercises", progress=progress, result=None)

    LOGGER.debug(" DID COMPRESS")

    exercises_list = Exercise.objects.filter(course=course)
    exercises_keys = list(exercises_list.values_list('exercise_key', flat=True))
    assets_zip_path = os.path.join(full_path, STUDENT_ASSETS_EXPORT_FILENAME)
    LOGGER.debug(" ASSETS ZIP_PATH " + str(assets_zip_path))
    for _, progress in _zip_assets_recursively(
        output_filepath=assets_zip_path, input_path=STUDENT_ASSETS_PATH, keys=exercises_keys
    ):
        yield TaskResult(status="Compressing assets", progress=progress, result=None)

    answerimages_zip_path = os.path.join(full_path, STUDENT_ANSWERIMAGES_EXPORT_FILENAME)
    LOGGER.debug(" ANSWERIMAGES ZIP_PATH " + str(answerimages_zip_path))
    for _, progress in _zip_assets_recursively(
        output_filepath=answerimages_zip_path,
        input_path=STUDENT_ANSWERIMAGES_PATH,
        keys=exercises_keys,
    ):
        yield TaskResult(status="Compressing images", progress=progress, result=None)

    total_zip_path = os.path.join(output_path, SERVER_EXPORT_FILENAME)
    LOGGER.debug("TOTAL ZIP PATH = " + str(total_zip_path))
    for status, progress in _zip_recursively(output_filepath=total_zip_path, input_path=full_path):
        yield TaskResult(status="Compiling output", progress=progress, result=status)
    # os.rename( total_zip_path, "/tmp/server.zip" )
    if settings.UNITTESTS:
        from shutil import copyfile

        copyfile(total_zip_path, "/tmp/server.zip")


def _zip_assets_recursively(
    output_filepath, input_path, relative_base=None, report_steps=10, keys=[]
):
    """Zip path recursively with progress report.

    Args:
        output_filepath (str): Path to output folder.
        input_path (str): Path to input folder.
        report_steps (int, optional): Number of steps to report progress in.

    Yields:
        tuple (output_filepath, fraction_complete)

    """
    if relative_base is None or settings.UNITTESTS:
        relative_base = input_path
    archive = zipfile.ZipFile(output_filepath, 'w')
    all_files = list(Path(input_path).glob("**/*/*"))
    files = []
    for file in all_files:
        if file.parts[3] in keys:
            files = files + [file]
    LOGGER.debug("ZIP_ASSETS_RECURSIVELY FILES  TO ZIP = " + str(files))
    num_files = len(files)
    for index, f in enumerate(files):
        archive.write(str(f.resolve()), str(f.relative_to(relative_base)))
        if index % (num_files // report_steps + 1) == 0:
            yield output_filepath, (index / num_files)
    archive.close()


def _export_databases(export_path, course=None):
    resources = [
        CourseResource,
        UserResource,
        OpenTAUserResource,
        ExerciseResource,
        ExerciseMetaResource,
        QuestionResource,
        AnswerResource,
        ImageAnswerResource,
        AuditExerciseResource,
    ]
    os.makedirs(export_path, exist_ok=True)
    n_resources = len(resources)
    for index, resource in enumerate(resources):
        dataset = resource(course=course).export()
        filename = "{index}_{name}.{ext}".format(
            index=index, name=resource.Meta.model.__name__, ext="csv"
        )
        path = os.path.join(export_path, filename)
        with open(path, 'w') as output_file:
            output_file.write(dataset.csv)
        yield "Database", index / n_resources


def import_server(import_zip_path, merge=False, legacy=False):
    """Import server zip file.

    Import a full server zip file containing possibly many courses.

    .. note::

        Without the `merge` option, this will only run if exercise file tree is empty.

    Args:
        import_zip_path (str): Full path to server zip file (generated by
            export_server).
        merge (bool, optional): Attempts to merge servers if true.

    """
    import exercises.paths

    if merge:
        LOGGER.info("Attempting a merge")

    LOGGER.debug("IMPORT SERVER")
    with tempfile.TemporaryDirectory() as tmpdir:
        server_zip = zipfile.ZipFile(import_zip_path, 'r')
        server_zip.extractall(path=tmpdir)
        faultless = True
        msg = ''
        for progress in _import_databases(tmpdir):
            try:
                yield progress
            except Exception as e:
                raise ImportError("D: " + str(e))

        if legacy:
            return

        LOGGER.debug("NOW DO IMPORT_SERVER")

        for course in Course.objects.all():
            LOGGER.debug("COURSE KEYS = " + str(course.course_key))
        course = Course.objects.last()
        LOGGER.debug("COURSE KEY = " + str(course.course_key))
        exercises_path = course.get_exercises_path()
        student_assets_path = course.get_student_assets_path()
        student_answerimages_path = course.get_student_answerimages_path()
        LOGGER.debug("exercises_path = s" + str(exercises_path))
        LOGGER.debug("student assets_path  " + str(student_assets_path))
        LOGGER.debug("student_answerimages_path s" + str(student_answerimages_path))
        # print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        os.makedirs(exercises_path, exist_ok=True)
        if os.listdir(exercises_path) and not merge:
            error_msg = "Exercises directory not empty, will only import into clean server."
            LOGGER.error(error_msg)
            raise ImportError("A:" + error_msg)

        try:
            LOGGER.debug("UNZIP EXERCIESES TO")
            exercises_zip_path = os.path.join(tmpdir, SERVER_EXERCISES_EXPORT_FILENAME)
            LOGGER.debug("UNZIP EXERCIESES TO" + str(exercises_zip_path))
            exercises_zip = zipfile.ZipFile(exercises_zip_path, 'r')
            exercises_zip.extractall(os.path.join(exercises_path, '../'))
            LOGGER.debug("UNZIPPED EXERCIESES TO" + str(exercises_zip_path))

        except Exception as e:
            faultless = False
            msg = msg + "EXERCISES unzip FAILED " + str(e)
            LOGGER.error("EXERCISES unzip FAILED " + str(e))

        if legacy:
            return

        try:
            os.makedirs(student_assets_path, exist_ok=True)
            assets_zip_path = os.path.join(tmpdir, STUDENT_ASSETS_EXPORT_FILENAME)
            LOGGER.debug("UNZIP ASSETS to " + str(assets_zip_path))
            if os.path.isfile(assets_zip_path):
                assets_zip = zipfile.ZipFile(assets_zip_path, 'r')
                assets_zip.extractall(os.path.join(student_assets_path, '../'))
            LOGGER.debug("UNZIPPED ASSETS")

        except Exception as e:
            msg = msg + "ASSETS unzip FAILED " + str(e)
            faultless = False
            LOGGER.error("ASSETS unzip FAILED " + str(e))

        try:
            os.makedirs(student_answerimages_path, exist_ok=True)
            answerimages_zip_path = os.path.join(tmpdir, STUDENT_ANSWERIMAGES_EXPORT_FILENAME)
            LOGGER.debug("UNZIP ANSWERIMAGES TO " + str(answerimages_zip_path))
            if os.path.isfile(answerimages_zip_path):
                LOGGER.debug("PATH EXISTS" + str(answerimages_zip_path))
                answerimages_zip = zipfile.ZipFile(answerimages_zip_path, 'r')
                LOGGER.debug("ZIP STRUCTURE OPTAINED")
                answerimages_zip.extractall(os.path.join(student_answerimages_path, '../'))
                LOGGER.debug("IMAGES EXTRACTED")
            LOGGER.debug("DONE UNZIPPING ANSERIMAGES")

        except Exception as e:
            faultless = False
            msg = msg + "ANSWERIMAGES unzip FAILED " + str(e)
            LOGGER.error("ANSWSERIMAGS unzip FAILED " + str(e))

        LOGGER.info('Started calculating results and statistics')
        for course in Course.objects.all():
            print("Calculating for course {}".format(course.course_name))
            student_statistics_exercises(force=True, course=course)
            print('Statistics done, now doing results.')
            students_results(force=True, course=course)
            print('Finished calculating results and statistics')

        if not faultless:
            LOGGER.error("B %s ", msg)
            raise ImportError("B" + msg)


def export_course_exercises(course, output_path):
    """Export exercises from course as zip.

    Saves a zip with all exercises in course. The resulting file will be
    named as the course.

    Args:
        course (course.models.Course): Course to export.
        output_path (str): Path where course zip will be placed.

    Yields:
        tuple: (output_path, fraction_complete)

    """
    filename = "{name}.{ext}".format(name=course.course_name, ext="zip")
    filepath = os.path.join(output_path, filename)
    LOGGER.debug("EXPORT COURSE EXERCISES" + str(filepath))
    for result in _zip_recursively(filepath, course.get_exercises_path()):
        yield result


def import_course_exercises(course, zip_file_path):
    """Import exercise zip into course.

    Extracts exercises into file tree and performs a reload on the specified
    course.

    Args:
        courase (course.models.Course): Course to import into.
        zip_file_path (str): Full path to exercises zip file.

    Returns:
        list: List of reload messages.

    """
    archive = zipfile.ZipFile(zip_file_path, 'r')
    namelist = archive.namelist()
    members = [filn for filn in namelist if '/exercisekey' not in filn]
    archive.extractall(course.get_exercises_path(), members=members)
    messages = []
    for progress in Exercise.objects.sync_with_disc(course, i_am_sure=True):
        messages = messages + progress
    return messages


def _import_databases(import_path):
    """Import databases.

    Looks for database export CSV's and tries to import them into the current
    database.

    Args:
        import_path (str): Path to folder containing database exports.

    """
    import_lookup = {
        "Question": QuestionResource(),
        "Answer": AnswerResource(),
        "ImageAnswer": ImageAnswerResource(),
        "Exercise": ExerciseResource(),
        "ExerciseMeta": ExerciseMetaResource(),
        "User": UserResource(),
        "OpenTAUser": OpenTAUserResource(),
        "Course": CourseResource(),
        "AuditExercise": AuditExerciseResource(),
    }
    files = sorted(os.listdir(import_path))
    n_total = len(files)
    msg1 = ''
    msg2 = ''
    # THIS LOGIC WAS NOT REALLY OK BEFORE
    # IF ** ANY ** dryrun results in an error
    # THE IMPORT SHOULD NOT BE DONE
    # THE OLD CODE COULD RESULT IN A PARTIAL IMPORT
    try:
        for dryrun in [False]:
            msg = ' (testing only)' if dryrun else ''
            for index, csv in enumerate(files):
                LOGGER.debug("CSV = " + str(csv))
                if csv.endswith('.csv'):
                    # time.sleep(0.3)
                    parts = csv.split('_')
                    class_name = parts[1].split('.')[0]
                    # LOGGER.debug("Importing " + str(  class_name ) )
                    yield class_name + msg, index / n_total
                    with open(os.path.join(import_path, csv)) as csv_file:
                        csv_contents = csv_file.read()
                        dataset = tablib.Dataset().load(csv_contents)
                        if class_name in import_lookup:
                            resource = import_lookup[class_name]
                            res = resource.import_data(dataset, dry_run=dryrun)
                            if res.has_errors():
                                # THIS WAS DIFFICULT TO DEBUG: LOTS OF INFO IF CRASH
                                LOGGER.debug("CSV_CONTENTS = " + str(csv_contents))
                                LOGGER.debug("RES HAS ERROR")
                                LOGGER.debug("RESOURCE = ")
                                raise ImportError("D: Importing " + str(class_name) + '. ')
                            else:
                                pass
                                # res = resource.import_data(dataset, dry_run=False)
    except Exception as e:
        raise ImportError("ERROR: C csv = : " + str(csv))  # + +str(e) + msg1 + msg2)


def _zip_recursively(output_filepath, input_path, relative_base=None, report_steps=10):
    """Zip path recursively with progress report.

    Args:
        output_filepath (str): Path to output folder.
        input_path (str): Path to input folder.
        report_steps (int, optional): Number of steps to report progress in.

    Yields:
        tuple (output_filepath, fraction_complete)

    """
    if relative_base is None or settings.UNITTESTS:
        relative_base = input_path
    archive = zipfile.ZipFile(output_filepath, 'w')
    files = list(Path(input_path).glob("**/*"))
    LOGGER.debug("ZIP_RECURSIVELY FILES  TO ZIP = " + str(files))
    num_files = len(files)
    for index, f in enumerate(files):
        archive.write(str(f.resolve()), str(f.relative_to(relative_base)))
        if index % (num_files // report_steps + 1) == 0:
            yield output_filepath, (index / num_files)
    archive.close()
