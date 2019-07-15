from django import forms
from course.models import Course
from django.utils.translation import ugettext_lazy as _


HELP_TEXTS = {
    'url': _("The course url, including http:// or https:// or leave blank" ),
    'registration_domains': _(
        'Comma separated list of email domains' ' that are permitted to self-register'
    ),
    'email_host_password': _(
        'Password for your email account (Please use SSO,'
        ' the password is stored in cleartext on the server)'
    ),
    'email_host': _('For instance smtp.gmail.com Uses port 587/TLS'),
    'email_reply_to': _('Full email of the course admin'),
    'email_host_user': _('Entire email of smtp account owner ,i.e. myemail@gmail.com'),
    'email_username': _('username only i.e. usually  myemail'),
    'languages': _(
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


class CourseFormFrontend(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CourseFormFrontend, self).__init__(*args, **kwargs)

    lti_key = forms.CharField(disabled=True)
    lti_secret = forms.CharField(disabled=True)

    class Meta:
        model = Course
        # fields = '__all__'
        fields = [
            'published',
            'course_name', 
            'course_long_name',
            'url', 
            'motd', 'difficulties',
            'deadline_time',
            'url',
            'lti_key',
            'lti_secret',
            'registration_by_domain',
            'registration_domains',
            'languages',
            'registration_password',
            'registration_by_password',
            'owners',
        ]
        widgets = {
            'owners': forms.CheckboxSelectMultiple(),
            'motd': forms.Textarea(attrs={'cols': 80, 'rows': 10}),
            'url': forms.Textarea(attrs={'cols': 80, 'rows': 1}),
            'difficulties': forms.Textarea(attrs={'cols': 80, 'rows': 10}),
        }
        help_texts = HELP_TEXTS
