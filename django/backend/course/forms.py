from django import forms
from course.models import Course
from django.utils.translation import ugettext as _


class CourseForm(forms.ModelForm):
    registration_password = forms.CharField(
        label=_('Registration password')
    )  # ,widget=forms.PasswordInput)

    class Meta:
        model = Course
        fields = '__all__'
