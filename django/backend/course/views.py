from rest_framework.decorators import api_view
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
import backend.settings as settings

from course.serializers import CourseSerializer, CourseStudentSerializer
from course.models import Course
from course.forms import CourseForm


class CourseUpdate(UpdateView):
    model = Course
    #    form_class = CourseForm
    fields = ['course_name', 'registration_password', 'registration_by_password']
    success_url = '/' + settings.SUBPATH + 'course/{id}/updateoptions'


@permission_required('course.administer_course')
def CourseUpdateView(request, course):
    result = CourseUpdate.as_view()(request, pk=course)
    if request.method == 'POST':
        result.set_cookie('course-submitted', 'true')
    else:
        result.set_cookie('course-submitted', 'false')
    return result


@api_view(['GET'])
def get_current_course(request):
    course = Course.objects.first()
    if request.user.is_staff:
        scourse = CourseSerializer(course)
    else:
        scourse = CourseStudentSerializer(course)
    return Response(scourse.data)


@api_view(['GET'])
def get_courses(request):
    courses = Course.objects.all()
    if request.user.is_staff:
        scourse = CourseSerializer(courses, many=True)
    else:
        scourse = CourseStudentSerializer(courses, many=True)
    return Response(scourse.data)
