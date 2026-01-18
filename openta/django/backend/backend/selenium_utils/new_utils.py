# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import datetime
import glob
import logging
import os
import shutil
import ipdb

import exercises.paths as paths
from course.models import Course
from exercises.models import Exercise
from exercises.parsing import (
    exercise_xml,
    exercise_xmltree,
    get_questionkeys_from_xml,
    global_and_question_xmltree_get,
)
from exercises.question import get_usermacros
from PIL import Image
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from users.models import OpenTAUser

from backend.selenium_utils import create_selenium
from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.mail import get_connection
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils import timezone

logger = logging.getLogger(__name__)


DEFAULT_EXERCISE_NAME = "Exercise1"
DEFAULT_EXERCISE_TEMPLATE = """
                <exercise>\n
                <exercisename>{name}</exercisename>\n
                <text>Test exercise text</text>\n
                <figure>figure.png</figure>\n
                <question type="compareNumeric" key="1">\n
                <text>compareNumeric</text>\n
                <expression>sin(2)</expression>\n
                </question>\n
                </exercise>\n
                """
DATABASE_PASSWORD = "pw"
DEFAULT_EXERCISE = DEFAULT_EXERCISE_TEMPLATE.format(name=DEFAULT_EXERCISE_NAME)


from course.models import Course

logger = logging.getLogger(__name__)


def touch_():
    if settings.MULTICOURSE:
        fname = os.path.join("/%s/" % settings.VOLUME, settings.SUBDOMAIN, "touchfile")
        if os.path.exists(fname):
            os.utime(fname, None)
        else:
            open(fname, "a").close()


def send_email_object(email):
    course = Course.objects.first()
    docustom = bool(
        course.use_email
        and course.email_host
        and course.email_host_password
        and course.email_reply_to
        and course.email_host_user
    )
    logger.error("SEND EMAIL OBJECT")
    if (
        (hasattr(settings, "USE_CUSTOM_SMTP_EMAIL") and settings.USE_CUSTOM_SMTP_EMAIL)
        or docustom
        or settings.ANYMAIL
        or settings.USE_GMAIL
    ):
        email_host = settings.EMAIL_HOST
        email_host_password = settings.EMAIL_HOST_PASSWORD
        email_host_user = settings.EMAIL_HOST_USER
        email_username = settings.EMAIL_HOST_USER
        settings.EMAIL_HOST_USER

        if docustom:
            logger.error("DOCUSTOM")
            email_host = course.email_host
            email_host_password = course.email_host_password
            course.email_reply_to
            email_host_user = course.email_host_user
            email_username = course.email_username
        elif hasattr(settings, "USE_CUSTOM_SMTP_EMAIL") and settings.USE_CUSTOM_SMTP_EMAIL:
            logger.error("USE_CUSTOM_SMTP_MAIL")
            email_host = settings.EMAIL_HOST
            email_host_password = settings.EMAIL_HOST_PASSWORD
            email_host_user = settings.EMAIL_HOST_USER
            email_username = settings.EMAIL_HOST_USER
            settings.EMAIL_HOST_USER
        elif hasattr(settings, "ANYMAIL"):
            logger.error("DO ANYMAIL")
            email_host = "smtp.mailgun.org"
            email_username = settings.EMAIL_HOST_USER
            email_host_password = settings.EMAIL_HOST_PASSWORD
            email_host_user = settings.EMAIL_HOST_USER
            settings.EMAIL_HOST_USER
        logger.error(" EMAIL BACKEND %s " % settings.EMAIL_BACKEND)
        logger.error(" EMAIL HOST %s " % email_host)
        logger.error(" EMAIL USERNAME %s " % email_username)
        logger.error(" EMAIL_HOST PASSWORD %s " % email_host_password)
        logger.error(" EMAIL_HOST_USER %s " % email_host_user)
        logger.error("EMAIL = %s " % email)
        logger.error("SUBJECT %s " % email.subject)
        logger.error(" TO %s " % email.to)
        logger.error(" FROM %s " % email.from_email)
        logger.error(" REPLOY_TO %s " % email.reply_to)
        logger.error(
            " COURSSE emails a: %s b:  %s c:  %s d: %s  "
            % (course.email_reply_to, course.email_host, course.email_host_user, course.email_username)
        )
        n_sent = 0
        with get_connection(
            host=email_host,
            port="587",
            username=email_username,
            password=email_host_password,
            email_host_user=email_host_user,
            email_host_reply_to="opentaproject@gmail.com",
            use_tls=True,
        ) as connection:
            email.connection = connection
        try:
            n_sent = email.send()
            logger.error("send_email_object success" + " (" + str(n_sent) + " delivered)")
        except Exception as e:
            logger.error(str(e))
            raise e
    else:
        logger.error("DO ORDINARY EMAIL %s " % email)
        try:
            n_sent = 0
            n_sent = email.send()
            logger.error("send_email_object success" + " (" + str(n_sent) + " delivered)")
        except Exception as e:
            logger.error("send_email_object fail" + str(e))
            raise e
    return n_sent


