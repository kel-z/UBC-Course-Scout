import asyncio
import json
import random
import sys
import webbrowser
from datetime import datetime

import requests
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QPalette, QIntValidator
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QComboBox, QLineEdit, \
    QCheckBox, QPushButton, QTableView, QHeaderView, QTabWidget, QGroupBox, QFormLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QWidget
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager

APP_NAME = 'UBC Course Scout v1.0'
SAVE_PATH = 'course_data'
URL_TEMPLATE = 'https://courses.students.ubc.ca/cs/courseschedule?' \
               'sesscd={}&pname=subjarea&tname=subj-section&sessyr={}&dept={}&course={}&section={}'

RESPONSE_CODE = {
    0: 'Failed to register',
    1: 'Registration successful',
    2: 'Can register',
    3: 'Section full',
    4: 'Pending refresh',
    5: 'Invalid section',
    6: 'Connection closed error'
}

RESPONSE_COLOUR = {
    0: 'red',
    1: 'green',
    2: 'yellow',
    3: 'grey',
    4: 'light grey',
    5: 'dark red',
    6: 'orange'
}

data = []


def save():
    fp = open(SAVE_PATH, 'w')
    json.dump(data, fp)
    fp.close()


def load():
    try:
        fp = open(SAVE_PATH, 'r')
        global data
        data = json.load(fp)
        fp.close()
    except FileNotFoundError:
        pass


def format_url(course):
    return URL_TEMPLATE.format(course['session'], course['year'], course['dept'], course['course'], course['section'])


def register_format_url(course):
    register_stub = '&submit=Register%20Selected&wldel={}%2C{}%2C{}'
    return format_url(course) + register_stub.format(course['dept'], course['course'], course['section'])


# From https://www.jcchouinard.com/random-user-agent-with-python-and-beautifulsoup/
def get_ua():
    ua_strings = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10) AppleWebKit/600.1.25 (KHTML, like Gecko) Version/8.0 "
        "Safari/600.1.25",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0",
        "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 "
        "Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.1.17 (KHTML, like Gecko) Version/7.1 "
        "Safari/537.85.10",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.104 Safari/537.36"
    ]
    return random.choice(ua_strings)


def get_soup(course):
    headers = {'User-Agent': get_ua()}
    r = requests.get(format_url(course), headers=headers)
    return BeautifulSoup(r.content, "html.parser")


def is_duplicate(course):
    for x in data:
        if "".join(course) == "".join(x[0].values()):
            return True
    return False


def get_seats(course):
    try:
        soup = get_soup(course)
        seats = {}
        for x in soup.find('table', attrs={'class': '\'table'}).contents:
            try:
                seats[x.td.text[0]] = int(x.strong.text)
            except AttributeError:
                pass
            except ValueError:
                pass
        return seats
    except AttributeError:
        return False
    except requests.exceptions.ConnectionError:
        raise requests.exceptions.ConnectionError()


def can_register(seats, opts):
    try:
        available = seats['G']
        if not opts['onlyGeneralSeats']:
            available += seats['R']
        if available > 0:
            return True
        else:
            return False
    except TypeError:
        raise TypeError("Invalid parameters")


async def is_available(course, opts):
    try:
        seats = get_seats(course)
        if not seats:
            return 5
        if can_register(seats, opts):
            return 2
        return 3
    except requests.exceptions.ConnectionError:
        return 6


