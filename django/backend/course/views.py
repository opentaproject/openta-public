from django.shortcuts import render
from course.models import Course
from django.views.generic.edit import UpdateView
from course.forms import CourseForm
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import permission_required


class CourseUpdate(UpdateView):
    model = Course
    form_class = CourseForm
    fields = ['course_name', 'registration_password', 'registration_by_password']
    success_url = '/course/{id}'


@permission_required('course.administer_course')
def CourseUpdateView(request, course):
    result = CourseUpdate.as_view()(request, pk=course)
    if request.method == 'POST':
        result.set_cookie('course-submitted', 'true')
    else:
        result.set_cookie('course-submitted', 'false')
    return result
