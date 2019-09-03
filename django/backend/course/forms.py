from django import forms
from django.conf import settings
from course.models import Course, send_email_object
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.core.exceptions import ValidationError
from google.cloud import translate
from google.oauth2 import service_account
import tempfile
import io, json
from django.contrib import messages


def patch_credential_string(value):
    return value.strip().lstrip('r').strip("'")


def google_auth_string_is_valid(value):
    try:
        print("VALUE = ", value)
        credentialstring = patch_credential_string(value)
        service_account_info = json.load(io.StringIO(credentialstring))
        credentials = service_account.Credentials.from_service_account_info(service_account_info)
        translate_client = translate.Client(credentials=credentials)
        should_be_en = translate_client.detect_language('This is a statement in english')[
            'language'
        ]
        print("SHOULD BVE EN ", should_be_en)
        return 'en' == should_be_en
    except Exception as e:
        print("GOOGLE AUTH STRING ERROR ", str(e))
        return False


HELP_TEXTS = {
    'use_lti': _('reveal LTI/Canvas parameters'),
    'use_email': _('Check to enable the use of  email'),
    'url': "Course url.  Reset by deleting it. Augment with /lti/config_xml/ for LTI URL configuration ",
    'registration_domains': _(
        'Comma separated list of email domains' ' that are permitted to self-register'
    ),
    'course_name': _(
        'A short name '
        'preferably without spaces or special characters; appears in course-url. Something like fysik2-2019 would be suitable. '
        'Do not plan to change this after students have begun using the course via canvas/lti. '
    ),
    'course_long_name': _('A descriptive name ' 'appearing in on web pages. Can include blanks'),
    'use_auto_translation': _('Check to enable the auto' 'translation; needs google_auth_string '),
    'registration_by_password': _('Set up a password which can be used' ' for self-registration'),
    'motd': _('Temporary message to appear on the login page and top of OpenTA pages'),
    'registration_by_domain': _('Allow self-registration with email ' 'from the listed domains'),
    'email_host_password': _(
        'Password for your email account (Please use SSO,'
        ' the password is stored in cleartext on the server)'
    ),
    'published': 'Publish the course to make it visible to student',
    'deadline_time': 'Exact time of day when exercises are due',
    'owners': 'Those staff members who can view this course as unpublished',
    'email_host': _('For instance smtp.chalmers.se Uses port 587/TLS'),
    'email_reply_to': _('For instance CID@chalmers.se'),
    'email_host_user': _('Email of smtp account owner ,i.e. CID@chalmers.se'),
    'email_username': _('Usually CID, but is net.chalmers.se\CID at chalmers'),
    'google_auth_string': 'Credentials for google translate, obtained from a google service account. ',
    'difficulties': _('List of labels which can be displayed as option for each exercise.'),
    'languages': _(
        'Languages for translations in the course:'
        ' the first language is dominant and used in emails.'
    ),
}
def email_verify(data):
        newdata = data
        print("EMAIL VERIFY " )
        print(data)
        for key,val in data.items() :
            print("KEY = ", key, "VAL = ", val )
        body = (
            " email_reply_to = "
            + str(data['email_reply_to'])
            + "\n email_host: "
            + str(data['email_host'])
            + "\n email_host_user: "
            + str(data['email_host_user'])
        )
        body = body + "\n email_username: " + str(data['email_username'])
        print("BODY =  ", body)
        if  data['use_email'] and (
            settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend'
        ):
            print("TRY SENDING EMAIL" )
            try:
                email_object = EmailMessage(
                    subject='EMAIL VERIFICATION TEST from ' + data['email_host'],
                    body=body,
                    from_email=data['email_host_user'],
                    to=[data['email_reply_to'] ],
                    reply_to=[data['email_reply_to']],
                )
                n_sent = send_email_object(
                    email_object, data['email_host'], data['email_username'], data['email_host_password']
                )
                assert n_sent == 1
                return (True, '' )
            except Exception as e:
                return (False, "PARAMETERS USED: "
                        + body
                        + "  ERROR"
                        + str(e)
                        + " HINT: remember that google passwords must be of type app-password" )

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        exclude = []
        widgets = {
            'registration_password': forms.PasswordInput(render_value=True),
            'email_host_password': forms.PasswordInput(render_value=True),
        }


