# -*- coding: utf-8 -*-

"""
Program: Color Master
Author: MrCrawL
Created Time: 2024-04-28
Last Modified: 2024-05-02
PS. 2024-05-01 by MrCrawL: Realize some basic functions
    2024-05-02 by MrCrawL: Optimize code and modify UI. Add color illustrator
    2024-05-03 by MrCrawL: Optimize UI
"""

''' TIP: Only Support Primary Screen '''

import sys, os
from time import localtime
import pyautogui
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout, QLabel, QScrollArea, QMessageBox
from PyQt6.QtGui import QPixmap, QIcon, QIntValidator, QTextCursor
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from colormaster_ui import Ui_Form
from mr_ico import icon_hex  # fixme: comment this line, or it might raise Exception
from pynput.keyboard import Listener


if getattr(sys, 'frozen', False):
    FILE_PATH = os.path.join(os.path.dirname(sys.executable), os.path.basename(sys.executable))
else:
    FILE_PATH = os.path.abspath(__file__)
FILE_DIRNAME = os.path.dirname(FILE_PATH)

WIDTH, HEIGHT = pyautogui.size()

class MonitorThread(QThread):
    rgbSignal = pyqtSignal(int, int, int)
    textSignal = pyqtSignal(int, int, int)

    def __init__(self):
        super().__init__()
        self.isMonitor = False

    def run(self):
        while self.isMonitor:
            x, y = pyautogui.position()
            if x < 0: x = 0
            elif x >= WIDTH: x = WIDTH
            if y < 0: y = 0
            elif y >= HEIGHT: y = HEIGHT
            r, g, b = pyautogui.pixel(x, y)
            self.rgbSignal.emit(r, g, b)
            self.textSignal.emit(r, g, b)


