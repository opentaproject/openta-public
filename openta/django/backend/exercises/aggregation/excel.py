# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import xlsxwriter
import io
import logging
import json
import pickle

logger = logging.getLogger(__name__)


def write_xlsx_from_results_list(filename, results):
    xlsx_data = create_xlsx_from_results_list(results)
    with open(filename, "wb") as f:
        f.write(xlsx_data)


def create_xlsx_from_results_list(results):
    # fp = open('/tmp/exceldata3.json', 'wb')
    # fp.write( b'abcdefg')
    # fp.close()
    output = io.BytesIO()
    # logger.error(str(results) )
    # with open('/tmp/exceldata.py','w') as f :
    #    print(results,file=f)
    fp = open("/tmp/exceldata3.pkl", "wb")
    pickle.dump(results, fp)
    fp.close()

    logger.debug("WROTE EXCELDATA3.pkl")
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    bold_format = workbook.add_format({"bold": True})
    right_border_format = workbook.add_format({"bold": True})
    right_border_format.set_right(1)
    # print("CREATED WORKBOOK" )
    worksheet = workbook.add_worksheet()
    ind = 0
    worksheet.write(0, ind, "ID")
    ind += 1
    worksheet.write(0, ind, "Username")
    ind += 1
    worksheet.write(0, ind, "First")
    ind += 1
    worksheet.write(0, ind, "Last")
    ind += 1
    worksheet.write(0, ind, "Obligatory ontime ", bold_format)
    ind += 1
    worksheet.write(0, ind, "Obligatory  late ", bold_format)
    ind += 1
    worksheet.write(0, ind, "Bonus ontime ", bold_format)
    ind += 1
    worksheet.write(0, ind, "Bonus late ", bold_format)
    ind += 1
    worksheet.write(0, ind, "Optional total", bold_format)
    ind += 1
    worksheet.write(0, ind, "Total ontime ", right_border_format)
    ind += 1
    worksheet.write(0, ind, "total Late ", right_border_format)
    ind += 1
    worksheet.write(0, ind, "Passed audits")
    ind += 1
    worksheet.write(0, ind, "Failed audits")
    ind += 1
    worksheet.write(0, ind, "Total audits")
    ind += 1
    worksheet.write(0, ind, "Manually passed")
    ind += 1
    exercises = results[0]["exercises"]
    for exercise in exercises:
        worksheet.write(0, ind, exercise["name"])
        ind += 1
        worksheet.write(0, ind, "late")
        ind += 1
        worksheet.write(0, ind, "points")
        ind += 1
    logger.debug("START ENUMERATION")
    for index, student in enumerate(results):
        required_late = student["required"]["n_complete_no_deadline"] - student["required"]["n_complete"]
        required_complete = student["required"]["n_complete"]
        bonus_late = student["bonus"]["n_complete_no_deadline"] - student["bonus"]["n_complete"]
        bonus_complete = student["bonus"]["n_complete"]
        optional_complete = student["optional"]["n_complete_no_deadline"]
        ind = 0
        worksheet.write(index + 1, ind, student["lti_user_id"])
        ind += 1
        worksheet.write(index + 1, ind, student["username"])
        ind += 1
        worksheet.write(index + 1, ind, student["first_name"])
        ind += 1
        worksheet.write(index + 1, ind, student["last_name"])
        ind += 1
        worksheet.write(index + 1, ind, required_complete, bold_format)
        ind += 1
        worksheet.write(index + 1, ind, required_late, bold_format)
        ind += 1
        worksheet.write(index + 1, ind, bonus_complete, bold_format)
        ind += 1
        worksheet.write(index + 1, ind, bonus_late, right_border_format)
        ind += 1
        worksheet.write(index + 1, ind, optional_complete)
        ind += 1
        worksheet.write(index + 1, ind, (bonus_complete + required_complete + optional_complete))
        ind += 1
        worksheet.write(index + 1, ind, (bonus_late + required_late))
        ind += 1
        worksheet.write(index + 1, ind, student["passed_audits"])
        ind += 1
        worksheet.write(index + 1, ind, student["failed_by_audits"])
        ind += 1
        worksheet.write(index + 1, ind, student["total_audits"])
        ind += 1
        worksheet.write(index + 1, ind, student["manually_passed"])
        ind += 1
        exercises = student["exercises"]
        for exercise in exercises:
            all_complete = exercise.get("all_complete", 0)
            points = exercise.get("points", "")
            complete_by_deadline = exercise.get("complete_by_deadline", 0)
            worksheet.write(index + 1, ind, complete_by_deadline)
            ind += 1
            worksheet.write(index + 1, ind, all_complete - complete_by_deadline)
            ind += 1
            worksheet.write(index + 1, ind, points)
            ind += 1
    workbook.close()
    output.seek(0)
    xls = output.read()
    fp = open("/tmp/out.xlsx", "wb")
    fp.write(xls)
    fp.close()
    return xls
