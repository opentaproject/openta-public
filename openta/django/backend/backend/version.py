# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Version string tools."""

import os
import sys
import subprocess


def get_version_string():
    """Uses git information to create a version string."""

    def _decode(string):
        return string.decode(sys.stdout.encoding)

    try:
        if os.path.isfile("/usr/bin/git"):
            branch_name = subprocess.check_output(["/usr/bin/git", "rev-parse", "--abbrev-ref", "HEAD"])
            short_hash = subprocess.check_output(["/usr/bin/git", "rev-parse", "--short", "HEAD"])
            commit_date = subprocess.check_output(
                ["/usr/bin/git", "show", "-s", "--format=%cd", "--date=short", "HEAD"]
            )
            tag = subprocess.check_output(["/usr/bin/git", "describe", "--tags"])
            version = "{} {} {}".format(_decode(tag.strip()), _decode(short_hash.strip()), _decode(commit_date.strip()))
        else:
            version = os.environ.get("OPENTA_VERSION", "OpenTA")
    except Exception:
        version = os.environ.get("OPENTA_VERSION", "OpenTA")

    return version
