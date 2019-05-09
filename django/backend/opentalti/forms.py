import logging
from django import forms
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.template import loader
from django.core.exceptions import ValidationError
from backend.user_utilities import send_activation_mail
from course.models import Course
from users.models import OpenTAUser


class EditProfileForm(forms.ModelForm):

    first_name = forms.CharField(label="First Name")
    last_name = forms.CharField(label="Last Name")
    email = forms.EmailField(label="Email")
    username = forms.CharField(label="Username")
    pk = forms.IntegerField(label="pk", widget=forms.HiddenInput())

    class Meta:
        model = OpenTAUser
        fields = ["first_name", "last_name", "email", "username", "pk"]
        exclude = []

    def clean(self):
        cleaned_data = self.cleaned_data
        logging.debug("TO THE CLEANER with %s", cleaned_data)
        username = cleaned_data["username"]
        users = User.objects.filter(username=cleaned_data["username"])
        logging.debug("USERS THAT MATCH = %s", users)
        for user in users:
            logging.debug("USER = %s", user.username)
            if not user.pk == cleaned_data["pk"]:
                logging.debug("REFUSE TO CHANGE ; username taken")
                raise ValidationError(username + " IS TAKEN")
        return cleaned_data
