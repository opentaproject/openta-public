from django.db import models

from django.contrib.auth.models import User

from course.models import Course


class OpenTAUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='opentauser')
    courses = models.ManyToManyField(Course)
    lti_user_id = models.CharField(max_length=256, null=True, blank=True, editable=False)
    lis_person_contact_email_primary = models.CharField(
        max_length=256, null=True, blank=True, editable=False
    )
    lti_tool_consumer_instance_guid = models.CharField(
        max_length=256, null=True, blank=True, editable=False
    )
    lti_context_id = models.CharField(max_length=256, null=True, blank=True, editable=False)
    lti_roles = models.CharField(max_length=256, null=True, blank=True)
    lis_person_name_full = models.CharField(max_length=256, null=True, blank=True)
    lis_person_name_given = models.CharField(max_length=256, null=True, blank=True)
    lis_person_name_family = models.CharField(max_length=256, null=True, blank=True)
    immutable_user_id = models.CharField(max_length=256, null=True, blank=True, editable=False)

    class Meta:
        unique_together = (('lti_user_id', 'lti_context_id', 'lti_tool_consumer_instance_guid'),)

    # SEE https://github.com/misli/django-verified-email-field

    def __str__(self):
        return 'Profile of user: {}'.format(self.user.username)

    def username(self):
        return self.user.username

    def email(self):
        return self.user.email

    def first_name(self):
        return self.user.first_name

    def last_name(self):
        return self.user.last_name
