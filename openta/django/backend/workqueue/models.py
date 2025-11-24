# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.db import models
import uuid
import slugify
from django.utils import timezone
from django.contrib.auth.models import User
from exercises.models import Exercise
from datetime import datetime, timedelta
import os
import redis
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
import logging

logger = logging.getLogger(__name__)
from django.conf import settings

from django.core.files.storage import FileSystemStorage

upload_storage = FileSystemStorage(location=settings.VOLUME, base_url="/")


def result_file_name(instance, filename):
    logger.debug(f"INSTANCE = {instance} filename={filename}")
    logger.debug(f"SPOOLDIR={settings.SPOOL_DIR}")
    basefilename = "/" + filename.split("/")[-1]
    uid = f"{uuid.uuid4()}"[0:4]
    # fullfile = settings.SPOOL_DIR +  '/'.join(
    #    [
    #        'taskresults',
    #        str(instance.pk)
    #        + "-"
    #        + "{:%Y%m%d-%H-%M}".format(instance.date)
    #        + "-"
    #        + instance.name.replace(' ', '-')
    #        + basefilename,
    #    ]
    # )
    # print(f"UID = {uid}")
    filebase = basefilename.split(".")[0]
    extension = basefilename.split(".")[-1]
    if filebase == "":
        filebase = "default"
    # logger.error(f"FILEBASE = {filebase} EXTENSION = {extension}")
    fullfile = settings.SPOOL_DIR + "/".join(
        [
            "taskresults",
            str(instance.pk) + "-" + uid
            # + "{:%Y%m%d-%H-%M}".format(instance.date)
            + "-" + instance.name.replace(" ", "-") + filebase + "." + extension,
        ]
    )

    fullfile = fullfile.replace("_", "-")
    # logger.error("FULL FILE IN RESULT FILE NAME = %s " % fullfile )
    return fullfile


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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        dt = timezone.now() - timedelta(minutes=20)
        for tasktype in [QueueTask]:
            tasks = tasktype.objects.filter(date__lt=dt)
            for task in tasks:
                task.delete()


class RegradeTask(models.Model):
    task_id = models.IntegerField(default=0)
    exercise_key = models.CharField(max_length=255, default="")
    subdomain = models.CharField(max_length=255, default="")
    resultsfile = models.CharField(max_length=255, default="")
    pklfile = models.CharField(max_length=255, default="")
    status = models.CharField(max_length=64, default="")

class AnalyzeTask(models.Model):
    task_id = models.IntegerField(default=0)
    exercise_key = models.CharField(max_length=255, default="")
    subdomain = models.CharField(max_length=255, default="")
    resultsfile = models.CharField(max_length=255, default="")
    pklfile = models.CharField(max_length=255, default="")
    status = models.CharField(max_length=64, default="")


@receiver(pre_delete, sender=RegradeTask)
def regrade_task(sender, instance, **kwargs):
    pklfile = instance.pklfile
    resultsfile = instance.resultsfile
    if os.path.exists(resultsfile):
        os.remove(resultsfile)
    if os.path.exists(pklfile):
        os.remove(pklfile)
