from django.db import models
from django.contrib.auth.models import User


def result_file_name(instance, filename):  # {{{
    return '/'.join(
        [
            'taskresults',
            str(instance.pk)
            + "_"
            + "{:%Y%m%d_%H:%M}".format(instance.date)
            + "_"
            + instance.name.replace(' ', '_')
            + filename,
        ]
    )  # }}}


class QueueTask(models.Model):
    owner = models.ForeignKey(User, default=None, null=True)
    date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    progress = models.PositiveIntegerField(default=0)
    done = models.BooleanField(default=False)
    status = models.CharField(max_length=255, default="Created")
    result_text = models.TextField(default=None, blank=True, null=True)
    result_file = models.FileField(default=None, blank=True, null=True, upload_to=result_file_name)
