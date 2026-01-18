# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import io
import json
import logging
import traceback
import os
import shutil

from course.models import Course
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account

from django import forms
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def patch_credential_string(value):
    return value.strip().lstrip("r").strip("'")


def google_auth_string_is_valid(value):
    if not settings.VALIDATE_GOOGLE_AUTH_STRING:
        return True
    try:
        credentialstring = patch_credential_string(value)
        service_account_info = json.load(io.StringIO(credentialstring))
        credentials = service_account.Credentials.from_service_account_info(service_account_info)
        translate_client = translate.Client(credentials=credentials)
        should_be_en = translate_client.detect_language("This is a statement in english")["language"]
        return "en" == should_be_en
    except Exception as e:
        logger.error("GOOGLE AUTH STRING ERROR %s " % str(e))
        return False


HELP_TEXTS = {
    "description" : _("appears on the course login page"),
    "use_lti": _("reveal LTI/Canvas parameters"),
    "use_email": _("Check to enable the use of  email"),
    "url": "Course url.  Reset by deleting it. Augment with /lti/config_xml/ for LTI URL configuration ",
    "registration_domains": _(
        "Comma separated list of email domains" " that are permitted to self-register. Regex such as .* is accepted"
    ),
    "course_name": _(
        "A short name "
        "without spaces , capitals or special characters; appears in course-url. Saving the course name enforces this. "
        "Do not plan to change this after students have begun using the course via canvas/lti. "
    ),
    "course_long_name": _("A descriptive name " "appearing in on web pages. Can include blanks"),
    "use_auto_translation": _("Check to enable the auto" "translation; needs google_auth_string "),
    "registration_by_password": _("Set up a password which can be used" " for self-registration"),
    "motd": _("Temporary message to appear on the login page and top of OpenTA pages"),
    "registration_by_domain": _("Allow self-registration with email " "from the listed domains"),
    "email_host_password": _(
        "Password for your email account (Please use SSO," " the password is stored in cleartext on the server)"
    ),
    "published": "Publish the course to make it visible to student",
    "deadline_time": "Exact time of day when exercises are due",
    "owners": "Those staff members who can view this course as unpublished",
    "email_host": _("For instance smtp.chalmers.se Uses port 587/TLS"),
    "email_reply_to": _("Default email reply to for instance CID@chalmers.se"),
    "email_host_user": _("Email of smtp account owner ,i.e. CID@chalmers.se"),
    "allow_anonymous_student": _("Allow anonymous student login"),
    "email_username": _("Usually CID, but is net.chalmers.se\CID at chalmers"),
    "google_auth_string": "Credentials for google translate, obtained from a google service account. GoogleCloudPlatform->ServiceAccounts-> (select project) -> Actions=... -> CreateKey-> JSON",
    "difficulties": _("List of labels which can be displayed as option for each exercise."),
    "languages": _("Languages for translations in the course:" " the first language is dominant and used in emails."),
}


