# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import csv


# import pdfkit
import html
from datetime import timezone
import json
import glob
import logging
import os
import re
import shutil
import subprocess
import tarfile
import time
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

import tablib
from exercises.assets import asset_types
from aggregation.models import Aggregation
from aggregation.serializers import AggregationSerializer
from course.models import Course
from exercises.models import (
    Answer,
    AuditExercise,
    Exercise,
    ExerciseMeta,
    ImageAnswer,
    Question,
    ExerciseManager
)
from exercises.serializers import ExerciseMetaSerializer
from django.db import transaction
from exercises.views.api import get_unsafe_exercise_summary
from import_export import fields, resources
from import_export.widgets import (
    DateTimeWidget,
    ForeignKeyWidget,
    ManyToManyWidget,
)
from tabulate import tabulate
from users.models import OpenTAUser
from workqueue.util import TaskResult

from backend.middleware import (
    add_database,
    verify_or_create_database_connection,
)
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.cache import caches
from django.db import connections
from django.utils.encoding import smart_str
from django.utils.timezone import get_current_timezone, make_aware

SERVER_EXERCISES_EXPORT_FILENAME = "exercises.zip"
STUDENT_ASSETS_EXPORT_FILENAME = "assets.zip"
STUDENT_ANSWERIMAGES_EXPORT_FILENAME = "answerimages.zip"
SERVER_EXPORT_FILENAME = "server.zip"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

logger = logging.getLogger(__name__)


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
            render_value = get_current_timezone().normalize(value).astimezone(timezone.utc)
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
                    dt = make_aware(dt, timezone.utc)
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
            logger.error(str(e))
            logger.error(str(row))


class CourseResource(resources.ModelResource):
    def __init__(self, *args, **kwargs):
        self._course = None
        if "course" in kwargs:
            self._course = kwargs.pop("course")
        super().__init__(*args, **kwargs)

    class Meta:
        model = Course
        fields = (
            "course_key",
            "course_name",
            "course_long_name",
            "registration_domains",
            "registration_by_domain",
            "languages",
        )
        exclude = ("id", "lti_secret", "lti_key", "email_host_password")
        import_id_fields = ("course_key",)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(pk=self._course.pk)
        else:
            return self._meta.model.objects.all()


class ExerciseResource(resources.ModelResource):
    course = fields.Field(
        column_name="course",
        attribute="course",
        widget=ForeignKeyWidget(Course, field="course_key"),
    )

    class Meta:
        model = Exercise
        exclude = ("id",)
        import_id_fields = ("exercise_key",)

    def __init__(self, *args, **kwargs):
        self._course = None
        if "course" in kwargs:
            self._course = kwargs.pop("course")
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(course=self._course)
        else:
            return self._meta.model.objects.all()


class ExerciseMetaResource(resources.ModelResource):
    exercise = fields.Field(
        column_name="exercise",
        attribute="exercise",
        widget=ForeignKeyWidget(Exercise, field="exercise_key"),
    )

    class Meta:
        model = ExerciseMeta
        newfields = [f.name for f in model._meta.get_fields()]
        newfields.remove("id")
        fields = tuple(newfields)
        logger.debug("fields" + str(fields))
        exclude = ("id",)
        import_id_fields = ("exercise",)
        # COMPUTE META FIELDS TO ADD
        # PLEASE RETAIN THIS COMMENT BLOCK
        # newfields = [f.name for f in model._meta.get_fields()]
        # newfields.remove('id')
        # fields = tuple(newfields)

    def __init__(self, *args, **kwargs):
        self._course = None
        if "course" in kwargs:
            self._course = kwargs.pop("course")
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(exercise__course=self._course)
        else:
            return self._meta.model.objects.all()


class AnswerResource(resources.ModelResource):
    user = fields.Field(column_name="user", attribute="user", widget=ForeignKeyWidget(User, field="username"))
    #question = fields.Field(column_name="Question", attribute="question", widget=QuestionForeignKeyWidget(Question))
    date = fields.Field(column_name="date", attribute="date", widget=TzDateTimeWidget(format=DATETIME_FORMAT))

    class Meta:
        model = Answer
        fields = (
            "user__id",
            "user",
            #"question__question_key",
            "answer",
            "grader_response",
            "correct",
            "date",
            "question__exercise__exercise_key",
        )
        import_id_fields = (
            "user",
            "date",
            "question",
        )
        exclude = (
            "id",
            "question",
        )

    def __init__(self, *args, **kwargs):
        self._course = None
        if "course" in kwargs:
            self._course = kwargs.pop("course")
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
    user = fields.Field(column_name="user", attribute="user", widget=ForeignKeyWidget(User, field="username"))
    exercise = fields.Field(
        column_name="exercise",
        attribute="exercise",
        widget=ForeignKeyWidget(Exercise, field="exercise_key"),
    )

    date = fields.Field(column_name="date", attribute="date", widget=TzDateTimeWidget(format=DATETIME_FORMAT))

    class Meta:
        model = ImageAnswer
        import_id_fields = ("user", "date", "exercise")
        newfields = [f.name for f in model._meta.get_fields()]
        newfields.remove("id")
        fields = tuple(newfields)
        logger.debug("fields" + str(fields))
        exclude = ("id",)

    def __init__(self, *args, **kwargs):
        self._course = None
        if "course" in kwargs:
            self._course = kwargs.pop("course")
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
        import_id_fields = ("exercise", "question_key")
        exclude = ("id",)

    def __init__(self, *args, **kwargs):
        self._course = None
        if "course" in kwargs:
            self._course = kwargs.pop("course")
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(exercise__course=self._course)
        else:
            return self._meta.model.objects.all()


class UserCoursesWidget(ManyToManyWidget):
    def render(self, value, obj=None):
        ids = [smart_str(obj.course_key) for obj in value.all()]
        logger.debug("COURSES IDS = %s", ids)
        return self.separator.join(ids)


CAREFUL_IMPORT = False


class OpenTAUserResource(resources.ModelResource):
    def skip_row(self, instance, original):
        if CAREFUL_IMPORT:
            return super(OpenTAUserResource, self).skip_row(instance, original)
        else:
            return False

    user = fields.Field(column_name="user", attribute="user", widget=ForeignKeyWidget(User, field="username"))
    courses = fields.Field(
        column_name="courses",
        attribute="courses",
        widget=UserCoursesWidget(Course, field="course_key"),
    )
    logger.debug("USER = %s, COURES = %s", user, courses)

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
        import_id_fields = ("user",)
        skip_unchanged = CAREFUL_IMPORT
        newfields = [f.name for f in model._meta.get_fields()]
        newfields.remove("id")
        fields = tuple(newfields)
        exclude = ("id",)
        logger.debug(" OPENTA_USER GETTING fields" + str(fields))

    def __init__(self, *args, **kwargs):
        self._course = None
        if "course" in kwargs:
            self._course = kwargs.pop("course")
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(courses=self._course)
        else:
            return self._meta.model.objects.all()


