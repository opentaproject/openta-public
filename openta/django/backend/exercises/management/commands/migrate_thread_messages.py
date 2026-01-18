# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

#
# WARNING THIS IS OBSOLETE AFTER INITIAL MIGRATION TO Message CLASS and having been run once
#
#
from django.core.management.base import BaseCommand

try:
    # Models are defined in django_ragamuffin
    from django_ragamuffin.models import Thread, Message
except Exception as e:
    Thread = None
    Message = None


class Command(BaseCommand):
    help = "Materialize per-thread JSON messages into Message rows, linking sequentially via previous."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print actions without modifying the database.",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        if Thread is None or Message is None:
            self.stderr.write(
                self.style.ERROR(
                    "Unable to import Thread/Message from django_ragamuffin.models. Is the app installed?"
                )
            )
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("Running in DRY-RUN mode; no changes will be saved."))

        threads = Thread.objects.all()
        print(f"THREADS = {threads}")
        for thread in threads.all():
            print(f"THREAD = {thread}")
            previous = None
            for msg in thread.thread_messages:
                print(f"MSG = {msg}")
                query = msg['user']
                response = msg['assistant']
                model = msg['model']
                ntokens = msg['ntokens']
                time_spent = msg['time_spent']
                response_id = msg.get('response_id', None)
                last_messages = msg['last_messages']
                summary = msg.get('summary', '')
                comment = msg.get('comment', '')
                choice = msg.get('choice', 0)
                instructions = msg.get('instructions', 'no instructions')
                previous_response_id = msg.get('previous_response_id', None)
                mhash = msg.get('hash')
                print(f"QUERY = {query}")
                print(f"RESPONSE = {response}")
                print(f"MODEL = {model}")
                print(f"ntokens = {ntokens}")
                print(f"time_spent = {time_spent}")
                print(f"response_id = {response_id}")
                print(f"LAST_MESSAGES = {last_messages}")
                print(f"SUMMARY = {summary}")
                print(f"comment = {comment}")
                print(f"choice = {choice}")
                print(f"instructions = {instructions}")
                print(f"previous_response_id ={previous_response_id}")
                print(f"MHASH = {mhash}")

                if dry_run:
                    print("DRY-RUN: would get_or_create Message with above fields")
                    print("DRY-RUN: would set thread and previous linkage")
                else:
                    message, created = Message.objects.get_or_create(
                        query=msg.get('user', ''),
                        response=response,
                        choice=choice,
                        summary=summary,
                        previous=previous,
                        ntokens=ntokens,
                        model=model,
                        time_spent=time_spent,
                        last_messages=last_messages,
                        response_id=response_id,
                        instructions=instructions,
                        previous_response_id=previous_response_id,
                        mhash=mhash,
                    )

                    message.save()
                    message.thread = thread
                    message.previous = previous
                    message.save(update_fields=['thread', 'previous'])
                    previous = message

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN complete. No changes were made."))
        else:
            self.stdout.write(self.style.SUCCESS("Completed migrating thread messages."))