def email_verify(data):
    for key, val in data.items():
        logger.debug("KEY = ", key, "VAL = ", val)
    body = (
        " email_reply_to = "
        + str(data["email_reply_to"])
        + "\n email_host: "
        + str(data["email_host"])
        + "\n email_host_user: "
        + str(data["email_host_user"])
    )
    body = body + "\n email_username: " + str(data["email_username"])
    logger.debug("BODY =  ", body)
    if data["use_email"] and (settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"):
        logger.debug("TRY SENDING EMAIL")
        try:
            email_object = EmailMessage(
                subject="EMAIL VERIFICATION TEST from " + data["email_host"],
                body=body,
                from_email=data["email_host_user"],
                to=[data["email_reply_to"]],
                reply_to=[data["email_reply_to"]],
            )
            n_sent = (
                email_object,
                data["email_host"],
                data["email_username"],
                data["email_host_password"],
            )
            assert n_sent == 1
            return (True, "")
        except Exception as e:
            return (
                False,
                "PARAMETERS USED: "
                + body
                + "  ERROR"
                + str(e)
                + " HINT: remember that google passwords must be of type app-password",
            )


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        # exclude = ['data'] # NOTE  UNCOMMENT TO EXCLUDE IN COURSE ADMIN FORM
        exclude = []
        widgets = {
            "registration_password": forms.PasswordInput(render_value=True),
            "email_host_password": forms.PasswordInput(render_value=True),
            "data": forms.Textarea(attrs={"rows": 1, "cols": 40}),
            "icon": forms.ImageField(),
        }

    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        # print(f"INIT")
        self.fields["icon"] = forms.ImageField(
            disabled=False
        )  # ,widget=forms.Textarea(attrs={'rows': 1, 'cols': 40})  )
        self.fields["icon"].required = False
        # self.fields["icon"].widget.needs_multipart_form = False
        # self.fields["icon"].widget.is_hidden = False
        # print(f" INIT2 ")


class CourseFormFrontend(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CourseFormFrontend, self).__init__(*args, **kwargs)
        # self.fields['lti_secret'].disabled = True
        # self.fields['lti_key'].disabled = True
        # print(f"FORM KWARGS = {kwargs}")
        instance = kwargs["instance"]
        # logger.error(f" INSTANCE = {vars(instance)}")
        # print(f" COURSE_KEY = {str( instance.course_key) }")
        # logger.error(f" INITIAL {self.initial}")
        try:
            description = self.initial["data"].get("description","no course description")
        except Exception as e:
            logger.error(f"COURSE_DESCRIPTION_MISSING ERROR = {type(e).__name__}")
            description =  str(self.initial.get("course_long_name",self.initial['course_name']))
        # description = "ABCDEFG"
        # print(f"INSTANCE DESCRIPION = {description}")
        self.fields["description"].initial = description
        self.fields["description"].help_text = "Appears course login page"
        self.fields["lti_key"].help_text = str(self.initial["lti_key"])
        self.fields["lti_secret"].help_text = str(self.initial["lti_secret"])
        self.fields["url"].help_text = str(self.initial["url"])
        self.fields["lti_key"].label = "Consumer key"
        self.fields["lti_secret"].label = "Shared secret"
        self.fields["icon"].label = "Course icon for login page"
        self.fields["data"].disabled = True
        self.fields["url"].label = "url"
        self.fields["course_key_copy"].initial = str(instance.course_key)
        if kwargs["instance"].use_lti:
            self.fields["url"].label = "Config url"
        #if settings.GOOGLE_AUTH_STRING_EXISTS:
        #    del self.fields["google_auth_string"]
        if kwargs["instance"].use_lti:
            if not 'localhost' in settings.OPENTA_SERVER :
                self.fields["url"].help_text = str(self.initial["url"]).replace("http://","https://") + "lti/config_xml/"
            else :
                self.fields["url"].help_text = str(self.initial["url"]) + "lti/config_xml/"

        #del self.fields["course_key_copy"]
        exclusions = {
            "use_email": [
                "email_host_password",
                "email_host",
                "email_host_user",
                "email_username",
            ],
            "registration_by_domain": ["registration_domains"],
            "registration_by_password": ["registration_password"],
            "use_lti": ["lti_secret", "lti_key"],
            #"use_auto_translation": ["google_auth_string"],
        }
        try:
            if self.fields.get("email_reply_to", False) and kwargs["instance"].use_email:
                self.fields["use_email"].help_text = "Press save below for email verification to be sent to " + str(
                    self.initial["email_reply_to"]
                )
        except KeyError as e:
            pass
        for key, fields in exclusions.items():
            # logger.debug(
            #    "__INIT__: DEAL WITH ",
            #    key,
            #    " BOOL ",
            #    self.initial[key],
            #    getattr(kwargs['instance'], key),
            # )
            if not getattr(kwargs["instance"], key):
                for field in fields:
                    # logger.debug("     POP ", field)
                    self.fields.pop(field, False)
                    # self.Meta.exclude = self.Meta.exclude + [field] # DOES NOT WORK
        if not settings.ENABLE_AUTO_TRANSLATE :
            del self.fields["use_auto_translation"];
            del self.fields["google_auth_string"]
        # del self.fields["data"]  # NOTE DELETE FIELD FROM FORM

    def clean(self):
        data = self.cleaned_data
        #logger.error(f"DATA ONLY IS { data['data']}")
        # logger.error(f"CLEAN DATA {data['description']}")
        if isinstance(data.get("data",None) , str):
            data["data"] = json.loads(data["data"])
        else :
            data["data"] = {}
        #if not data["data"]:
        #    data["data"] = {}
        data["data"]["description"] = data["description"]
        for key, value in data.items():
            logger.debug(" %s %s %s %s " % ("CLEAN: KEY = ", key, "VALUE = ", value))

            logger.debug("CLEAN: UNCHANGED")
        else:
            for field in self.changed_data:
                logger.debug("CLEAN: FIELD THAT CHANGE %s " % field)

        if data.get("owners") == None:
            raise ValidationError({"published": "Must set at least one owner!"}, code="invalid")
        admins = User.objects.filter(groups__name="Admin")
        # if not  "description" in self.initial['data'] :
        #    self.initial["data"]["description"] = {}
        # self.initial["data"]["description"] = "FROM 223" # data["description"]  ## NOTE NEED TO DO THIS SINCE IT WAS DELETED IN FORM
        # print(f"OWNERS = {admins}")

        # if (
        #    'email_host' in data.keys()
        #    and data['use_email']
        #    and settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend'
        # ):
        #    # if not 'email_host' in data.keys() :
        #    #    #raise ValidationError({'use_email': "Save the paramaters" },code='invalid')
        #    #    raise ValidationError({"email_reply_to": "MESSAGE"}, code='invalid')
        #    #(success, msg) = email_verify(data)
        #    # logger.debug(  "SUCCESS" , success, "MSG = ", msg )
        #    #if not success:
        #    #    raise ValidationError({'use_email': msg}, code='invalid')
        # if data['use_email'] and 'email_host' not in data.keys() :
        #        data['use_email'] = False

        if not data["email_reply_to"]:
            raise ValidationError({"email_reply_to": "email reply to must correspond to a superuser"}, code="invalid")
        else:
            if not User.objects.filter(is_superuser=True, email=data["email_reply_to"]).exists():
                raise ValidationError(
                    {"email_reply_to": "email reply to must correspond the superuser responsible for the course"},
                    code="invalid",
                )

        if data["registration_by_domain"]:
            # if not data.get('use_email'):
            #    raise ValidationError(
            #        {
            #            'registration_by_domain': 'Cannot be checked if email is not working',
            #            'use_email': 'This has to be enabled first to do registration_by_domain',
            #        },
            #        code='invalid',
            #    )
            if not data.get("registration_domains", False):
                if "registration_by_domain" not in self.changed_data:
                    logger.error("BLANK DOMAINS")
                    raise ValidationError(
                        {
                            "registration_by_domain": "Cannot be checked with improper domain list",
                            "registration_domains": "Cannot be blank if registration by domain is checked",
                        },
                        code="invalid",
                    )

        if data["registration_by_password"]:
            if not data.get("registration_password", False):
                if "registration_by_password" not in self.changed_data:
                    logger.error("BLANK PASSWORD")
                    raise ValidationError(
                        {
                            "registration_password": "Cannot be blank if registration by password is checked",
                            "registration_by_password": "Cannot be checked if password is blank",
                        },
                        code="invalid",
                    )

        if data.get("use_auto_translation",False):
            logger.debug("USE AUTO TRANSLATION IS SET")
            if data.get("languages") == None:
                raise ValidationError(
                    {
                        "use_auto_translation": "Cannot be checked if languages are blank",
                    },
                    code="invalid",
                )

            if settings.VALIDATE_GOOGLE_AUTH_STRING and data.get("google_auth_string", False):
                if "use_auto_translation" not in self.changed_data:
                    logger.debug("BLANK GOOGLE AUTH STRING")
                    raise ValidationError(
                        {
                            "google_auth_string": "Cannot be blank if use_auto_translation is checked",
                            "use_auto_translation": "Cannot be checked if google_auth_string is blank",
                        },
                        code="invalid",
                    )
            if settings.VALIDATE_GOOGLE_AUTH_STRING:
                if "use_auto_translation" not in self.changed_data and "google_auth_string" in self.changed_data:
                    logger.debug("HANDLE NONBLANK GOOGLE AUTH STRING")
                    if not google_auth_string_is_valid(data["google_auth_string"]):
                        raise ValidationError(
                            {
                                "google_auth_string": "Invalid google auth string",
                                "use_auto_translation": "Cannot be checked if google_auth_string is invalid",
                            },
                            code="invalid",
                        )

        # data['url'] = 'NEW URL'
        try:
            self.save(commit=True)
        except Exception as e:
            formatted_lines = traceback.format_exc()
            logger.error(f"FORMATTED_LINES {formatted_lines}")
            msg = f"ERROR E554433 : {type(e).__name__} error saving { settings.SUBDOMAIN} data={data} "
            logger.error(msg)
            raise ValidationError(
                {
                    "published": "Save error. Make sure you are course owner. If save still does not work,  try logging out of the course and log in again"
                },
                code="invalid",
            )
        return data

    def nosave(self, commit=True):
        # print(f"SAVE SELF {vars(self.instance)} ")
        instance = super(CourseFormFrontend, self).save(commit=True)
        # print(f"INSATANCE = {instance} {vars(instance)}")
        iconfile = instance.icon.name
        changed = self.changed_data
        #
        # MONKEYPATCH ; cannot get image field to respect localized value of upload fileo
        # so it is hacked by moving the file
        #
        if "icon" in changed:
            if instance.icon.name:
                target = os.path.join(settings.VOLUME, settings.SUBDOMAIN, instance.icon.name)
                orig = os.path.join(settings.VOLUME, instance.icon.name)
                shutil.copy(orig, target)

        # print(f" OPENTASITE {instance.pk} = {instance.opentasite} ")
        # subdomain = str( instance.opentasite)
        # pk = str( instance.pk)
        # o = OpenTASite.objects.using('opentasites').get(subdomain=subdomain)
        # print(f"DATA = {o.data[pk]}")
        # old_description = o.data[pk]['description']
        # print(f"OLD DESCRIPTION  = {old_description}")
        # print(f"NEW_DESCRITPTION = {instance.data['description']}")
        # o.data[pk]['description'] = instance.data['description']
        # o.save()
        return instance

    description = forms.CharField(disabled=False, widget=forms.Textarea(attrs={"rows": 1, "cols": 40}))
    course_key_copy =  forms.CharField(disabled=False, widget=forms.Textarea(attrs={"rows": 1, "cols": 40}))
    # lti_secret = forms.CharField(disabled=True,widget=forms.Textarea(attrs={'rows': 1, 'cols': 40}) )
    # use_email = forms.BooleanField(required=False)
    # use_lti = forms.BooleanField(required=False)
    # use_auto_translation = forms.BooleanField(required=False)

    class Meta:
        model = Course
        active = True
        fields = (
            "published",
            "course_name",
            "course_long_name",
            "motd",
            "difficulties",
            "deadline_time",
            "registration_by_password",
            "registration_password",
            "registration_domains",
            "registration_by_domain",
            "email_reply_to",
            # "email_host",
            # "email_host_user",
            # "email_username",
            # "email_host_password",
            "use_auto_translation",
            "google_auth_string",
            "languages",
            "owners",
            "motd",
            "deadline_time",
            "difficulties",
            "allow_anonymous_student",
            "use_lti",
            "url",
            "lti_key",
            "lti_secret",
            "data",  # UNCOMMENT TO GET DATA IN COURSE FRONTEND FORM; CANT GET WIDGET WORKING
            "icon",
            "description",
            "course_key_copy",
            "use_email",
        )
        if not settings.USE_GMAIL:
            fields = fields + ("email_host", "email_host_user", "email_host_password", "email_username")

        # if not settings.VALIDATE_GOOGLE_AUTH_STRING :
        #    fields.remove('google_auth_string')
        if not settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend":
            exclude = [
                "email_host_password",
                "email_host",
                "email_host_user",
                "email_username",
            ]
        if True :
            widgets = {
                "owners": forms.CheckboxSelectMultiple(),
                "motd": forms.Textarea(attrs={"cols": 40, "rows": 1}),
                "lti_key": forms.Textarea(attrs={"cols": 40, "rows": 1}),
                "lti_secret": forms.Textarea(attrs={"cols": 40, "rows": 1}),
                "google_auth_string": forms.Textarea(attrs={"cols": 40, "rows": 1}),
                #'url': forms.Textarea(attrs={'cols': 80, 'rows': 1}),
                "email_host_user": forms.Textarea(attrs={"cols": 40, "rows": 1}),
                "course_long_name": forms.Textarea(attrs={"cols": 40, "rows": 1}),
                "url": forms.HiddenInput(),
                "difficulties": forms.Textarea(attrs={"cols": 40, "rows": 1}),
                "registration_password": forms.TextInput(),
                "email_host_password": forms.TextInput(),
                "data": forms.TextInput(),  # MAKE ONLY description editable
            }
        else :
            widgets = {
                "owners": forms.CheckboxSelectMultiple(),
                "motd": forms.Textarea(attrs={"cols": 40, "rows": 1}),
                "lti_key": forms.HiddenInput(),
                "lti_secret": forms.HiddenInput(),
                "google_auth_string": forms.Textarea(attrs={"cols": 40, "rows": 1}),
                #'url': forms.Textarea(attrs={'cols': 80, 'rows': 1}),
                "email_host_user": forms.Textarea(attrs={"cols": 40, "rows": 1}),
                "course_long_name": forms.Textarea(attrs={"cols": 40, "rows": 1}),
                "url": forms.HiddenInput(),
                "difficulties": forms.Textarea(attrs={"cols": 40, "rows": 1}),
                "registration_password": forms.TextInput(),
                "email_host_password": forms.TextInput(),
                "data": forms.TextInput(),  # MAKE ONLY description editable
            }

        help_texts = HELP_TEXTS


class CustomUserForm(forms.ModelForm):
    request_username = forms.CharField()

    # class Meta:
    #    model: User
    #    fields = '__all__'

    def __init__(self, *args, **kwargs):
        instance = kwargs["instance"]
        email = instance.email
        super(CustomUserForm, self).__init__(*args, **kwargs)
        try:
            request_username = self.fields["request_username"].initial
        except:
            request_username = "super"
        instance_username = instance.username
        self.fields["user_permissions"].initial = instance.user_permissions
        lis = list(Group.objects.all().values("pk", "name"))
        CHOICES = [(item["pk"], item["name"]) for item in lis]
        self.fields["groups"].widget = forms.CheckboxSelectMultiple(
            choices=CHOICES, attrs={"className": "uk-text uk-text-danger"}
        )
        # self.initial['password'] = '-----------------'
        hide_password_change = not ( request_username == 'super' ) and  settings.LOCK_SUPER 
        if instance.is_superuser and not (instance_username == request_username) and hide_password_change :
            self.fields["username"].widget.attrs["readonly"] = True
            self.fields["username"].help_text = ""
        else:
            self.fields[
                "username"
            ].help_text = f'<h3> <a href="../password/"> Change password by clicking HERE </a>  </h3><h3> <em> if you set the password to the email <b> {email} </b>  the user will be forced to reset on first login. </em>  </h3> '
        # print(f" FORMS INIT PASSWORD = {instance}")
        user = User.objects.get(username=instance.username)
        # print(f"USER = {user} pwd=>{user.password}<")
        if not request_username == "super":
            self.fields["is_superuser"].widget.attrs["disabled"] = True  # =  forms.HiddenInput()
            self.fields["user_permissions"].widget = forms.HiddenInput(attrs={"disabled": True, "required": False})
            self.fields["is_staff"].widget = forms.HiddenInput()
        # self.fields['password'].initial = 'pbkdf2_sha256$216000$tYGZvRDAwX3h$nTUEVc6Med3CwjZJEOug98hJo11gPWZHO4b+NFM9tC4=<'
        # self.fields['password'].label = 'Encrypted password'
        # self.fields['password'].widget = forms.HiddenInput()
        self.fields['password'].required = False
        # self.fields['password'].widget = forms.PasswordInput()
        # self.fields['password'].disabled = True
        self.fields["request_username"].required = False
        # self.fields["password"].widget = forms.HiddenInput(attrs={'disabled': True, 'required':False, 'label' : 'Encrypted password', 'readonly' : True , 'size' : 3 } )

        ##### EXPLICITLY SET UP INITIAL VALUES
        # user_groups = [ item.name for item in list( self.instance.groups.all() ) ]
        # self.initial['groups'] = []
        # for key,val in CHOICES:
        #     if val in user_groups :
        #         print(f"{key} {val} ")
        #         self.initial['groups'].append(str( int(key) ) )
        ##### END OF EXPLICIT SETUP

        # self.fields['tags'].widget = admin.widgets.AdminTextareaWidget()

    def clean(self):
        data = self.cleaned_data
        data["is_staff"] = False
        if data["groups"]:
            dt = [item.name for item in list(data["groups"])]
            data["is_staff"] = False
            if len(data["groups"]) > 3:
                raise ValidationError({"groups": "Too many groups"})
            if len(data["groups"]) == 0:
                raise ValidationError({"groups": "Choose a group"})
            # if len( data["groups"] ) == 3  :
            #    if 'Admin' in dt and 'Author' in dt  and 'View' in dt :
            #        data['is_staff'] = True
            #        pass
            #    else :
            #        raise ValidationError( { "groups": " Only group of three:  Admin, Author and View  ", }, code="invalid",)
            # print("A1c")
            # if len(data["groups"]) == 2:
            #    if "Author" in dt and "View" in dt:
            #        data["is_staff"] = True
            #    else:
            #        raise ValidationError(
            #            {
            #                "groups": " Only group  of 2 : Author and View  ",
            #            },
            #            code="invalid",
            #        )
            if "Author" in dt or "Admin" in dt:
                data["is_staff"] = True
        else:
            if data["is_active"]:
                raise ValidationError({"groups": "Choose a group or untick the box active"})
        if data["is_superuser"]:
            data["is_staff"] = True
        try :
             subdomain = settings.SUBDOMAIN
             courses = Course.objects.all().filter(opentasite=subdomain)
             user = User.objects.get(username=data["username"])
             if data["is_staff"]:
                 for course in courses:
                     owners = list(course.owners.all())
                     if not user in owners:
                         course.owners.add(user)
             else:
                 for course in courses:
                     owners = list(course.owners.all())
                     if user in owners:
                         course.owners.remove(user)
             ## PATCH BROKEN COURSE OWNERSHIP ON USER SAVE
             staffs = User.objects.all().filter(is_staff=True)
             for user in staffs:
                 for course in courses:
                     owners = list(course.owners.all())
                     if not user in owners:
                         course.owners.add(user)
        except Exception as e :
            logger.error(f" FAILED LINE {subdomain} 544 data = {data}")
        return data