class UbcAppUi(QWidget):

    def __init__(self):
        super().__init__()

        self.loggedIn = False

        # Tabs setup
        self.model = QStandardItemModel()
        self.setWindowTitle(APP_NAME)
        self.container = QVBoxLayout()

        self.tabs = QTabWidget()
        self.main_tab = QWidget()
        self.settings_tab = QWidget()
        self.tabs.addTab(self.main_tab, "App")
        self.tabs.addTab(self.settings_tab, "Settings")

        self.tab1 = QVBoxLayout()
        self.main_tab.setLayout(self.tab1)

        self.tab2 = QVBoxLayout()
        self.settings_tab.setLayout(self.tab2)

        self.container.addWidget(self.tabs)
        self.setLayout(self.container)

        # Tab 1: Section input
        self.top_groupbox = QGroupBox("Add section")
        self.top_layout = QVBoxLayout()
        self.top_groupbox.setLayout(self.top_layout)

        self.session = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.addItems(["Winter", "Summer"])
        self.year = QLineEdit(placeholderText="Year")
        self.year.setValidator(QIntValidator())
        self.session.addWidget(QLabel("Session:", self), 0)
        self.session.addWidget(self.combo, 1)
        self.session.addWidget(self.year, 2)

        self.section = QHBoxLayout()
        self.dept = QLineEdit(placeholderText="Department")
        self.course = QLineEdit(placeholderText="Course #")
        self.course.setValidator(QIntValidator())
        self.sect = QLineEdit(placeholderText="Section")
        self.section.addWidget(QLabel("Section:", self), 0)
        self.section.addWidget(self.dept, 1)
        self.section.addWidget(self.course, 2)
        self.section.addWidget(self.sect, 3)

        self.submit = QHBoxLayout()
        self.general = QCheckBox("Only general seats")
        self.general.setCheckState(2)
        self.register = QCheckBox("Auto register")
        self.register.setCheckState(0)
        self.add = QPushButton("Add")
        self.add.clicked.connect(
            lambda: self.add_section([self.combo.currentText()[0], self.year.text(), self.dept.text().upper().strip(),
                                      self.course.text().strip(), self.sect.text().upper()],
                                     self.general.isChecked(), self.register.isChecked()))
        self.submit.addWidget(self.general, 0)
        self.submit.addWidget(self.register, 1)
        self.submit.addWidget(self.add, 2)

        self.top_layout.addLayout(self.session)
        self.top_layout.addLayout(self.section)
        self.top_layout.addLayout(self.submit)

        # Tab 1: Table
        self.model.setHorizontalHeaderLabels(['Added courses', 'Status', 'Only general seats', 'Auto register'])
        self.update_model()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 125)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 125)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        # self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.resizeRowToContents(True)
        self.table.clicked.connect(self.handle_click)
        self.pal = QPalette()
        self.pal.setColor(12, QColor('light blue'))
        self.pal.setColor(13, QColor('black'))
        self.table.setPalette(self.pal)

        # Tab 1: Bottom buttons
        self.bottom_layout = QHBoxLayout()

        self.remove = QPushButton("Remove")
        self.remove.clicked.connect(lambda: self.remove_selected_sections(self.table))

        self.reset = QPushButton("Reset all status")
        self.reset.clicked.connect(self.reset_status)

        self.refresh = QPushButton("Refresh")
        self.refresh.clicked.connect(lambda: asyncio.run(self.refresh_and_register()))

        self.bottom_layout.addWidget(self.remove)
        self.bottom_layout.addWidget(self.reset)
        self.bottom_layout.addWidget(self.refresh)

        # Tab 1 setup
        self.tab1.addWidget(self.top_groupbox)
        self.tab1.addWidget(self.table)
        self.tab1.addLayout(self.bottom_layout)
        self.last_refresh = QLabel("Last refresh: ")
        self.tab1.addWidget(self.last_refresh)

        # Tab 2: Login Settings
        self.settings = QVBoxLayout()
        self.groupBoxLogin = QGroupBox("CWL Login")
        self.login = QFormLayout()
        self.usr = QLineEdit()
        self.pw = QLineEdit()
        self.pw.setEchoMode(QLineEdit.Password)
        self.login.addRow(QLabel("Username:"), self.usr)
        self.login.addRow(QLabel("Password:"), self.pw)
        self.testButton = QPushButton("Test Login")
        self.testButton.clicked.connect(lambda: self.test_login([self.usr.text(), self.pw.text()]))
        self.login_status = QLabel("Automatic registration INACTIVE")

        self.settings.addWidget(self.groupBoxLogin)
        self.login.addWidget(self.testButton)
        self.login.addWidget(self.login_status)
        self.groupBoxLogin.setLayout(self.login)

        # Tab 2: Refresh Timer
        self.refresh = QVBoxLayout()
        self.groupBoxRefresh = QGroupBox("Automatic refresh timer")
        self.refresh_settings = QFormLayout()
        self.interval_input = QLineEdit(placeholderText="60")
        self.interval_input.setText("60")
        self.interval_input.setValidator(QIntValidator())
        self.refresh_settings.addRow(QLabel("Refresh interval (seconds):"), self.interval_input)
        self.timerButton = QPushButton("Start")
        self.timerButton.clicked.connect(self.toggle_timer)
        self.refresh_settings.addWidget(self.timerButton)

        self.groupBoxRefresh.setLayout(self.refresh_settings)

        self.refresh.addWidget(self.groupBoxRefresh)

        self.tab2.addLayout(self.settings)
        self.tab2.addLayout(self.refresh)

        self.refreshTimer = QTimer()
        self.refreshTimer.timeout.connect(lambda: asyncio.run(self.refresh_and_register()))

    def clear_inputs(self):
        to_clear = [self.year, self.dept, self.course, self.sect]
        for x in to_clear:
            x.setText("")

    def toggle_timer(self):
        if self.refreshTimer.isActive():
            self.refreshTimer.stop()
            self.interval_input.setEnabled(True)
            self.timerButton.setText("Start")
        else:
            asyncio.run(self.refresh_and_register())
            self.interval_input.setEnabled(False)
            self.timerButton.setText("Stop")
            try:
                self.refreshTimer.start(int(self.interval_input.text()) * 1000)
            except ValueError:
                self.interval_input.setText("60")
                self.refreshTimer.start(60000)

    def reset_status(self):
        for x in range(len(data)):
            data[x][1]['onlyGeneralSeats'] = self.model.item(x, 2).checkState() == 2
            data[x][1]['registerImmediately'] = self.model.item(x, 3).checkState() == 2
            status = {
                'status': 4,
                'response': 'Pending refresh'
            }
            data[x][2] = status
        save()
        self.update_model()

    def handle_click(self, index):
        if index.column() == 0:
            webbrowser.open(format_url(data[index.row()][0]))

    def update_model(self):
        for x in range(0, len(data)):
            course_item = QStandardItem(' '.join(list(data[x][0].values())))
            course_item.setEditable(False)
            course_item.setForeground(QColor('#0074D9'))
            only_general = QStandardItem()
            only_general.setCheckState(2 if data[x][1]['onlyGeneralSeats'] else 0)
            only_general.setCheckable(True)
            auto_register = QStandardItem()
            auto_register.setCheckState(2 if data[x][1]['registerImmediately'] else 0)
            auto_register.setCheckable(True)
            is_registrable = QStandardItem(str(data[x][2]['response']))
            is_registrable.setBackground(QColor(RESPONSE_COLOUR[data[x][2]['status']]))
            is_registrable.setEditable(False)
            self.model.setItem(x, 0, course_item)
            self.model.setItem(x, 2, only_general)
            self.model.setItem(x, 3, auto_register)
            self.model.setItem(x, 1, is_registrable)

    def remove_selected_sections(self, table):
        rows = table.selectionModel().selectedRows()
        for i in sorted(rows, reverse=True):
            self.model.removeRow(i.row())
            del data[i.row()]
        save()

    def add_section(self, course, onlyGen, autoReg):
        if not is_duplicate(course):
            try:
                int(course[1])
                str(course[2])
                int(course[3])
                str(course[4])

                course_info = {
                    'session': course[0],
                    'year': course[1],
                    'dept': course[2],
                    'course': course[3],
                    'section': course[4]
                }

                pref = {
                    'onlyGeneralSeats': onlyGen,
                    'registerImmediately': autoReg
                }

                r = {
                    'response': 'Pending refresh',
                    'status': 4
                }
                data.append([course_info, pref, r])
                self.update_model()
            except ValueError:
                print("Illegal values in input")
        self.clear_inputs()

    def test_login(self, login):
        session = RegisterSession()
        if session.is_valid_login(login):
            self.login_status.setText("Automatic registration ACTIVE")
            self.loggedIn = True
        else:
            self.login_status.setText("Automatic registration INACTIVE (Login failed)")
            self.pw.selectAll()
            self.loggedIn = False

    async def refresh_and_register(self):
        loop = asyncio.get_running_loop()
        registrable = loop.create_future()
        loop.create_task(self.refresh_sections(registrable))
        if await registrable and self.loggedIn:
            session = RegisterSession()
            session.register(registrable.result(), [self.usr.text(), self.pw.text()])
        self.update_model()
        save()

    def update_checked(self):
        for x in range(len(data)):
            data[x][1]['onlyGeneralSeats'] = self.model.item(x, 2).checkState() == 2
            data[x][1]['registerImmediately'] = self.model.item(x, 3).checkState() == 2

    async def refresh_sections(self, fut):
        op = []
        to_refresh = []

        # Filter out unneeded sections (Status code 0, 1, and 5)
        self.update_checked()
        for x in data:
            status = x[2]['status']
            if not (status == 0 or status == 1 or status == 5):
                to_refresh.append(x)

        for x in range(len(to_refresh)):
            task = asyncio.create_task(is_available(to_refresh[x][0], to_refresh[x][1]))
            op.append(task)

        for x in op:
            await x

        registrable = []
        for x in range(len(to_refresh)):
            to_refresh[x][2]['status'] = op[x].result()
            to_refresh[x][2]['response'] = RESPONSE_CODE[op[x].result()]
            if op[x].result() == 2 and to_refresh[x][1]['registerImmediately']:
                registrable.append([to_refresh[x][0], to_refresh[x][2]])

        self.last_refresh.setText("Last refresh: " + str(datetime.now().strftime("%m/%d/%Y %H:%M:%S")))
        fut.set_result(registrable)

    def closeEvent(self, QCloseEvent) -> None:
        self.update_checked()
        save()
        QCloseEvent.accept()


