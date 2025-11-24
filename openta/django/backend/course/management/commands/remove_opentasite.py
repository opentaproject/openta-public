# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Remove name and surname from users."""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import logging
from exercises.models import Exercise
from course.models import Course
from course.export_import import UserResource, OpenTAUserResource, server_reset
from django.conf import settings
import re
import os
import json
import logging

logger = logging.getLogger(__name__)
import glob
from django.core.cache import caches
import tablib
from collections import OrderedDict
from course.duplicate import resource_lookup
from users.models import OpenTAUser
import subprocess


class Command(BaseCommand):

    # def add_arguments(self, parser):
    #    parser.add_argument( '--subdomain', dest='subdomain', default=None, help='specify subdomain.')

    def handle(self, *args, **options):
        """Remove name and surname from users."""
        if 'opentasites' in settings.INSTALLED_APPS :
            print(f" REMOVE {settings.SUBDOMAIN}")
            opentasite = OpenTASite.objects.using("default").get(subdomain=settings.SUBDOMAIN)
            print(f" OPNETASITE = {opentasite}")
            opentasite.delete()
