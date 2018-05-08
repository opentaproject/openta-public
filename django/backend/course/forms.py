from django import forms
from course.models import Course


HELP_TEXTS = {
    'url': "The course url, including http:// or https://",
    'registration_domains': (
        'Comma separated list of email domains' ' that are permitted to self-register'
    ),
    'email_host_password': (
        'Password for your email account (Please use SSO,'
        ' the password is stored in cleartext on the server)'
    ),
    'email_host': 'Uses port 587/TLS',
    'email_reply_to': 'Email of the course admin',
    'languages': (
        'Languages for translations in the course:'
        ' the first language is dominant and used in emails.'
    ),
}


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        exclude = []
        fields = '__all__'
        widgets = {'registration_password': forms.PasswordInput(render_value=True)}
        help_texts = HELP_TEXTS


class CourseFormFrontend(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'published',
            'course_name',
            'course_long_name',
            'deadline_time',
            'url',
            'registration_by_domain',
            'registration_domains',
            'languages',
            'registration_password',
            'registration_by_password',
            'owners',
        ]
        widgets = {'owners': forms.CheckboxSelectMultiple()}
        help_texts = HELP_TEXTS
