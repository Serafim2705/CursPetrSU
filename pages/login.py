from flask_login import LoginManager, login_required, login_user, logout_user
from flask import render_template, request, redirect, url_for, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
import re
from Models import User
from ldap3 import Server, Connection, ALL
from config import *
from datetime import datetime, timedelta

login_routes = Blueprint('login', __name__)

ldap_server = Server(LDAP_SERVER, port=LDAP_PORT,
                     use_ssl=LDAP_USE_SSL, get_info=ALL)


@login_routes.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")

    username = request.form['username']
    print(username)
    password = request.form['password']

    if not re.fullmatch(r'[a-zA-Z]+', username):
        return render_template("login.html", message='Логин должен состоять из букв латинского алфавита')

    user = User.query.filter_by(username=username).first()

    if user and not check_password_hash(user.password, password):
        return render_template("login.html", message='Неверный логин или пароль')

    if not user or (user.last_login and user.last_login < datetime.now().date() - timedelta(days=30)):
        raise NotImplementedError("Подключить ldap")
        # код для авторизации по ldap(работает только на каппе),
        # если авторизация прошла добавляем пользователя в нашу бд и авторизуем его
        c = Connection(ldap_server)
        c.bind()
        c.search(search_base="OU=people,DC=cs,DC=karelia,DC=ru",
                 search_filter="(uid={})".format(username))

        if not c.response:
            c.unbind()
            return render_template("login.html", message='Неверный логин или пароль')

        dn = c.response[0]['dn']

        response_ok = c.rebind(user=dn, password=password)
        c.unbind()
        if not response_ok:
            return render_template("login.html", message='Неверный логин или пароль')

        parts = dn.split(',')
        ous = [part.replace('ou=', '') for part in parts if part.startswith('ou=')]

        group_or_dep = ous[0] if len(ous) > 0 else None
        domen_type = ous[1] if len(ous) > 1 else None

        # print('Группа/кафедра', group_or_dep)
        # print('Домен:', domen_type)

        if not user:
            cn_part = dn.split(',')[0]
            full_name = cn_part.replace('cn=', '')
            names = full_name.split(" ")

            if len(names) >= 2:
                first_name = names[1]
                second_name = names[0]
            else:
                return render_template("login.html", message='Учетные данные не найдены, обратитесь к '
                                                             'администратору')
            third_name = ""
            if len(names) == 3:
                third_name = names[2]

            user = User(username=username, password=generate_password_hash(password),
                        first_name=first_name, second_name=second_name,
                        third_name=third_name, is_student=domen_type == "students")

        user.last_login = datetime.now()
        user.cur_group_or_dep = group_or_dep
        db.session.add(user)
        db.session.commit()

    login_user(user)

    return redirect(url_for('index.index'))


@login_routes.route('/exit')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login.login'))