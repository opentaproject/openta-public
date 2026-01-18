# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

"""Version string tools."""

import os
import sys
import subprocess
#from django.conf import settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIT_DIR = '/'.join( BASE_DIR.split('/')[0:-3] )+"/.git"


def get_version_string(gitdir):
    """Uses git information to create a version string.

    If there is no tag reachable from HEAD, the tag field is left blank
    but the git hash and date are still included.
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _decode(b):
        try:
            return b.decode(sys.stdout.encoding or "utf-8", errors="replace")
        except Exception:
            return str(b)

    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        #assert False, 'False'
        #print(f"BASE_DIR = {BASE_DIR}")
        if os.path.isfile("/usr/bin/git") and os.path.isdir(gitdir):
            # Collect git metadata
            # branch_name currently unused but kept for parity with original implementation
            try:
                branch_name = subprocess.check_output(["/usr/bin/git", "-C", gitdir, "rev-parse", "--abbrev-ref", "HEAD"])  # noqa: F841
            except Exception:
                branch_name = b""  # not critical for version string

            short_hash = subprocess.check_output(["/usr/bin/git", "-C", gitdir, "rev-parse", "--short", "HEAD"])
            commit_date = subprocess.check_output(["/usr/bin/git", "-C", gitdir, "show", "-s", "--format=%cd", "--date=short", "HEAD"])

            # Get tag if available; if not, leave it blank
            try:
                tag = subprocess.check_output(["/usr/bin/git", "-C", gitdir, "describe", "--tags"])
                tag_s = _decode(tag.strip())
            except Exception:
                tag_s = ""

            version = "{} {} {}".format(tag_s, _decode(short_hash.strip()), _decode(commit_date.strip())).strip()
        else:
            # Fallback to reading pre-generated version file if available
            version = open(os.path.join(BASE_DIR, "backend", "version.txt"), "r").read().strip()
    except Exception:
        # Final fallback to environment or a default string
        try :
            version = open(os.path.join(BASE_DIR, "backend", "version.txt"), "r").read().strip()
        except Exception as err :
            version = os.environ.get("OPENTA_VERSION", f"OpenTA {str(err)} ")
    return version


def _invoked_by_post_commit_hook() -> bool:
    """Best-effort detection if this script is run via .githooks/post-commit.

    We check the parent process command line for a reference to a
    `post-commit` hook under a `.githooks` directory. If detection fails,
    we assume it's NOT from the hook (so the file write proceeds).
    """
    try:
        ppid = os.getppid()
        # Works on macOS and Linux; returns the parent command line
        out = subprocess.check_output(["/bin/ps", "-o", "command=", "-p", str(ppid)])
        cmd = out.decode("utf-8", errors="ignore").strip()
        return ("post-commit" in cmd) and (".githooks" in cmd)
    except Exception:
        return False

version = get_version_string(GIT_DIR)
#print(f"{version}")

# Also persist to version.txt unless invoked by post-commit hook
if not _invoked_by_post_commit_hook():
    try:
        with open(os.path.join(BASE_DIR, "backend", "version.txt"), "w") as f:
            f.write(version + "\n")
    except Exception:
        # Non-fatal: keep stdout behavior even if file write fails
        pass
