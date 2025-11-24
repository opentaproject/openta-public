# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander
"""
 - Command: python manage.py import_answers_from_archive --subdomain ffm516-2025 --since 2d
  - Optional dry-run first: python manage.py import_answers_from_archive --subdomain ffm516-2025 --since 2d --dry-run
  - Archive path: VOLUME/ffm516-2025/json-answer-backups/<course_key>/<username>/<exercise_key>/<question_key>.json
  - Duplicate safety: Skips existing (user, question, date, answer) entries; won’t overwrite model rows.
"""

import os
import re
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone

from backend.middleware import verify_or_create_database_connection
from django.contrib.auth.models import User
from course.models import Course
from exercises.models import Exercise, Question, Answer
from django.db.models.signals import post_save, post_delete
from exercises.models import signal_handler

logger = logging.getLogger(__name__)


def _parse_since(value: Optional[str]) -> datetime:
    """Parse a --since value.

    Accepts absolute datetimes (ISO-like) or relative values like '48h', '2d', '90m'.
    Defaults to now()-2 days when value is None/empty.
    """
    now = timezone.now()
    if not value:
        return now - timedelta(days=2)

    v = value.strip().lower()
    # Relative forms: Nd, Nh, Nm
    m = re.match(r"^(\d+)([dhm])$", v)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if unit == "d":
            return now - timedelta(days=n)
        if unit == "h":
            return now - timedelta(hours=n)
        if unit == "m":
            return now - timedelta(minutes=n)

    # Absolute: try fromisoformat; accept trailing 'Z'
    try:
        if v.endswith("z"):
            v = v[:-1] + "+00:00"
        dt = datetime.fromisoformat(v)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt
    except Exception:
        raise CommandError(
            "--since must be like '2d', '48h', '90m' or an ISO datetime (e.g., 2025-01-20T10:00:00+01:00)"
        )


def _parse_json_date(s: str) -> Optional[datetime]:
    """Parse the 'date' value stored as str(...) in the archive JSON.

    Returns an aware datetime on success, or None on failure.
    """
    if not s:
        return None
    val = s.strip()
    try:
        if val.endswith("Z"):
            val = val[:-1] + "+00:00"
        dt = datetime.fromisoformat(val)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt
    except Exception:
        return None


def _str_to_bool(s: str) -> bool:
    return str(s).strip().lower() in {"true", "1", "yes", "y"}


def _iter_archive_files(base_dir: str):
    """Yield tuples (course_key, username, exercise_key, question_key, json_path)."""
    if not os.path.isdir(base_dir):
        return
    for course_key in os.listdir(base_dir):
        course_dir = os.path.join(base_dir, course_key)
        if not os.path.isdir(course_dir):
            continue
        for username in os.listdir(course_dir):
            user_dir = os.path.join(course_dir, username)
            if not os.path.isdir(user_dir):
                continue
            for exercise_key in os.listdir(user_dir):
                exercise_dir = os.path.join(user_dir, exercise_key)
                if not os.path.isdir(exercise_dir):
                    continue
                for fname in os.listdir(exercise_dir):
                    if not fname.endswith(".json"):
                        continue
                    question_key = fname[:-5]
                    yield (
                        course_key,
                        username,
                        exercise_key,
                        question_key,
                        os.path.join(exercise_dir, fname),
                    )


