import os
from course.models import Course
from users.models import OpenTAUser
from django.contrib.auth.models import User, Group, Permission
from PIL import Image

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
DATABASE_PASSWORD = 'pw'
DEFAULT_EXERCISE = DEFAULT_EXERCISE_TEMPLATE.format(name=DEFAULT_EXERCISE_NAME)


def create_database(password="pw", course_key=None):
    if course_key is not None:
        course, created = Course.objects.get_or_create(
            course_name="Test course", course_key=course_key, published=True)
    else:
        course, created = Course.objects.get_or_create(course_name="Test course", published=True)
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
    u1 = create_user('student1', 'student1@test.se', 'pw', course=course)
    u2 = create_user('student2', 'student2@test.se', 'pw', course=course)
    uadmin = User.objects.create_superuser('admin1', 'admin1@test.se', 'pw')
    usuper = User.objects.create_superuser('super', 'admin1@test.se', 'pw')
    student.user_set.add(u1)
    student.user_set.add(u2)
    admin.user_set.add(uadmin)
    view.user_set.add(uadmin)
    admin.user_set.add(usuper)
    author.user_set.add(usuper)
    view.user_set.add(usuper)


def create_exercises_from_dir(course, directory):
    exerciselist = []
    for name in os.listdir(directory):
        path = os.path.join(directory, course.get_exercises_folder(), name)
        exerciselist = exerciselist + [os.path.join(name)]
    return exerciselist


def create_exercise_from_dir(course, directory, name):
    path = os.path.join(directory, course.get_exercises_folder(), name)
    return os.path.join(name)


def create_exercise(course, directory, name, content=DEFAULT_EXERCISE):
    path = os.path.join(directory, course.get_exercises_folder(), name)
    os.makedirs(path)
    exercise_path = os.path.join(path, "exercise.xml")
    image_path = os.path.join(path, "figure.png")
    with open(exercise_path, "w") as f:
        f.write(content)
    image = Image.new('RGBA', size=(100, 100), color=(0, 255, 0))
    with open(image_path, 'wb') as f:
        image.save(f, 'PNG')
    return os.path.join(name)


def create_user(name, email, pw, course):
    user = User.objects.create_user(name, email, pw)
    opentauser, _ = OpenTAUser.objects.get_or_create(user=user)
    opentauser.courses.add(course)
    return user
