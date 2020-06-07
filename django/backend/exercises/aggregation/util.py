from django.core.files.base import ContentFile
import logging
from django.conf import settings
from .excel import create_xlsx_from_results_list
from .results import students_results, calculate_students_results, calculate_students_custom_results
import csv
import json
from django.core.serializers.json import DjangoJSONEncoder


logger = logging.getLogger(__name__)


def excel_custom_results_pipeline(dbexercises, task, course):
    # print("EXCEL CUSTOM RESULTS PIPELINE")
    logger.debug("EXECL CUSTOM_RESULTS_PPIPE " + str(dbexercises.count()))
    results = calculate_students_custom_results(dbexercises, task, course=course)
    xlsx_data = create_xlsx_from_results_list(results)
    in_memory_file = ContentFile(xlsx_data)
    in_memory_file.name = ".xlsx"
    task.result_file = in_memory_file
    task.status = "Done"
    task.done = True
    task.save()
    # print("XLSX_DATA", xlsx_data)
    # if settings.UNITTESTS:
    #    b = []
    #    for item in results:
    #        del item['pk']
    #        b = b + [item]
    #    json1  = json.dumps(  results,default=str)
    #    with open("/tmp/results.txt", mode="w") as out:
    #        out.write(json1 )
    fp = open('/tmp/results.xlsx', 'wb')
    fp.write(xlsx_data)
    fp.close()
    # your_csv_file = open('/tmp/your_csv_file.csv', 'w')
    # wr = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)
    # sh = xlsx_data
    # for rownum in range(sh.nrows):
    #    wr.writerow(sh.row_values(rownum))

    # your_csv_file.close()


def students_results_async_pipeline(task, course):
    task.status = "Working"
    task.save()
    fp = open("/tmp/debug.txt",'a+')
    fp.write("STUDENTS_RESULTS_ASYNC_PIPELINE STARTED\n")
    result = students_results(task=task, course=course)
    fp.write("STUDENTS_RESULTS_ASYNC_PIPELINE ENDED\n")
    fp.close()
    task.done = True
    task.status = "Working"
    task.progress = 100
    task.save()
    return result
