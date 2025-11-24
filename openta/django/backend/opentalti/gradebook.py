# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

import csv
import io
import os
import logging

from django.core.files.base import ContentFile
from exercises.aggregation import students_results

logger = logging.getLogger(__name__)

import json
CANVAS_STUDENT = "Student"
CANVAS_ID = "ID"
CANVAS_SIS_USER_ID = "SIS User ID"
CANVAS_SIS_LOGIN_ID = "SIS Login ID"
CANVAS_SECTION = "Section"


class GradeBookParseError(Exception):
    """Gradebook parse error"""


def canvas_gradebook_pipeline(task, course, csv_file):
    try:
        parse_canvas_gradebook(task, course, csv_file)
    except Exception as e:
        task.status = str(e)
        task.done = True
        task.save()


def extract_required_fields(row):
    """Extract required fields from row.

    Args:
        row (dict): Row with student data from Canvas

    Returns:
        list: New row containing just the required fields for a result update.

    """
    try:
        new_row = [row[CANVAS_STUDENT], row[CANVAS_ID]]
        if CANVAS_SIS_USER_ID in row:
            new_row.append(row[CANVAS_SIS_USER_ID])
        if CANVAS_SIS_LOGIN_ID in row:
            new_row.append(row[CANVAS_SIS_LOGIN_ID])
        new_row.append(row[CANVAS_SECTION])
    except KeyError:
        raise GradeBookParseError("Invalid Canvas gradebook")

    return new_row


def get_header(row):
    header = [CANVAS_STUDENT, CANVAS_ID]
    if CANVAS_SIS_USER_ID in row:
        header.append(CANVAS_SIS_USER_ID)
    if CANVAS_SIS_LOGIN_ID in row:
        header.append(CANVAS_SIS_LOGIN_ID)
    header.append(CANVAS_SECTION)
    return header


def collect_results(result_for_student):
    csv_results = [
        result_for_student["required"]["n_complete"],
        result_for_student["required"]["n_complete_no_deadline"],
        result_for_student["bonus"]["n_complete"],
        result_for_student["bonus"]["n_complete_no_deadline"],
        result_for_student["optional"]["n_complete_no_deadline"],
    ]
    return csv_results


def get_results_header():
    return ["required-ontime", "required-all", "bonus-ontime", "bonus-all", "optional-all"]


def parse_canvas_gradebook(task, course, file_path):
    # Calculate OpenTA results
    #print(f"PARSE_CANVAS_GRADEBOOK FILE_PATH = {file_path}")
    results = students_results(task=task, course=course, force=True)
    #logger.error(f"RESULTS = {results}")
    fp = open("/tmp/results.json","w");
    s = json.dumps( results );
    fp.write(s);
    fp.close();
    results = [ i for i in results if i.get('lti_user_id',None) != None   ];
    #for i in results :
    #    try :
    #        results_lti_id[i['lti_user_id'] ]= i 
    #    except :
    #        print(f" FAILED {i}")
    #        pass
    #print(f"{results_lti_id}")
    # Create a map with lti_user_id as key
    results_lti_id = {res["lti_user_id"]: res for res in results}
    # Parse and amend gradebook CSV
    n = 0;
    with open(file_path) as file_handle:
        n = n + 1;
        out_file_buffer = io.StringIO(newline="")
        csv_file_in = csv.DictReader(file_handle, delimiter=",")
        csv_file_out = csv.writer(out_file_buffer, delimiter=",")
        try:
            row = next(csv_file_in)
            first_row = row
        except Exception as e:
            raise AssertionError(f"ERROR = {type(e).__name__} {str(e)} ")
        header = get_header(row) + get_results_header()
        csv_file_out.writerow(header)
        #print(f"WRITE HEADER  {header}")
        try:
            if first_row[CANVAS_ID] in results_lti_id:
                new_row = extract_required_fields(first_row)
                new_row = new_row + collect_results(results_lti_id[first_row[CANVAS_ID]])
                #print(f"NEW_ROW = {new_row}")
                csv_file_out.writerow(new_row)
            else :
                if n > 2 : # SKIP REWRITING THE OLD HEADER
                    csv_file_out.writerow(first_row)

        except Exception as e:
            raise AssertionError(f"ERROR in first dataline = {type(e).__name__} {str(e)} ")

        try:
            for row in csv_file_in:
                if row[CANVAS_ID] in results_lti_id:
                    new_row = extract_required_fields(row)
                    new_row = new_row + collect_results(results_lti_id[row[CANVAS_ID]])
                    csv_file_out.writerow(new_row)
                else :
                    new_row = extract_required_fields(row)
                    csv_file_out.writerow(new_row)

        except Exception as e:
            raise AssertionError(f"ERROR {type(e).__name__} {str(e)} {row}  ")
        out_file_buffer.seek(0)
        in_memory_file = ContentFile(out_file_buffer.read())
        in_memory_file.name = course.course_name + ".csv"

        task.result_file = in_memory_file
        task.status = "Complete"
        task.done = True
        task.save()

    # os.unlink(file_path)
