import os
from .models import Exercise, ExerciseMeta, Question, Answer, ImageAnswer, AuditExercise
from course.models import Course
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
import exercises.paths as paths


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
    u1 = User.objects.create_user('student1', 'student1@test.se', 'pw')
    u2 = User.objects.create_user('student2', 'student2@test.se', 'pw')
    uadmin = User.objects.create_superuser('admin1', 'admin1@test.se', 'pw')
    student.user_set.add(u1)
    student.user_set.add(u2)
    admin.user_set.add(uadmin)
    author.user_set.add(uadmin)


def create_exercise(directory, name):
    path = os.path.join(directory.name, name)
    os.makedirs(path)
    exercise_path = os.path.join(path, "exercise.xml")
    print(exercise_path)
    with open(exercise_path, "w") as f:
        f.write(
            """
                <exercise>\n
                <exercisename>Exercise1</exercisename>\n
                <text>Test exercise text</text>\n
                <question type="compareNumeric">\n
                <text>compareNumeric</text>\n
                <expression>sin(2)</expression>\n
                </question>\n
                </exercise>\n
                """
        )
    return os.path.join(name)
