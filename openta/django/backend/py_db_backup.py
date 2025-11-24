#!/usr/bin/env python3
"""
Pure-Python database backup utility (no subprocess)

This script mirrors the existing `db_backup` flow but avoids shelling out to
pg_dump. Instead, it uses Django's management API to:

- Run migrations for a subdomain database alias
- Dump all model data to a JSON fixture
- Rotate backups using V<N> and W<week> copies

Notes:
- This produces logical JSON backups (data only). Schema is managed by
  migrations during restore. If you require pg_restore-compatible archives,
  that cannot be produced without invoking external tools like `pg_dump`.

Usage:
    ./py_db_backup.py <subdomain_glob> [--force]

Examples:
    ./py_db_backup.py ffm*
    ./py_db_backup.py mysubdomain --force
"""

import os
import sys
import glob as _glob
import json
import shutil
import datetime

from typing import Optional


def _minute_hash() -> str:
    # Keep behavior similar to bash script: rotate 0..9 by minute bucket
    epoch = int(datetime.datetime.now().timestamp())
    return str((epoch // 60) % 10)


def _setup_django():
    # Ensure Django is importable from backend directory
    here = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.abspath(os.path.join(here, os.pardir))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings_manage")
    import django

    django.setup()


def _dump_database_to_json(alias: str, out_path: str, *, indent: int = 2):
    """Dump all data for a given database alias to JSON.

    Excludes sessions and admin log entries to keep backups cleaner.
    """
    from django.core.management import call_command

    # Use `--natural-foreign` and `--natural-primary` to improve portability
    with open(out_path, "w", encoding="utf-8") as fp:
        call_command(
            "dumpdata",
            "--natural-foreign",
            "--natural-primary",
            "--indent",
            str(indent),
            # Commonly excluded noise tables
            "-e",
            "sessions",
            "-e",
            "admin.logentry",
            database=alias,
            stdout=fp,
        )


def _verify_or_create_db(alias: str):
    """Ensure a database alias exists in settings and connections.

    Leverages backend.middleware.verify_or_create_database_connection to add
    dynamic subdomain databases using /subdomain-data/<subdomain>/dbname.txt.
    """
    from backend.middleware import verify_or_create_database_connection

    verify_or_create_database_connection(alias)


def _get_dbname_for_alias(alias: str) -> Optional[str]:
    from django.conf import settings

    db = settings.DATABASES.get(alias)
    if not db:
        return None
    return db.get("NAME")


def _run_migrations(alias: str):
    from django.core.management import call_command

    call_command("migrate", database=alias)


def _rotate_backups(dir_path: str, base_filename: str):
    """Create rotating copies V<num> and W<week> inside dir_path.

    Copies `${dir_path}/../{base_filename}` into `${dir_path}/{base_filename}-V<num>`
    and `${dir_path}/{base_filename}-W<week>` similar to the bash script.
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        src = os.path.join(os.path.dirname(dir_path), base_filename)
        if not os.path.isfile(src):
            return

        # Determine next V number (mod 28)
        import re as _re
        existing = sorted(
            [p for p in _glob.glob(os.path.join(dir_path, "*-V*.json")) if os.path.isfile(p)]
        )
        if existing:
            latest = os.path.basename(existing[-1])
            m = _re.search(r"-V(\d+)\.", latest)
            if m:
                try:
                    vnum = (int(m.group(1)) + 1) % 28
                except Exception:
                    vnum = 0
            else:
                vnum = 0
        else:
            vnum = 0

        # Week number (00-53)
        wnum = int(datetime.datetime.now().strftime("%U"))

        base, ext = os.path.splitext(base_filename)
        vdst = os.path.join(dir_path, f"{base}-V{vnum}{ext}")
        wdst = os.path.join(dir_path, f"{base}-W{wnum}{ext}")
        shutil.copy2(src, vdst)
        shutil.copy2(src, wdst)
    except Exception:
        # Don't fail hard on rotation errors; best-effort
        pass


def backup_core_databases(force: bool):
    """Backup core Django databases: default, sites, opentasites.

    Writes JSON fixtures to `/subdomain-data/db-backup/<NAME>-<hash>.json`.
    """
    from django.conf import settings

    out_root = "/subdomain-data/db-backup"
    os.makedirs(out_root, exist_ok=True)
    aliases = ["default", "sites", "opentasites"]

    for alias in aliases:
        name = _get_dbname_for_alias(alias)
        if not name:
            continue
        out_path = os.path.join(out_root, f"{name}-{_minute_hash()}.json")
        try:
            _dump_database_to_json(alias, out_path)
            # Basic sanity check: non-trivial size
            if os.path.getsize(out_path) < 1000:
                # Remove tiny/failed dump
                try:
                    os.remove(out_path)
                except OSError:
                    pass
        except Exception as e:
            # Non-fatal; continue with others
            try:
                os.remove(out_path)
            except Exception:
                pass


def backup_subdomains(pattern: str, force: bool):
    """Backup each subdomain matching `/subdomain-data/<pattern>`.

    Produces JSON dumps under `/subdomain-data/<subdomain>/<dbname>.json` and
    rotates copies under `/subdomain-data/<subdomain>/backups/`.
    """
    volume_root = "/subdomain-data"
    matches = sorted(_glob.glob(os.path.join(volume_root, pattern)))
    if not matches:
        print(f"No subdomains matched: {pattern}")
        return

    for path in matches:
        subdomain = os.path.basename(path)
        dbname_file = os.path.join(volume_root, subdomain, "dbname.txt")
        touch_file = os.path.join(volume_root, subdomain, "touchfile")

        if not os.path.exists(dbname_file):
            # Skip uninitialized subdomain
            continue

        if not (force or os.path.exists(touch_file)):
            # Skip if not forced and no touchfile
            continue

        # Ensure alias and connection exist
        _verify_or_create_db(subdomain)

        # Run migrations for the subdomain
        _run_migrations(subdomain)

        # Determine DB name and output paths
        dbname = _get_dbname_for_alias(subdomain) or subdomain
        out_dir = os.path.join(volume_root, subdomain)
        os.makedirs(out_dir, exist_ok=True)
        tmp_out = "/tmp/py_dump.json"
        final_out = os.path.join(out_dir, f"{dbname}.json")

        try:
            _dump_database_to_json(subdomain, tmp_out)
            size = os.path.getsize(tmp_out)
            print(f"FILESIZE={size}")
            if size > 1000:
                # Move into place atomically
                shutil.move(tmp_out, final_out)
                # Remove touchfile on success
                try:
                    os.remove(touch_file)
                except OSError:
                    pass

                # Rotate copies
                backups_dir = os.path.join(out_dir, "backups")
                _rotate_backups(backups_dir, f"{dbname}.json")
            else:
                print("NOT DONE  ERROR IN BACKUP (too small)")
                try:
                    os.remove(tmp_out)
                except OSError:
                    pass
        except Exception as e:
            print(f"Backup failed for {subdomain}: {e}")
            try:
                if os.path.exists(tmp_out):
                    os.remove(tmp_out)
            except OSError:
                pass


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: py_db_backup.py <subdomain_glob> [--force]")
        return 2

    pattern = argv[1]
    force = "--force" in argv[2:]

    # Initialize Django once
    _setup_django()

    # Core DB backups (data-only JSON)
    backup_core_databases(force)

    # Per-subdomain backups
    backup_subdomains(pattern, force)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
