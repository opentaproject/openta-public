from course.models import Course
from users.models import OpenTAUser
from django.contrib.auth.models import User
from django.conf import settings
from exercises.models import Exercise
settings.DB_NAME='ffy143-2019'
settings.SUBDOMAIN='ffy143-2019'
users = User.objects.all();
course = Course.objects.get(pk=1);
print("COURSE PK = ", course.pk)
for user in users:
   try: 
        print("USER = ", user.email)
        opentauser ,_ = OpenTAUser.objects.get_or_create(user=user)
        opentauser.courses.add(course)
        opentauser.save()
        user.save()
        print("OK USER %s " %  user.email)
   except:
        print("FAILED %s " %  user.email)

exercises = Exercise.objects.all()
for exercise in exercises  :
   try: 
        print("path = ",exercise.path)
        print("OK USER %s " %  exercise)
        exercise.path = exercise.path.strip('/')
        exercise.course = course
        exercise.save()
   except:
        print("FAILED %s " %  exercise)
