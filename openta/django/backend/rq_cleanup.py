#!/usr/bin/env python
"""
Safe RQ cleanup script.
Compatible with rq 2.6.x and django-rq.
"""

import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

import django_rq
from rq import Worker
from rq.registry import (
    FailedJobRegistry,
    FinishedJobRegistry,
    StartedJobRegistry,
)

QUEUE_NAME = "default"

def cleanup(queue_name=QUEUE_NAME, wipe_failed=True, wipe_finished=False):
    queue = django_rq.get_queue(queue_name)
    conn = queue.connection

    print(f"🧹 Cleaning RQ queue: {queue_name}")

    now = timezone.now()
    workers = Worker.all(connection=conn)

    # 1️⃣ Reap workers with stale or missing heartbeat
    for w in workers:
        heartbeat = w.last_heartbeat

        is_dead = (
            heartbeat is None or
            (now - heartbeat) > timedelta(minutes=5)
        )

        if is_dead:
            print(f"  ❌ Reaping dead worker: {w.name}")
            w.register_death()

    # 2️⃣ Clean started jobs (orphans)
    started = StartedJobRegistry(queue_name, connection=conn)
    for job_id in started.get_job_ids():
        print(f"  ⚠️  Removing started job: {job_id}")
        started.remove(job_id, delete_job=True)

    # 3️⃣ Optionally clean failed jobs
    if wipe_failed:
        failed = FailedJobRegistry(queue_name, connection=conn)
        for job_id in failed.get_job_ids():
            print(f"  💀 Removing failed job: {job_id}")
            failed.remove(job_id, delete_job=True)

    # 4️⃣ Optionally clean finished jobs
    if wipe_finished:
        finished = FinishedJobRegistry(queue_name, connection=conn)
        for job_id in finished.get_job_ids():
            print(f"  ✅ Removing finished job: {job_id}")
            finished.remove(job_id, delete_job=True)

    print("✨ RQ cleanup complete")

if __name__ == "__main__":
    cleanup()