class Window(QWidget, Ui_Form):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 设置窗口图标 fixme: comment the following 4 lines, or it might raise Exception
        self.pixmap = QPixmap()
        self.pixmap.loadFromData(bytes.fromhex(icon_hex))
        self.icon = QIcon(self.pixmap)
        self.setWindowIcon(self.icon)

        # 设置窗口外观
        self.setWindowTitle('Color Master')
        self.setFixedSize(self.width(), self.height())
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.buttonPick.setAutoDefault(True)
        self.buttonPick.setFocus()

        # 输入整数验证
        intValidator = QIntValidator(0, 255)
        self.lineEdit_R.setValidator(intValidator)
        self.lineEdit_G.setValidator(intValidator)
        self.lineEdit_B.setValidator(intValidator)

        # 绑定信号
        self.lineEdit_R.returnPressed.connect(lambda: self.get_input_rgb(self.lineEdit_R))
        self.lineEdit_G.returnPressed.connect(lambda: self.get_input_rgb(self.lineEdit_G))
        self.lineEdit_B.returnPressed.connect(lambda: self.get_input_rgb(self.lineEdit_B))
        self.lineEdit_Hex.returnPressed.connect(self.get_input_hex)
        self.lineEdit_R.textChanged.connect(lambda: self.lineEdit_change(self.lineEdit_R))
        self.lineEdit_G.textChanged.connect(lambda: self.lineEdit_change(self.lineEdit_G))
        self.lineEdit_B.textChanged.connect(lambda: self.lineEdit_change(self.lineEdit_B))
        self.lineEdit_Hex.textChanged.connect(self.hex_change)
        self.buttonShow.clicked.connect(self.get_input_rgb)
        self.buttonPick.clicked.connect(self.toggle_monitor)
        self.buttonRecord.clicked.connect(self.record_rgb)
        self.buttonSave.clicked.connect(self.save_log)
        self.buttonClear.clicked.connect(self.clear_log)
        self.buttonIllustrator.clicked.connect(self.toggle_illustrator)

        # 线程设置
        self.monitorThread = MonitorThread()
        self.monitorThread.rgbSignal.connect(self.set_label_color)
        self.monitorThread.textSignal.connect(self.set_lineEdit_text)

        # 监听键盘
        self.listener = Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()
        self.is_R_pressed = False

        # 颜色展示
        self.illustrator = ColorIllustrator()
        self.illustrator.closed.connect(self.illustrator_close)
        self.ill_x = None
        self.ill_y = None
        # self.pos_x = self.illustrator.x()
        # self.pos_y = self.illustrator.y()

    # def moveEvent(self, event):
    #     """颜色展示跟随主窗口移动"""
    #     position = QPoint(event.pos().x() - self.pos_x + self.illustrator.pos().x(),
    #                       event.pos().y() - self.pos_y + self.illustrator.pos().y())
    #     self.illustrator.move(position)
    #     self.pos_x = event.pos().x()
    #     self.pos_y = event.pos().y()

    def illustrator_close(self):
        self.buttonIllustrator.setText('Show Illustrator')

    def toggle_illustrator(self):
        if self.illustrator.isHidden():
            if not self.ill_x or not self.ill_y:
                self.illustrator.setGeometry(self.x() + self.width(), self.y() + 30,
                                             self.illustrator.width(), self.illustrator.height())
            else:
                self.illustrator.setGeometry(self.ill_x, self.ill_y + 30,
                                             self.illustrator.width(), self.illustrator.height())
            self.illustrator.show()
            self.buttonIllustrator.setText('Hide Illustrator')
            self.activateWindow()
        else:
            self.ill_x = self.illustrator.x()
            self.ill_y = self.illustrator.y()
            self.illustrator.hide()
            self.buttonIllustrator.setText('Show Illustrator')

    def save_log(self):
        filename = f'ColorMaster-RGB-log-{get_time()}.txt'
        filepath = os.path.join(FILE_DIRNAME, filename)
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(self.textEdit_log.toPlainText())

    def on_press(self, key):
        if hasattr(key, 'char'):
            if key.char == 'r' and not self.is_R_pressed:
                self.is_R_pressed = True
                self.buttonRecord.click()

    def on_release(self, key):
        if hasattr(key, 'char'):
            if key.char == 'r' and self.is_R_pressed:
                self.is_R_pressed = False

    @staticmethod
    def to_hex(r: int, g:int, b:int):
        hex_string = f'#{hex(int(r))[2:].zfill(2)}{hex(int(g))[2:].zfill(2)}{hex(int(b))[2:].zfill(2)}'.upper()
        return hex_string

    def record_rgb(self):
        r = self.lineEdit_R.text()
        g = self.lineEdit_G.text()
        b = self.lineEdit_B.text()
        h = self.to_hex(r, g, b)
        text = f'rgb({r}, {g}, {b})  {h}'
        self.textEdit_log.append(text)
        cursor = self.textEdit_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.textEdit_log.setTextCursor(cursor)
        self.illustrator.add_label(int(r), int(g), int(b))

    def clear_log(self):
        self.textEdit_log.setText('')
        self.illustrator.delete_all_labels()

    def set_label_color(self, r: int, g: int, b: int):
        self.label_color.setStyleSheet(f'background: rgb({r}, {g}, {b});')

    def set_lineEdit_text(self, r: int, g: int, b: int):
        self.lineEdit_R.setText(str(r))
        self.lineEdit_G.setText(str(g))
        self.lineEdit_B.setText(str(b))
        self.lineEdit_Hex.setText(self.to_hex(r, g, b))

    def toggle_monitor(self):
        if self.monitorThread.isMonitor:
            self.buttonPick.setText('Start Pick Color')
            self.monitorThread.isMonitor = False
        else:
            self.buttonPick.setText('Stop Pick Color')
            self.monitorThread.isMonitor = True
            self.monitorThread.start()

    def get_input_rgb(self, line_edit: QLineEdit):
        r = self.validate_rgb(self.lineEdit_R)
        g = self.validate_rgb(self.lineEdit_G)
        b = self.validate_rgb(self.lineEdit_B)
        self.lineEdit_Hex.setText(self.to_hex(r, g, b))
        self.set_label_color(r, g, b)
        line_edit.selectAll()

    def get_input_hex(self):
        input_string = self.lineEdit_Hex.text().upper()
        self.lineEdit_Hex.selectAll()
        if len(input_string) == 7:
            r_hex = input_string[1:3]
            g_hex = input_string[3:5]
            b_hex = input_string[5:]
            try:
                r = int(r_hex, 16)
                g = int(g_hex, 16)
                b = int(b_hex, 16)
                self.set_label_color(r, g, b)
                return None
            except Exception:
                pass
        self.error_hex()

    def error_hex(self):
        msgBox = QMessageBox()
        msgBox.setWindowIcon(self.icon) # fixme: comment this line, or it might raise Exception
        msgBox.setWindowTitle('Notification')
        msgBox.setIcon(QMessageBox.Icon.Information)
        msgBox.setText('Wrong color hex! Please check and try again.')
        msgBox.addButton(QMessageBox.StandardButton.Ok)
        msgBox.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        msgBox.exec()

    def hex_change(self):
        text = self.lineEdit_Hex.text().upper()
        if text:
            if text[0] != '#':
                self.lineEdit_Hex.setText('#' + self.lineEdit_Hex.text())

    def hideEvent(self, a0):
        self.illustrator.hide()
        self.buttonIllustrator.setText('Open Illustrator')
        a0.accept()

    def closeEvent(self, a0):
        self.illustrator.close()
        a0.accept()

    @staticmethod
    def validate_rgb(line_edit: QLineEdit):
        text = line_edit.text()
        if text:
            if int(text) > 255:
                line_edit.setText('255')
                return 255
            line_edit.setText(str(int(text)))
            return int(text)
        line_edit.setText('0')
        return 0

    @staticmethod
    def lineEdit_change(line_edit: QLineEdit):
        text = line_edit.text()
        if text:
            if int(text) > 255:
                line_edit.setText('255')
            while len(text) > 1 and text[0] == '0':
                text = text[1:]
                line_edit.setText(text)


