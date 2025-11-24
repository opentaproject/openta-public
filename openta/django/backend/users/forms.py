from users.models import OpenTAUser
from django import forms
from django.conf import settings


class OpenTAUserForm(forms.ModelForm):
    class Meta:
        model = OpenTAUser
        exclude = ["courses"]
