import xlsxwriter
import io


def write_xlsx_from_results_list(filename, results):
    xlsx_data = create_xlsx_from_results_list(results)
    with open(filename, 'wb') as f:
        f.write(xlsx_data)


def create_xlsx_from_results_list(results):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()
    worksheet.write(0, 0, 'Username')
    worksheet.write(0, 1, 'First')
    worksheet.write(0, 2, 'Last')
    worksheet.write(0, 3, 'Obligatory (answer correct and image)')
    worksheet.write(0, 4, 'Obligatory (answer correct before deadline and image)')
    worksheet.write(0, 5, 'Obligatory (answer correct and image before deadline)')
    worksheet.write(0, 6, 'Bonus (answer correct and image)')
    worksheet.write(0, 7, 'Bonus (answer correct before deadline and image)')
    worksheet.write(0, 8, 'Bonus (answer correct and image before deadline)')
    worksheet.write(0, 9, 'Optional')
    worksheet.write(0, 10, 'After deadline')
    worksheet.write(0, 11, 'Failed by audit')
    worksheet.write(0, 12, 'Passed audits')
    worksheet.write(0, 13, 'Total audits')
    worksheet.write(0, 14, 'Manually passed')
    worksheet.write(0, 15, 'Total (Correct exercises)')
    for index, student in enumerate(results):
        worksheet.write(index + 1, 0, student['username'])
        worksheet.write(index + 1, 1, student['first_name'])
        worksheet.write(index + 1, 2, student['last_name'])
        worksheet.write(index + 1, 3, student['required']['n_correct'])
        worksheet.write(index + 1, 4, student['required']['n_deadline'])
        worksheet.write(index + 1, 5, student['required']['n_image_deadline'])
        worksheet.write(index + 1, 6, student['bonus']['n_correct'])
        worksheet.write(index + 1, 7, student['bonus']['n_deadline'])
        worksheet.write(index + 1, 8, student['bonus']['n_image_deadline'])
        worksheet.write(index + 1, 9, student['optional'])
        worksheet.write(
            index + 1,
            10,
            (
                student['required']['n_correct']
                - student['required']['n_image_deadline']
                + student['bonus']['n_correct']
                - student['bonus']['n_image_deadline']
            ),
        )
        worksheet.write(index + 1, 11, student['failed_by_audits'])
        worksheet.write(index + 1, 12, student['passed_audits'])
        worksheet.write(index + 1, 13, student['total_audits'])
        worksheet.write(index + 1, 14, student['manually_passed'])
        worksheet.write(index + 1, 15, student['total'])
    workbook.close()
    output.seek(0)
    return output.read()
