# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.conf import settings
import os
import re


class CustomStrategy(object):
    """
    A strategy that ensures file creation on save and existence

    """

    def on_existence_required(self, file):
        # print(f"CUSTOM_STRATEGY {file} Type(self) = {type(self)}")
        file.generate()
        # print("FILE GENERATED")

    def on_content_required(self, file):
        # print(f"B GENERATE {file}")
        file.generate()

    def on_source_saved(self, file):
        # print(f"C GENERATE {file}")
        file.generate()


def my_source_name_as_path(generator):
    """
    A namer that, given the following source file name::

        photos/thumbnails/bulldog.jpg

    will generate a name like this::

        /path/to/generated/images/photos/thumbnails/bulldog/5ff3233527c5ac3e4b596343b440ff67.jpg

    where "/path/to/generated/images/" is the value specified by the
    ``IMAGEKIT_CACHEFILE_DIR`` setting.

    """
    # print("MY_SOURCE_NAME")
    source_filename = getattr(generator.source, "name", None)
    # print(f"MYSOURCE {source_filename}")
    source_filename = re.sub(r"subdomain-data/", "", source_filename)
    dir = os.path.join(settings.IMAGEKIT_CACHEFILE_DIR, os.path.splitext(source_filename)[0])
    ext = source_filename.split(".")[-1]
    # print(f"MY SOURCE {source_filename} {ext}")
    res = os.path.normpath(os.path.join(dir, "%s.%s" % (generator.get_hash(), ext)))
    # print(f"RES = {res}")
    return res
