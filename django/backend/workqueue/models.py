from django.db import models
from django.contrib.auth.models import User
from exercises.models import Exercise
import os
import redis
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
import logging
logger = logging.getLogger(__name__)
from django.conf import settings

from django.core.files.storage import FileSystemStorage
upload_storage  = FileSystemStorage(location=settings.VOLUME, base_url='/')




def result_file_name(instance, filename):
    logger.info("INSTANCE = %s " % str(instance) )
    basefilename = '/' + filename.split('/')[-1]
    fullfile = settings.SPOOL_DIR +  '/'.join(
        [
            'taskresults',
            str(instance.pk)
            + "_"
            + "{:%Y%m%d_%H:%M}".format(instance.date)
            + "_"
            + instance.name.replace(' ', '_')
            + basefilename,
        ]
    )
    logger.info("FULL FILE IN ESULT FILE NAME = %s " % fullfile )
    return  fullfile


class QueueTask(models.Model):
    owner = models.ForeignKey(User, default=None, null=True, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    subdomain = models.CharField(max_length=255)
    progress = models.PositiveIntegerField(default=0)
    done = models.BooleanField(default=False)
    status = models.CharField(max_length=255, default="Created")
    result_file = models.FileField(
        default=None, blank=True, null=True, upload_to=result_file_name, max_length=512, storage=upload_storage
    )


class RegradeTask(models.Model):
    task_id = models.IntegerField(default=0)
    exercise = models.ForeignKey(Exercise, default=None, null=True, on_delete=models.PROTECT)
    resultsfile = models.CharField(max_length=255, default='')
    pklfile = models.CharField(max_length=255, default='')
    status = models.CharField(max_length=64, default='')


@receiver(pre_delete, sender=RegradeTask)
def regrade_task(sender, instance, **kwargs):
    pklfile = instance.pklfile
    resultsfile = instance.resultsfile
    if os.path.exists(resultsfile):
        os.remove(resultsfile)
    if os.path.exists(pklfile):
        os.remove(pklfile)