class UserResource(resources.ModelResource):
    groups = fields.Field(column_name="groups", attribute="groups", widget=ManyToManyWidget(Group, field="name"))

    class Meta:
        model = User
        exclude = ("id",)
        import_id_fields = ("username",)
        skip_unchanged = CAREFUL_IMPORT

    def __init__(self, *args, **kwargs):
        self._course = None
        if "course" in kwargs:
            self._course = kwargs.pop("course")
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(opentauser__courses=self._course).exclude(is_staff=False)
        else:
            return self._meta.model.objects.all().exclude(is_staff=False)


class AuditExerciseResource(resources.ModelResource):
    student = fields.Field(column_name="student", attribute="student", widget=ForeignKeyWidget(User, field="username"))
    auditor = fields.Field(column_name="auditor", attribute="auditor", widget=ForeignKeyWidget(User, field="username"))
    exercise = fields.Field(
        column_name="exercise",
        attribute="exercise",
        widget=ForeignKeyWidget(Exercise, field="exercise_key"),
    )

    class Meta:
        model = AuditExercise
        exclude = ("id",)
        import_id_fields = ("student", "exercise")

    def __init__(self, *args, **kwargs):
        self._course = None
        if "course" in kwargs:
            self._course = kwargs.pop("course")
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        if self._course is not None:
            return self._meta.model.objects.filter(exercise__course=self._course)
        else:
            return self._meta.model.objects.all()