class CourseFormFrontend(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CourseFormFrontend, self).__init__(*args, **kwargs)
        # self.fields['lti_secret'].disabled = True
        # self.fields['lti_key'].disabled = True
        self.fields['lti_key'].help_text = str(self.initial['lti_key'])
        self.fields['lti_secret'].help_text = str(self.initial['lti_secret'])
        self.fields['url'].help_text = "base url:  " + str(self.initial['url'])
        if kwargs['instance'].use_lti:
            self.fields['url'].help_text = (
                "Config URL: " + str(self.initial['url']) + 'lti/config_xml/'
            )
        exclusions = {
            'use_email': ['email_host_password', 'email_host', 'email_host_user', 'email_username'],
            'registration_by_domain': ['registration_domains'],
            'registration_by_password': ['registration_password'],
            'use_lti': ['lti_secret', 'lti_key'],
            'use_auto_translation': ['google_auth_string'],
        }
        if self.fields.get('email_reply_to',False )  and kwargs['instance'].use_email  :
            self.fields['use_email'].help_text =  'Press save below for email verification to be sent to ' + str( self.initial['email_reply_to'] )
        for key, fields in exclusions.items():
            print(
                "__INIT__: DEAL WITH ",
                key,
                " BOOL ",
                self.initial[key],
                getattr(kwargs['instance'], key),
            )
            if not getattr(kwargs['instance'], key):
                for field in fields:
                    print("     POP ", field)
                    self.fields.pop(field, False)
                    #self.Meta.exclude = self.Meta.exclude + [field] # DOES NOT WORK


    def clean(self):
        data = self.cleaned_data
        # data = super().clean()
        for key, value in data.items():
            print("CLEAN: KEY = ", key, "VALUE = ", value)
        if self.changed_data == []:
            print("CLEAN: UNCHANGED")
        else:
            for field in self.changed_data:
                print("CLEAN: FIELD THAT CHANGE", field)
            
        
        if  'email_host' in data.keys() and data['use_email']  and  settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend' :
            #if not 'email_host' in data.keys() :
            #    #raise ValidationError({'use_email': "Save the paramaters" },code='invalid')
            #    raise ValidationError({"email_reply_to": "MESSAGE"}, code='invalid')
            (success,msg) = email_verify( data )
            #print(  "SUCCESS" , success, "MSG = ", msg )
            if not success :
                raise ValidationError( {'use_email': msg }, 
                    code='invalid'
                )
        #if data['use_email'] and 'email_host' not in data.keys() :
        #        data['use_email'] = False 

        if data['registration_by_domain']:
            if not data.get('use_email'):
                raise ValidationError(
                    {
                        'registration_by_domain': 'Cannot be checked if email is not working',
                        'use_email': 'This has to be enabled first to do registration_by_domain',
                    },
                    code='invalid',
                )
            if not data.get('registration_domains', False):
                if 'registration_by_domain' not in self.changed_data:
                    print("BLANK DOMAINS")
                    raise ValidationError(
                        {
                            'registration_by_domain': 'Cannot be checked with imporper domain list',
                            'registration_domains': 'Cannot be blank if registration by domain is checked',
                        },
                        code='invalid',
                    )

        if data['registration_by_password']:
            if not data.get('registration_password', False):
                if 'registration_by_password' not in self.changed_data:
                    print("BLANK PASSWORD")
                    raise ValidationError(
                        {
                            'registration_password': 'Cannot be blank if registration by password is checked',
                            'registration_by_password': 'Cannot be checked if password is blank',
                        },
                        code='invalid',
                    )

        if data['use_auto_translation']:
            if not data.get('google_auth_string', False):
                if 'use_auto_translation' not in self.changed_data:
                    print("BLANK GOOGLE AUTH STRING")
                    raise ValidationError(
                        {
                            'google_auth_string': 'Cannot be blank if use_auto_translation is checked',
                            'use_auto_translation': 'Cannot be checked if google_auth_string is blank',
                        },
                        code='invalid',
                    )
            else:
                if (
                    'use_auto_translation' not in self.changed_data
                    and 'google_auth_string' in self.changed_data
                ):
                    print("HANDLE NONBLANK GOOGLE AUTH STRING")
                    if not google_auth_string_is_valid(data['google_auth_string']):
                        raise ValidationError(
                            {
                                'google_auth_string': 'Invalid google auth string',
                                'use_auto_translation': 'Cannot be checked if google_auth_string is invalid',
                            },
                            code='invalid',
                        )

        #data['url'] = 'NEW URL'
        self.save(commit=True)
        return data

    def save(self, commit=True):
        instance = super(CourseFormFrontend, self).save(commit=True)
        print("INSTANCE IS GOING TO BE SAVED")
        return instance

    # lti_key = forms.CharField(disabled=True,widget=forms.Textarea(attrs={'rows': 1, 'cols': 40})  )
    # lti_secret = forms.CharField(disabled=True,widget=forms.Textarea(attrs={'rows': 1, 'cols': 40}) )
    # use_email = forms.BooleanField(required=False)
    # use_lti = forms.BooleanField(required=False)
    # use_auto_translation = forms.BooleanField(required=False)

    class Meta:
        model = Course
        active = True
        fields = [
            'published',
            'course_name', 
            'course_long_name',
            'url', 
            'motd', 'difficulties',
            'deadline_time',
            'use_lti',
            'url',
            'lti_key',
            'lti_secret',
            'registration_by_password',
            'registration_password',
            'registration_domains',
            'registration_by_domain',
            'use_email',
            'email_reply_to',
            'email_host',
            'email_host_user',
            'email_username',
            'email_host_password',
            'use_auto_translation',
            'google_auth_string',
            'languages',
            'owners',
            'motd',
            'deadline_time',
            'difficulties',
        ]
        exclude = []

        if not settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
            exclude = ['email_host_password', 'email_host', 'email_host_user', 'email_username']
        widgets = {
            'owners': forms.CheckboxSelectMultiple(),
            'motd': forms.Textarea(attrs={'cols': 40, 'rows': 1}),
            'lti_key': forms.HiddenInput(),
            'lti_secret': forms.HiddenInput(),
            'google_auth_string': forms.Textarea(attrs={'cols': 40, 'rows': 1}),
            #'url': forms.Textarea(attrs={'cols': 80, 'rows': 1}),
            'email_host_user': forms.Textarea(attrs={'cols': 40, 'rows': 1}),
            'course_long_name': forms.Textarea(attrs={'cols': 40, 'rows': 1}),
            'url': forms.HiddenInput(),
            'difficulties': forms.Textarea(attrs={'cols': 40, 'rows': 1}),
            'registration_password': forms.PasswordInput(render_value=True),
            'email_host_password': forms.PasswordInput(render_value=True),
        }
        help_texts = HELP_TEXTS
