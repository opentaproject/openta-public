from rest_framework.decorators import api_view
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import permission_required
from django.utils.translation import ugettext as _
from rest_framework.response import Response
import backend.settings as settings

from course.serializers import CourseSerializer, CourseStudentSerializer
from course.models import Course
from course.forms import CourseFormFrontend


class CourseUpdate(UpdateView):
    model = Course
    form_class = CourseFormFrontend
    # fields = ['course_name', 'registration_password', 'registration_by_password', 'owners']
    success_url = '/' + settings.SUBPATH + 'course/{id}/updateoptions'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_text'] = _('Save')
        return context


@permission_required('course.administer_course')
def CourseUpdateView(request, course):
    result = CourseUpdate.as_view()(request, pk=course)
    if request.method == 'POST':
        result.set_cookie('submitted', 'true')
    else:
        result.set_cookie('submitted', 'false')
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
    if request.user.is_superuser:
        scourse = CourseSerializer(courses, many=True)
    elif request.user.is_staff:
        courses_owned = Course.objects.filter(owners=request.user)
        scourse = CourseSerializer(courses_owned, many=True)
    else:
        courses = request.user.opentauser.courses.filter(published=True)
        scourse = CourseStudentSerializer(courses, many=True)

    return Response(scourse.data)