class Command(BaseCommand):
    help = (
        "Import Answer rows from archived JSON under VOLUME/<subdomain>/json-answer-backups.\n"
        "Skips files older than --since (default: 2d). Avoids duplicates by (user,question,date,answer)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--subdomain", required=True, help="Database/subdomain alias to import into")
        parser.add_argument(
            "--since",
            dest="since",
            default=None,
            help=(
                "Only import answers with JSON date >= this. Accepts relative '2d', '48h', '90m' or absolute "
                "ISO datetime like 2025-01-20T10:00:00+01:00. Default: 2d"
            ),
        )
        parser.add_argument("--dry-run", action="store_true", help="Scan and log without creating entries")
        parser.add_argument(
            "--volume",
            dest="volume",
            default=None,
            help="Override base archive volume path; defaults to settings.VOLUME or '/subdomain-data'",
        )
        parser.add_argument(
            "--mute-signals",
            action="store_true",
            help="Temporarily disable model post_save/post_delete signals during import",
        )

    def handle(self, *args, **kwargs):
        subdomain = (kwargs.get("subdomain") or "").strip()
        if not subdomain:
            raise CommandError("--subdomain is required")

        since_dt = _parse_since(kwargs.get("since"))
        dry_run = bool(kwargs.get("dry_run"))
        volume_override = (kwargs.get("volume") or "").strip() or None

        # Prepare DB context
        settings.DB_NAME = subdomain
        settings.SUBDOMAIN = subdomain
        verify_or_create_database_connection(subdomain)
        db = subdomain

        # Optionally mute signals to avoid aggregation side effects/touching during import
        mute = bool(kwargs.get("mute_signals"))
        if mute:
            try:
                post_save.disconnect(signal_handler)
                post_delete.disconnect(signal_handler)
            except Exception:
                pass

        # Resolve VOLUME with safe fallback and optional override
        volume = volume_override or getattr(settings, "VOLUME", "/subdomain-data")
        # Ensure base volume/subdomain exists to avoid signal handlers failing on os.utime
        try:
            os.makedirs(os.path.join(volume, subdomain), exist_ok=True)
        except Exception as e:
            logger.warning(
                f"Could not ensure volume path exists at {os.path.join(volume, subdomain)}: {type(e).__name__}: {e}"
            )

        base_dir = os.path.join(volume, subdomain, "json-answer-backups")
        if not os.path.isdir(base_dir):
            raise CommandError(f"Archive base directory not found: {base_dir}")

        created = 0
        skipped_old = 0
        skipped_existing = 0
        errors = 0
        scanned = 0

        for course_key, username, exercise_key, question_key, json_path in _iter_archive_files(base_dir):
            scanned += 1
            try:
                with open(json_path, "r") as fp:
                    data = json.load(fp)
            except Exception as e:
                errors += 1
                logger.warning(f"Failed to read {json_path}: {type(e).__name__}: {e}")
                continue

            # Parse fields from JSON
            answer_text = str(data.get("answer", ""))
            correct_flag = _str_to_bool(data.get("correct", "false"))
            questionseed = str(data.get("questionseed", ""))
            grader_response = str(data.get("grader_response", ""))
            json_date_raw = str(data.get("date", "")).strip()
            answer_dt = _parse_json_date(json_date_raw)

            # Fallback to file mtime if JSON date is unparseable
            if answer_dt is None:
                try:
                    ts = os.path.getmtime(json_path)
                    answer_dt = timezone.make_aware(datetime.fromtimestamp(ts))
                except Exception:
                    errors += 1
                    logger.warning(f"Could not determine date for {json_path}; skipping")
                    continue

            # Filter by --since
            if answer_dt < since_dt:
                skipped_old += 1
                continue

            # Resolve ORM objects
            try:
                # Validate course context (not strictly required to create Answer, but provides sanity)
                course = Course.objects.using(db).get(course_key=course_key)
                exercise = Exercise.objects.using(db).get(exercise_key=exercise_key)
                # Ensure exercise belongs to course in this DB
                if str(exercise.course.course_key) != str(course.course_key):
                    logger.warning(
                        f"Exercise {exercise_key} not in course {course_key} for {json_path}; skipping"
                    )
                    errors += 1
                    continue
                question = Question.objects.using(db).get(exercise=exercise, question_key=question_key)
                user = User.objects.using(db).get(username=username)
            except Course.DoesNotExist:
                errors += 1
                logger.warning(f"Course {course_key} not found in {db}; skipping {json_path}")
                continue
            except Exercise.DoesNotExist:
                errors += 1
                logger.warning(f"Exercise {exercise_key} not found in {db}; skipping {json_path}")
                continue
            except Question.DoesNotExist:
                errors += 1
                logger.warning(
                    f"Question {question_key} for exercise {exercise_key} not found in {db}; skipping {json_path}"
                )
                continue
            except User.DoesNotExist:
                errors += 1
                logger.warning(f"User {username} not found in {db}; skipping {json_path}")
                continue

            # Avoid duplicates: consider (user, question, date, answer) as identity
            exists = (
                Answer.objects.using(db)
                .filter(user=user, question=question, date=answer_dt, answer=answer_text)
                .exists()
            )
            if exists:
                skipped_existing += 1
                continue

            if dry_run:
                created += 1  # would create
                continue

            # Create Answer with date from JSON
            try:
                ans = Answer(
                    user=user,
                    question=question,
                    answer=answer_text,
                    grader_response=grader_response,
                    correct=correct_flag,
                    date=answer_dt,
                    questionseed=questionseed,
                )
                ans.save(using=db)
                created += 1
            except Exception as e:
                errors += 1
                logger.warning(
                    f"Failed to create Answer for {json_path}: {type(e).__name__}: {e}"
                )
                continue

        # Reconnect signals
        if mute:
            try:
                post_save.connect(signal_handler)
                post_delete.connect(signal_handler)
            except Exception:
                pass

        self.stdout.write(
            self.style.SUCCESS(
                "Import complete: scanned=%d, created=%d, skipped_old=%d, skipped_existing=%d, errors=%d"
                % (scanned, created, skipped_old, skipped_existing, errors)
            )
        )
