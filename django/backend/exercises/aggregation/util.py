from django.core.files.base import ContentFile
import logging
from .excel import create_xlsx_from_results_list
from .results import calculate_students_results_subset, students_results

logger = logging.getLogger(__name__)


def excel_custom_results_pipeline(dbexercises, task):
    results = calculate_students_results_subset(dbexercises, task)
    xlsx_data = create_xlsx_from_results_list(results)
    in_memory_file = ContentFile(xlsx_data)
    in_memory_file.name = ".xlsx"
    task.result_file = in_memory_file
    task.status = "Done"
    task.done = True
    task.save()


def students_results_async_pipeline(task):
    task.status = "Working"
    task.save()
    result = students_results(task=task)
    task.done = True
    task.status = "Working"
    task.progress = 100
    task.save()
    return result
