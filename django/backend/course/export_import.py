import os
from exercises.models import Exercise, Answer, Question, ExerciseMeta, ImageAnswer, AuditExercise
from course.models import Course
from users.models import OpenTAUser
from django.contrib.auth.models import User, Group

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
import exercises.paths as paths

import logging
import tempfile
from django.utils.encoding import smart_text
from workqueue.util import TaskResult

SERVER_EXERCISES_EXPORT_FILENAME = 'exercises.zip'
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
            print(str(e))
            print(row)


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
        exclude = ('id',)
        import_id_fields = ('exercise',)
        # COMPUTE META FIELDS TO ADD
        # PLEASE RETAIN THIS COMMENT BLOCK
        # newfields = [f.name for f in model._meta.get_fields()]
        # newfields.remove('id')
        # fields = tuple(newfields)

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
            return self._meta.model.objects.filter(question__exercise__course=self._course).exclude(
                question__isnull=True
            )
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
        exclude = ('id',)

    def __init__(self, *args, **kwargs):
        self._course = None
        if 'course' in kwargs:
            self._course = kwargs.pop('course')
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(exercise__course=self._course).exclude(
                exercise__isnull=True
            )
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
        return self.separator.join(ids)


class OpenTAUserResource(resources.ModelResource):
    user = fields.Field(
        column_name='user', attribute='user', widget=ForeignKeyWidget(User, field='username')
    )
    courses = fields.Field(
        column_name='courses',
        attribute='courses',
        widget=UserCoursesWidget(Course, field="course_key"),
    )

    class Meta:
        model = OpenTAUser
        exclude = ('id',)
        fields = ('user', 'courses')
        import_id_fields = ('user',)

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

    for status, progress in _export_databases(full_path):
        yield TaskResult(status=status, progress=progress, result=None)

    exercises_zip_path = os.path.join(full_path, SERVER_EXERCISES_EXPORT_FILENAME)
    for _, progress in _zip_recursively(
        output_filepath=exercises_zip_path, input_path=paths.EXERCISES_PATH
    ):
        yield TaskResult(status="Compressing exercises", progress=progress, result=None)
    total_zip_path = os.path.join(output_path, SERVER_EXPORT_FILENAME)
    for _, progress in _zip_recursively(output_filepath=total_zip_path, input_path=full_path):
        yield TaskResult(status="Compiling output", progress=progress, result=total_zip_path)


def export_course(course, output_path='export'):
    subpath = "server"
    full_path = os.path.join(output_path, subpath)
    for status, progress in _export_databases(full_path, course=course):
        yield TaskResult(status=status, progress=progress, result=None)

    exercises_zip_path = os.path.join(full_path, SERVER_EXERCISES_EXPORT_FILENAME)
    for _, progress in _zip_recursively(
        output_filepath=exercises_zip_path,
        input_path=course.get_exercises_path(),
        relative_base=paths.EXERCISES_PATH,
    ):
        yield TaskResult(status="Compressing exercises", progress=progress, result=None)
    total_zip_path = os.path.join(output_path, SERVER_EXPORT_FILENAME)
    for status, progress in _zip_recursively(output_filepath=total_zip_path, input_path=full_path):
        yield TaskResult(status="Compiling output", progress=progress, result=status)


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


def import_server(import_zip_path, merge=False):
    """Import server zip file.

    Import a full server zip file containing possibly many courses.

    .. note::

        Without the `merge` option, this will only run if exercise file tree is empty.

    Args:
        import_zip_path (str): Full path to server zip file (generated by
            export_server).
        merge (bool, optional): Attempts to merge servers if true.

    """
    os.makedirs(paths.EXERCISES_PATH, exist_ok=True)
    if os.listdir(paths.EXERCISES_PATH) and not merge:
        error_msg = "Exercises directory not empty, will only import into clean server."
        LOGGER.error(error_msg)
        raise ImportError(error_msg)

    if merge:
        LOGGER.info("Attempting a merge")

    with tempfile.TemporaryDirectory() as tmpdir:
        server_zip = zipfile.ZipFile(import_zip_path, 'r')
        server_zip.extractall(path=tmpdir)
        for progress in _import_databases(tmpdir):
            yield progress
        try:
            exercises_zip_path = os.path.join(tmpdir, SERVER_EXERCISES_EXPORT_FILENAME)
            exercises_zip = zipfile.ZipFile(exercises_zip_path, 'r')
            exercises_zip.extractall(paths.EXERCISES_PATH)
        except Exception as e:
            LOGGER.error(str(e))
            raise e


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
    archive.extractall(course.get_exercises_path())
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
    for index, csv in enumerate(files):
        if csv.endswith('.csv'):
            parts = csv.split('_')
            class_name = parts[1].split('.')[0]
            LOGGER.info("Importing %s", class_name)
            yield class_name, index / n_total
            with open(os.path.join(import_path, csv)) as csv_file:
                csv_contents = csv_file.read()
                dataset = tablib.Dataset().load(csv_contents)
                if class_name in import_lookup:
                    resource = import_lookup[class_name]
                    res = resource.import_data(dataset, dry_run=True)
                    if res.has_errors():
                        LOGGER.error(res)
                    else:
                        res = resource.import_data(dataset, dry_run=False)
            yield class_name, index / n_total


def _zip_recursively(output_filepath, input_path, relative_base=None, report_steps=10):
    """Zip path recursively with progress report.

    Args:
        output_filepath (str): Path to output folder.
        input_path (str): Path to input folder.
        report_steps (int, optional): Number of steps to report progress in.

    Yields:
        tuple (output_filepath, fraction_complete)

    """
    if relative_base is None:
        relative_base = input_path
    archive = zipfile.ZipFile(output_filepath, 'w')
    files = list(Path(input_path).glob("**/*"))
    num_files = len(files)
    for index, f in enumerate(files):
        archive.write(str(f.resolve()), str(f.relative_to(relative_base)))
        if index % (num_files // report_steps + 1) == 0:
            yield output_filepath, (index / num_files)
    archive.close()
