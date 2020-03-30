from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import permission_required
from django.utils.translation import ugettext as _
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from rest_framework.response import Response
import backend.settings as settings

from course.serializers import CourseSerializer, CourseStudentSerializer
from course.models import Course
from course.forms import CourseFormFrontend
from course.export_import import import_course_exercises


class CourseUpdate(UpdateView):
    model = Course
    form_class = CourseFormFrontend
    # fields = ['course_name', 'registration_password', 'registration_by_password', 'owners']
    readonly_fields = ('course_key', 'lti_key', 'lti_secret')
    success_url = '/' + settings.SUBPATH + 'course/{id}/updateoptions/'

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
def get_course(request, course_pk):
    course = Course.objects.get(pk=course_pk)
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
        courses_enrolled = Course.objects.filter(
            pk__in=request.user.opentauser.courses.values_list('pk', flat=True)
        )
        scourse = CourseSerializer(courses_owned | courses_enrolled, many=True)
    else:
        courses = request.user.opentauser.courses.filter(published=True)
        scourse = CourseStudentSerializer(courses, many=True)

    return Response(scourse.data)


@api_view(['POST'])
@parser_classes((MultiPartParser,))
def upload_exercises(request, course_pk):
    if request.FILES['file'].size > 100e6:
        return Response("File larger than 100mb", status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        dbcourse = Course.objects.get(pk=course_pk)
        if not request.user.has_perm('exercises.edit_exercise'):
            return Response({}, status.HTTP_403_FORBIDDEN)
        res = import_course_exercises(dbcourse, request.FILES['file'].temporary_file_path())
        return Response(res)

    except Exception as e:
        return Response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
