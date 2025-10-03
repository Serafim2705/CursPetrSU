import unittest
from app import app
from db import db
from Models import Courseworks, User
from bs4 import BeautifulSoup
import tracemalloc
from werkzeug.security import generate_password_hash


def add_test_content(db_context):
    db_context.session.add(Courseworks(year='2012', title='test', group='22605',
                                       departament='ИМО', student="test_student1"))
    db_context.session.add(Courseworks(year='2012', title='test', group='22605',
                                       departament='ПМиК', student="test_student2"))
    db_context.session.add(Courseworks(year='2012', title='test', group='22405',
                                       departament='ИМО', student="test_student3"))
    # существующая работа для проверки валидности ссылок
    db_context.session.add(Courseworks(year='2022', title='test_data_with_valid_url', group='22505',
                                       departament='ИМО', student="serov"))
    db_context.session.commit()


class MyTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # tracemalloc.start()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_db.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        cls.app = app.test_client()
        cls.app.testing = True
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost:5432/test_db'
        with app.app_context():
            db.drop_all()
            db.create_all()
            test_user = User(username='test', first_name='ivan', second_name="ivanov", third_name='ivanovich',
                             password=generate_password_hash("123"),
                             cur_group_or_dep='22605')
            db.session.add(test_user)
            db.session.commit()
            # Добавляем "фикстуры"
            add_test_content(db_context=db)
            # Авторизуем тестового студента
            cls.app.post('/login', data=dict(username='test', password='123'), follow_redirects=True)
            # with cls.app.session_transaction() as sess:
            #     sess.clear()
        # db.init_app(app)

    @classmethod
    def tearDownClass(cls):
        # snapshot = tracemalloc.take_snapshot()
        # top_stats = snapshot.statistics('lineno')

        # for stat in top_stats[:10]:
        #     print(stat)

        # tracemalloc.stop()
        with app.app_context():
            cls.app.get('/login/exit')
            # db.session.remove()
            # Чистим тестовую базу
            db.drop_all()

    def test_login_negative(self):
        self.app.get('/login/exit')
        self.app.cookie_jar.clear()
        response = self.app.post('/login', data={"username": "incorrect", "password": "123"}, follow_redirects=True)

        self.assertIn('Неверный логин или пароль', response.text)

    def test_login_negative_2(self):
        self.app.get('/login/exit')
        self.app.cookie_jar.clear()
        response = self.app.post('/login', data={"username": "test_incorrect", "password": "123"}, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        self.assertIn('Логин должен состоять из букв латинского алфавита', response.text)

    def test_login_positive(self):
        response = self.app.post('/login', data={"username": "test", "password": "123"})
        self.assertEqual(response.status_code, 308)

    def test_login_positive_with_redirect(self):
        response = self.app.post('/login', data={"username": "test", "password": "123"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request.path, '/index/')

    def test_index_route(self):
        response = self.app.get('/index', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Поиск и просмотр работ', response.text)

    def test_index_post_valid_links(self):
        response = self.app.post('/index', data={"years": "",
                                                 "groups": "",
                                                 "department": "",
                                                 "name": '',
                                                 "adviser-name": '',
                                                 "have-index": "registered",
                                                 "group-method": "default",
                                                 "sort-method": "by-student-name",
                                                 "button": "Найти",
                                                 "sort-order": "ascending"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Поиск и просмотр работ', response.text)

        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        tables = soup.find_all('table')
        if not tables:
            raise Exception("Отсутствуют данные")
        table = tables[0]
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            for cell in cells:
                links = cell.find_all('a')
                if links:
                    href = links[0].get('href')
                    doc_content = self.app.get(href)
                    with doc_content:
                        content_type = doc_content.headers.get('content-type')
                        self.assertIn('application/pdf', content_type)

    def test_index_post_empty_resp(self):
        response = self.app.post('/index', data={"years": "2010",
                                                 "groups": "",
                                                 "department": "",
                                                 "name": '',
                                                 "adviser-name": '',
                                                 "have-index": "registered",
                                                 "group-method": "default",
                                                 "sort-method": "by-student-name",
                                                 "button": "Найти",
                                                 "sort-order": "ascending"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('По указанным фильтрам не нашлось работ!', response.text)

    def test_index_post_broken_req(self):
        response = self.app.post('/index', data={"years": "2010",
                                                 "sort-order": "ascending"}, follow_redirects=True)
        self.assertEqual(response.status_code, 400)

    def test_index_post_data_consistency(self):
        req_data = {"years": "",
                    "groups": "",
                    "department": "",
                    "name": '',
                    "adviser-name": '',
                    "have-index": "registered",
                    "group-method": "flatten",
                    "sort-method": "by-student-name",
                    "button": "Найти",
                    "sort-order": "ascending"}
        response = self.app.post('/index', data=req_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # print(response.text)
        with app.app_context():
            count = len(Courseworks.query.all())
        if not count:
            raise Exception("Нет данных для тестов")

        self.assertIn(f'Всего работ: {count}', response.text)

        test_year = "2012"
        req_data['years'] = test_year
        response = self.app.post('/index', data=req_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            count = len(Courseworks.query.filter_by(year=test_year).all())

        self.assertIn(f'Всего работ: {count}', response.text)

        test_dep = "ИМО"
        req_data['department'] = test_dep
        response = self.app.post('/index', data=req_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            count = len(Courseworks.query.filter_by(year=test_year, departament=test_dep).all())
        self.assertIn(f'Всего работ: {count}', response.text)

        test_group = "22405"
        req_data['groups'] = test_group
        response = self.app.post('/index', data=req_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            count = len(Courseworks.query.filter_by(year=test_year, departament=test_dep, group=test_group).all())
        self.assertIn(f'Всего работ: {count}', response.text)

    def test_index_post_report(self):
        req_data = {"years": "",
                    "groups": "",
                    "department": "",
                    "name": '',
                    "adviser-name": '',
                    "have-index": "registered",
                    "group-method": "flatten",
                    "sort-method": "by-student-name",
                    "button": "Отчет",
                    "sort-order": "ascending"}
        response = self.app.post('/index', data=req_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with response:
            content_type = response.headers.get('content-type')
            self.assertIn('application/pdf', content_type)


if __name__ == '__main__':
    unittest.main()
