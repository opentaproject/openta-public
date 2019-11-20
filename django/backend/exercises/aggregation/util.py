from django.core.files.base import ContentFile
import logging
from .excel import create_xlsx_from_results_list
from .results import students_results, calculate_students_results, calculate_students_custom_results


logger = logging.getLogger(__name__)


def excel_custom_results_pipeline(dbexercises, task, course):
    print("EXCEL CUSTOM RESULTS PIPELINE")
    logger.debug("EXECL CUSTOM_RESULTS_PPIPE " + str(  dbexercises.count()) )
    results = calculate_students_custom_results(dbexercises, task, course=course)
    xlsx_data = create_xlsx_from_results_list(results)
    in_memory_file = ContentFile(xlsx_data)
    in_memory_file.name = ".xlsx"
    task.result_file = in_memory_file
    task.status = "Done"
    task.done = True
    task.save()


def students_results_async_pipeline(task, course):
    task.status = "Working"
    task.save()
    print("STUDENTS_RESULTS_ASYNC_PIPELINE STARTED")
    result = students_results(task=task, course=course)
    print("STUDENTS_RESULTS_ASYNC_PIPELINE ENDED")
    task.done = True
    task.status = "Working"
    task.progress = 100
    task.save()
    return result
