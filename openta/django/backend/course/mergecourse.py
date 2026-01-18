# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import glob
import os
import re
import shutil
import tempfile
import zipfile
import secrets
import string
import logging
import subprocess
from typing import Optional

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from django.conf import settings

logger = logging.getLogger(__name__)


def _random_dbname(length: int = 8) -> str:
    alphabet = string.ascii_lowercase
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _normalize_pg_host(host: Optional[str]) -> Optional[str]:
    if not host:
        return host
    # Align with shell scripts that remap pgbouncer-service to db-server
    if host == "pgbouncer-service":
        return "db-server"
    return host


def mergecourse_from_zip(zip_path: str, subdomain: str) -> str:
    """Merge/import a course zip into a new database and site folder.

    This mirrors the behavior of the previous shell script `db_mergecourse_from_zip`:
    - Unpack the zip, strip non-DB content, and rewrite the dbname.
    - Replace `/subdomain-data/<subdomain>` with the unpacked contents (archiving old).
    - Create a new Postgres database and restore it from the dump.
    - Update course and file-path references to the new subdomain.

    Args:
        zip_path: Path to the uploaded zip file.
        subdomain: Target subdomain name.

    Returns:
        The newly created database name.

    Raises:
        RuntimeError: On validation, filesystem, or database errors.
    """

    volume = getattr(settings, "VOLUME", "/subdomain-data")
    pguser = getattr(settings, "PGUSER", "postgres")
    pgpassword = getattr(settings, "PGPASSWORD", None)
    pghost = _normalize_pg_host(getattr(settings, "PGHOST", None))

    # 1) Unpack to temp dir and sanitize contents
    tmpdir = tempfile.mkdtemp(prefix="mergecourse-")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmpdir)
        # Remove presentation-only or generated content if present
        for entry in ["html", "xsl", "csv", "index.html", "README"]:
            try:
                path = os.path.join(tmpdir, entry)
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                elif os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

        dbname_file = os.path.join(tmpdir, "dbname.txt")
        if not os.path.exists(dbname_file):
            raise RuntimeError("dbname.txt missing in zip")
        with open(dbname_file, "r") as f:
            old_dbname = f.read().strip()
        if not re.fullmatch(r"[A-Za-z0-9_\-]+", old_dbname or ""):
            raise RuntimeError("Invalid original db name in dbname.txt")

        old_dump = os.path.join(tmpdir, f"{old_dbname}.db")
        if not os.path.exists(old_dump):
            raise RuntimeError("No database dump found in zip")

        new_dbname = _random_dbname(8)
        new_dump = os.path.join(tmpdir, f"{new_dbname}.db")
        os.rename(old_dump, new_dump)
        with open(dbname_file, "w") as f:
            f.write(new_dbname)

        # Detect previous subdomain marker
        old_subdomain = None
        markers = glob.glob(os.path.join(tmpdir, "subdomain-*"))
        if markers:
            # Take last by lexical order; typical scripts only expect one
            marker = os.path.basename(sorted(markers)[-1])
            m = re.match(r"subdomain-(.+)", marker)
            if m:
                old_subdomain = m.group(1)
            # Remove previous markers
            for mk in markers:
                try:
                    os.remove(mk)
                except Exception:
                    pass

        # Add new subdomain marker
        open(os.path.join(tmpdir, f"subdomain-{subdomain}"), "a").close()

        # 2) Replace site directory
        target_dir = os.path.join(volume, subdomain)
        deleted_dir = os.path.join(volume, "deleted")
        os.makedirs(deleted_dir, exist_ok=True)
        if os.path.isdir(target_dir):
            archive_name = f"{subdomain}-{new_dbname}"
            shutil.move(target_dir, os.path.join(deleted_dir, archive_name))
        shutil.move(tmpdir, target_dir)
        # After move, switch context to the new location
        site_dir = target_dir
        new_dump = os.path.join(site_dir, f"{new_dbname}.db")

        # 3) Create DB and restore dump
        # Connect to the maintenance DB to issue CREATE DATABASE
        maint_db = "postgres"
        conn_kwargs = {"user": pguser}
        if pghost:
            conn_kwargs["host"] = pghost
        if pgpassword:
            conn_kwargs["password"] = pgpassword
        try:
            conn = psycopg2.connect(dbname=maint_db, **conn_kwargs)
            try:
                # Ensure CREATE DATABASE runs outside an implicit transaction
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                with conn.cursor() as cur:
                    cur.execute(
                        sql.SQL("CREATE DATABASE {} OWNER {};").format(
                            sql.Identifier(new_dbname), sql.Identifier(pguser)
                        )
                    )
            finally:
                conn.close()
        except Exception as e:
            raise RuntimeError(f"Failed to create database {new_dbname}: {e}")

        # Use pg_restore for custom-format dump
        env = os.environ.copy()
        if pghost:
            env["PGHOST"] = pghost
        if pguser:
            env["PGUSER"] = pguser
        if pgpassword:
            env["PGPASSWORD"] = pgpassword
        try:
            subprocess.run(
                ["pg_restore", "--no-owner", "-d", new_dbname, new_dump],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"pg_restore failed: {e.stderr or e.stdout}")

        # 4) Post-restore fixes on the new DB
        try:
            with psycopg2.connect(dbname=new_dbname, **conn_kwargs) as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute("BEGIN;")
                    cur.execute("UPDATE course_course SET opentasite = %s;", (subdomain,))
                    cur.execute("COMMIT;")
                    cur.execute("BEGIN;")
                    cur.execute("UPDATE course_course SET course_name = %s;", (f"course-{subdomain}",))
                    cur.execute("COMMIT;")
                    cur.execute("BEGIN;")
                    cur.execute("UPDATE course_course SET data = %s;", ('"{}"',))
                    cur.execute("COMMIT;")
                    if old_subdomain:
                        cur.execute("BEGIN;")
                        cur.execute(
                            "UPDATE exercises_imageanswer SET image = REPLACE(image, %s, %s);",
                            (old_subdomain, subdomain),
                        )
                        cur.execute("COMMIT;")
                        cur.execute("BEGIN;")
                        cur.execute(
                            "UPDATE exercises_imageanswer SET pdf = REPLACE(pdf, %s, %s);",
                            (old_subdomain, subdomain),
                        )
                        cur.execute("COMMIT;")
        except Exception as e:
            raise RuntimeError(f"Post-restore SQL updates failed: {e}")

        # 5) Touch reload marker for lazy reloads elsewhere
        try:
            open(os.path.join(site_dir, "reload"), "a").close()
        except Exception:
            pass

        return new_dbname
    except Exception:
        # Ensure we clean up the temp dir on early failures
        try:
            if os.path.isdir(tmpdir):
                shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass
        raise
