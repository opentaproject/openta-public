from django.core.management.base import BaseCommand, CommandError
from exercises.aggregation import student_statistics_exercises, students_results
import logging

from course.models import Course

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculates results and statistics and stores to cache'

    def handle(self, *args, **options):
        logger.info('Started calculating results and statistics')
        for course in Course.objects.all():
            if course.published:
                logger.info("Calculating for course {}".format(course.course_name))
                student_statistics_exercises(force=True, course=course)
                logger.info('Statistics done, now doing results.')
                students_results(force=True, course=course)
                logger.info('Finished calculating results and statistics')
            else:
                logger.info(
                    "Skip calculating results for unpublished course {}".format(course.course_name)
                )
