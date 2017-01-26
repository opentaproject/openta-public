from django.core.management.base import BaseCommand, CommandError
from exercises.aggregation import student_statistics_exercises, students_results
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculates results and statistics and stores to cache'

    def handle(self, *args, **options):
        logger.info('Started calculating results and statistics')
        student_statistics_exercises(force=True)
        students_results(force=True)
        logger.info('Finished calculating results and statistics')

        # raise CommandError('Poll "%s" does not exist' % poll_id)
        # self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