def export_server(output_path="export", subdomain="openta"):
    """Export server to zip file.

    Exports all supported models to a portable CSV format.
    Saves the full exercise file tree for all courses.

    Args:
        output_path (str, optional): Where to save the server export. Defaults to 'export'.

    Yields:
        float: Fraction complete

    """

    # logger.error(f"EXPORT SERVER {output_path} subdomain={subdomain}")
    # DOES NOT WORK
    # pdfkit.from_url('https://v320c.localhost:8000/exercise/c6e015ed-7801-4e02-b28b-5e727a153592', '/tmp/out.pdf')
    print(f"EXPORT_SERVER {subdomain}")
    subpath = subdomain
    db = subdomain
    verify_or_create_database_connection(db)
    courses = list(Course.objects.using(db).all())
    summary = {}
    xslpath = os.path.join(settings.VOLUME, subdomain, "xsl")
    shutil.copytree("xsl", os.path.join(settings.VOLUME, subdomain, "xsl"), dirs_exist_ok=True)
    shutil.copy2("xsl/baseindex.html", os.path.join(settings.VOLUME, subdomain, "index.html"))
    shutil.copy2("xsl/README", os.path.join(settings.VOLUME, subdomain, "README"))
    exercises_path = os.path.join(settings.VOLUME, subdomain, "exercises")
    for root, directories, filenames in os.walk(exercises_path, followlinks=True):
        for filename in filenames:
            if filename == "exercise.xml":
                name = os.path.basename(os.path.normpath(root))
                relpath = root[len(exercises_path) :]
                if not relpath == "":
                    shutil.copy2("xsl/display.html", root)
                    shutil.copy2("xsl/display.html", root)
                    # print(f"ROOT = {root}")

    print(f"EXPORT_COURSES = {courses}")
    for course in courses:
        coursename = course.course_name
        print(f"EXPORT COURSE_NAME = {coursename}")
        try :
            cfile = f"{settings.VOLUME}/auth/google_auth_string.txt"
            old_google_auth_string = course.google_auth_string
            if os.path.exists(cfile):
                course.google_auth_string = ""
                course.save()
        except Exception as e :
            print(f"EXPORT_ERROR W GOOGLE_AUTH_STRING {str(e)}")
            pass
        students = list(User.objects.using(db).all().order_by("username"))
        print(f"EXPORT_STUDENTS = {students}")
        dbexercises = list(Exercise.objects.using(db).select_related("meta", "course").filter(course=course))
        # for dbexercise in dbexercises :
        #    full_path = dbexercise.get_full_path()
        #    for p in ['display.html','ex3.html','ex.html','index.html'] :
        #        pa = os.path.join(full_path,p)
        #        if os.path.exists(pa ):
        #            os.remove(pa)
        #    shutil.copy2("xsl/display.html",os.path.join(full_path,"display.html") )
        #    shutil.copy2("xsl/display.html",os.path.join(full_path,"display.html") )
        #    # symlinks do not propagate in zip
        #    #os.symlink('../../../xsl/ex.html', os.path.join(full_path,"display.html") )
        #    print(f"{full_path}")
        # print(f"USERS = {students}")
        summary[coursename] = []
        n = max(float(len(students)), 1)
        print(f"EXPORT N = {n}")
        for index, student in enumerate(students):
            # print(f"STUDENT={student}")
            s = get_unsafe_exercise_summary(student, course.pk, dbexercises, subdomain)
            # print(f" {json.dumps(s,indent=2)}")
            sp = {"name": student.username.split("@")[0]}
            for cat in ["required", "bonus", "optional"]:
                sp[cat + "-ontime"] = s[cat]["number_complete_by_deadline"]
                sp[cat + "-late"] = s[cat]["number_complete"] - s[cat]["number_complete_by_deadline"]
            summary[coursename].append(sp)
            yield TaskResult(status="working on student summary", progress=index / max(n, 1), result=None)
            # print(f"index={index} {student}")
        su = summary[coursename]
        print(f"EXPORT SU = {su}")
    full_path = os.path.join(output_path, subpath)
    src = f"{settings.VOLUME}/{subdomain}"
    print(f"SRC = {src}")
    # subprocess.run(['touch',os.path.join(src,'touchfile') ])
    try :
        subprocess.run([settings.DB_BACKUP, subdomain, "--force"])
    except :
        print(f"BACKUP NOT DONE ")
    ags = (
        Aggregation.objects.using(subdomain)
        .select_related("user", "course", "exercise")
        .all()
        .order_by("exercise__name", "user__username")
    )
    users = ags.values_list("user", flat=True)
    print(f"USERS = {users}")
    # print(f"users={users}")
    res = {}
    n = max(float(ags.count()), 1)
    images = ImageAnswer.objects.using(db).select_related("user", "exercise").all()
    # print(f"IMAGES")
    allaudits = (
        AuditExercise.objects.using(db).select_related("student", "auditor", "exercise", "exercise__course").all()
    )
    # print(f"ALLAUDITS")
    for index, ag in enumerate(ags):
        course = ag.course
        #print(f"EXPORT AG COURSE  = {course}")
        user = ag.user
        exercise = ag.exercise
        # print(f"COURSE EXERCISES_PATH = {course.get_exercises_path()} ")
        # print(f"COURSE REL PATH = {exercise.path}")
        e_full_path = os.path.join(course.get_exercises_path(), exercise.path)
        # print(f"E_FULL_PATH = {e_full_path}")
        serializer = AggregationSerializer(ag)
        data = serializer.data
        # print("DATA")
        coursename = course.course_name
        # print(f"COURSENAME")
        username = user.username
        # print(f"USERNAME")
        exercisename = exercise.name
        exercise_key = exercise.exercise_key[0:8]
        agimages = list(images.filter(user=user, exercise=exercise))
        msg = ""
        auditor = ""
        try:
            # audit = AuditExercise.objects.using(db).get(student=user, exercise=exercise)
            audits = allaudits.filter(student=user, exercise=exercise)
            if audits.count() > 0:
                audit = audits.last()
                msg = audit.message
                auditor = audit.auditor
                if "@" in auditor:
                    auditor = auditor.split("@")[0]
            # saudit = AuditExerciseSerializer(audit)
            # sdata = saudit.data
            # print(f"AUDITDATA = {sdata}")
            # print(f"AUDIT MESSAGE = {audit.message}")
            # auditor = sdata['auditor_data']['username']
            # print(f"AUDITOR = {auditor}")
            # msg =  sdata['message']
            # updated = sdata['updated']
            # modified = sdata['modified']
            # points  = sdata['points']
            # sent = sdata['sent']
            # auditdata = {'auditor' : auditor, 'msg' : msg , 'updated' : updated , 'modified' : modified, 'points' : points , 'sent' : sent }
            # print(f"auditdata = {auditdata}")
        except Exception as e:
            auditdata = None
        fils = []
        i = 0
        s = ""
        #print("EXPORT_AGIMAGES")
        for agimage in agimages:
            p = None
            if agimage.pdf:
                p = agimage.pdf.path
            elif agimage.image:
                p = agimage.image.path
            if p:
                p = "/".join(p.split("/")[3:])
                p = "../" + p
                fils = fils + [p]
                i = i + 1
                s = s + f'<a href="{p}">{i}</a>'
        # print("s = {s}")
        if not coursename in res.keys():
            res[coursename] = {}
        if not username in res[coursename].keys():
            res[coursename][username] = []
        u = username.split("@")[0]
        # print(f"U = {u}")
        dat = {"username": u, "exercise": exercise.name, "key": exercise.exercise_key[0:8], "images": s}
        # print(f"DAT = {dat}")
        full_path = "../" + "/".join((e_full_path).split("/")[3:])
        # print(f"FULL_PATH = {full_path}")
        orig_full_path = e_full_path
        # print(f"ORIG FULL_PATH { orig_full_path}")
        # print(f"{os.path.exists('./xsl/index.html')} {os.path.exists(orig_full_path)}")
        # print(f"FULL_PATH = {full_path}")
        dat.update(dict(data))
        dat["audit_message_text"] = msg
        dat["key"] = f"<a href=\"{full_path}/display.html\">{dat['key']}</a>"
        dat["auditor"] = auditor
        del dat["course"]
        del dat["user"]
        dat["exercise"] = exercise.name  # dat['exercise'][0:8]
        dat["answer_date"] = dat["answer_date"]
        #print(f"EXPORT_DAT = {type(dat)}")
        res[coursename][username].append(dat)
        yield TaskResult(status="individual data ", progress=index / max(n, 1), result=None)

    #print(f"RES = {res}")
    #print( json.dumps( res, indent=2) )
    csvdir = f"{settings.VOLUME}/{subdomain}/csv"
    htmldir = f"{settings.VOLUME}/{subdomain}/html"
    os.makedirs(csvdir, exist_ok=True)
    os.makedirs(htmldir, exist_ok=True)
    head = '<head><meta charset="UTF-8" /><style> \
        table, th, td { border: 1px solid white; border-collapse: collapse; text-align: center; } \
        th, td { background-color: #96D4D4; text-align: center; }</style><body>'
    tail = "</body>"
    indexstring = f"<html>{head}<h3> Archive of server {subdomain} </h3> \n<table border=1>\n"
    for coursename in res.keys():
        indexstring = (
            indexstring
            + f'<tr><td><a href="./{coursename}-user-SUMMARY.html">{coursename} user summary </a></td></tr>\n'
        )
        usernames = res[coursename].keys()
        for username in usernames:
            # print(f"USER={username} COURS={coursename}")
            d = res[coursename][username]
            # print(json.dumps(d, indent=2) )
            # with open(f'{csvdir}/{coursename}-{username}-results.csv','w') as f :
            keys = d[0].keys()
            # print(f"FIELDNAMES = {keys}")
            u = username.split("@")[0]
            with open(f"{csvdir}/{coursename}-{u}-results.csv", "w") as f:
                w = csv.DictWriter(f, keys)
                w.writeheader()
                w.writerows(d)
            f.close()

            headers = list(d[0].keys())
            tab = []
            for item in d:
                row = list(item.values())
                tab = tab + [[str(i) for i in row]]
            # print(f"TAB = {tab}")
            html_ = tabulate(tab, headers, tablefmt="html")
            html_ = head + html.unescape(html_) + tail
            # print(f"HTML = {html_}")
            with open(f"{htmldir}/{coursename}-{u}-results.html", "w") as f:
                f.write(html_)
            f.close()

        # print(f"WRITE CSV")
        with open(f"{csvdir}/{coursename}-user-SUMMARY.csv", "w") as f:
            d = summary[coursename]
            keys = d[0].keys()
            w = csv.DictWriter(f, keys)
            w.writeheader()
            w.writerows(d)
        f.close()

        headers = list(d[0].keys())
        tab = []
        for item in d:
            u = item["name"]
            filname = f"{htmldir}/{coursename}-{u}-results.html"
            if os.path.exists(filname):
                item["name"] = f'<a href="./{coursename}-{u}-results.html">{u}</a>'
            row = list(item.values())
            tab = tab + [[str(i) for i in row]]
        # print(f"TAB = {tab}")
        html_ = tabulate(tab, headers, tablefmt="html")
        html_ = head + html.unescape(html_) + tail
        html_ = re.sub(r"style=\"text-align: right;\"", "", html_)
        # print(f"HTML = {html_}")
        with open(f"{htmldir}/{coursename}-user-SUMMARY.html", "w") as f:
            f.write(html_)
        f.close()
    indexstring = indexstring + "</table>\n</body>\n</html>"
    #print(f"EXPORT_INDEXSTRING={indexstring}")
    with open(f"{htmldir}/index.html", "w") as f:
        f.write(indexstring)
    # print(f"indexstring = {indexstring}")

    # for status, progress in _export_databases(full_path):
    #    yield TaskResult(status=status, progress=progress, result=None)
    # exercises_zip_path = os.path.join(full_path, SERVER_EXERCISES_EXPORT_FILENAME)
    # for _, progress in _zip_recursively(
    #    output_filepath=exercises_zip_path, input_path=EXERCISES_PATH
    # ):
    #    yield TaskResult(status="Compressing exercises", progress=progress, result=None)

    # assets_zip_path = os.path.join(full_path, STUDENT_ASSETS_EXPORT_FILENAME)
    # for _, progress in _zip_recursively(
    #    output_filepath=assets_zip_path, input_path=STUDENT_ASSETS_PATH
    # ):
    #    yield TaskResult(status="Compressing assets", progress=progress, result=None)
    now = datetime.now()
    filename = (
        f"{subdomain}-server-export-{now.year}-{'%02d' % now.month}-{now.day}-{now.hour}-{'%02d' % now.minute}.zip"
    )
    print(f"EXPORT_FILENAME = {filename}")
    total_zip_path = os.path.join(output_path, filename)
    # print(f" TOTAL_ZIP_PATH = {total_zip_path} inputPath ={settings.VOLUME}/{subdomain}")
    for _, progress in _zip_recursively(output_filepath=total_zip_path, input_path=f"{settings.VOLUME}/{subdomain}", include_exercisekey = True ) :
        yield TaskResult(status="Compiling output", progress=progress, result=total_zip_path)
    # restore google_auth_string  legacy precaution
    if False :
        for course in courses:
            cfile = f"{settings.VOLUME}/auth/google_auth_string.txt"
            if os.path.exists(cfile):
                course.google_auth_string = old_google_auth_string
                course.save()
        purge_export_htmls(exercises_path)

    # for root, directories, filenames in os.walk( exercises_path , followlinks=True):
    #        for filename in filenames:
    #            if filename == "exercise.xml":
    #                name = os.path.basename(os.path.normpath(root))
    #                relpath = root[len(exercises_path) :]
    #                if ( not relpath == ""):
    #                     fils = ['display.html','ex.html','meta.json']
    #                     for fil in fils :
    #                        ffil = f"{root}/{fil}"
    #                        print(f"ffil = {ffil}")
    #                        if os.path.isfile(ffil ):
    #                            print(f"REMOVE {ffil}")
    #                            os.remove(ffil)