class ColorIllustrator(QWidget):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()

        # fixme: comment the following 4 lines, or it might raise Exception
        self.pixmap = QPixmap()
        self.pixmap.loadFromData(bytes.fromhex(icon_hex))
        self.icon = QIcon(self.pixmap)
        self.setWindowIcon(self.icon)

        self.setWindowTitle('Color')
        self.setFixedSize(200, 320)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, False)

        # Create a scroll area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        # Create a widget to contain the labels
        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)

        # Create a layout for the content widget
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Set the layout of the content widget
        self.content_widget.setLayout(self.layout)

        # Set the main layout of the window
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.scroll_area)
        self.setLayout(self.main_layout)

        self.labels = []

    def add_label(self, r: int, g: int, b: int):
        label = QLabel(f'rgb({r}, {g}, {b})')
        label.setFixedHeight(20)
        label.setAlignment(Qt.AlignmentFlag.AlignRight)
        fontColor = cal_color(r, g, b)
        label.setStyleSheet(f'background: rgb({r}, {g}, {b}); color: {fontColor};')
        self.layout.addWidget(label)
        self.labels.append(label)
        scroll_bar = self.scroll_area.verticalScrollBar()
        if scroll_bar:
            scroll_bar.setValue(scroll_bar.maximum())

    def delete_all_labels(self):
        for label in self.labels:
            self.layout.removeWidget(label)
            label.deleteLater()
        self.labels = []

    def closeEvent(self, a0):
        self.hide()
        self.closed.emit()


def cal_color(r: int, g: int, b: int):
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    if luminance > 0.5:
        return 'black'
    else:
        return 'white'


def get_time():
    year = str(localtime().tm_year).zfill(4)
    month = str(localtime().tm_mon).zfill(2)
    day = str(localtime().tm_mday).zfill(2)
    hour = str(localtime().tm_hour).zfill(2)
    minute = str(localtime().tm_min).zfill(2)
    sec = str(localtime().tm_sec).zfill(2)
    date = f'{year}{month}{day}-{hour}{minute}{sec}'
    return date


def main():
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()