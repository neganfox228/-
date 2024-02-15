import sys
import pymysql.cursors
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QPushButton, \
    QDialog, QFormLayout, QLineEdit, QComboBox, QMessageBox, QRadioButton, QGroupBox, QFileDialog, \
    QListWidget, QHBoxLayout, QLabel, QMainWindow
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets


class AddCarDialog(QDialog):
    def __init__(self, car_list, parent=None, connection=None, car_id=None):
        super(AddCarDialog, self).__init__(parent)
        self.setWindowTitle("Добавить авто")
        self.car_list = car_list
        self.connection = connection
        self.car_id = car_id

        layout = QFormLayout(self)

        self.brand_edit = QLineEdit(self)
        self.model_edit = QLineEdit(self)
        self.price_spin = QLineEdit(self)
        self.mileage_spin = QLineEdit(self)
        self.class_combo = QComboBox(self)
        self.transmission_radio_group = QGroupBox("Коробка передач", self)
        self.transmission_radio_layout = QHBoxLayout(self.transmission_radio_group)
        self.type_combo = QComboBox(self)
        self.drive_combo = QComboBox(self)
        self.image_path_edit = QLineEdit(self)
        self.image_path_button = QPushButton("Выбрать", self)
        self.add_button = QPushButton("Добавить", self)

        layout.addRow("Марка:", self.brand_edit)
        layout.addRow("Модель:", self.model_edit)
        layout.addRow("Цена (руб.):", self.price_spin)
        layout.addRow("Пробег (км):", self.mileage_spin)
        layout.addRow("Класс:", self.class_combo)
        layout.addRow(self.transmission_radio_group)
        layout.addRow("Тип автомобиля:", self.type_combo)
        layout.addRow("Привод:", self.drive_combo)
        layout.addRow("Изображение:", self.image_path_edit)
        layout.addRow(self.image_path_button)
        layout.addRow(self.add_button)

        self.transmission_radio_layout.addWidget(QRadioButton("Механическая", self.transmission_radio_group))
        self.transmission_radio_layout.addWidget(QRadioButton("Автомат", self.transmission_radio_group))
        self.transmission_radio_group.setFlat(True)

        self.class_combo.addItems(["Легковой", "Внедорожник"])
        self.type_combo.addItems(["Новый", "С пробегом"])
        self.drive_combo.addItems(["Передний", "Полный", "Задний"])

        self.image_path_button.clicked.connect(self.choose_image)
        self.add_button.clicked.connect(self.add_car)

    def choose_image(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.xpm *.jpg *.bmp)")
        file_dialog.selectFile("*.png")
        if file_dialog.exec_() == QFileDialog.Accepted:
            selected_file = file_dialog.selectedFiles()[0]
            self.image_path_edit.setText(selected_file)

    def add_car(self):
        brand = self.brand_edit.text()
        model = self.model_edit.text()
        price = int(self.price_spin.text())
        class_ = self.class_combo.currentText()

        try:
            transmission = [radio.text() for radio in self.transmission_radio_group.findChildren(QRadioButton) if
                            radio.isChecked()][0]
        except IndexError:
            transmission = ""

        type_ = self.type_combo.currentText()
        mileage = int(self.mileage_spin.text())
        drive = self.drive_combo.currentText()
        image_path = self.image_path_edit.text()

        try:
            with self.connection.cursor() as cursor:
                if self.car_id is None:
                    # Если car_id не установлен, добавляем новую запись
                    sql = "INSERT INTO cars (brand, model, price, mileage, class, transmission, type, drive, image_path) " \
                          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(sql, (brand, model, price, mileage, class_, transmission, type_, drive, image_path))
                else:
                    # Если car_id установлен, обновляем существующую запись
                    sql = "UPDATE cars SET brand=%s, model=%s, price=%s, mileage=%s, class=%s, transmission=%s, " \
                          "type=%s, drive=%s, image_path=%s WHERE id=%s"
                    cursor.execute(sql, (
                    brand, model, price, mileage, class_, transmission, type_, drive, image_path, self.car_id))

                self.connection.commit()

                # Обновляем список автомобилей во вкладке "Автомобили" после добавления/редактирования автомобиля
                self.car_list.clear()
                self.car_list.addItems(self.get_car_list_items())

        except Exception as e:
            print(f"Error adding/editing car to database: {e}")

        self.accept()

    def get_car_list_items(self):
        # Получаем список автомобилей в формате "Марка - Модель"
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT brand, model FROM cars"
                cursor.execute(sql)
                cars_data = cursor.fetchall()

                return [f"{car_data['brand']} - {car_data['model']}" for car_data in cars_data]

        except Exception as e:
            print(f"Error loading cars from database: {e}")
            return []


class SearchDialog(QDialog):
    def __init__(self, parent=None):
        super(SearchDialog, self).__init__(parent)
        self.setWindowTitle("Параметры поиска")

        self.connection = pymysql.connect(host='5.183.188.132', user='db_stud_max_usr',
                                          password='YuYFhr1kjWIcJsDo', db='db_stud_max',
                                          cursorclass=pymysql.cursors.DictCursor)

        layout = QFormLayout(self)

        # Добавьте атрибуты для выпадающих списков
        self.brand_combo = QComboBox(self)
        self.model_combo = QComboBox(self)

        # Добавьте атрибуты для других полей поиска

        self.search_button = QPushButton("Найти", self)

        layout.addRow("Марка:", self.brand_combo)
        layout.addRow("Модель:", self.model_combo)
        layout.addRow(self.search_button)

        # Добавьте обработчик события для заполнения выпадающих списков
        self.brand_combo.addItems(self.get_brand_list())
        self.brand_combo.currentIndexChanged.connect(self.update_model_list)

        # Добавьте обработчик события для кнопки поиска
        self.search_button.clicked.connect(self.accept)

    def get_brand_list(self):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT DISTINCT brand FROM cars"
                cursor.execute(sql)
                brands = [result['brand'] for result in cursor.fetchall()]
                return brands
        except Exception as e:
            print(f"Error loading brand list from database: {e}")
            return []

    def update_model_list(self):
        try:
            selected_brand = self.brand_combo.currentText()
            with self.connection.cursor() as cursor:
                sql = "SELECT DISTINCT model FROM cars WHERE brand = %s"
                cursor.execute(sql, (selected_brand,))
                models = [result['model'] for result in cursor.fetchall()]
                self.model_combo.clear()
                self.model_combo.addItems(models)
        except Exception as e:
            print(f"Error updating model list: {e}")

    def accept(self):
        super(SearchDialog, self).accept()

    def get_search_params(self):

        return {
            'brand': self.brand_combo.currentText() if self.brand_combo.currentText() != "Все" else None,
            'model': self.model_combo.currentText() if self.model_combo.currentText() != "Все" else None
        }


