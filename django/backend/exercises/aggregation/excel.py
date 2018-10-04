import xlsxwriter
import io


def write_xlsx_from_results_list(filename, results):
    xlsx_data = create_xlsx_from_results_list(results)
    with open(filename, 'wb') as f:
        f.write(xlsx_data)


def create_xlsx_from_results_list(results):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    bold_format = workbook.add_format({'bold': True})
    right_border_format = workbook.add_format({'bold': True})
    right_border_format.set_right(1)
    worksheet = workbook.add_worksheet()
    worksheet.write(0, 0, 'Username')
    worksheet.write(0, 1, 'First')
    worksheet.write(0, 2, 'Last')
    worksheet.write(0, 3, 'Obligatory (before deadline)', bold_format)
    worksheet.write(0, 4, 'Bonus (before deadline)', bold_format)
    worksheet.write(0, 5, 'Optional', bold_format)
    worksheet.write(0, 6, 'Total (before deadline)', right_border_format)
    worksheet.write(0, 7, 'Obligatory (no deadline)')
    worksheet.write(0, 8, 'Bonus (no deadline)')
    worksheet.write(0, 9, 'After deadline')
    worksheet.write(0, 10, 'Failed by audit')
    worksheet.write(0, 11, 'Passed audits')
    worksheet.write(0, 12, 'Total audits')
    worksheet.write(0, 13, 'Manually passed')
    worksheet.write(0, 14, 'Total (no deadline)')
    worksheet.write(0, 15, 'Correct answer (no other requirements)')
    for index, student in enumerate(results):
        worksheet.write(index + 1, 0, student['username'])
        worksheet.write(index + 1, 1, student['first_name'])
        worksheet.write(index + 1, 2, student['last_name'])
        worksheet.write(index + 1, 3, student['required']['n_complete'], bold_format)
        worksheet.write(index + 1, 4, student['bonus']['n_complete'], bold_format)
        worksheet.write(index + 1, 5, student['optional'], bold_format)
        worksheet.write(
            index + 1, 6, student['total_complete_before_deadline'], right_border_format
        )
        worksheet.write(index + 1, 7, student['required']['n_complete_no_deadline'])
        worksheet.write(index + 1, 8, student['bonus']['n_complete_no_deadline'])
        worksheet.write(
            index + 1,
            9,
            (
                student['required']['n_complete_no_deadline']
                - student['required']['n_complete']
                + student['bonus']['n_complete_no_deadline']
                - student['bonus']['n_complete']
            ),
        )
        worksheet.write(index + 1, 10, student['failed_by_audits'])
        worksheet.write(index + 1, 11, student['passed_audits'])
        worksheet.write(index + 1, 12, student['total_audits'])
        worksheet.write(index + 1, 13, student['manually_passed'])
        worksheet.write(index + 1, 14, student['total_complete_no_deadline'])
        worksheet.write(index + 1, 15, student['total'])
    workbook.close()
    output.seek(0)
    return output.read()
