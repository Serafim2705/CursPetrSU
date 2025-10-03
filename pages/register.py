from Models import Courseworks
from utils import get_current_year
from config import *
from db import db
from types import SimpleNamespace
from flask import render_template, request, Blueprint
from flask_login import current_user, login_required
from datetime import datetime

reg_routes = Blueprint('register', __name__)


@reg_routes.route('/', methods=['GET'])
@login_required
def reg_get_years():
    available_years = Courseworks.query.filter(Courseworks.student == current_user.username) \
        .group_by(Courseworks.year).order_by(Courseworks.year.desc()).all()

    av_years = [e.year for e in available_years]
    cur_year = get_current_year()

    if cur_year not in av_years:
        available_years.insert(0, Courseworks(year=cur_year))

    return render_template("register_work.html", stud_name=current_user.first_name, available_years=available_years)


@reg_routes.route('/<int:year>', methods=['POST', 'GET'])
@login_required
def reg_for_year(year):
    cur_work = Courseworks.query.filter(Courseworks.student == current_user.username,
                                        Courseworks.year == year).first()

    is_new_work = not cur_work and get_current_year() == year

    if not is_new_work and not cur_work:
        return f"Работа за {year}г. не найдена", 404

    if request.method == 'GET':
        if is_new_work:
            cur_work = SimpleNamespace(tutor_pos="", tutor_rank="", group=current_user.cur_group_or_dep,
                                       year=year, tutor_name="")

        return render_template("register_work_form.html", stud_name=current_user.first_name,
                               is_new_work=is_new_work, message=None, work_data=cur_work,
                               tutor_positions=TUTOR_POSITIONS, tutor_ranks=TUTOR_RANKS)

    if request.method == 'POST':
        data = request.form

        if data.get('copy'):
            # Копируем данные прошлого года
            last_work = Courseworks.query.filter(Courseworks.student == current_user.username,
                                                 Courseworks.year != year).order_by(Courseworks.year.desc()).first()
            if not last_work:
                new_work = SimpleNamespace(tutor_pos="", tutor_rank="", group=current_user.cur_group_or_dep,
                                           year=year, tutor_name="")

                return render_template("register_work_form.html", stud_name=current_user.first_name,
                                       work_data=new_work, tutor_positions=TUTOR_POSITIONS, tutor_ranks=TUTOR_RANKS,
                                       is_new_work=False, message="Данных по прошлым работам не найдено!")
            prev_year = last_work.year
            last_work.year = get_current_year()
            last_work.group = current_user.cur_group_or_dep

            return render_template("register_work_form.html", stud_name=current_user.first_name, work_data=last_work,
                                   is_new_work=False, tutor_positions=TUTOR_POSITIONS, tutor_ranks=TUTOR_RANKS,
                                   message=f"Получены данные за {prev_year} учебный год, чтобы "
                                           f"зарегистрировать новую работу подтвердите отправку!")

        error_message = None

        tutor_name = data.get('adviser-name')
        if not tutor_name:
            error_message = 'Не указаны ФИО руководителя!'
        tutor_pos = data.get('adviser-position')
        if tutor_pos not in TUTOR_POSITIONS:
            error_message = 'Неверная должность руководителя!'
        tutor_status = data.get('adviser-status')
        tutor_rank = data.get('adviser-rank').strip()
        if tutor_rank not in TUTOR_RANKS and tutor_rank != "":
            error_message = "Некорректное звание руководителя"
        department = data.get('department')
        if department not in DEP_LIST:
            error_message = "Неверная кафедра "
        title = data.get('title')
        if not title or title == " ":
            error_message = 'Не указана тема курсовой!'

        if error_message:
            received_work = SimpleNamespace(tutor_pos=tutor_pos, tutor_rank=tutor_rank,
                                            group=current_user.cur_group_or_dep,
                                            year=year, tutor_name=tutor_name, departament=department, title=title)

            return render_template("register_work_form.html", stud_name=current_user.first_name,
                                   is_new_work=is_new_work,
                                   work_data=received_work, tutor_positions=TUTOR_POSITIONS, tutor_ranks=TUTOR_RANKS,
                                   message=error_message)
        if is_new_work:
            new_work = Courseworks(student=current_user.username, studentName=get_name_initials(),
                                   year=year, title=title, tutor_name=tutor_name, group=current_user.cur_group_or_dep,
                                   tutor_pos=tutor_pos, tutor_status=tutor_status, tutor_rank=tutor_rank,
                                   departament=department, date_reg=datetime.now())
            db.session.add(new_work)
            db.session.commit()

            return render_template("register_work_form.html", stud_name=current_user.first_name,
                                   work_data=new_work, is_new_work=False,
                                   tutor_positions=TUTOR_POSITIONS, tutor_ranks=TUTOR_RANKS,
                                   message="Работа успешно загружена!")

        if get_current_year() == cur_work.year:
            cur_work.group = current_user.cur_group_or_dep
            # TODO подгрузка актуальной группы с ldap?

        cur_work.title = title
        cur_work.tutor_name = tutor_name
        cur_work.tutor_pos = tutor_pos
        cur_work.tutor_status = tutor_status
        cur_work.tutor_rank = tutor_rank
        cur_work.departament = department

        db.session.add(cur_work)
        db.session.commit()

        return render_template("register_work_form.html", stud_name=current_user.first_name, is_new_work=False,
                               work_data=cur_work, tutor_positions=TUTOR_POSITIONS, tutor_ranks=TUTOR_RANKS,
                               message="Данные успешно обновлены!")


def get_name_initials():
    third_name_initial = ''
    if current_user.third_name:
        third_name_initial = f"{current_user.third_name[0].upper()}. "
    return f"{current_user.first_name[0].upper()}. {third_name_initial}{current_user.second_name}"