# def export_course(course, output_path='export'):
#    print(f"EXPORT COURSE {course} {output_path}")
#    logger.debug("EXPORT_COURSE output_path = " + str(output_path))
#    _EXERCISES_PATH = course.get_exercises_path()
#    logger.debug("EXERCISES_PATH = " + str(_EXERCISES_PATH))
#    subpath = "server"
#    full_path = os.path.join(output_path, subpath)
#    for status, progress in _export_databases(full_path, course=course):
#        logger.debug("STATUS, PROGRESS" + str(status) + str(progress))
#        yield TaskResult(status=status, progress=progress, result=None)
#
#
#    exercises_zip_path = os.path.join(full_path, SERVER_EXERCISES_EXPORT_FILENAME)
#    # logger.debug(" A: EXERCISES ZIP_PATH " + str(exercises_zip_path))
#    # logger.debug(" B: EXERCISES_PATH " + str(_EXERCISES_PATH))
#    # logger.debug(" C: INPUT_PATH " + str(course.get_exercises_path()))
#    # logger.debug(" D: DIRLIST = " + str(os.listdir(course.get_exercises_path())))
#
#    for _, progress in _zip_recursively(
#        output_filepath=exercises_zip_path,
#        input_path=course.get_exercises_path(),
#        relative_base=_EXERCISES_PATH,
#    ):
#        yield TaskResult(status="Compressing exercises", progress=progress, result=None)
#
#    # logger.debug(" DID COMPRESS")
#
#    exercises_list = Exercise.objects.filter(course=course)
#    exercises_keys = list(exercises_list.values_list('exercise_key', flat=True))
#    assets_zip_path = os.path.join(full_path, STUDENT_ASSETS_EXPORT_FILENAME)
#    # logger.debug(" ASSETS ZIP_PATH " + str(assets_zip_path))
#    for _, progress in _zip_assets_recursively(
#        output_filepath=assets_zip_path, input_path=STUDENT_ASSETS_PATH, keys=exercises_keys
#    ):
#        yield TaskResult(status="Compressing assets", progress=progress, result=None)
#
#    answerimages_zip_path = os.path.join(full_path, STUDENT_ANSWERIMAGES_EXPORT_FILENAME)
#    # logger.debug(" ANSWERIMAGES ZIP_PATH " + str(answerimages_zip_path))
#    for _, progress in _zip_assets_recursively(
#        output_filepath=answerimages_zip_path,
#        input_path=STUDENT_ANSWERIMAGES_PATH,
#        keys=exercises_keys,
#    ):
#        yield TaskResult(status="Compressing images", progress=progress, result=None)
#
#    total_zip_path = os.path.join(output_path, SERVER_EXPORT_FILENAME)
#    # logger.debug("TOTAL ZIP PATH = " + str(total_zip_path))
#    for status, progress in _zip_recursively(output_filepath=total_zip_path, input_path=full_path):
#       yield TaskResult(status="Compiling output", progress=progress, result=status)
#    # os.rename( total_zip_path, "/tmp/server.zip" )
#    if settings.UNITTESTS:
#        from shutil import copyfile
#
#        copyfile(total_zip_path, "/tmp/server.zip")
#