class SellCarDialog(QDialog):
    def __init__(self, car_list, parent=None):
        super(SellCarDialog, self).__init__(parent)
        self.setWindowTitle("Продажа авто")
        self.car_list = car_list

        self.connection = pymysql.connect(host='5.183.188.132', user='db_stud_max_usr',
                                          password='YuYFhr1kjWIcJsDo', db='db_stud_max',
                                          cursorclass=pymysql.cursors.DictCursor)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit(self)
        self.birthdate_edit = QLineEdit(self)
        self.email_edit = QLineEdit(self)
        self.phone_edit = QLineEdit(self)
        self.passport_edit = QLineEdit(self)
        self.address_edit = QLineEdit(self)
        self.confirm_button = QPushButton("Подтвердить", self)

        layout.addRow("ФИО клиента:", self.name_edit)
        layout.addRow("Дата рождения:", self.birthdate_edit)
        layout.addRow("Email:", self.email_edit)
        layout.addRow("Контактный номер:", self.phone_edit)
        layout.addRow("Паспортные данные:", self.passport_edit)
        layout.addRow("Адрес проживания:", self.address_edit)
        layout.addRow(self.confirm_button)

        self.confirm_button.clicked.connect(self.confirm_sale)  # Connect the button to confirm_sale method

    def confirm_sale(self):
        client_data = self.get_client_info()
        selected_item = self.car_list.currentItem()

        if selected_item and client_data:
            car_info = selected_item.text().split(" - ")
            car_brand, car_model = car_info[0], car_info[1]

            try:
                with self.connection.cursor() as cursor:
                    sql_get_car_data = "SELECT * FROM cars WHERE brand = %s AND model = %s"
                    cursor.execute(sql_get_car_data, (car_brand, car_model))
                    car_data = cursor.fetchone()

                    # Вставка данных о продаже в таблицу 'sales'
                    sql_save_sale = "INSERT INTO sales (car_brand, car_model, price, mileage, class, transmission, type, drive, image_path, clients_name) " \
                                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(sql_save_sale,
                                   (car_brand, car_model, car_data['price'], car_data['mileage'], car_data['class'],
                                    car_data['transmission'], car_data['type'], car_data['drive'],
                                    car_data['image_path'], client_data['name']))
                    self.connection.commit()

                    # Обновление списка клиентов во вкладке "Клиенты" после добавления нового клиента
                    # self.update_clients_tab(client_data['name'], client_data['phone'],client_date=self.get_client_info())

                    # Удаление автомобиля из списка после продажи
                    try:
                        with self.connection.cursor() as cursor:
                            # Удаление данных об автомобиле из таблицы cars
                            sql_delete_car = "DELETE FROM cars WHERE brand = %s AND model = %s"
                            cursor.execute(sql_delete_car, (car_brand, car_model))
                            self.connection.commit()
                    except Exception as e:
                        print(f"Error deleting car data after sale: {e}")


            except Exception as e:
                print(f"Error confirming sale: {e}")

            self.accept()

    def get_client_info(self):
        return {
            'name': self.name_edit.text(),
            'birthdate': self.birthdate_edit.text(),
            'email': self.email_edit.text(),
            'phone': self.phone_edit.text(),
            'passport': self.passport_edit.text(),
            'address': self.address_edit.text(),
        }


class EditClientDialog(QDialog):
    def __init__(self, client_info, parent=None):
        super(EditClientDialog, self).__init__(parent)
        self.setWindowTitle("Редактировать клиента")
        self.client_info = client_info.copy()
        self.connection = connection

        self.connection = pymysql.connect(host='5.183.188.132', user='db_stud_max_usr',
                                          password='YuYFhr1kjWIcJsDo', db='db_stud_max',
                                          cursorclass=pymysql.cursors.DictCursor)

        layout = QVBoxLayout(self)

        self.name_edit = QLineEdit(self)
        self.birthdate_edit = QLineEdit(self)
        self.email_edit = QLineEdit(self)
        self.phone_edit = QLineEdit(self)
        self.passport_edit = QLineEdit(self)
        self.address_edit = QLineEdit(self)

        self.name_edit.setText(client_info['name'])
        self.birthdate_edit.setText(client_info['birthdate'])
        self.email_edit.setText(client_info['email'])
        self.phone_edit.setText(client_info['phone'])
        self.passport_edit.setText(client_info['passport'])
        self.address_edit.setText(client_info['address'])

        layout.addWidget(QLabel("ФИО клиента:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Дата рождения:"))
        layout.addWidget(self.birthdate_edit)
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.email_edit)
        layout.addWidget(QLabel("Контактный номер:"))
        layout.addWidget(self.phone_edit)
        layout.addWidget(QLabel("Паспортные данные:"))
        layout.addWidget(self.passport_edit)
        layout.addWidget(QLabel("Адрес проживания:"))
        layout.addWidget(self.address_edit)

        save_button = QPushButton("Сохранить", self)
        save_button.clicked.connect(self.save_edited_client)

        layout.addWidget(save_button)

    def save_edited_client(self):
        edited_info = {
            'name': self.name_edit.text(),
            'birthdate': self.birthdate_edit.text(),
            'email': self.email_edit.text(),
            'phone': self.phone_edit.text(),
            'passport': self.passport_edit.text(),
            'address': self.address_edit.text(),
        }

        try:
            with self.connection.cursor() as cursor:
                sql_update_client = "UPDATE clients SET name=%s, birthdate=%s, email=%s, phone=%s, passport=%s, address=%s WHERE id=%s"
                cursor.execute(sql_update_client, (
                edited_info['name'], edited_info['birthdate'], edited_info['email'], edited_info['phone'],
                edited_info['passport'], edited_info['address'], self.client_info['id']))
                self.connection.commit()

        except Exception as e:
            print(f"Error updating client data in database: {e}")

        self.accept()