def response_from_messages(messages):
    result = dict(status=set())
    result["messages"] = messages
    for msg in messages:
        result["status"].add(msg[0])
    if "error" not in result["status"]:
        result["success"] = True
    return result


def get_localized_template(template_name):
    """Get major language version of template."""
    course = Course.objects.first()
    try:
        first_language = course.languages.split(",")[0]
    except AttributeError:
        first_language = "en"
    try:
        template = get_template(template_name + "." + first_language)
    except TemplateDoesNotExist as exception:
        logger.error(template_name + "." + first_language + " does not exist")
        raise exception
    return template


def create_database(password="pw", course_key=None, course_name="Test course"):
    if course_key is not None:
        course, created = Course.objects.get_or_create(course_name=course_name, course_key=course_key, published=True, opentasite="openta")
    else:
        course, created = Course.objects.get_or_create(course_name=course_name, published=True, opentasite="openta")
    perm_edit_exercise = Permission.objects.get(codename="edit_exercise")
    perm_admin_exercise = Permission.objects.get(codename="administer_exercise")
    perm_log_answer = Permission.objects.get(codename="log_question")
    student, created = Group.objects.get_or_create(name="Student")
    student.permissions.add(perm_log_answer)
    student.save()
    admin, created = Group.objects.get_or_create(name="Admin")
    admin.permissions.add(perm_admin_exercise)
    admin.save()
    author, created = Group.objects.get_or_create(name="Author")
    author.permissions.add(perm_edit_exercise)
    author.save()
    view, created = Group.objects.get_or_create(name="View")
    view.save()
    u1 = create_user("student1", "student1@test.se", password, course=course)
    u2 = create_user("student2", "student2@test.se", password, course=course)
    u3 = create_user("admin3", "admin3@test.se", password, course=course)
    u4 = create_user("admin4", "admin4@test.se", "admin4@test.se", course=course)
    u5 = create_user("admin5", "admin5@test.se", "admin5", course=course)
    uadmin = User.objects.create_superuser("admin1", "admin1@test.se", password)
    usuper = User.objects.create_superuser("super", "admin1@test.se", password)
    student.user_set.add(u1)

    for u in [u3, u4, u5]:
        admin.user_set.add(u)
        author.user_set.add(u)
        view.user_set.add(u)
    # student.user_set.add(u3)
    student.user_set.add(u2)
    admin.user_set.add(uadmin)
    view.user_set.add(uadmin)
    admin.user_set.add(usuper)
    author.user_set.add(usuper)
    view.user_set.add(usuper)


def create_exercises_from_dir(course, directory):
    logger.error("CREATE EXERCISES FROM DIRECTORY %s", directory)
    exerciselist = []
    src = os.path.join(directory, "exercises", course.get_exercises_folder())
    logger.error("EXERCISES_PATH = %s " % course.get_exercises_path())
    logger.error("SRC = %s " % src)
    dest = course.get_exercises_path()
    logger.error("DEST =  %s " % dest)
    psrc = "/".join(src.split("/")[0:-2])
    pdest = "/".join(dest.split("/")[0:-2])
    logger.error("PSRC = %s PDEST = %s " % (psrc, pdest))
    shutil.copytree(psrc, pdest, dirs_exist_ok=True)
    for name in os.listdir(src):
        logger.error("NAME = %s " % name)
        path = os.path.join(directory, course.get_exercises_folder(), name)
        logger.error("PATH = %s " % path)
        exerciselist = exerciselist + [name]
    logger.error("EXERCISELIST = %s " % exerciselist)
    return exerciselist


def create_exercise_from_dir(course, directory, name):
    logger.error(f"CREATE EXERCISE FROM DIR {directory}")
    path = os.path.join(directory, course.get_exercises_folder(), name)
    logger.error("PATH = %s " % path)
    return os.path.join(name)