def _zip_assets_recursively(output_filepath, input_path, relative_base=None, report_steps=10, keys=[]):
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
    archive = zipfile.ZipFile(output_filepath, "w")
    all_files = list(Path(input_path).glob("**/*/*"))
    files = []
    for file in all_files:
        if file.parts[3] in keys:
            files = files + [file]
    # logger.debug("ZIP_ASSETS_RECURSIVELY FILES  TO ZIP = " + str(files))
    num_files = max(len(files), 1)
    for index, f in enumerate(files):
        archive.write(str(f.resolve()), str(f.relative_to(relative_base)))
        if index % (num_files // report_steps + 1) == 0:
            yield output_filepath, (index / num_files)
    archive.close()


def _export_databases(export_path, course=None):
    resources = [
        # CourseResource,
        UserResource,
        OpenTAUserResource,
        # ExerciseResource,
        # ExerciseMetaResource,
        # QuestionResource,
        # AnswerResource,
        # ImageAnswerResource,
        # AuditExerciseResource,
    ]
    os.makedirs(export_path, exist_ok=True)
    n_resources = len(resources)
    for index, resource in enumerate(resources):
        dataset = resource(course=course).export()
        filename = "{index}_{name}.{ext}".format(index=index, name=resource.Meta.model.__name__, ext="csv")
        path = os.path.join(export_path, filename)
        with open(path, "w") as output_file:
            output_file.write(dataset.csv)
        yield "Database", index / max(n_resources, 1)

def supervisor_running() -> bool:
    try:
        result = subprocess.run(
            ["supervisorctl", "status"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def reload_supervisor():
    subprocess.run(
        ["supervisorctl", "reload"],
        check=True,
    )



def import_server(import_zip_path, subdomain, merge=False, legacy=False):
    from .mergecourse import mergecourse_from_zip
    logger.error(f"import_zip_path = {import_zip_path}")
    tmp_zip_path = f"/tmp/{subdomain}.zip"
    logger.error(f"ZIPFILE = {tmp_zip_path}")
    shutil.copy2(import_zip_path, tmp_zip_path)
    logger.error("COPY")
    try:
        new_dbname = mergecourse_from_zip(tmp_zip_path, f"{subdomain}")
        logger.error(f"MERGE DONE new_dbname={new_dbname}")
        yield "DONE", 1
    except Exception as e:
        msg = str(e)
        logger.error(f"IMPORT ERROR: {msg}")
        yield msg, 0.9

    if supervisor_running():
        logger.error("Supervisor is running – reloading.")
        reload_supervisor()
    else:
        logger.error("Supervisor is not running.")
    from backend.middleware import verify_or_create_database_connection
    verify_or_create_database_connection(subdomain)
    conn = connections[subdomain]
    conn.connect()

    try :
        @transaction.atomic(using="default")
        def sync():
            messges = []
            courses = Course.objects.using(subdomain)
            course = courses[0]
            messages = []
            for progress in Exercise.objects.sync_with_disc(course, i_am_sure=True):
                messages = messages + progress
            messages = [];
        sync();
    except Exception as err :
        logger.error(f" ERROR IN SYNC {str(err)}")
    


# THe following was too fragile to be useful
# create new courses by uploading a zip then 
# exec into the container and execute the commands
# You can only create this new course with super priviledges .
# exec into the openta container
# exec -it openta-app -- /bin/bash into the openta container
# Then find the zip file in the /tmp/directory
# Make sure the directory /subdomain-data/new-subdomain does not exist
# Then execute the command db_createcourse_from_zip zipfile new-subdomain

def old_import_server(import_zip_path, subdomain, merge=False, legacy=False):
    # logger.error(f"IMPORT SERVER {subdomain}")
    uidtmp = str(uuid.uuid4())[0:7]
    subdomain_tmp = f"{subdomain}-{uidtmp}"
    now = datetime.now()
    src = f"{settings.VOLUME}/{subdomain}"
    dest = f"{settings.VOLUME}/{subdomain_tmp}"
    # make simple validatio of zip file
    try:
        server_zip = zipfile.ZipFile(import_zip_path, "r")
        namelist = server_zip.namelist()
        assert "dbname.txt" in namelist, "dbname.txt must be in zip archive"
        old_dbname = server_zip.read("dbname.txt")
        old_dbname = (old_dbname).decode("utf-8").strip()
        old_db_file = f"{old_dbname}.db"
        assert old_db_file in namelist, f"{old_db_file} is not in the archive"
    except Exception as e:
        raise ImportError(f"Import was rejected: {type(e).__name__} {str(e)} ")
    yield f"Make safe copy of {subdomain}", 0.1
    # try :
    #    datestring = f"{now.year}-{now.month}-{now.day}-{now.hour}-{now.minute}"
    #    old_subdomain = ( str( list( Path(src).glob("subdomain-*") )[0] ).split('/')[-1] ).split('-')[1]
    #    #print("OLD_SUBDOMAIN = {old_subdomain}")
    #    with open(f'{src}/dbname.txt', 'r') as file:
    #        old_database = file.read().strip()
    #    archive_path = f"{settings.VOLUME}/deleted/{subdomain}-archived-{now.year}-{now.month}-{now.day}-{now.hour}-{now.minute}"
    #    Path(archive_path).mkdir(mode=755,parents=True,exist_ok=True)
    #    yield f"Move entire filetree to archive", 0.6
    #    dest = archive_path
    #    #print(f"MOVE {src} to {dest}")
    #    os.rename(f"{src}/",dest)
    # except Exception as e:
    #    logger.error(f"import error 10981 {type(e).__name__}")
    Path(dest).mkdir(parents=True, exist_ok=True)
    Path(dest).chmod(0o755)
    yield "Unzip uploaded archive", 0.2
    ntot = float(len(namelist))
    for index, member in enumerate(namelist):
        server_zip.extract(member, path=dest)
        prog = int(index / ntot * 100 + 0.5) / 100.0
        yield "Unzipping ", prog
    yield "Unzip done   ", float(0.6)
    # try :
    #    old_subdomain = ( str( list( Path(src).glob("subdomain-*") )[0] ).split('/')[-1] ).split('-')[1]
    #    #print("OLD_SUBDOMAIN = {old_subdomain}")
    #    archive_path = f"{settings.VOLUME}/deleted/{subdomain}-archived-{now.year}-{now.month}-{now.day}-{now.hour}-{now.minute}"
    #    Path(archive_path).mkdir(mode=755,parents=True,exist_ok=True)
    #    yield f"Move entire filetree to archive", 0.6
    #    os.rename(f"{src}/",archive_path)
    # except Exception as e:
    #    logger.error(f"import error 10981 {type(e).__name__}")
    uidold = str(uuid.uuid4())[0:7]
    subprocess.run(["chmod", "-R", "0755", dest])
    yield "run chmod", 0.65
    # try :
    #    conn = connections[subdomain]
    #    conn.close()
    # except Exception as e:
    #    logger.error(f"Import error 2 {type(e).__name__}")
    with open(f"{src}/dbname.txt", "r") as file:
        old_database = file.read().strip()
    with open(f"{dest}/dbname.txt", "r") as file:
        new_database = file.read().strip()
    yield "rename databases ", 0.68
    oldsrc = f"{src}-{uidold}"
    os.rename(src, oldsrc)
    os.rename(dest, src)
    os.rename(f"{src}/{new_database}.db", f"{src}/{old_database}.db")
    # subprocess.run(['echo',f"{old_database}" , '>',f"{src}/dbname.txt"])
    with open(f"{src}/dbname.txt", "w") as f:
        f.write(old_database)
    # server_reset(subdomain)
    # subprocess.run(['./db_rename',subdomain, f"{subdomain}-{uidold}"])
    # subprocess.run(['./db_rename',subdomain_tmp,subdomain])
    # subprocess.run(['./db_reset', subdomain], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT )
    opath = f"/tmp/outdated"
    try:
        os.makedirs(opath, exist_ok=True)
    except Exception as e:
        logger.error(f" EXPORT_IMPORT_ERROR {type(e).__name__} {str(e)}")
    donefile = f"/tmp/outdated/{subdomain}"
    subprocess.run(["touch", donefile])
    subprocess.run(["rm", "-f",f"{src}/subdomain-*"])
    subprocess.run(["touch",f"{src}/subdomain-{subdomain}"])
    if settings.RUNNING_DEVSERVER:
        time.sleep(5)
        subprocess.run(["touch", "backend/settings.py"])
    logger.error("COMPLETED LOAD")
    donefile = f"{settings.VOLUME}/{subdomain}/reset_done"
    # if not os.path.isfile(donefile ) :
    #    return
    # else :
    #    os.remove(donefile)
    subprocess.run(["db_reset", subdomain], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    logger.error("SERVER_RESET")
    tick = 0
    while not os.path.isfile( donefile ) or tick < 5 :
       yield f"Resetting {donefile}", tick * 10.0
       tick = tick + 1 ;
       time.sleep(0.1)
    try:
        os.remove(donefile)
    except Exception as e:
        logger.error(f"ERROR {type(e).__name__} {str(e)}")
    for conn in connections.all():
        logger.error(f" CONN={conn}")
        conn.close_if_unusable_or_obsolete()
    cache = caches["aggregation"]
    for key in cache.keys(f"*{subdomain}*"):
        cache.delete(key)
    try:
        settings.DATABASES[subdomain] = add_database(subdomain)
    except Exception as e:
        logger.error(f"Import error 3 {type(e).__name__}")
    logger.error("OK SO FAR")
    try:
        verify_or_create_database_connection(subdomain)
        conn = connections[subdomain]
        conn.connect()
    except Exception as e:
        logger.error(f"Import error 4 {type(e).__name__}")
    yield f"Clear caches for {subdomain}", .95
    courses = Course.objects.using(subdomain).all()
    logger.error(f"COURSES = {courses}")
    for course in courses:
        logger.error(f"COURSE = {course}")
        course.opentasite = subdomain
        course.google_auth_string = ""
        course.save()
    #    #logger.error(f" subdomain={subdomain} Imported Course = {course} with opentasite = {course.opentasite}")
    # yield f"Almost done importing  ", .99
    exercises_path = f"{settings.VOLUME}/{subdomain}/exercises"
    # purge_export_htmls( exercises_path )
    # yield f"Done removing tempfiles", 1
    #print("DONE!")


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
    db = course.opentasite
    # print(f"EXPORT_COURSE_EXERCISES DB = {db}")
    if settings.RUNTESTS:
        db = "default"
        subdomain = "openta"
    else:
        db = course.opentasite
        subdomain = db
    verify_or_create_database_connection(db)
    metas = list(ExerciseMeta.objects.using(db).select_related("exercise").filter(exercise__course=course))
    exercises_path = os.path.join(settings.VOLUME, subdomain, "exercises")
    for root, directories, filenames in os.walk(exercises_path, followlinks=True):
        for filename in filenames:
            if filename == "exercise.xml":
                name = os.path.basename(os.path.normpath(root))
                relpath = root[len(exercises_path) :]
                if not relpath == "":
                    shutil.copy2("xsl/display.html", root)
                    shutil.copy2("xsl/display.html", root)
                    # print(f"ROOT = {root}")

    for meta in metas:
        exercise = meta.exercise
        try:
            serializer = ExerciseMetaSerializer(meta)
            data = json.dumps(serializer.data)
            full_path = os.path.join(settings.VOLUME, db, "exercises", f"{course.course_key}", exercise.path)
            p = os.path.join(full_path, "meta.json")
            f = open(p, "w")
            f.write(data)
            f.close()
        except Exception as e:
            logger.error(f" Tried to open {p} export meta={meta} exercise={exercise}   and failed")

    logger.debug("EXPORT_COUSER_EXERCISES OPUTPUT_PATH = %s " % output_path)
    _EXERCISES_PATH = course.get_exercises_path()
    # filename = "{name}-cours-exercises.{ext}".format(name=course.course_name, ext="zip")
    now = datetime.now()
    filename = f"{subdomain}-{course.course_name}-exercises-export-{now.year}-{'%02d' % now.month}-{'%02d' % now.day}-{'%02d' % now.hour}-{'%02d' % now.minute}.zip"
    filepath = os.path.join(output_path, filename)
    shutil.copytree("xsl", os.path.join(_EXERCISES_PATH, "xsl"), dirs_exist_ok=True)
    shutil.copy2("xsl/README", os.path.join(_EXERCISES_PATH, "README"))
    logger.debug("EXPORT COURSE EXERCISES exercises_path " + str(course.get_exercises_path()))
    logger.debug("EXPORT COURSE EXERCISES" + str(filepath))
    for result in _zip_recursively(filepath, course.get_exercises_path(), include_exercisekey = False ):
        yield result
    purge_export_htmls(exercises_path)
    # for root, directories, filenames in os.walk( exercises_path , followlinks=True):
    #        for filename in filenames:
    #            if filename == "exercise.xml":
    #                name = os.path.basename(os.path.normpath(root))
    #                relpath = root[len(exercises_path) :]
    #                if ( not relpath == ""):
    #                    fils = ['display.html','ex.html','meta.json']
    #                    for fil in fils :
    #                        ffil = f"{root}/{fil}"
    #                        if os.path.isfile(ffil ):
    #                            os.remove(ffil)


def purge_export_htmls(exercises_path):
    for root, directories, filenames in os.walk(exercises_path, followlinks=True):
        for filename in filenames:
            if filename == "exercise.xml":
                name = os.path.basename(os.path.normpath(root))
                relpath = root[len(exercises_path) :]
                if not relpath == "":
                    fils = ["display.html", "ex.html", "meta.json"]
                    for fil in fils:
                        ffil = f"{root}/{fil}"
                        if os.path.isfile(ffil):
                            os.remove(ffil)


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
    caches["default"].set("temporarily_block_translations", True, 15)
    archive = zipfile.ZipFile(zip_file_path, "r")
    if not settings.RUNTESTS:
        settings.ENABLE_AUTO_TRANSLATE = False
    namelist = archive.namelist()
    members = [filn for filn in namelist if "/exercisekey" not in filn]
    #for name in namelist :
    #    print("NAME = ", name )
    logger.debug("EXTRACTALL TO %s ", course.get_exercises_path())
    exercises_path = course.get_exercises_path()
    archive.extractall(course.get_exercises_path(), members=members)
    for root, directories, filenames in os.walk(exercises_path, followlinks=True):
        for filename in filenames:
            fullfilename = os.path.join(root, filename)
            os.chmod(fullfilename, 0o755)

    messages = []
    for progress in Exercise.objects.sync_with_disc(course, i_am_sure=True):
        messages = messages + progress
    if settings.RUNTESTS:
        db = "default"
    else:
        db = course.opentasite
    exercises = Exercise.objects.using(db).select_related("course", "meta").filter(course=course)
    for exercise in exercises:
        ca = caches["default"].get("temporarily_block_translations")
        # logger.error(f"CA = {ca}" )
        # print(f"EXERCIS IN IMPORT {exercise}")
        meta = exercise.meta
        fullpath = exercise.get_full_path()
        jsonfile = os.path.join(fullpath, "meta.json")
        if os.path.exists(jsonfile):
            # print(f"jsonfile = {jsonfile} exists ")
            with open(jsonfile, "r") as f:
                s = f.read()
            j = json.loads(s)
            # print(f"j = {j}")
            for key in [
                "difficulty",
                "required",
                "image",
                "allow_pdf",
                "bonus",
                "published",
                "locked",
                "sort_key",
                "feedback",
                "deadline_date",
            ]:
                jm = getattr(meta, key)
                # print(f"KEY={key} {j[key]} {jm}")
                setattr(meta, key, j[key])
            # print(f" META = {meta}")
            meta.save()
            exercise.meta = meta
            exercise.save()
            os.remove(jsonfile)
    purge_export_htmls(exercises_path)
    caches["default"].delete("temporarily_block_translations")
    return messages


def import_course_zip(course, zip_file_path, destination):
    """Import exercise zip into course.

    Extracts exercises into file tree and performs a reload on the specified
    course.

    Args:
        courase (course.models.Course): Course to import into.
        zip_file_path (str): Full path to exercises zip file.

    Returns:
        list: List of reload messages.

    """
    logger.error("IMPORT_COURSE_ZIP DESTINATION = %s " % destination)
    db = course.subdomain;
    filetype = zip_file_path.split(".")[-1]
    logger.error("LOC2")
    messages = [];
    filelist = [];
    if filetype == "zip":
        archive = zipfile.ZipFile(zip_file_path, "r")
        namelist = archive.namelist()
        logger.debug("namelist = %s " % namelist)
        members = namelist
        filelist = namelist
        try :
            archive.extractall(destination, members=members)
            messages.append(("success", "Upload to %s was completed; " % destination))
        except Exception as e :
            messages.append(("error", str(e)))

    else:
        logger.error("BEGIN TAR EXTRACTION ZIP_FILE_PATH = %s " % zip_file_path)
        filelist_raw = '';
        filelist = [] ;
        try :
            tar = tarfile.open(zip_file_path, encoding="UTF-8")
        except Excption as e :
            messages.append(('error' , f"{type(e).__name__} {str(e)}"))
            return messages

        with tar as mytar:
                for member in mytar.getmembers():
                    #print(f"MEMBER = {member} destination={destination}")
                    filelist_raw = filelist_raw + str(member) + ", "
                    filelist.append( member.name )
                    mytar.extract(member, path=destination)
    if settings.RUNTESTS :
        return messages
    for filename in filelist:
        logger.error(f"PROCESS {filename}")
        subdir = filename.split('.def')[0];
        basedir = os.path.join( destination, subdir)
        os.makedirs( basedir , exist_ok=True )
        shutil.move(os.path.join(destination,filename), basedir)
    deffiles= glob.glob(f"{destination}/*/*.def")
    #print(f"deffiles = {deffiles}")
    resource_files = [];
    is_def = False
    ids = {}
    basedirs = [];
    for filename in deffiles :
        is_def = True
        f = open(filename,'r')
        basedir = os.path.dirname( filename )
        for line in  f :
            #print(f" LINE = {line}")
            if 'problem_id ' in line :
                problem_id = line.split('=')[-1].strip();
            if 'source_file' in line :
                source = line.split('=')[-1].strip();
                ids[problem_id] = source
                full_source =  os.path.join(settings.WEBWORK_LIBRARY ,source)
                os.makedirs( basedir, exist_ok=True)
                basedirs.append(basedir)
                if os.path.exists(full_source ):
                    shutil.copy2(full_source,basedir)
                #else :
                #    print(f" FULL_SOURCE {full_source} DOES NOT EXIST")
                if os.path.exists( full_source ):
                    f = open( full_source ,'r')
                    for line in f:
                        for resource_type in asset_types :
                            if resource_type in line:
                                m = re.search(rf"\w+{resource_type}",line)
                                if m :
                                    fr = m.group(0);
                                    rdir1 = '/'.join( full_source.split('/')[0:-1] )
                                    rdir2 = '/'.join( full_source.split('/')[0:-2] )
                                    r1 = os.path.join(rdir1,fr);
                                    r2 = os.path.join(rdir2,fr);
                                    for r in [r1,r2]:
                                        if ( os.path.exists(r) ) :
                                            resource_files.append(fr)
                                            shutil.copy2(r,basedir) 
        if is_def :
            os.remove(filename)
                

    pgfiles = glob.glob(f"{destination}/*/*.pg")
    for pgfile in  pgfiles :
        filename = pgfile.split('/')[-1];
        basedir = os.path.dirname( pgfile)
        d  = filename.split('.pg')[0];
        basedirs.append( basedir)
        dest =  os.path.join( basedir,d ) 
        #print(f"basedir = {basedir} dest = {dest}")
        if not os.path.exists( dest ):
            os.makedirs(dest, exist_ok=True )
            shutil.move( pgfile , dest )
        else :
            messages.append(("error", f" {d} already exists; upload not done " ) )
    pgfiles = glob.glob(f"{destination}/*/*/*.pg")
    paths = [];
    resource_dir = None
    #print(f"PGFILES = {pgfiles}")
    for pgfile in pgfiles :
        pgdir = os.path.dirname( pgfile )
        pname = os.path.basename( pgfile );
        name = pname
        #print(f"PGDIR = {pgdir} pname={pname} ")
        for i in ids.keys():
            try : 
                ni = f"{int(i):02}" 
            except :
                ni = i
            if name in ids[i]:
                name = f"problem-{ni}"
        if not os.path.exists( os.path.join( pgdir, 'exercise.xml' ) ) :
            s = f"<exercise><exercisename>{name}</exercisename>\n<global/>\n<question type=\"webworks\" key=\'{name}-1\'>\n<source>{pname}</source>\n</question>\n</exercise>\n";
            #print(f"\n{s}\n")
            epath =  os.path.join( pgdir, "exercise.xml")
            f = open(epath, 'w' )
            f.write(s)
            #print(f"PGDIR = {pgdir}")
        #    pathsplit = pgdir.split('/')
        #    path = f"/{pathsplit[-2]}/{pathsplit[-1]}";
        #    paths.append(path)
            exercise_key = str( uuid.uuid4() )
            f = open( os.path.join( pgdir, 'exercisekey') ,'w' )
            f.write(exercise_key)
        #    #print(f"path = {path}")
        #    #ex.save()
 
    messages.append(("success", "Upload tarfile to %s was completed; " % destination))
    print(f"ASSET_TYPES = {asset_types}")
    for pgfile in pgfiles :
        f = open( pgfile,'r')
        for line in f:
            for resource_type in asset_types :
                if resource_type in line and not resource_type == '.pl' :
                    m = re.search(rf"\w+{resource_type}",line)
                    if m :
                        print(f"LINE IS {line} {asset_types} ")
                        fr = m.group(0);
                        print(f"FR = {fr} pgfile={pgfile} ")
                        dirname = os.path.dirname(pgfile)
                        subdir = os.path.join(dirname, "..")
                        r = os.path.join(subdir, fr )
                        if os.path.exists( r ):
                            print(f"RESOURCE {r} exists ")                               
                            try :
                                shutil.move( r , dirname )
                            except Exception as e :
                                messages.append(("error",f" {type(e).__name__} File {r} in {dirname} exists"))
                        else :
                            print(f"RESOURCE {r} DOES NOT EXISTS")
                         
                        #if fr in resource_files :
                        #    exercise_dir  = '/'.join( pgfile.split('/')[0:-1] )
                        #    resource_dir  = '/'.join( pgfile.split('/')[0:-2] )
                        #    resource_path = os.path.join( resource_dir , fr )
                        #    if os.path.exists(resource_path ) :
                        #        shutil.copy2( resource_path, exercise_dir)

        #if resource_dir :
        #    for f in list( set( resource_files  ) ):
        #        os.remove(os.path.join( resource_dir, f ) )
    basedirs = list( set( basedirs) )
    #for basedir in basedirs :
    #    subpath = basedir.split('/')[-1];
    #    for progress in Exercise.objects.sync_with_disc(course, i_am_sure=True,db=db ):
    #        messages = messages + progress
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
    msg1 = ""
    msg2 = ""
    # THIS LOGIC WAS NOT REALLY OK BEFORE
    # IF ** ANY ** dryrun results in an error
    # THE IMPORT SHOULD NOT BE DONE
    # THE OLD CODE COULD RESULT IN A PARTIAL IMPORT
    try:
        for dryrun in [False]:
            msg = " (testing only)" if dryrun else ""
            for index, csv in enumerate(files):
                logger.debug("CSV = " + str(csv))
                if csv.endswith(".csv"):
                    # time.sleep(0.3)
                    parts = csv.split("_")
                    class_name = parts[1].split(".")[0]
                    # logger.debug("Importing " + str(  class_name ) )
                    yield class_name + msg, index / max(n_total, 1)
                    with open(os.path.join(import_path, csv)) as csv_file:
                        csv_contents = csv_file.read()
                        dataset = tablib.Dataset().load(csv_contents)
                        if class_name in import_lookup:
                            resource = import_lookup[class_name]
                            res = resource.import_data(dataset, dry_run=dryrun)
                            if res.has_errors():
                                # THIS WAS DIFFICULT TO DEBUG: LOTS OF INFO IF CRASH
                                logger.debug("CSV_CONTENTS = " + str(csv_contents))
                                logger.debug("RES HAS ERROR")
                                logger.debug("RESOURCE = ")
                                raise ImportError("D: Importing " + str(class_name) + ". ")
                            else:
                                pass
                                # res = resource.import_data(dataset, dry_run=False)
    except Exception as e:
        raise ImportError("ERROR: C csv = : " + str(csv))  # + +str(e) + msg1 + msg2)


def _zip_recursively(output_filepath, input_path, include_exercisekey ):
    """Zip path recursively with progress report.

    Args:
        output_filepath (str): Path to output folder.
        input_path (str): Path to input folder.
        report_steps (int, optional): Number of steps to report progress in.

    Yields:
        tuple (output_filepath, fraction_complete)

    """
    relative_base = None;
    report_steps = 10;
    if relative_base is None or settings.UNITTESTS:
        relative_base = input_path
    archive = zipfile.ZipFile(output_filepath, "w")
    files = list(Path(input_path).glob("**/*"))
    num_files = max(len(files), 1)
    for index, f in enumerate(files):
        # logger.debug("ZIP INDEX = %s " %  index )
        sf = str(f)
        if not "/backups/" in sf and not "/history/" in sf:
            if 'exercisekey' in sf and not include_exercisekey :
                pass ;
            else :
                archive.write(str(f.resolve()), str(f.relative_to(relative_base)))
        if index % (num_files // report_steps + 1) == 0:
            yield output_filepath, (index / num_files)
    archive.close()