class ClientInfoDialog(QDialog):
    def __init__(self, full_client_info, parent=None):
        super(ClientInfoDialog, self).__init__(parent)
        self.setWindowTitle("Информация о клиенте")
        self.full_client_info = full_client_info

        self.connection = pymysql.connect(host='5.183.188.132', user='db_stud_max_usr',
                                          password='YuYFhr1kjWIcJsDo', db='db_stud_max',
                                          cursorclass=pymysql.cursors.DictCursor)

        layout = QVBoxLayout(self)

        # Создаем и добавляем метку для отображения информации о клиенте
        self.info_label = QLabel(self)
        self.update_info_label()
        layout.addWidget(self.info_label)

        # Создаем кнопки "Редактировать" и "Удалить"
        edit_button = QPushButton("Редактировать", self)
        delete_button = QPushButton("Удалить", self)

        # Создаем экземпляр EditClientDialog

        # Подключаем сигнал к методу exec_ экземпляра
        edit_button.clicked.connect(self.edit_client)

        delete_button.clicked.connect(self.delete_client)

        # Добавляем кнопки в макет
        layout.addWidget(edit_button)
        layout.addWidget(delete_button)

    def edit_client(self):
        edit_dialog = EditClientDialog(self.full_client_info)
        if edit_dialog.exec_():
            pass

    def update_info_label(self):
        # Обновляем текст метки с информацией о клиенте
        info_text = f"Имя: {self.full_client_info['name']}\n" \
                    f"Дата рождения: {self.full_client_info['birthdate']}\n" \
                    f"Email: {self.full_client_info['email']}\n" \
                    f"Телефон: {self.full_client_info['phone']}\n" \
                    f"Паспортные данные: {self.full_client_info['passport']}\n" \
                    f"Адрес проживания: {self.full_client_info['address']}"
        self.info_label.setText(info_text)

    def delete_client(self):
        # Предупреждение перед удалением
        warning = QMessageBox.warning(self, "Подтверждение удаления",
                                      "Вы уверены, что хотите удалить этого клиента?",
                                      QMessageBox.Yes | QMessageBox.No)

        if warning == QMessageBox.Yes:
            try:
                # Удаляем клиента из базы данных
                with self.connection.cursor() as cursor:
                    sql_delete_client = "DELETE FROM clients WHERE id=%s"
                    cursor.execute(sql_delete_client, (self.full_client_info['id'],))
                    self.connection.commit()

                QMessageBox.information(self, "Успешно", "Клиент успешно удален.")
                self.accept()  # Закрываем диалог после удаления

            except Exception as e:
                print(f"Error deleting client: {e}")
                QMessageBox.critical(self, "Ошибка", "Ошибка при удалении клиента.")


class ReserveCarDialog(QDialog):
    def __init__(self, car_list, parent=None):
        super(ReserveCarDialog, self).__init__(parent)
        self.setWindowTitle("Резерв авто")
        self.car_list = car_list

        self.connection = pymysql.connect(host='5.183.188.132', user='db_stud_max_usr',
                                          password='YuYFhr1kjWIcJsDo', db='db_stud_max',
                                          cursorclass=pymysql.cursors.DictCursor)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit(self)
        self.birthdate_edit = QLineEdit(self)
        self.email_edit = QLineEdit(self)
        self.phone_edit = QLineEdit(self)
        self.passport_edit = QLineEdit(self)
        self.address_edit = QLineEdit(self)
        self.reserve_button = QPushButton("Зарезервировать", self)

        layout.addRow("ФИО клиента:", self.name_edit)
        layout.addRow("Дата рождения:", self.birthdate_edit)
        layout.addRow("Email:", self.email_edit)
        layout.addRow("Контактный номер:", self.phone_edit)
        layout.addRow("Паспортные данные:", self.passport_edit)
        layout.addRow("Адрес проживания:", self.address_edit)
        layout.addRow(self.reserve_button)

        self.reserve_button.clicked.connect(
            self.reserve_car)  # Подключаем обработчик события для кнопки "Зарезервировать"

    def reserve_car(self):
        client_data = self.get_client_info()
        selected_item = self.car_list.currentItem()

        if selected_item and client_data:
            car_info = selected_item.text().split(" - ")
            car_brand, car_model = car_info[0], car_info[1]

            try:
                with self.connection.cursor() as cursor:
                    # Insert client information into the 'clients_reserve' table
                    sql_insert_client_reserve = "INSERT INTO clients (name, birthdate, email, phone, passport, address) " \
                                                "VALUES (%s, %s, %s, %s, %s, %s)"
                    cursor.execute(sql_insert_client_reserve,
                                   (client_data['name'], client_data['birthdate'], client_data['email'],
                                    client_data['phone'], client_data['passport'], client_data['address']))
                    self.connection.commit()

                    self.accept()

            except Exception as e:
                print(f"Error reserving car: {e}")

    def get_client_info(self):
        return {
            'name': self.name_edit.text(),
            'birthdate': self.birthdate_edit.text(),
            'email': self.email_edit.text(),
            'phone': self.phone_edit.text(),
            'passport': self.passport_edit.text(),
            'address': self.address_edit.text(),
        }


