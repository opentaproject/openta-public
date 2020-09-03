import os

from django.core.files.base import ContentFile
import csv
import io

from exercises.aggregation import student_statistics_exercises, students_results

CANVAS_STUDENT = 'Student'
CANVAS_ID = 'ID'
CANVAS_SIS_USER_ID = 'SIS User ID'
CANVAS_SIS_LOGIN_ID = 'SIS Login ID'
CANVAS_SECTION = 'Section'


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
        result_for_student['required']['n_complete'],
        result_for_student['required']['n_complete_no_deadline'],
        result_for_student['bonus']['n_complete'],
        result_for_student['bonus']['n_complete_no_deadline'],
    ]
    return csv_results


def get_results_header():
    return ["required-ontime", "required-all", "bonus-ontime", "bonus-all"]


def parse_canvas_gradebook(task, course, file_path):
    # Calculate OpenTA results
    results = students_results(task=task, course=course, force=True)

    # Create a map with lti_user_id as key
    results_lti_id = {res['lti_user_id']: res for res in results}

    # Parse and amend gradebook CSV
    with open(file_path) as file_handle:
        out_file_buffer = io.StringIO(newline='')
        csv_file_in = csv.DictReader(file_handle, delimiter=',')
        csv_file_out = csv.writer(out_file_buffer, delimiter=',')
        row = next(csv_file_in)
        header = get_header(row) + get_results_header()
        csv_file_out.writerow(header)
        for row in csv_file_in:
            if row[CANVAS_ID] in results_lti_id:
                new_row = extract_required_fields(row)
                new_row = new_row + collect_results(results_lti_id[row[CANVAS_ID]])
                csv_file_out.writerow(new_row)

        out_file_buffer.seek(0)
        in_memory_file = ContentFile(out_file_buffer.read())
        in_memory_file.name = ".csv"

        task.result_file = in_memory_file
        task.status = "Complete"
        task.done = True
        task.save()

    os.unlink(file_path)
