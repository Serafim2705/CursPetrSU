from flask import Blueprint, redirect, url_for, render_template, request, send_file
from Models import Courseworks
from flask_login import current_user, login_required
from utils import file_exists, get_current_year, get_pdf_from_html
from sqlalchemy import or_, and_


index_routes = Blueprint('index', __name__)


@index_routes.route('/', methods=['POST', 'GET'])
@login_required
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login.login'))

    if request.method == 'GET':
        return render_template("index.html", curr_year=get_current_year())

    and_conditions = []
    year_filter = []
    group_filter = []

    if request.form['name'] != '':
        st_name = request.form.get('name').strip()
        if st_name[0].islower() and len(st_name) > 2:
            st_name = st_name[0].upper() + st_name[1:]

        and_conditions.append(Courseworks.studentName.like(f"%{st_name}%"))
    if request.form['adviser-name'] != '':
        t_name = request.form.get('adviser-name').strip()
        if t_name[0].islower() and len(t_name) > 2:
            t_name = t_name[0].upper() + t_name[1:]

        and_conditions.append(Courseworks.tutor_name.like(f"%{t_name}%"))
    if request.form['department'] != '':
        and_conditions.append(Courseworks.departament == request.form['department'])

    is_flatten = False

    if request.form['years'] != '':
        years = request.form.getlist('years')
        if len(years) > 1:
            year_filter = [Courseworks.year == year1 for year1 in years]
        else:
            and_conditions.append(Courseworks.year == request.form['years'])

    if request.form['groups'] != '':
        grps = request.form.getlist('groups')
        if len(grps) > 1:
            group_filter = [Courseworks.group == grp for grp in grps]
        else:
            and_conditions.append(Courseworks.group == request.form['groups'])

    if year_filter:
        conditions = or_(*year_filter), and_(*and_conditions)
    else:
        conditions = and_conditions
    if group_filter:
        conditions = or_(*group_filter), and_(*conditions)

    if request.form['group-method'] == 'flatten':
        is_flatten = True

    if request.form['sort-method'] == 'by-student-name':
        if request.form['sort-order'] == 'ascending':
            response = Courseworks.query.filter(*conditions).order_by(Courseworks.year,
                                                                      Courseworks.studentName).all()
        else:
            response = Courseworks.query.filter(*conditions).order_by(Courseworks.year,
                                                                      Courseworks.studentName.desc()).all()
    elif request.form['sort-method'] == 'by-adviser-name':
        if request.form['sort-order'] == 'ascending':
            response = Courseworks.query.filter(*conditions).order_by(Courseworks.year,
                                                                      Courseworks.tutor_name).all()
        else:
            response = Courseworks.query.filter(*conditions).order_by(Courseworks.year,
                                                                      Courseworks.tutor_name.desc()).all()
    else:
        if request.form['sort-order'] == 'ascending':
            response = Courseworks.query.filter(*conditions).order_by(Courseworks.year, Courseworks.date_reg,
                                                                      Courseworks.group).all()
        else:
            response = Courseworks.query.filter(*conditions).order_by(Courseworks.year.desc(),
                                                                      Courseworks.date_reg.desc(),
                                                                      Courseworks.group).all()

    answer = {}
    count_dict = {}
    detail_level = 1
    button_id = request.form.get('button')
    if not is_flatten or button_id == 'Отчет':
        for e in response:
            answer.setdefault(e.year, {}) \
                .setdefault(e.departament, {}) \
                .setdefault(e.group, []) \
                .append({
                "title": e.title,
                "name": e.studentName,
                "tutor": e.tutor_name,
                "student": e.student,
                "in_time": e.in_time
            })

        # Подсчет записей
        for _year in answer.keys():
            recs_per_year = 0
            count_dict[_year] = {}
            for _dep in answer[_year].keys():
                recs_per_dep = 0
                count_dict[_year][_dep] = {}
                for _group in answer[_year][_dep].keys():
                    recs_per_group = len(answer[_year][_dep][_group])
                    count_dict[_year][_dep][_group] = recs_per_group
                    recs_per_dep += recs_per_group
                count_dict[_year][_dep]['count'] = recs_per_dep
                recs_per_year += recs_per_dep
            count_dict[_year]['count'] = recs_per_year

    else:
        curs = {}
        for e in response:
            curs[str(e.group)[2:3]] = 1

        if "6" in curs.keys() and len(curs.keys()) == 1:
            detail_level = 3
        elif "4" in curs.keys() and len(curs.keys()) == 1:
            detail_level = 2
        answer = response

    # print("запрос за ", time.time() - st_time1)
    if len(answer) == 0:
        return render_template("index.html", curr_year=get_current_year(),
                               message='По указанным фильтрам не нашлось работ!')

    if button_id == 'Отчет':

        html = render_template("report_pdf_template.html", data=answer, file_exists=file_exists,
                               count_data=count_dict)
        pdf_bytes = get_pdf_from_html(html)

        if not pdf_bytes:
            return 'Ошибка построения отчета', 500

        return send_file(pdf_bytes,
                         download_name='report.pdf',
                         as_attachment=False,
                         mimetype='application/pdf')

    return render_template("index.html", data=answer, count_data=count_dict, flatten=is_flatten,
                           curr_year=get_current_year(), _anchor='start_table', file_exists=file_exists,
                           detail_level=detail_level, total_count=len(answer))