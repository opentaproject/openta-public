# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander
"""
- Dry-run for last 2 days:
      - python manage.py recover_image_answers --subdomain ffm516-2025 --since 2d --dry-run
  - Run for real:
      - python manage.py recover_image_answers --subdomain ffm516-2025 --since 2d
  - If needed, specify volume:
      - python manage.py recover_image_answers --subdomain ffm516-2025 --since 2d --volume /subdomain-data
  
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from backend.middleware import verify_or_create_database_connection
from django.contrib.auth.models import User
from course.models import Course
from exercises.models import Exercise, ImageAnswer
from django.db.models.signals import post_save, post_delete
from exercises.models import signal_handler

logger = logging.getLogger(__name__)


def _aware_from_ts(ts: float) -> datetime:
    dt = datetime.fromtimestamp(ts)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt

def _parse_since(value: Optional[str]) -> datetime:
    """Parse a --since value for filtering files by mtime/date.

    Accepts relative values like '2d', '48h', '90m' or absolute ISO
    timestamps (e.g., 2025-01-20T10:00:00+01:00). Defaults to now()-2 days.
    """
    now = timezone.now()
    if not value:
        return now - timedelta(days=2)
    v = value.strip().lower()
    m = __import__('re').match(r"^(\d+)([dhm])$", v)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if unit == 'd':
            return now - timedelta(days=n)
        if unit == 'h':
            return now - timedelta(hours=n)
        if unit == 'm':
            return now - timedelta(minutes=n)
    try:
        if v.endswith('z'):
            v = v[:-1] + '+00:00'
        dt = datetime.fromisoformat(v)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt
    except Exception:
        raise CommandError(
            "--since must be like '2d', '48h', '90m' or an ISO datetime (e.g., 2025-01-20T10:00:00+01:00)"
        )


class Command(BaseCommand):
    help = (
        "Recover missing ImageAnswer rows by scanning existing files under "
        "<VOLUME>/<subdomain>/media/answerimages/<course_key>/<username>/<exercise_key>/*."
    )

    def add_arguments(self, parser):
        parser.add_argument("--subdomain", required=True, help="Database/subdomain alias to import into")
        parser.add_argument("--dry-run", action="store_true", help="Scan and log without creating entries")
        parser.add_argument(
            "--since",
            dest="since",
            default=None,
            help=(
                "Only include files with mtime/date >= this. Accepts relative '2d', '48h', '90m' or absolute "
                "ISO datetime like 2025-01-20T10:00:00+01:00. Default: 2d"
            ),
        )
        parser.add_argument(
            "--volume",
            dest="volume",
            default=None,
            help="Override base archive volume path; defaults to settings.VOLUME or '/subdomain-data'",
        )
        parser.add_argument(
            "--extensions",
            dest="extensions",
            default="jpg,jpeg,png,pdf,PNG,JPG,JPEG,PDF",
            help="Comma-separated list of file extensions to consider",
        )
        parser.add_argument(
            "--mute-signals",
            action="store_true",
            help="Temporarily disable model post_save/post_delete signals during recovery",
        )

    def handle(self, *args, **kwargs):
        subdomain = (kwargs.get("subdomain") or "").strip()
        if not subdomain:
            raise CommandError("--subdomain is required")

        dry_run = bool(kwargs.get("dry_run"))
        since_dt = _parse_since(kwargs.get("since"))
        volume_override = (kwargs.get("volume") or "").strip() or None
        extensions = {e.strip().lstrip(".") for e in (kwargs.get("extensions") or "").split(",") if e.strip()}

        # Prepare DB context
        settings.DB_NAME = subdomain
        settings.SUBDOMAIN = subdomain
        verify_or_create_database_connection(subdomain)
        db = subdomain

        # Optionally mute signals to avoid aggregation side effects while recovering
        # (set via env RECOVER_IMAGE_ANSWERS_MUTE or pass by editing if needed)
        mute = bool(kwargs.get("mute_signals")) or bool(os.environ.get("RECOVER_IMAGE_ANSWERS_MUTE", "True").lower() in ("1","true","t","yes"))
        if mute:
            try:
                post_save.disconnect(signal_handler)
                post_delete.disconnect(signal_handler)
            except Exception:
                pass

        # Resolve VOLUME
        volume = volume_override or getattr(settings, "VOLUME", "/subdomain-data")
        base_dir = os.path.join(volume, subdomain, "media", "answerimages")
        if not os.path.isdir(base_dir):
            raise CommandError(f"Base dir not found: {base_dir}")

        scanned = 0
        created = 0
        skipped_existing = 0
        skipped_old = 0
        errors = 0

        # Walk structure: <course_key>/<username>/<exercise_key>/*
        for course_key in os.listdir(base_dir):
            course_dir = os.path.join(base_dir, course_key)
            if not os.path.isdir(course_dir):
                continue
            try:
                course = Course.objects.using(db).get(course_key=course_key)
            except Course.DoesNotExist:
                logger.warning(f"Course not found {course_key} in DB {db}; skipping dir {course_dir}")
                errors += 1
                continue
            for username in os.listdir(course_dir):
                user_dir = os.path.join(course_dir, username)
                if not os.path.isdir(user_dir):
                    continue
                try:
                    user = User.objects.using(db).get(username=username)
                except User.DoesNotExist:
                    logger.warning(f"User not found {username} in DB {db}; skipping dir {user_dir}")
                    errors += 1
                    continue
                for exercise_key in os.listdir(user_dir):
                    ex_dir = os.path.join(user_dir, exercise_key)
                    if not os.path.isdir(ex_dir):
                        continue
                    try:
                        exercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
                        if str(exercise.course.course_key) != str(course.course_key):
                            logger.warning(
                                f"Exercise {exercise_key} not in course {course_key}; skipping dir {ex_dir}"
                            )
                            errors += 1
                            continue
                    except Exercise.DoesNotExist:
                        logger.warning(f"Exercise not found {exercise_key} in DB {db}; skipping dir {ex_dir}")
                        errors += 1
                        continue

                    for fname in os.listdir(ex_dir):
                        fpath = os.path.join(ex_dir, fname)
                        if not os.path.isfile(fpath):
                            continue
                        ext = fname.split(".")[-1]
                        if extensions and ext not in extensions:
                            continue
                        scanned += 1

                        # Relative name for FileField (relative to storage root)
                        rel_name = os.path.join(
                            subdomain,
                            "media",
                            "answerimages",
                            course_key,
                            username,
                            exercise_key,
                            fname,
                        )

                        # Check time window by file mtime
                        try:
                            mtime = os.path.getmtime(fpath)
                            adate = _aware_from_ts(mtime)
                        except Exception:
                            adate = timezone.now()
                        if adate < since_dt:
                            skipped_old += 1
                            continue

                        # Duplicate guard: same user, exercise, and file path
                        exists = (
                            ImageAnswer.objects.using(db)
                            .filter(user=user, exercise=exercise)
                            .filter(Q(image=rel_name) | Q(pdf=rel_name))
                            .exists()
                        )
                        if exists:
                            skipped_existing += 1
                            continue

                        if dry_run:
                            created += 1
                            continue

                        # Create ImageAnswer with date from file mtime
                        try:
                            ia = ImageAnswer(user=user, exercise=exercise, date=adate)
                            if ext.lower() == "pdf":
                                ia.filetype = ImageAnswer.PDF
                                ia.pdf.name = rel_name
                            else:
                                ia.filetype = ImageAnswer.IMAGE
                                ia.image.name = rel_name
                            ia.save(using=db)
                            created += 1
                        except Exception as e:
                            errors += 1
                            logger.warning(
                                f"Failed to create ImageAnswer for {fpath}: {type(e).__name__}: {e}"
                            )

        # Reconnect signals
        if mute:
            try:
                post_save.connect(signal_handler)
                post_delete.connect(signal_handler)
            except Exception:
                pass

        self.stdout.write(
            self.style.SUCCESS(
                "Recovery complete: scanned=%d, created=%d, skipped_old=%d, skipped_existing=%d, errors=%d"
                % (scanned, created, skipped_old, skipped_existing, errors)
            )
        )
