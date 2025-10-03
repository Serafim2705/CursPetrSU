from datetime import datetime
from io import BytesIO
import os
import pdfkit

# TODO поменять путь к утилите для построения pdf по html верстке (для линукс bin или dll)
PATH_HTML_TO_PDF = "bin/wkhtmltopdf.exe"
CONTENT_PATH = "E:/files"


# TODO используется упрощенная иерархия папок, если нет желания парсить можно добавить группу, курс и получить
#  структуру как на каппе
def file_exists(filename, username, year):
    file_path = F'{CONTENT_PATH}/reports_storage/{year}/{username}/{filename}'
    return os.path.isfile(file_path)


def get_current_year():
    cur_year = datetime.now().year
    if datetime.now().month < 8:
        cur_year -= 1
    return cur_year


def get_pdf_from_html(html):
    pdf_data = pdfkit.from_string(html, False, configuration=pdfkit.configuration(wkhtmltopdf=PATH_HTML_TO_PDF))
    return BytesIO(pdf_data)


def save_pdf(pdf_content, year, username, file_name):
    os.makedirs(F'{CONTENT_PATH}/reports_storage/{year}/{username}', exist_ok=True)
    with open(F'{CONTENT_PATH}/reports_storage/{year}/{username}/{file_name}.pdf', 'wb') as f:
        f.write(pdf_content)


def delete_pdf(year, username, file_name):
    if not file_exists(F"{file_name}.pdf", username, year):
        return False
    os.remove(F'{CONTENT_PATH}/reports_storage/{year}/{username}/{file_name}.pdf')
    return True
