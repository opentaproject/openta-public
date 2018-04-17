import os
from course.models import Course
from django.contrib.auth.models import User, Group, Permission
from PIL import Image

DEFAULT_EXERCISE = """
                <exercise>\n
                <exercisename>Exercise1</exercisename>\n
                <text>Test exercise text</text>\n
                <figure>figure.png</figure>\n
                <question type="compareNumeric" key="1">\n
                <text>compareNumeric</text>\n
                <expression>sin(2)</expression>\n
                </question>\n
                </exercise>\n
                """


def create_database(password="pw"):
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
    u1 = User.objects.create_user('student1', 'student1@test.se', 'pw')
    u2 = User.objects.create_user('student2', 'student2@test.se', 'pw')
    uadmin = User.objects.create_superuser('admin1', 'admin1@test.se', 'pw')
    usuper = User.objects.create_superuser('super', 'admin1@test.se', 'pw')
    student.user_set.add(u1)
    student.user_set.add(u2)
    admin.user_set.add(uadmin)
    view.user_set.add(uadmin)
    admin.user_set.add(usuper)
    author.user_set.add(usuper)
    view.user_set.add(usuper)
    course, created = Course.objects.get_or_create(course_name="Test course")


def create_exercise(directory, name, content=DEFAULT_EXERCISE):
    path = os.path.join(directory.name, name)
    os.makedirs(path)
    exercise_path = os.path.join(path, "exercise.xml")
    image_path = os.path.join(path, "figure.png")
    print(exercise_path)
    with open(exercise_path, "w") as f:
        f.write(content)
    image = Image.new('RGBA', size=(100, 100), color=(0, 255, 0))
    with open(image_path, 'wb') as f:
        image.save(f, 'PNG')
    return os.path.join(name)
