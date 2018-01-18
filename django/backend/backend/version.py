"""Version string tools."""

import sys
import subprocess


def get_version_string():
    """Uses git information to create a version string."""

    def _decode(string):
        return string.decode(sys.stdout.encoding)

    try:
        branch_name = subprocess.check_output(["/usr/bin/git", "rev-parse", "--abbrev-ref", "HEAD"])
        short_hash = subprocess.check_output(["/usr/bin/git", "rev-parse", "--short", "HEAD"])
        commit_date = subprocess.check_output(
            ["/usr/bin/git", "show", "-s", "--format=%cd", "--date=short", "HEAD"]
        )
        version = "{} {} {}".format(
            _decode(branch_name.strip()), _decode(short_hash.strip()), _decode(commit_date.strip())
        )
    except Exception:
        version = "Unknown - check settings.py"

    return version