class MyForm(QWidget):
    def __init__(self):
        super(MyForm, self).__init__()

        self.setWindowTitle("Система управления автомобилями")

        self.connection = pymysql.connect(host='5.183.188.132', user='db_stud_max_usr',
                                          password='YuYFhr1kjWIcJsDo', db='db_stud_max',
                                          cursorclass=pymysql.cursors.DictCursor)

        # Создаем вкладки
        tabs = QTabWidget()
        tab_cars = QWidget()
        tab_clients = QWidget()
        tab_reserve = QWidget()
        tab_sales = QWidget()
        tab_account = QWidget()

        self.clients_list = QListWidget()
        self.sales_list = QListWidget()

        # Добавляем вкладки в QTabWidget
        tabs.addTab(tab_cars, "Автомобили")
        tabs.addTab(tab_clients, "Клиенты")
        tabs.addTab(tab_reserve, "Резерв")
        tabs.addTab(tab_sales, "Продажи")
        tabs.addTab(tab_account, "Учетная запись")

        layout_clients = QVBoxLayout(tab_clients)
        layout_clients.addWidget(self.clients_list)

        layout_sales = QVBoxLayout(tab_sales)
        layout_sales.addWidget(self.sales_list)

        self.reserve_list = QListWidget(tab_reserve)
        layout_reserve = QVBoxLayout(tab_reserve)
        layout_reserve.addWidget(self.reserve_list)

        # Размещаем виджет QTabWidget на главном макете
        layout = QVBoxLayout(self)
        layout.addWidget(tabs)

        # Настраиваем вкладку "Автомобили"
        self.setup_cars_tab(tab_cars)

        # Настраиваем вкладку "Продажи"
        self.setup_sales_tab(tab_sales)

        # Настраиваем вкладку "Клиенты"
        self.setup_clients_tab(tab_clients)

        # Настраиваем вкладку "Резерв"
        self.setup_reserv_tab(tab_reserve)

        # Настраиваем вкладку "Учетная запись"
        self.setup_account_tab(tab_account)

    def setup_account_tab(self, tab):
        layout_account = QVBoxLayout(tab)
        try:
            with self.connection.cursor() as cursor:
                # Получаем имя продавца (можно использовать здесь ваш ID продавца)
                seller_id = username  # Пример ID продавца
                sql_get_seller_name = "SELECT name FROM prodavec WHERE Login = %s"
                cursor.execute(sql_get_seller_name, (seller_id,))
                result = cursor.fetchone()
                if result:
                    seller_name = result['name']

                # Получаем количество продаж продавца (используем только тестовые данные)
                sql_get_total_sales = "SELECT COUNT(*) AS total_sales FROM sales"
                cursor.execute(sql_get_total_sales)
                result = cursor.fetchone()
                if result:
                    total_sales = result['total_sales']

        except Exception as e:
            print(f"Error retrieving seller information from the database: {e}")

        if seller_name is not None:
            name_label = QLabel(f"ФИО продавца: {seller_name}")
            layout_account.addWidget(name_label)

        total_sales_label = QLabel(f"Количество проданных машин: {total_sales}")
        layout_account.addWidget(total_sales_label)

        self.exit_button = QPushButton("Выйти", tab)
        layout_account.addWidget(self.exit_button)
        self.exit_button.clicked.connect(self.exit)

    def exit(self):
        self.close()
        self.login = LoginWindow()
        self.login.show()

    def update_cars_tab(self, search_params=None):
        # Метод для обновления данных во вкладке "Автомобили"
        self.load_cars_from_database(search_params)

    def update_sales_tab(self):
        # Метод для обновления данных во вкладке "Продажи"
        self.load_sales_from_database()

    def update_clients_tab(self, name, phone):
        # Метод для обновления данных во вкладке "Клиенты"
        self.setup_clients_tab(name, phone)

    def update_reserved_tab(self):
        # Метод для обновления данных во вкладке "Резерв"
        self.load_reserved_cars_database()

    def load_reserved_cars_database(self):
        # Загрузка данных из базы данных и обновление списка зарезервированных автомобилей
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM cars_reserv"
                cursor.execute(sql)
                reserved_cars_data = cursor.fetchall()

                # Очищаем список перед загрузкой новых данных
                self.reserve_list.clear()

                # Добавляем каждый автомобиль в список
                for reserved_car_data in reserved_cars_data:
                    reserved_car_text = f"{reserved_car_data['car_brand']} - {reserved_car_data['car_model']}"
                    self.reserve_list.addItem(reserved_car_text)

        except Exception as e:
            print(f"Error loading reserved cars from database: {e}")

    def load_clients_from_database(self, name, phone):
        # Загрузка данных из базы данных и обновление списка клиентов
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM clients"
                cursor.execute(sql)
                clients_data = cursor.fetchall()

                # Очистка списка перед загрузкой новых данных
                self.clients_list.clear()

                # Добавление каждого клиента в список
                for client_data in clients_data:
                    client_text = f"{name} - {phone}"
                    self.clients_list.addItem(client_text)
        except Exception as e:
            print(f"Error updating clients tab: {e}")

    def load_sales_from_database(self):
        # Загрузка данных из базы данных и обновление списка продаж
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM sales"
                cursor.execute(sql)
                sales_data = cursor.fetchall()

                # Очистка списка перед загрузкой новых данных
                self.sales_list.clear()

                # Добавление каждой продажи в список
                for sale_data in sales_data:
                    sale_text = f"{sale_data['car_brand']} - {sale_data['car_model']}"
                    self.sales_list.addItem(sale_text)
        except Exception as e:
            print(f"Error loading sales from database: {e}")

    def setup_reserv_tab(self, tab):
        try:
            with self.connection.cursor() as cursor:
                # Загружаем данные о зарезервированных автомобилях из базы данных
                sql = "SELECT car_brand, car_model FROM cars_reserv"
                cursor.execute(sql)
                reserved_cars_data = cursor.fetchall()

                # Очищаем список перед загрузкой новых данных
                self.reserve_list.clear()

                # Добавляем каждый зарезервированный автомобиль в список
                for reserved_car_data in reserved_cars_data:
                    reserved_car_text = f"{reserved_car_data['car_brand']} - {reserved_car_data['car_model']}"
                    self.reserve_list.addItem(reserved_car_text)

        except Exception as e:
            print(f"Error loading reserved cars from database: {e}")

        self.reserve_list.itemDoubleClicked.connect(self.show_reserve_info)

    def show_reserve_info(self, item):
        car_brand, car_model = item.text().split(" - ")

        try:
            with self.connection.cursor() as cursor:
                # Получаем все данные о зарезервированном автомобиле из базы данных
                sql = "SELECT * FROM cars_reserv WHERE car_brand=%s AND car_model=%s"
                cursor.execute(sql, (car_brand, car_model))
                reserved_car_data = cursor.fetchone()

                if reserved_car_data:
                    reserve_info_dialog = QDialog(self)
                    reserve_info_dialog.setWindowTitle(
                        f"Информация о зарезервированном автомобиле: {car_brand} - {car_model}")

                    layout = QVBoxLayout(reserve_info_dialog)

                    info_text = f"Марка: {reserved_car_data['car_brand']}\n" \
                                f"Модель: {reserved_car_data['car_model']}\n" \
                                f"Цена: {reserved_car_data['price']} руб.\n" \
                                f"Пробег: {reserved_car_data['mileage']} км\n" \
                                f"Класс: {reserved_car_data['class']}\n" \
                                f"Трансмиссия: {reserved_car_data['transmission']}\n" \
                                f"Тип автомобиля: {reserved_car_data['type']}\n" \
                                f"Привод: {reserved_car_data['drive']}"

                    info_label = QLabel(info_text, reserve_info_dialog)
                    layout.addWidget(info_label)

                    # Добавляем кнопку "Удалить"
                    remove_button = QPushButton("Удалить", reserve_info_dialog)
                    layout.addWidget(remove_button)

                    # Подключаем обработчик события для кнопки "Удалить"
                    remove_button.clicked.connect(lambda: self.remove_reserved_car(car_brand, car_model))

                    sell_button = QPushButton("Продажа", reserve_info_dialog)
                    layout.addWidget(sell_button)

                    # Подключаем обработчик события для кнопки "Продажа"
                    sell_button.clicked.connect(lambda: self.sell_reserved_car(car_brand, car_model))

                    reserve_info_dialog.exec_()

        except Exception as e:
            print(f"Error loading reserved car data for info: {e}")

    def sell_reserved_car(self, car_brand, car_model):
        try:
            with self.connection.cursor() as cursor:
                # Получаем данные о зарезервированном автомобиле
                sql_get_reserved_car = "SELECT * FROM cars_reserv WHERE car_brand=%s AND car_model=%s"
                cursor.execute(sql_get_reserved_car, (car_brand, car_model))
                reserved_car_data = cursor.fetchone()

                if reserved_car_data:
                    # Удаляем запись из таблицы cars_reserv
                    sql_remove_from_reserved = "DELETE FROM cars_reserv WHERE car_brand=%s AND car_model=%s"
                    cursor.execute(sql_remove_from_reserved, (car_brand, car_model))

                    # Вставляем данные об автомобиле в таблицу sales
                    sql_insert_into_sales = "INSERT INTO sales (car_brand, car_model, price, mileage, class, transmission, type, drive, image_path, clients_name) " \
                                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(sql_insert_into_sales,
                                   (car_brand, car_model, reserved_car_data['price'], reserved_car_data['mileage'],
                                    reserved_car_data['class'], reserved_car_data['transmission'],
                                    reserved_car_data['type'],
                                    reserved_car_data['drive'], reserved_car_data['image_path'],
                                    reserved_car_data['clients_name']))
                    self.connection.commit()

                    # Обновляем данные во вкладке "Резерв"
                    self.load_reserved_cars_from_database()
                    self.update_sales_tab()

        except Exception as e:
            print(f"Error selling reserved car: {e}")

    def remove_reserved_car(self, car_brand, car_model):
        try:
            with self.connection.cursor() as cursor:
                # Получаем данные о зарезервированном автомобиле
                sql_get_reserved_car = "SELECT * FROM cars_reserv WHERE car_brand=%s AND car_model=%s"
                cursor.execute(sql_get_reserved_car, (car_brand, car_model))
                reserved_car_data = cursor.fetchone()

                if reserved_car_data:
                    # Удаляем запись из таблицы cars_reserv
                    sql_remove_from_reserved = "DELETE FROM cars_reserv WHERE car_brand=%s AND car_model=%s"
                    cursor.execute(sql_remove_from_reserved, (car_brand, car_model))

                    # Вставляем данные об автомобиле в таблицу cars
                    sql_insert_into_cars = "INSERT INTO cars (brand, model, price, mileage, class, transmission, type, drive, image_path) " \
                                           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(sql_insert_into_cars,
                                   (car_brand, car_model, reserved_car_data['price'], reserved_car_data['mileage'],
                                    reserved_car_data['class'], reserved_car_data['transmission'],
                                    reserved_car_data['type'],
                                    reserved_car_data['drive'], reserved_car_data['image_path']))
                    self.connection.commit()

                    # Обновляем данные во вкладке "Резерв"
                    self.load_reserved_cars_from_database()
                    self.update_reserved_tab()
                    self.update_cars_tab()
                    self.update_sales_tab()


        except Exception as e:
            print(f"Error removing reserved car: {e}")

    def setup_cars_tab(self, tab):
        # Создаем список автомобилей
        self.car_list = QListWidget(tab)

        # Создаем кнопки
        add_car_button = QPushButton("Добавить авто", tab)
        search_car_button = QPushButton("Поиск", tab)
        cancel_button = QPushButton("Отменить поиск", tab)

        # Размещаем список, кнопки и элементы управления на вкладке
        layout = QVBoxLayout(tab)
        layout.addWidget(self.car_list)
        layout.addWidget(add_car_button)
        layout.addWidget(search_car_button)
        layout.addWidget(cancel_button)

        # Добавляем обработчики событий для кнопок
        add_car_button.clicked.connect(self.show_add_car_dialog)
        search_car_button.clicked.connect(self.show_search_dialog)
        cancel_button.clicked.connect(self.cancel_search)

        # Создаем обработчик события для двойного щелчка на элементе списка
        self.car_list.itemDoubleClicked.connect(self.show_car_options)

        # Загружаем данные из базы данных и отображаем только марку и модель
        self.load_cars_from_database()

    def load_cars_from_database(self, search_params=None):
        try:
            with self.connection.cursor() as cursor:
                # Постройте запрос в зависимости от параметров поиска
                sql = "SELECT brand, model FROM cars"
                conditions = []

                if search_params:
                    if search_params['brand'] and search_params['brand'] != "Все":
                        conditions.append(f"brand = '{search_params['brand']}'")

                    if search_params['model'] and search_params['model'] != "Все":
                        conditions.append(f"model = '{search_params['model']}'")

                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)

                cursor.execute(sql)
                cars_data = cursor.fetchall()

                # Очищаем список перед загрузкой новых данных
                self.car_list.clear()

                # Добавляем каждую марку и модель в список
                for car_data in cars_data:
                    car_text = f"{car_data['brand']} - {car_data['model']}"
                    self.car_list.addItem(car_text)

        except Exception as e:
            print(f"Error loading cars from database: {e}")

    def cancel_search(self):
        self.update_cars_tab()

    def setup_sales_tab(self, tab):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM sales"
                cursor.execute(sql)
                sales_data = cursor.fetchall()

                for sale_data in sales_data:
                    sale_text = f"{sale_data['car_brand']} - {sale_data['car_model']}"
                    self.sales_list.addItem(sale_text)

        except Exception as e:
            print(f"Error loading sales from database: {e}")

        self.sales_list.itemDoubleClicked.connect(self.show_sale_info)

    def show_sale_info(self, item):
        sale_info = item.text().split(" - ")

        try:
            with self.connection.cursor() as cursor:
                # Получаем все данные о продаже из базы данных
                sql = "SELECT * FROM sales WHERE car_brand=%s AND car_model=%s"
                cursor.execute(sql, (sale_info[0], sale_info[1]))
                sale_data = cursor.fetchone()

                if sale_data:
                    options_dialog = QDialog(self)
                    options_dialog.setWindowTitle(f"Информация о продаже: {sale_info[0]} - {sale_info[1]}")

                    layout = QVBoxLayout(options_dialog)

                    # Отображение изображения
                    image_label = QLabel(options_dialog)
                    pixmap = QPixmap(sale_data['image_path'])
                    image_label.setPixmap(pixmap.scaledToWidth(300))  # Произвольная ширина
                    layout.addWidget(image_label)

                    info_text = f"Марка: {sale_data['car_brand']}\n" \
                                f"Модель: {sale_data['car_model']}\n" \
                                f"Цена: {sale_data['price']} руб.\n" \
                                f"Пробег: {sale_data['mileage']} км\n" \
                                f"Класс: {sale_data['class']}\n" \
                                f"Трансмиссия: {sale_data['transmission']}\n" \
                                f"Тип автомобиля: {sale_data['type']}\n" \
                                f"Привод: {sale_data['drive']}\n" \
                                f"Имя клиента: {sale_data['clients_name']}"

                    info_label = QLabel(info_text, options_dialog)
                    layout.addWidget(info_label)

                    options_dialog.exec_()

        except Exception as e:
            print(f"Error loading sale data for info: {e}")

    def show_add_car_dialog(self):
        dialog = AddCarDialog(self.car_list, self, connection=self.connection)
        dialog.exec_()

    def show_search_dialog(self):
        search_dialog = SearchDialog(self)
        if search_dialog.exec_():
            search_params = search_dialog.get_search_params()
            print(f"Выполнен поиск с параметрами: {search_params}")
            self.load_cars_from_database(search_params)

    def show_car_options(self, item):
        brand, model = item.text().split(" - ")

        try:
            with self.connection.cursor() as cursor:
                # Получаем все данные об автомобиле из базы данных
                sql = "SELECT * FROM cars WHERE brand=%s AND model=%s"
                cursor.execute(sql, (brand, model))
                car_data = cursor.fetchone()

                if car_data:
                    options_dialog = QDialog(self)
                    options_dialog.setWindowTitle(f"Опции автомобиля: {brand} - {model}")

                    layout = QVBoxLayout(options_dialog)

                    # Отображение изображения
                    image_label = QLabel(options_dialog)
                    pixmap = QPixmap(car_data['image_path'])
                    image_label.setPixmap(pixmap.scaledToWidth(300))  # Произвольная ширина
                    layout.addWidget(image_label)

                    info_text = f"Марка: {car_data['brand']}\n" \
                                f"Модель: {car_data['model']}\n" \
                                f"Цена: {car_data['price']} руб.\n" \
                                f"Пробег: {car_data['mileage']} км\n" \
                                f"Класс: {car_data['class']}\n" \
                                f"Трансмиссия: {car_data['transmission']}\n" \
                                f"Тип автомобиля: {car_data['type']}\n" \
                                f"Привод: {car_data['drive']}"

                    info_label = QLabel(info_text, options_dialog)
                    layout.addWidget(info_label)

                    edit_button = QPushButton("Редактировать", options_dialog)
                    sell_button = QPushButton("Продажа", options_dialog)
                    reserve_button = QPushButton("Зарезервировать", options_dialog)

                    layout.addWidget(edit_button)
                    layout.addWidget(sell_button)
                    layout.addWidget(reserve_button)

                    edit_button.clicked.connect(lambda: self.show_edit_car_dialog(brand, model))
                    sell_button.clicked.connect(self.show_sell_dialog)
                    reserve_button.clicked.connect(self.show_reserve_dialog)

                    options_dialog.exec_()

        except Exception as e:
            print(f"Error loading car data for options: {e}")

    def show_reserve_dialog(self):
        selected_item = self.car_list.currentItem()

        if selected_item:
            reserve_dialog = ReserveCarDialog(self.car_list, self)
            reserve_dialog.setWindowTitle("Резерв авто")

            if reserve_dialog.exec_():
                client_info = reserve_dialog.get_client_info()

                # Get the car information
                car_info = selected_item.text().split(" - ")
                car_brand, car_model = car_info[0], car_info[1]

                # Add reserved car's data to the 'Reserve' list in the UI
                self.reserve_list.addItem(f"{car_brand} - {car_model}")

                try:
                    with self.connection.cursor() as cursor:
                        sql_get_car_data = "SELECT * FROM cars WHERE brand = %s AND model = %s"
                        cursor.execute(sql_get_car_data, (car_brand, car_model))
                        car_data = cursor.fetchone()

                        # Вставляем данные о резервации в таблицу 'cars_reserve'
                        sql_save_reserve = "INSERT INTO cars_reserv (car_brand, car_model, price, mileage, class, transmission, " \
                                           "type, drive, image_path, clients_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql_save_reserve, (car_brand, car_model, car_data['price'], car_data['mileage'],
                                                          car_data['class'], car_data['transmission'], car_data['type'],
                                                          car_data['drive'], car_data['image_path'],
                                                          client_info['name']))
                        self.connection.commit()

                        # Удаляем автомобиль из таблицы 'cars' после резервации
                        sql_delete_car = "DELETE FROM cars WHERE brand = %s AND model = %s"
                        cursor.execute(sql_delete_car, (car_brand, car_model))
                        self.connection.commit()

                        # Обновляем список зарезервированных автомобилей на вкладке "Резерв"
                        self.load_reserved_cars_from_database()
                        self.update_reserved_tab()
                        self.update_cars_tab()
                        self.update_clients_tab(client_info['name'], client_info['phone'])
                        self.update_sales_tab()


                except Exception as e:
                    print(f"Error reserving car: {e}")

    def load_reserved_cars_from_database(self):
        try:
            with self.connection.cursor() as cursor:
                # Загружаем данные о зарезервированных автомобилях из базы данных
                sql = "SELECT car_brand, car_model FROM cars_reserv"
                cursor.execute(sql)
                reserved_cars_data = cursor.fetchall()

                # Очищаем список перед загрузкой новых данных
                self.reserve_list.clear()

                # Добавляем каждый зарезервированный автомобиль в список
                for reserved_car_data in reserved_cars_data:
                    reserved_car_text = f"{reserved_car_data['car_brand']} - {reserved_car_data['car_model']}"
                    self.reserve_list.addItem(reserved_car_text)

        except Exception as e:
            print(f"Error loading reserved cars from database: {e}")

    def show_car_info(self, item):
        brand, model = item.text().split(" - ")

        try:
            with self.connection.cursor() as cursor:
                # Получаем все данные об автомобиле из базы данных
                sql = "SELECT * FROM cars WHERE brand=%s AND model=%s"
                cursor.execute(sql, (brand, model))
                car_data = cursor.fetchone()

                if car_data:
                    info_dialog = QDialog(self)
                    info_dialog.setWindowTitle(f"Информация об автомобиле: {brand} - {model}")

                    layout = QVBoxLayout(info_dialog)

                    info_text = f"Марка: {car_data['brand']}\n" \
                                f"Модель: {car_data['model']}\n" \
                                f"Цена: {car_data['price']} руб.\n" \
                                f"Пробег: {car_data['mileage']} км\n" \
                                f"Класс: {car_data['class']}\n" \
                                f"Трансмиссия: {car_data['transmission']}\n" \
                                f"Тип автомобиля: {car_data['type']}\n" \
                                f"Привод: {car_data['drive']}\n" \
                                f"Изображение: {car_data['image_path']}"

                    info_label = QLabel(info_text, info_dialog)
                    layout.addWidget(info_label)

                    info_dialog.exec_()

        except Exception as e:
            print(f"Error loading car data for info: {e}")

    def show_edit_car_dialog(self, brand, model):
        try:
            with self.connection.cursor() as cursor:
                # Получаем все данные об автомобиле из базы данных
                sql = "SELECT * FROM cars WHERE brand=%s AND model=%s"
                cursor.execute(sql, (brand, model))
                car_data = cursor.fetchone()

                if car_data:
                    # Создаем диалог редактирования
                    edit_dialog = AddCarDialog(self.car_list, self, connection=self.connection, car_id=car_data['id'])
                    edit_dialog.setWindowTitle("Редактировать авто")

                    # Заполняем поля диалога текущими значениями из базы данных
                    edit_dialog.brand_edit.setText(car_data['brand'])
                    edit_dialog.model_edit.setText(car_data['model'])
                    edit_dialog.price_spin.setText(str(car_data['price']))
                    edit_dialog.mileage_spin.setText(str(car_data['mileage']))
                    edit_dialog.class_combo.setCurrentText(car_data['class'])

                    transmission_radio = edit_dialog.transmission_radio_group.findChildren(QRadioButton,
                                                                                           f"text={car_data['transmission']}")
                    if transmission_radio:
                        transmission_radio[0].setChecked(True)

                    edit_dialog.type_combo.setCurrentText(car_data['type'])
                    edit_dialog.drive_combo.setCurrentText(car_data['drive'])
                    edit_dialog.image_path_edit.setText(car_data['image_path'])

                    # Подключаем обработчик события для сохранения изменений
                    edit_dialog.add_button.clicked.connect(edit_dialog.add_car)

                    # Отображаем диалог редактирования
                    edit_dialog.exec_()

        except Exception as e:
            print(f"Error loading car data for editing: {e}")

    def save_edited_car(self, edit_dialog, car_id):
        brand = edit_dialog.brand_edit.text()
        model = edit_dialog.model_edit.text()
        price = int(edit_dialog.price_spin.text())
        class_ = edit_dialog.class_combo.currentText()

        try:
            transmission = [radio.text() for radio in edit_dialog.transmission_radio_group.findChildren(QRadioButton) if
                            radio.isChecked()][0]
        except IndexError:
            transmission = ""

        type_ = edit_dialog.type_combo.currentText()
        mileage = int(edit_dialog.mileage_spin.text())
        drive = edit_dialog.drive_combo.currentText()
        image_path = edit_dialog.image_path_edit.text()

        try:
            with self.connection.cursor() as cursor:
                # Обновляем данные в базе данных
                sql = "UPDATE cars SET brand=%s, model=%s, price=%s, mileage=%s, class=%s, transmission=%s, " \
                      "type=%s, drive=%s, image_path=%s WHERE id=%s"
                cursor.execute(sql,
                               (brand, model, price, mileage, class_, transmission, type_, drive, image_path, car_id))
                self.connection.commit()

                # Обновляем список автомобилей во вкладке "Автомобили" после редактирования
                self.load_cars_from_database()

        except Exception as e:
            print(f"Error updating car data in database: {e}")

    def show_sell_dialog(self):
        selected_item = self.car_list.currentItem()

        if selected_item:
            sell_dialog = SellCarDialog(self.car_list, self)
            sell_dialog.setWindowTitle("Продажа авто")

            if sell_dialog.exec_():
                client_info = sell_dialog.get_client_info()

                # Get the car information
                car_info = selected_item.text().split(" - ")
                car_brand, car_model = car_info[0], car_info[1]

                try:
                    with self.connection.cursor() as cursor:
                        # Insert client information into the database
                        sql_insert_client = "INSERT INTO clients (name, birthdate, email, phone, passport, address) VALUES (%s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql_insert_client, (
                        client_info['name'], client_info['birthdate'], client_info['email'], client_info['phone'],
                        client_info['passport'], client_info['address']))
                        self.connection.commit()

                except Exception as e:
                    print(f"Error selling car: {e}")

        self.setup_account_tab()

    def setup_clients_tab(self, tab):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM clients"
                cursor.execute(sql)
                clients_data = cursor.fetchall()

                for client_data in clients_data:
                    client_text = f"{client_data['name']} - {client_data['phone']}"
                    self.clients_list.addItem(client_text)

        except Exception as e:
            print(f"Error loading clients from database: {e}")

        # Добавьте обработчик события для двойного щелчка на элементе списка клиентов
        self.clients_list.itemDoubleClicked.connect(self.show_client_info)

    def show_client_info(self, item):
        # Получите имя и номер телефона клиента из элемента списка
        client_info = item.text().split(" - ")
        client_name, client_phone = client_info[0], client_info[1]

        # Загрузите полную информацию о клиенте из базы данных
        full_client_info = self.load_client_info_from_database(client_name, client_phone)

        # Отобразите полную информацию о клиенте в диалоговом окне
        if full_client_info:
            client_info_dialog = ClientInfoDialog(full_client_info, self)
            client_info_dialog.exec_()

    def load_client_info_from_database(self, client_name, client_phone):
        try:
            with self.connection.cursor() as cursor:
                # Получите полную информацию о клиенте из базы данных
                sql = "SELECT * FROM clients WHERE name=%s AND phone=%s"
                cursor.execute(sql, (client_name, client_phone))
                full_client_info = cursor.fetchone()
                return full_client_info
        except Exception as e:
            print(f"Error loading full client info from database: {e}")
            return None

    def update_clients_tab(self, client_name, client_phone):
        self.clients_list.addItem(f"{client_name} - {client_phone}")

    def show_sell_dialog(self):
        selected_item = self.car_list.currentItem()

        if selected_item:
            sell_dialog = SellCarDialog(self.car_list, self)
            sell_dialog.setWindowTitle("Продажа авто")

            if sell_dialog.exec_():
                client_info = sell_dialog.get_client_info()

                car_info = selected_item.text().split(" - ")
                car_brand, car_model = car_info[0], car_info[1]

                self.car_list.takeItem(self.car_list.row(selected_item))

                self.sales_list.addItem(f"{car_brand} - {car_model}")

                try:
                    with self.connection.cursor() as cursor:
                        sql_insert_client = "INSERT INTO clients (name, birthdate, email, phone, passport, address) VALUES (%s, %s, %s, %s, %s, %s)"
                        cursor.execute(sql_insert_client, (
                        client_info['name'], client_info['birthdate'], client_info['email'], client_info['phone'],
                        client_info['passport'], client_info['address']))
                        self.connection.commit()

                        self.update_clients_tab(client_info['name'], client_info['phone'])

                except Exception as e:
                    print(f"Error selling car: {e}")


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Авторизация продавца')
        self.setGeometry(100, 100, 300, 150)

        self.username_label = QLabel('Логин:')
        self.username_input = QLineEdit()

        self.password_label = QLabel('Пароль:')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton('Войти')
        self.login_button.clicked.connect(self.authenticate)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def authenticate(self):
        global username
        username = self.username_input.text()
        password = self.password_input.text()

        try:
            self.connection = pymysql.connect(host='5.183.188.132', user='db_stud_max_usr',
                                              password='YuYFhr1kjWIcJsDo', db='db_stud_max',
                                              cursorclass=pymysql.cursors.DictCursor)

            cursor = connection.cursor()
            cursor.execute("SELECT * FROM prodavec WHERE Login=%s AND Password=%s", (username, password))

            if cursor.fetchone():
                self.close()
                self.open_main_window()
            else:
                QMessageBox.warning(self, 'Ошибка', 'Логин или пароль введены неверно.')
        except pymysql.connect.Error as error:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при подключении к БД: {error}')

    def open_main_window(self):
        # app = QApplication(db_stud_max.argv)
        self.main_window = MyForm()
        self.main_window.show()
        # db_stud_max.exit(app.exec_())


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # MySQL connection parameters
    host = '5.183.188.132'
    user = 'db_stud_max_usr'
    password = 'YuYFhr1kjWIcJsDo'
    db = 'db_stud_max'

    # Establish a connection to the MySQL database
    connection = pymysql.connect(host=host, user=user, password=password, db=db, cursorclass=pymysql.cursors.DictCursor)

    form = LoginWindow()
    form.connection = connection  # Pass the connection to the form
    form.show()
    sys.exit(app.exec_())
