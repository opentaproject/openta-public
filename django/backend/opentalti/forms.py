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
    email = forms.EmailField(label="Email")  # ,widget=forms.HiddenInput() ) #, required=True)
    username = forms.CharField(label="Username")
    pk = forms.IntegerField(label="pk", widget=forms.HiddenInput())

    class Meta:
        model = OpenTAUser
        fields = ["first_name", "last_name", "email", "username", "pk"]
        exclude = []

    def clean(self):
        cleaned_data = self.cleaned_data
        print("TO THE CLEANER with ", cleaned_data)
        username = cleaned_data["username"]
        users = User.objects.filter(username=cleaned_data["username"])
        print("USERS THAT MATCH = ", users)
        for user in users:
            print("USER = ", user.username)
            if not user.pk == cleaned_data["pk"]:
                print("REFUSE TO CHANGE ; username taken")
                raise ValidationError(username + " IS TAKEN")
        # if OpenTAUser.objects.filter(user_alias=cleaned_data['user_alias']).exists():
        #    raise ValidationError(
        #          'Solution with this Name already exists for this problem')
        return cleaned_data
