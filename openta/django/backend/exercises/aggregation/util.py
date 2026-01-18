# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.core.files.base import ContentFile
from django.conf import settings
import random
import logging
from django.conf import settings
from .excel import create_xlsx_from_results_list
from .results import students_results, calculate_students_custom_results
import csv
import json
from django.core.serializers.json import DjangoJSONEncoder


logger = logging.getLogger(__name__)


def excel_custom_results_pipeline(dbexercises, task, course):
    # print("EXCEL CUSTOM RESULTS PIPELINE")
    # logger.debug("EXECL CUSTOM_RESULTS_PPIPE " + str(dbexercises.count()))
    # logger.debug("TASK = %s " % task )
    # if not course.opentasite == settings.SUBDOMAIN :
    #    msg = f"ERROR EXCEL_CUSTOM_RESULS PIPLINE ERROR {course.opentasite} != {settings.SUBDOMAIN}"
    #    logger.error(msg)
    if settings.MULTICOURSE:
        #if not course.opentasite == settings.SUBDOMAIN:
        #    msg = f"ERROR EXCEL_CUSTOM_RESULS PIPLINE ERROR {course.opentasite} != {settings.SUBDOMAIN}"
        #logger.error(msg)
        settings.SUBDOMAIN = course.opentasite
        settings.DB_NAME = course.opentasite
    results = calculate_students_custom_results(dbexercises, task, course=course)
    # logger.debug("EXECL CUSTOM_RESULTS_PPIPE RESULTS " + str(results))
    r = str(random.randint(111, 999))
    xlsx_data = create_xlsx_from_results_list(results)
    in_memory_file = ContentFile(xlsx_data)
    in_memory_file.name = f"{settings.SUBDOMAIN}-{r}.xlsx"
    task.result_file = in_memory_file
    task.status = "Done"
    task.done = True
    task.save(using='default')
    # print("XLSX_DATA", xlsx_data)
    # if settings.UNITTESTS:
    #    b = []
    #    for item in results:
    #        del item['pk']
    #        b = b + [item]
    #    json1  = json.dumps(  results,default=str)
    #    with open("/tmp/results.txt", mode="w") as out:
    #        out.write(json1 )
    fp = open("/tmp/results.xlsx", "wb")
    fp.write(xlsx_data)
    fp.close()
    # your_csv_file = open('/tmp/your_csv_file.csv', 'w')
    # wr = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)
    # sh = xlsx_data
    # for rownum in range(sh.nrows):
    #    wr.writerow(sh.row_values(rownum))

    # your_csv_file.close()


def students_results_async_pipeline(task, course, username, has_perm=False,selected=[] ):
    #logger.error(f"PIPELINE selected = {selected}")
    task.status = "Working"
    task.save(using='default')
    # logger.debug("STUDENTS_RESULTS_ASYNC_PIPELINE STARTED with course = %s " % course)
    # Log has_perm both from argument and job meta for sanity in rqworker
    try:
        from rq import get_current_job

        job = get_current_job()
        meta_perm = None
        job_id = None
        if job is not None:
            job_id = job.id
            if isinstance(job.meta, dict):
                meta_perm = job.meta.get("has_perm")
        logger.error(
            f"RQPIPE students_results_async_pipeline task_id={getattr(task,'pk',None)} job_id={job_id} has_perm_arg={has_perm} job_meta_has_perm={meta_perm}"
        )
    except Exception as e:
        logger.error(f"RQPIPE meta inspection failed: {type(e).__name__} {e}")

    #logger.error("CALL STUDENTS RESULTS")
    result = students_results(task=task, course=course, has_perm=has_perm,selected=selected)
    # logger.debug("STUDENTS_RESULTS_ASYNC_PIPELINE ENDED")
    task.done = True
    task.status = "Done"
    task.progress = 100
    # logger.info("STUDENTS_RESULTS_ASYNC_PIPELINE RESULT =  %s " % len(  result) )
    task.result = result
    task.save(using='default')
    return result
