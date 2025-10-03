from flask_login import login_required, LoginManager, current_user
from flask import Flask, request, redirect, send_file
from pages.index import index_routes
from pages.login import login_routes
from pages.register import reg_routes
from pages.upload import upload_routes
from Models import User
from db import db
from utils import *
from config import *

app = Flask(__name__)
app.register_blueprint(index_routes, url_prefix='/index')
app.register_blueprint(login_routes, url_prefix='/login')
app.register_blueprint(reg_routes, url_prefix='/register')
app.register_blueprint(upload_routes, url_prefix='/upload')

app.secret_key = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///curs_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login.login'


@login_manager.user_loader
def load_user(user_id):
    print(user_id)
    return User.query.get(int(user_id))


@app.route('/download/<username>/<year>/<filename>')
@login_required
def download(filename, username, year):
    file_path = F'{CONTENT_PATH}/reports_storage/{year}/{username}/{filename}'
    if os.path.isfile(file_path):
        return send_file(file_path, as_attachment=False)
    return "Файл не найден", 404


@app.route('/delete/<int:year>', methods=['POST'])
@login_required
def delete_for_year(year):
    if not year:
        return "Неверный год", 400

    doc_type = request.form['for-doc']

    if doc_type not in REPORT_DATA_MAP:
        return 'Неверный тип отчета', 400

    file_name, _, _ = REPORT_DATA_MAP.get(doc_type)

    if delete_pdf(year, current_user.username, file_name):
        return redirect(F'/upload/{year}')

    return 'Файл не найден', 404


@app.route('/list_unreg', methods=['POST', 'GET'])
@login_required
def report_unreg():
    # TODO подтягивать данные с ldap
    return "Здесь будем показывать pdf со студентами, не загрузившими работы"


if __name__ == "__main__":
    app.run(debug=True)
