from Models import Courseworks
from config import *
from db import db
from flask import render_template, request, Blueprint
from flask_login import current_user, login_required
from datetime import datetime
from utils import file_exists, save_pdf


upload_routes = Blueprint('upload', __name__)


@upload_routes.route('/', methods=['GET'])
@login_required
def load():
    available_years = Courseworks.query.filter(Courseworks.student == current_user.username) \
        .group_by(Courseworks.year).order_by(Courseworks.year.desc()).all()

    return render_template("load.html",
                           stud_name=current_user.first_name,
                           available_years=available_years)


@upload_routes.route('/<int:year>', methods=['POST', 'GET'])
@login_required
def load_for_year(year):
    cur_work = Courseworks.query.filter(Courseworks.student == current_user.username,
                                        Courseworks.year == year).first()
    if not cur_work:
        return "Работа за указанный год не найдена", 404

    if not cur_work.year or not cur_work.departament or not cur_work.group:
        return "Данные по работе неполные или были повреждены, требуется зарегистрировать работу повторно или " \
               "обратиться к администратору", 404

    if request.method == 'GET':
        return render_template("load_form.html", stud_name=current_user.first_name, file_exists=file_exists,
                               word_data=cur_work, course=cur_work.group[2:3], message=None)

    doc_type = request.form['for-doc']

    if doc_type not in REPORT_DATA_MAP:
        return 'Неверный тип отчета', 400
    file_name, update_bit, target_curs = REPORT_DATA_MAP.get(doc_type)

    if target_curs and str(cur_work.group[2:3]) not in target_curs:
        return "Недоступно для текущего курса", 400

    pdf_file = request.files['doc-file']
    if not pdf_file:
        return "Файл не загружен", 400

    pdf_file_name = pdf_file.filename.lower()
    if not (pdf_file_name.endswith('.pdf') and pdf_file.mimetype == 'application/pdf'):
        return "Неверный тип файла, ожидается PDF", 400

    pdf_content = pdf_file.read()
    save_pdf(pdf_content, year, current_user.username, file_name)

    cur_curs = cur_work.group[2:3]
    date_format = "%d.%m.%y"
    prev_in_time = cur_work.in_time
    if not prev_in_time:
        prev_in_time = "00000000"
    if update_bit in [0, 1]:
        deadline_str = DEADLINES["interim_reports_date"][cur_curs]
    else:
        deadline_str = DEADLINES["final_reports_date"][cur_curs]

    deadline_year = cur_work.year if int(deadline_str[3:5]) > 7 else cur_work.year + 1
    deadline_str += f".{str(deadline_year)[2:4]}"
    deadline_date_target = datetime.strptime(deadline_str, date_format)
    print(f"now: {datetime.now()}, deadline: {deadline_date_target}")

    if deadline_date_target > datetime.now():
        prev_in_time = prev_in_time[:update_bit] + '1' + prev_in_time[update_bit + 1:]
        cur_work.in_time = prev_in_time
    else:
        prev_in_time = prev_in_time[:update_bit] + '0' + prev_in_time[update_bit + 1:]
        cur_work.in_time = prev_in_time

    db.session.add(cur_work)
    db.session.commit()

    return render_template("load_form.html", stud_name=current_user.first_name, file_exists=file_exists,
                           word_data=cur_work, course=cur_work.group[2:3], message=file_name)