def create_exercise(course, directory, name, content=DEFAULT_EXERCISE):
    logger.error(f"CREATE EXERCISES DIRECTORY = {directory}")
    logger.error(f"CREATE EXERCISES EXERCISE_FOLDER = {course.get_exercises_folder()}")
    logger.error(f"CREATE EXERCISES NAME = {name}")
    path = os.path.join(directory, course.get_exercises_path(), name)
    logger.error(f"PATH = {path}")
    os.makedirs(path)
    exercise_path = os.path.join(path, "exercise.xml")
    image_path = os.path.join(path, "figure.png")
    with open(exercise_path, "w") as f:
        f.write(content)
    image = Image.new("RGBA", size=(100, 100), color=(0, 255, 0))
    with open(image_path, "wb") as f:
        image.save(f, "PNG")
    return os.path.join(name)


def create_user(name, email, pw, course):
    user = User.objects.create_user(name, email, pw)
    if "admin" in name:
        user.is_staff = True
        user.save()
    opentauser, _ = OpenTAUser.objects.get_or_create(user=user)
    opentauser.courses.add(course)
    return user


class OpenTAStaticLiveServerTestCase(StaticLiveServerTestCase):
    """

    The standard test case class only gives the base URL to the server. To
    to live_server_url.

    """

    dirname = None
    course_key = None
    username = None
    role = None
    selenium = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = create_selenium()
        cls.selenium.implicitly_wait(0)

    @classmethod
    def tearDownClass(cls):
        logger.error("RUNNING TEARDOWN AFTER TEST COMPLETE")
        cls.selenium.quit()
        super().tearDownClass()

    @property
    def live_server_url(self):
        return super().live_server_url

    def setUp(self, dirname=None):
        if os.path.isdir(f"{settings.VOLUME}/openta"):
            shutil.rmtree(f"{settings.VOLUME}/openta")
        super().setUp()

        if dirname is not None:
            logger.error("SET UP DIRNAME = %s " % dirname)
            dirs = glob.glob(dirname + "/exercises/*")
            dirlist_ = [item.split("/")[-1] for item in dirs]
            dirlist = list(filter(lambda c: len(c) > 15, dirlist_))
            logger.error("DIRLIST = %s " % dirlist)
            [course_key] = dirlist
            create_database(password="pw", course_key=course_key)
            course = Course.objects.first()
            create_exercises_from_dir(course, dirname)
            paths.EXERCISES_PATH = dirname
            paths.STUDENT_ASSETS_PATH = dirname + "/studentassets"
            for msg in Exercise.objects.sync_with_disc(course, i_am_sure=True):
                logger.error(msg)
            self.dirname = dirname
            self.course_key = course_key

    def open_site(self):
        sel = self.selenium
        sel.get(self.live_server_url)

    def login(self, username="admin3", pw="pw", assert_role="admin"):
        sel = self.selenium
        wait = WebDriverWait(sel, settings.LONG_WAIT)
        self.username = username
        self.role = assert_role
        input_username = sel.find_element(By.CSS_SELECTOR, "input[id=id_username]")
        input_password = sel.find_element(By.CSS_SELECTOR, "input[id=id_password]")
        login = sel.find_element(By.CSS_SELECTOR, "input[type=submit]")
        input_username.clear()
        input_username.send_keys(username)
        input_password.clear()
        input_password.send_keys(pw)
        logger.error("CLICK LOGIN")
        logger.error("DIRNAME = %s " % self.dirname)
        login.click()
        logger.error("NOW WAIT FOR OpenHeader TO COME UP")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "OpenHeader")))
        logger.error("NOW WAIT FOR APP TEST_STUDENT.PY TO COME UP")
        sel.find_element(By.CLASS_NAME, "OpenHeader").click()
        logger.error("NOW WAIT FOR APP TO COME UP")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.course-exercise-item")))
        # wait.until(EC.text_to_be_present_in_element((By.ID, 'app'), assert_role))
        # logger.error("ASSERT_ROLE", assert_role)
        # assert assert_role in sel.page_source

    def tearDown(self):
        super().tearDown()

    def logout(self):
        sel = self.selenium
        wait = WebDriverWait(sel, settings.LONG_WAIT)
        logger.error("NOW WAIT FOR LOGOUT TO APPEAR")
        wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'logout')]")))
        sel.find_element(By.XPATH, "//a[contains(@href,'logout')]").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//form[contains(@action, 'login')]")))
        logger.error("NOW LOGIN HAS REAPPEARED")

    def find_exercise_element(self, exercise):
        """Return the element that matches the exercise"""
        if hasattr(exercise, "exercise_key"):
            exercise_key = exercise.exercise_key
            return self.selenium.find_element(By.CSS_SELECTOR, f"li.course-exercise-item[id={exercise_key}]")

        return self.selenium.find_element(By.XPATH, '//a[@id="course-exercise-item-button"]')

    def click_exercise(self, exercise):
        sel = self.selenium
        wait = WebDriverWait(sel, settings.LONG_WAIT)

        element = self.find_exercise_element(exercise)

        try:
            element.click()

        except StaleElementReferenceException:
            # it's possible the page was reloaded and the element has not reloaded yet
            #
            # find it again and then click on it
            element = self.find_exercise_element(exercise)
            element.click()

        wait.until(EC.presence_of_element_located((By.XPATH, "//article")))

    def answerall(self, exercise, answerdict=None):
        name = exercise.path
        exercise_key = exercise.exercise_key
        logger.error("ANSWERALL NAME = %s " % name)
        logger.error("EXERCISEKEY = %s " % exercise_key)
        xmlpath = os.path.join(self.dirname, "exercises", self.course_key, name)
        logger.error("XMLPATH CONTAINS %s " % os.listdir(xmlpath))
        xml = exercise_xml(xmlpath)
        questionkeys = get_questionkeys_from_xml(xml)
        logger.error("QUESTIONKEYS = %s " % questionkeys)
        user = User.objects.get(username=self.username)

        sel = self.selenium
        wait = WebDriverWait(sel, settings.LONG_WAIT)
        tot = 0
        for questionkey in questionkeys:
            usermacros = get_usermacros(
                user, exercise_key, question_key=questionkey, before_date=None, db=settings.DB_NAME
            )
            exercisetree = exercise_xmltree(xmlpath, usermacros)
            [globaltree, exercisetree] = global_and_question_xmltree_get(exercisetree, questionkey, usermacros)

            logger.error("QUESTIONKEY = %s " % questionkey)
            logger.error("USERMACROS = %s " % usermacros)

            if questionkey in answerdict:
                ans = answerdict[questionkey]
                logger.error("ANSWERDICT = %s " % answerdict)
                logger.error("ANS = %s " % ans)

                selector = f"//textarea[contains(@qkey,'{questionkey}')]"
                wait.until(EC.presence_of_element_located((By.XPATH, selector)))

                # see: How To Handle Stale Element Reference
                # https://www.lambdatest.com/blog/handling-stale-element-exceptions-in-selenium-java/
                repeat = 0;
                while repeat < 3:
                    try:
                        answerarea = sel.find_element(By.XPATH, selector)
                        answerarea.click()
                        answerarea.send_keys(ans)
                        break
                    except StaleElementReferenceException as e:
                        logger.error(f" ERROR IN SEND KEYS {type(e).__name__} {str(e)}")
                    repeat += 1

            st = "//a/i[contains(@qkey, '" + questionkey + "')]"
            wait.until(EC.presence_of_element_located((By.XPATH, st)))
            button = sel.find_element(By.XPATH, st)
            button.click()
            readystring = f"//div[contains(@class, 'ready') and contains(@id, '{questionkey}') ]"
            wait.until(EC.presence_of_element_located((By.XPATH, readystring)))
            tot = tot + 1

        yescorrects = sel.find_elements(
            By.XPATH, "//div[contains(@class, 'yescorrect') and contains(@class, 'uk-alert') ]"
        )
        # longyes = sel.find_elements(By.XPATH, "//div[contains(@class, 'yescorrect') ]")
        logger.error(f"YESCORRECTS {len(yescorrects)}")
        isunchecked = sel.find_elements(
            By.XPATH, "//div[contains(@class, 'isunchecked') and contains(@class, 'uk-alert') ]"
        )
        logger.error(f"ISUNCHECED {len(isunchecked)}")
        nocorrects = sel.find_elements(
            By.XPATH, "//div[contains(@class, 'nocorrect') and contains(@class, 'uk-alert') ]"
        )
        logger.error(f"NOCORRECTS {len(nocorrects)}")
        syntaxerrors = sel.find_elements(
            By.XPATH, "//div[contains(@class, 'hassyntaxerror') and contains(@class, 'uk-alert') ]"
        )
        logger.error(f"SYNTAXERRORS {len(syntaxerrors)}")
        summit = len(yescorrects) + len(isunchecked) + len(nocorrects) + len(syntaxerrors)
        check = tot - summit
        if check != 0:
            ipdb.set_trace()
        ret = [tot, len(yescorrects), len(isunchecked), len(nocorrects), len(syntaxerrors)]
        assert check == 0
        logger.error(f"RET = {ret}")
        logger.error(f"READY RET = {ret}")
        return ret

    def change_exercise_options(self, exercise):
        exercise.meta.published = True
        exercise.meta.required = True
        exercise.meta.feedback = True
        exercise.meta.feedback = True
        exercise.meta.image = True
        exercise.meta.deadline_date = timezone.now() + datetime.timedelta(days=2)
        exercise.meta.save()