class RegisterSession(object):

    def __init__(self):
        self.driver = webdriver.Edge(EdgeChromiumDriverManager().install())

    def register(self, courses_to_register, login):
        url = "https://cas.id.ubc.ca/ubc-cas/login?TARGET=https%3A%2F%2Fcourses.students.ubc.ca%2Fcs%2Fsecure" \
              "%2Flogin%3FIMGSUBMIT.x%3D20%26IMGSUBMIT.y%3D13"
        self.try_login(url, login)

        # Check for logout button to confirm login
        WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.ID, 'cwl-logout')))

        to_register_urls = []
        for x in courses_to_register:
            to_register_urls.append(register_format_url(x[0]))

        for i in range(len(to_register_urls)):
            self.driver.get(to_register_urls[i])
            try:
                elem = self.driver.find_element_by_class_name("alert.alert-success")
                courses_to_register[i][1]['response'] = elem.get_attribute('innerText').strip('\n')
                courses_to_register[i][1]['status'] = 1
            except NoSuchElementException:
                try:
                    elem = self.driver.find_element_by_class_name("alert.alert-error")
                    courses_to_register[i][1]['response'] = elem.get_attribute('innerText').strip('\n')
                    courses_to_register[i][1]['status'] = 0
                except NoSuchElementException:
                    courses_to_register[i][1]['response'] = 'No response when registering'
                    courses_to_register[i][1]['status'] = 0

        self.driver.quit()

    def try_login(self, url, login):
        self.driver.get(url)
        elem = self.driver.find_elements_by_class_name("required")
        for i in range(2):
            elem[i].clear()
            elem[i].send_keys(login[i])
        elem = self.driver.find_element_by_class_name("btn-submit")
        elem.click()

    def is_valid_login(self, login):
        url = "https://cas.id.ubc.ca/ubc-cas/login"
        self.try_login(url, login)
        element = WebDriverWait(self.driver, 15) \
            .until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span, .alert-success")))
        result = element[0].text
        self.driver.quit()
        return "Log In Successful" in result


def main():
    load()
    ubc_app = QApplication([])
    view = UbcAppUi()
    view.show()
    sys.exit(ubc_app.exec_())


if __name__ == '__main__':
    main()
