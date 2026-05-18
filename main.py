import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
import webbrowser
import zipfile
import ctypes

import requests
from PySide6.QtCore import Qt, QTimer, Signal, qInstallMessageHandler
from PySide6.QtGui import QFont, QIcon, QPainter, QColor, QImage, QPixmap, QTextCursor

def qt_message_handler(mode, context, message):
    if "QThreadStorage" not in message: 
        sys.stdout.write(f"{message}\n")
qInstallMessageHandler(qt_message_handler)

from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton,
    QProgressBar, QRadioButton, QScrollArea, QSizePolicy, QStackedWidget,
    QTextEdit, QVBoxLayout, QWidget, QFileDialog, QMessageBox
)

if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(os.path.realpath(sys.executable))
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

bin_path = os.path.join(base_dir, "bin").replace("\\", "/")
os.environ["PATH"] = bin_path + os.pathsep + os.environ.get("PATH", "")

CURRENT_THEME = "dark" 

THEMES = {
    "dark": {
        "bg": "#181a1f", "card": "#21252b", "input": "#15171b", "input2": "#16191f",
        "border": "#3a3f4b", "blue": "#1f538d", "blue_hover": "#2464aa", "blue_dark": "#14375e",
        "button": "#2c313a", "button_hover": "#353b46", "combo_button": "#2c3e50",
        "text": "#f0f4ff", "muted": "#9aa4b2", "muted2": "#7e8794", "danger": "#a94442",
    },
    "light": {
        "bg": "#ffffff", "card": "#f0f2f5", "input": "#ffffff", "input2": "#e4e6eb",
        "border": "#ccd0d5", "blue": "#3ba1ff", "blue_hover": "#288ce6", "blue_dark": "#1d4ed8",
        "button": "#f0f2f5", "button_hover": "#e4e6eb", "combo_button": "#e4e6eb", 
        "text": "#1c1e21", "muted": "#606770", "muted2": "#8d949e", "danger": "#ff5252",
    }
}
COLORS = THEMES[CURRENT_THEME]

def apply_theme_titlebar(window):
    if sys.platform == "win32":
        try:
            hwnd = window.winId().__int__()
            if CURRENT_THEME == "dark":
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(ctypes.c_int(0x001F1A18)), 4)
            else:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(0)), 4)
                # 🔻 Cor alterada para Branco Puro (0x00FFFFFF)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(ctypes.c_int(0x00FFFFFF)), 4) 
        except Exception: pass

def center_window(window):
    screen_center = QApplication.primaryScreen().availableGeometry().center()
    frame_geo = window.frameGeometry()
    frame_geo.moveCenter(screen_center)
    window.move(frame_geo.topLeft())

def set_app_icon(app):
    for icon_path in ("bin/icon.ico", "bin/icon.png", "bin/logo.png"):
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            break

def apply_ui_ux_cursors(window):
    for widget_class in [QPushButton, QComboBox]:
        for widget in window.findChildren(widget_class):
            widget.setCursor(Qt.CursorShape.PointingHandCursor)

    for widget_class in [QCheckBox, QRadioButton]:
        for widget in window.findChildren(widget_class):
            widget.setCursor(Qt.CursorShape.PointingHandCursor)
            widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

def get_app_qss():
    return f"""
* {{ font-family: 'Segoe UI'; color: {COLORS['text']}; outline: none; }}
QMainWindow, QDialog {{ background-color: {COLORS['bg']}; }}
QFrame#mainCard, QFrame#dialogCard, QFrame#queueCard {{ background-color: {COLORS['card']}; border-radius: 20px; }}
QFrame#navFrame, QFrame#settingsNavFrame {{ background-color: {COLORS['card']}; border-radius: 20px; }}
QFrame#inputFrame {{ background-color: {COLORS['input']}; border: 1px solid {COLORS['border']}; border-radius: 10px; }}
QLabel#title, QLabel#dialogTitle {{ font-size: 16px; font-weight: 700; color: {COLORS['text']}; }}
QLabel#version, QLabel#muted, QLabel#fieldLabel {{ color: {COLORS['muted']}; }}
QLabel#sectionTitle {{ font-size: 14px; font-weight: 700; color: {COLORS['text']}; }}
QPushButton {{ background-color: {COLORS['button']}; border: none; border-radius: 10px; padding: 8px 16px; min-height: 19px; font-size: 12px; }}
QPushButton:hover {{ background-color: {COLORS['button_hover']}; }}
QPushButton:disabled {{ color: {COLORS['muted2']}; background-color: {COLORS['input2']}; }}
QPushButton#primaryButton {{ background-color: {COLORS['blue']}; color: white; font-weight: 700; }}
QPushButton#primaryButton:hover {{ background-color: {COLORS['blue_hover']}; }}
QPushButton#primaryButton:disabled {{ background-color: {COLORS['input2']}; color: {COLORS['muted2']}; }}
QPushButton#dangerButton {{ background-color: {COLORS['combo_button']}; color: {COLORS['text']}; }}
QPushButton#dangerButton:hover {{ background-color: {COLORS['danger']}; color: white; }}
QPushButton#dangerButton:disabled {{ background-color: {COLORS['input']}; color: {COLORS['muted2']}; }}
QPushButton#browseButton {{ background-color: {COLORS['combo_button']}; color: {COLORS['text']}; }}
QPushButton#browseButton:hover {{ background-color: {COLORS['blue_hover']}; color: white; }}
QPushButton#pill {{ background-color: transparent; color: {COLORS['muted']}; border-radius: 18px; padding: 8px 12px; font-weight: 700; min-width: 82px; min-height: 19px; }}
QPushButton#pill:hover {{ background-color: {COLORS['button_hover']}; }}
QPushButton#pill:checked {{ background-color: {COLORS['blue']}; color: white; }}
QPushButton#smallFooter {{ background-color: {COLORS['card']}; border-radius: 10px; padding: 8px 18px; }}
QPushButton#smallFooter:hover {{ background-color: {COLORS['button_hover']}; }}
QLineEdit {{ background-color: {COLORS['input']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 6px 8px; selection-background-color: {COLORS['blue']}; }}
QLineEdit#mainEntry {{ border: none; background-color: transparent; padding-left: 13px; }}
QComboBox {{ background-color: {COLORS['input']}; border: none; border-radius: 8px; padding: 8px 10px; min-height: 18px; }}
QComboBox#cardCombo {{ background-color: {COLORS['card']}; }}
QComboBox:disabled {{ background-color: {COLORS['input2']}; color: {COLORS['muted2']}; }}
QComboBox::drop-down:disabled {{ background-color: {COLORS['input2']}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 34px; border: none; border-top-right-radius: 8px; border-bottom-right-radius: 8px; background-color: {COLORS['combo_button']}; }}
QComboBox::drop-down:hover, QComboBox::drop-down:on {{ background-color: {COLORS['blue_hover']}; }}
QComboBox::down-arrow {{ image: none; width: 0; height: 0; }}
QComboBox QAbstractItemView {{ background-color: {COLORS['input']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; outline: 0; }}
QComboBox QAbstractItemView::item:selected {{ background-color: {COLORS['blue']}; color: white; }}
QComboBox QAbstractItemView::item:hover {{ background-color: {COLORS['input2'] if CURRENT_THEME == 'light' else "#303030"}; color: {COLORS['text']}; }}
QCheckBox {{ spacing: 8px; color: {COLORS['text']}; }}
QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 5px; border: 2px solid {COLORS['muted']}; background-color: transparent; }}
QCheckBox::indicator:hover {{ border-color: {COLORS['text']}; }}
QCheckBox::indicator:checked {{ background-color: {COLORS['blue']}; border: 2px solid {COLORS['blue']}; }}
QCheckBox:disabled {{ color: {COLORS['muted2']}; }}
QCheckBox::indicator:disabled {{ border-color: {COLORS['muted2']}; }}
QRadioButton {{ spacing: 8px; color: {COLORS['text']}; }}
QRadioButton::indicator {{ width: 14px; height: 14px; border-radius: 9px; border: 2px solid {COLORS['muted']}; background-color: transparent; }}
QRadioButton::indicator:hover {{ border-color: {COLORS['text']}; }}
QRadioButton::indicator:checked {{ width: 8px; height: 8px; border-radius: 9px; border: 5px solid {COLORS['blue']}; background-color: transparent; }}
QCheckBox#switch {{ spacing: 9px; color: {COLORS['muted']}; }}
QCheckBox#switch::indicator {{ width: 34px; height: 18px; border-radius: 9px; border: none; background-color: {COLORS['muted2']}; }}
QCheckBox#switch::indicator:unchecked {{ background-color: {COLORS['muted2']}; }}
QCheckBox#switch::indicator:checked {{ background-color: {COLORS['blue']}; }}
QProgressBar {{ background-color: {COLORS['input']}; border: none; border-radius: 3px; height: 6px; text-align: center; }}
QProgressBar::chunk {{ background-color: {COLORS['blue']}; border-radius: 3px; }}
QTextEdit {{ background-color: {COLORS['input']}; color: {COLORS['text']}; border: none; border-radius: 6px; padding: 10px; font-family: Consolas; font-size: 11px; selection-background-color: {COLORS['blue']}; }}
QScrollArea {{ border: none; background-color: transparent; }}
QScrollArea#settingsScroll, QScrollArea#settingsScroll > QWidget, QScrollArea#settingsScroll > QWidget > QWidget, QStackedWidget#settingsStack, QStackedWidget#settingsStack > QWidget {{ background-color: {COLORS['card']}; border: none; }}
QScrollBar:vertical {{ background-color: transparent; width: 10px; margin: 4px 0 4px 0; }}
QScrollBar::handle:vertical {{ background-color: {COLORS['muted']}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QMenu {{ background-color: {COLORS['card']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; padding: 4px; }}
QMenu::item {{ padding: 4px 24px; border-radius: 4px; }}
QMenu::item:selected {{ background-color: {COLORS['blue']}; color: white; }}
QMenu::separator {{ height: 1px; background-color: {COLORS['border']}; margin: 4px 0px; }}
"""

class PillButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._hovered = False
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(34)
        self.setMinimumWidth(95)
        self.setFlat(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
    def enterEvent(self, event): self._hovered = True; self.update(); super().enterEvent(event)
    def leaveEvent(self, event): self._hovered = False; self.update(); super().leaveEvent(event)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect().adjusted(0, 0, -1, -1)
        radius = rect.height() / 2
        if not self.isEnabled(): bg_color, text_color = QColor(0, 0, 0, 0), QColor(COLORS["muted2"])
        elif self.isChecked(): bg_color, text_color = QColor(COLORS["blue"]), QColor("#ffffff")
        elif self._hovered: bg_color, text_color = QColor(COLORS["button_hover"]), QColor(COLORS["muted"])
        else: bg_color, text_color = QColor(0, 0, 0, 0), QColor(COLORS["muted"])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(rect, radius, radius)
        font = QFont("Segoe UI", 9)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())

class Switch(QCheckBox):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("switch")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class SegmentedTabs(QWidget):
    def __init__(self, tabs, stack, parent=None):
        super().__init__(parent)
        self.stack = stack
        self.buttons = []
        frame = QFrame()
        frame.setObjectName("settingsNavFrame")
        frame.setFixedHeight(40)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1); layout.addWidget(frame); layout.addStretch(1)
        nav = QHBoxLayout(frame)
        nav.setContentsMargins(3, 3, 3, 3); nav.setSpacing(3)
        group = QButtonGroup(self)
        group.setExclusive(True)
        for index, tab in enumerate(tabs):
            btn = PillButton(tab)
            btn.setObjectName("pill")
            btn.setFixedWidth(90)
            btn.clicked.connect(lambda checked=False, i=index: self.stack.setCurrentIndex(i))
            nav.addWidget(btn); group.addButton(btn); self.buttons.append(btn)
        self.buttons[0].setChecked(True)
        
class QueueDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.setWindowTitle("Process Queue")
        self.setFixedSize(552, 502)
        
        self._build_ui()
        apply_theme_titlebar(self)
        center_window(self)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 22, 16, 14)
        title = QLabel("Process Queue"); title.setObjectName("dialogTitle"); title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        card = QFrame(); card.setObjectName("queueCard")
        layout.addWidget(card, 1)
        self.card_layout = QVBoxLayout(card)
        self.card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content.setStyleSheet("background-color: transparent;")
        self.queue_layout = QVBoxLayout(self.content)
        self.queue_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.content)
        self.card_layout.addWidget(self.scroll, 1)

        bottom = QHBoxLayout()
        clear = QPushButton("Clear queue"); clear.setFixedWidth(100)
        clear.clicked.connect(self.main_app.clear_entire_queue)
        bottom.addStretch(1); bottom.addWidget(clear)
        layout.addLayout(bottom)
        
        apply_ui_ux_cursors(self)

    def update_list(self, queue_data, is_running):
        self.setUpdatesEnabled(False)
        try:
            # Limpa widgets anteriores
            for i in reversed(range(self.queue_layout.count())):
                widget = self.queue_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            # Caso Fila Vazia
            if not queue_data:
                self.queue_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty = QLabel("Queue is empty.")
                empty.setObjectName("muted")
                empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.queue_layout.addWidget(empty)
                return

            self.queue_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            for index, task in enumerate(queue_data):
                full_name = task.get("name", "Media Task")
                is_active = (index == 0 and is_running)

                limit = 48 if is_active else 57
                name = full_name[:limit-3] + "..." if len(full_name) > limit else full_name

                f = QFrame()
                f.setStyleSheet(f"QFrame {{ background-color: {COLORS['input']}; border-radius: 8px; }}")
                f.setMinimumHeight(44)
                f_lay = QHBoxLayout(f)

                btn_up = QPushButton("▲")
                btn_down = QPushButton("▼")
                btn_remove = QPushButton("X")

                lbl = QLabel(f"{index+1}. {name}")
                lbl.setMaximumWidth(365)

                if is_active:
                    btn_remove.setEnabled(False)
                    btn_up.setEnabled(False)
                    btn_down.setEnabled(False)
                    lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLORS['blue']};")
                else:
                    btn_remove.clicked.connect(lambda checked=False, i=index: self.main_app.remove_from_queue(i))
                    btn_up.setEnabled(index > (1 if is_running else 0))
                    btn_up.clicked.connect(lambda checked=False, i=index: self.main_app.move_queue_item(i, -1))
                    btn_down.setEnabled(index < len(queue_data)-1)
                    btn_down.clicked.connect(lambda checked=False, i=index: self.main_app.move_queue_item(i, 1))
                    lbl.setStyleSheet("font-size: 13px;")

                # Estilização dos botões
                btn_style = f"QPushButton {{ background-color: {COLORS['button']}; color: {COLORS['text']}; border-radius: 4px; padding: 0px; font-weight: bold; font-size: 13px; }} QPushButton:hover {{ background-color: {COLORS['button_hover']}; }} QPushButton:disabled {{ background-color: {COLORS['input2']}; color: {COLORS['muted2']}; }}"
                btn_remove_style = f"QPushButton {{ background-color: {COLORS['button']}; color: {COLORS['text']}; border-radius: 4px; padding: 0px; font-weight: bold; font-size: 13px; }} QPushButton:hover {{ background-color: {COLORS['danger']}; color: white; }} QPushButton:disabled {{ background-color: {COLORS['input2']}; color: {COLORS['muted2']}; }}"

                btn_up.setStyleSheet(btn_style)
                btn_up.setFixedSize(30, 24)
                btn_down.setStyleSheet(btn_style)
                btn_down.setFixedSize(30, 24)

                btn_remove.setStyleSheet(btn_remove_style)
                btn_remove.setFixedSize(30, 24)

                f_lay.addWidget(lbl, 1)
                f_lay.addWidget(btn_up)
                f_lay.addWidget(btn_down)
                f_lay.addWidget(btn_remove)
                self.queue_layout.addWidget(f)

        finally:
            self.setUpdatesEnabled(True)

    def closeEvent(self, event):
        self.hide(); event.ignore()

class LogsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.setWindowTitle("Execution Logs")
        self.setFixedSize(600, 430)
        
        self._build_ui()
        apply_theme_titlebar(self)
        center_window(self)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.text_box = QTextEdit()
        self.text_box.setReadOnly(True)
        self.text_box.document().setMaximumBlockCount(5000)
        layout.addWidget(self.text_box, 1)
        
        row = QHBoxLayout()
        clear = QPushButton("Clear log"); clear.setFixedWidth(100); clear.clicked.connect(self.main_app.clear_logs)
        copy = QPushButton("Copy all"); copy.setObjectName("primaryButton"); copy.setFixedWidth(100); copy.clicked.connect(self.main_app.copy_logs)
        row.addWidget(clear); row.addWidget(copy); row.addStretch(1)
        layout.addLayout(row)
        
        apply_ui_ux_cursors(self)
        
    def update_logs(self, log_list):
        self.text_box.setPlainText("\n".join(log_list) + "\n")
        self.text_box.moveCursor(QTextCursor.MoveOperation.End)

    def append_log(self, text):
        # Inserção inteligente: Apenas adiciona a nova linha no final, sem reescrever tudo
        cursor = self.text_box.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text + "\n")
        self.text_box.setTextCursor(cursor)
        self.text_box.verticalScrollBar().setValue(self.text_box.verticalScrollBar().maximum())

    def closeEvent(self, event):
        self.hide(); event.ignore()

class ManualSelectionDialog(QDialog):
    def __init__(self, url, base_cmd, out_tmpl, formats, parent=None):
        super().__init__(parent)
        self.main_app = parent; self.url = url; self.base_cmd = base_cmd; self.out_tmpl = out_tmpl; self.allowed_formats = formats
        self.setWindowTitle("Manual Format Selection")
        self.setFixedSize(750, 550)
        
        self._build_ui()
        apply_theme_titlebar(self)
        center_window(self)
        self.fetch_data_task()

    def _build_ui(self):
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget(); main_layout.addWidget(self.stack)

        page_loading = QWidget()
        load_layout = QVBoxLayout(page_loading); load_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_loading = QLabel("Fetching formats and thumbnail..."); lbl_loading.setStyleSheet("font-size: 13px;")
        load_layout.addWidget(lbl_loading, 0, Qt.AlignmentFlag.AlignCenter)
        self.spinner = QProgressBar(); self.spinner.setRange(0, 0); self.spinner.setFixedSize(300, 6)
        load_layout.addWidget(self.spinner, 0, Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(page_loading)

        self.page_content = QWidget()
        self.content_layout = QVBoxLayout(self.page_content)
        self.content_layout.setContentsMargins(20, 20, 20, 20); self.content_layout.setSpacing(15)
        self.stack.addWidget(self.page_content)

    def fetch_data_task(self):
        def task():
            try:
                cmd_json = self.base_cmd.copy()
                for arg in ["--newline"]: 
                    if arg in cmd_json: cmd_json.remove(arg)
                cmd_json += ["-J", "--no-warnings", "--no-playlist", self.url]
                output = subprocess.check_output(
                    cmd_json, 
                    stderr=subprocess.DEVNULL, 
                    text=True, 
                    encoding='utf-8', 
                    errors='replace', 
                    startupinfo=self.main_app.startupinfo,
                    timeout=60
                )
                video_data = json.loads(output)
                self.main_app.safe_ui(self.build_content, video_data)
            except subprocess.CalledProcessError as e:
                self.main_app.safe_ui(self.handle_error, f"Failed to fetch formats:\n{e.output.strip() if e.output else 'Unknown error'}")
            except Exception as e:
                self.main_app.safe_ui(self.handle_error, f"Failed to parse data: {e}")
        threading.Thread(target=task, daemon=True).start()

    def handle_error(self, msg):
        QMessageBox.critical(self, "Error", f"Failed to fetch data:\n{msg}")
        self.reject()

    def build_content(self, data):
        self.spinner.setRange(0, 100); self.spinner.setValue(100)
        
        header_frame = QHBoxLayout()
        self.img_label = QLabel("Loading\nThumbnail..."); self.img_label.setFixedSize(160, 90); self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.img_label.setStyleSheet(f"background-color: {COLORS['card']}; border-radius: 8px;")
        header_frame.addWidget(self.img_label)
        self.title_label = QLabel(data.get('title', 'Unknown Video')); self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;"); self.title_label.setWordWrap(True)
        header_frame.addWidget(self.title_label, 1)
        self.content_layout.addLayout(header_frame)

        if data.get('thumbnail'):
            def fetch_img():
                try:
                    with requests.get(data['thumbnail'], stream=True, timeout=5, headers={"User-Agent": "Mozilla/5.0"}) as r:
                        if r.status_code == 200:
                            img = QImage()
                            img.loadFromData(r.content)
                            self.main_app.safe_ui(lambda: self.img_label.setPixmap(QPixmap.fromImage(img).scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)))
                except: pass
            threading.Thread(target=fetch_img, daemon=True).start()

        lists_frame = QHBoxLayout(); lists_frame.setSpacing(15)
        
        self.vid_group = QButtonGroup(self); self.aud_group = QButtonGroup(self)
        
        def create_list(title, group):
            card = QFrame(); card.setStyleSheet(f"QFrame {{ background-color: {COLORS['card']}; border-radius: 10px; }}")
            lay = QVBoxLayout(card)
            lbl = QLabel(title); lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
            lay.addWidget(lbl, 0, Qt.AlignmentFlag.AlignCenter)
            scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFixedHeight(300)
            content = QWidget(); content.setStyleSheet("background-color: transparent;")
            scroll_lay = QVBoxLayout(content); scroll_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
            rb_none = QRadioButton("None"); rb_none.setProperty("fmt_id", "none"); rb_none.setStyleSheet("font-size: 13px; padding: 4px 0px;"); group.addButton(rb_none); scroll_lay.addWidget(rb_none)
            scroll.setWidget(content); lay.addWidget(scroll)
            return card, scroll_lay

        vid_card, vid_lay = create_list("Select Video", self.vid_group)
        aud_card, aud_lay = create_list("Select Audio", self.aud_group)

        for f in data.get('formats', []):
            fmt_id = f.get('format_id', 'N/A')
            ext = f.get('ext', 'N/A')
            vc = f.get('vcodec', 'none')
            ac = f.get('acodec', 'none')
            if 'mhtml' in ext or 'sb' in ext or (vc == 'none' and ac == 'none'): continue
            
            size = f.get('filesize') or f.get('filesize_approx') or 0
            size_str = f"{size / (1024 * 1024):.1f} MB" if size else "Unknown size"

            if vc == 'none' and ac != 'none':
                rb = QRadioButton(f"ID: {fmt_id} | {ext.upper()} | {ac} | {size_str}")
                rb.setStyleSheet("font-size: 13px; padding: 4px 0px;")
                rb.setProperty("fmt_id", fmt_id); self.aud_group.addButton(rb); aud_lay.addWidget(rb)
            elif vc != 'none':
                res = f.get('resolution', 'Unknown')
                if res == 'Unknown': res = f"{f.get('width', '?')}x{f.get('height', '?')}"
                t_note = "[Video+Audio]" if ac != 'none' else "[Video Only]"
                rb = QRadioButton(f"ID: {fmt_id} | {res} | {ext.upper()} | {vc} {t_note} | {size_str}")
                rb.setStyleSheet("font-size: 13px; padding: 4px 0px;")
                rb.setProperty("fmt_id", fmt_id); self.vid_group.addButton(rb); vid_lay.addWidget(rb)

        lists_frame.addWidget(vid_card, 1); lists_frame.addWidget(aud_card, 1)
        self.content_layout.addLayout(lists_frame, 1)

        footer = QHBoxLayout()
        footer.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox(); self.format_combo.setObjectName("cardCombo"); self.format_combo.addItems(self.allowed_formats); self.format_combo.setFixedWidth(100)
        if len(self.allowed_formats) == 1: self.format_combo.setEnabled(False)
        footer.addWidget(self.format_combo); footer.addStretch(1)

        btn_down = QPushButton("Download selected"); btn_down.setObjectName("primaryButton"); btn_down.setFixedSize(145, 35)
        btn_down.clicked.connect(self.start_download)
        footer.addWidget(btn_down)
        
        self.content_layout.addLayout(footer)
        self.stack.setCurrentIndex(1)
        
        apply_ui_ux_cursors(self)

    def start_download(self):
        vid = self.vid_group.checkedButton().property("fmt_id") if self.vid_group.checkedButton() else None
        aud = self.aud_group.checkedButton().property("fmt_id") if self.aud_group.checkedButton() else None
        
        if not vid and not aud:
            QMessageBox.critical(self, "Error", "Please select at least one Video or Audio track.")
            return
            
        if vid != "none" and aud != "none" and vid and aud: fmt = f"{vid}+{aud}"
        elif vid != "none" and vid: fmt = vid            
        elif aud != "none" and aud: fmt = aud
        else:
            QMessageBox.critical(self, "Error", "Invalid selection.")
            return

        ext_final = self.format_combo.currentText().lower()
        
        # 🔻 LÊ O CAMINHO CORRETO DAS CONFIGURAÇÕES 🔻
        is_video = self.main_app.current_category in [self.main_app.TAB_VID, self.main_app.TAB_C_VID]
        gen_cfg = self.main_app.config_data.get("General", {})
        base_path = os.path.expanduser(gen_cfg.get("video_path") if is_video else gen_cfg.get("audio_path"))
        full_out_tmpl = f"{base_path}/{self.out_tmpl}"
        
        cmd = self.base_cmd.copy()
        
        if ext_final in ["webm", "wav"]:
            cmd = [arg for arg in cmd if arg not in ("--embed-thumbnail", "--embed-metadata", "--parse-metadata", "%(playlist_index|)s:%(track_number)s", "%(release_year,release_date,date,upload_date).4s:%(meta_date)s", "%(album_artist,creator,channel|)s:%(meta_album_artist)s", "--embed-subs")]

        if self.main_app.current_category == self.main_app.TAB_AUD: 
            cmd += ["-f", fmt, "--audio-format", ext_final, "-o", full_out_tmpl, self.url]
        else: 
            cmd += ["-f", fmt, "--merge-output-format", ext_final, "--remux-video", ext_final, "-o", full_out_tmpl, "-o", f"subtitle:{base_path}/subtitles/{self.out_tmpl}", self.url]

        self.main_app.run_command(cmd, task_name=self.url)
        self.accept()

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.setWindowTitle("About CopynDown")
        self.setFixedSize(620, 520)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self._build_ui()
        apply_theme_titlebar(self)
        center_window(self)

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(26, 28, 26, 14)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        content = QWidget(); content.setStyleSheet("background-color: transparent;")
        scroll.setWidget(content)
        body = QVBoxLayout(content); body.setContentsMargins(0, 0, 12, 0); body.setSpacing(18)
        
        header_box = QVBoxLayout(); header_box.setSpacing(4)
        title = QLabel("CopynDown"); title.setStyleSheet("font-size: 24px; font-weight: 700;")
        version = QLabel(f"Version {self.main_app.version}"); version.setObjectName("muted")
        header_box.addWidget(title); header_box.addWidget(version)
        body.addLayout(header_box)
        dev = QLabel("Developed by DanMixerBR"); dev.setObjectName("sectionTitle"); body.addWidget(dev); body.addSpacing(12)
        
        desc = QLabel("A modern, fast, and cross-platform media downloader and converter.\n\nSupported platforms: YouTube, Vimeo, Dailymotion, Twitch, Instagram, TikTok, Kwai,\nFacebook, Twitter/X, Reddit, SoundCloud, LinkedIn, Pinterest, Snapchat, Bilibili, Rumble,\nBandcamp, Mixcloud, Kick, and Odysee.")
        desc.setWordWrap(True); body.addWidget(desc); body.addSpacing(16)
        
        credits = QLabel("Credits & License"); credits.setObjectName("sectionTitle"); body.addWidget(credits)
        built = QLabel("Built with:\n\n• Python\n• PySide6\n• yt-dlp\n• FFmpeg\n• Deno\n\nThis software is distributed under the MIT License.")
        built.setWordWrap(True); body.addWidget(built); body.addStretch(1)
        layout.addWidget(scroll, 1)
        
        bottom = QHBoxLayout(); bottom.addStretch(1)
        github = QPushButton("GitHub"); github.setFixedWidth(120); github.clicked.connect(lambda: webbrowser.open_new("https://github.com/DanMixerBR/CopynDown"))
        
        btn_state = False if self.main_app.is_busy else True
        self.update_btn = QPushButton("Check for updates"); self.update_btn.setObjectName("primaryButton"); self.update_btn.setFixedWidth(135); self.update_btn.setEnabled(btn_state)
        def do_check():
            self.update_btn.setEnabled(False)
            self.update_btn.setText("Checking...")
            self.main_app.start_github_update(self.update_btn, self)
            
        self.update_btn.clicked.connect(do_check)
        
        bottom.addWidget(github); bottom.addSpacing(16); bottom.addWidget(self.update_btn); bottom.addStretch(1)
        layout.addLayout(bottom)
        
        apply_ui_ux_cursors(self)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.cfg = parent.config_data
        self.setWindowTitle("Settings")
        self.setFixedSize(650, 550)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self._build_ui()
        apply_theme_titlebar(self)
        center_window(self)

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 20, 10, 10); layout.setSpacing(12)
        title = QLabel("Settings"); title.setObjectName("dialogTitle"); title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        card = QFrame(); card.setObjectName("dialogCard"); layout.addWidget(card, 1)
        card_layout = QVBoxLayout(card); card_layout.setContentsMargins(20, 10, 20, 20); card_layout.setSpacing(18)

        stack = QStackedWidget()
        stack.setObjectName("settingsStack")
        tabs = SegmentedTabs(["General", "Media", "Conversion", "Network"], stack)
        
        # 🔻 CRIA A SCROLL AREA (BARRA DE ROLAGEM)
        scroll = QScrollArea()
        scroll.setObjectName("settingsScroll")
        scroll.setWidgetResizable(True) # Faz o conteúdo se adaptar à largura
        scroll.setWidget(stack)         # Coloca as abas dentro da rolagem
        
        # Adiciona a Scroll Area no layout (em vez do stack direto)
        card_layout.addWidget(tabs); card_layout.addWidget(scroll, 1)

        stack.addWidget(self._general_tab()); stack.addWidget(self._media_tab()); stack.addWidget(self._conversion_tab()); stack.addWidget(self._network_tab())

        bottom = QHBoxLayout(); bottom.setContentsMargins(10, 2, 10, 0)
        restore = QPushButton("Restore defaults"); restore.setFixedWidth(140); restore.clicked.connect(self.restore_defaults)
        save = QPushButton("Save settings"); save.setObjectName("primaryButton"); save.setFixedWidth(140); save.clicked.connect(self.save_settings)
        bottom.addWidget(restore); bottom.addStretch(1); bottom.addWidget(save)
        layout.addLayout(bottom)
        
        apply_ui_ux_cursors(self)

    def _general_tab(self):
        w = QWidget(); layout = QVBoxLayout(w); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(12)
        layout.addWidget(self._section("General Options"))
        
        self.cb_auto = QCheckBox("Auto-paste URLs"); self.cb_auto.setChecked(self.cfg["General"].get("auto_paste", True)); layout.addWidget(self.cb_auto)
        self.cb_hide = QCheckBox("Hide UI options before pasting URL"); self.cb_hide.setChecked(self.cfg["General"].get("hide_options", False)); layout.addWidget(self.cb_hide)
        self.cb_prefer = QCheckBox("Prefer video over playlist (If URL contains both)"); self.cb_prefer.setChecked(self.cfg["General"].get("prefer_video", False)); layout.addWidget(self.cb_prefer)
        
        layout.addSpacing(10)
        theme_row = QHBoxLayout(); theme_row.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox(); self.theme_combo.addItems(["Dark", "Light"]); self.theme_combo.setFixedWidth(200)
        self.theme_combo.setCurrentText(CURRENT_THEME.capitalize()); theme_row.addWidget(self.theme_combo); theme_row.addStretch(1); layout.addLayout(theme_row)
        
        layout.addSpacing(10); layout.addWidget(self._section("Outputs"))
        self.vid_path = self._path_row(layout, "Video output folder:", self.cfg["General"].get("video_path", "~/Videos/CopynDown"), True)
        self.aud_path = self._path_row(layout, "Audio output folder:", self.cfg["General"].get("audio_path", "~/Music/CopynDown"), True)
        
        row = QHBoxLayout(); row.addWidget(QLabel("Filename template:"))
        self.tmpl_combo = QComboBox(); self.tmpl_combo.addItems(["Title (Default)", "Title + Video ID", "Title + Format ID", "Title + Resolution"]); self.tmpl_combo.setFixedWidth(200)
        self.tmpl_combo.setCurrentText(self.cfg["General"].get("file_template", "Title (Default)")); row.addWidget(self.tmpl_combo); row.addStretch(1); layout.addLayout(row)

        layout.addStretch(1); return w

    def _media_tab(self):
        w = QWidget(); layout = QVBoxLayout(w); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        layout.addWidget(self._section("Embedding")); layout.addSpacing(12)
        
        self.cb_thumb = QCheckBox("Embed thumbnail (Cover art)"); self.cb_thumb.setChecked(self.cfg[self.main_app.TAB_VID].get("thumb", True))
        self.cb_meta = QCheckBox("Embed metadata (Artist, Title, etc)"); self.cb_meta.setChecked(self.cfg[self.main_app.TAB_AUD].get("meta", True))
        layout.addWidget(self.cb_thumb); layout.addSpacing(8); layout.addWidget(self.cb_meta)
        
        layout.addSpacing(24); layout.addWidget(self._section("Subtitles")); layout.addSpacing(12)
        self.cb_native = QCheckBox("Download standard subtitles"); self.cb_native.setChecked(self.cfg[self.main_app.TAB_VID].get("native_subs", False))
        self.cb_auto_sub = QCheckBox("Download auto-generated subtitles"); self.cb_auto_sub.setChecked(self.cfg[self.main_app.TAB_VID].get("auto_subs", False))
        self.cb_embed = QCheckBox("Embed subtitles into video"); self.cb_embed.setChecked(self.cfg[self.main_app.TAB_VID].get("embed_subs", False))
        
        def update_subs():
            self.cb_embed.setEnabled(self.cb_native.isChecked() or self.cb_auto_sub.isChecked())
            if not self.cb_embed.isEnabled(): self.cb_embed.setChecked(False)
        self.cb_native.stateChanged.connect(update_subs); self.cb_auto_sub.stateChanged.connect(update_subs); update_subs()
        
        layout.addWidget(self.cb_native); layout.addSpacing(8); layout.addWidget(self.cb_auto_sub); layout.addSpacing(8); layout.addWidget(self.cb_embed)
        
        lang_map = {"none": "None", "en": "English", "pt": "Portuguese", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian", "ja": "Japanese", "ko": "Korean", "ru": "Russian"}
        self.rev_map = {v: k for k, v in lang_map.items()}
        
        layout.addSpacing(20); lang_row = QHBoxLayout(); lang_row.setSpacing(8)
        lang_col = QVBoxLayout(); lang_col.addWidget(QLabel("Original language:"))
        self.lang_combo = QComboBox(); self.lang_combo.addItems(list(lang_map.values())[1:]); self.lang_combo.setFixedWidth(140); self.lang_combo.setCurrentText(lang_map.get(self.cfg[self.main_app.TAB_VID].get("langs", "en"), "English"))
        lang_col.addWidget(self.lang_combo); lang_row.addLayout(lang_col)
        
        trans_col = QVBoxLayout(); trans_col.addWidget(QLabel("Translate to:"))
        self.trans_combo = QComboBox(); self.trans_combo.addItems(list(lang_map.values())); self.trans_combo.setFixedWidth(140); self.trans_combo.setCurrentText(lang_map.get(self.cfg[self.main_app.TAB_VID].get("trans_langs", "none"), "None"))
        trans_col.addWidget(self.trans_combo); lang_row.addLayout(trans_col); lang_row.addStretch(1)
        
        layout.addLayout(lang_row); layout.addStretch(1); return w

    def _conversion_tab(self):
        w = QWidget(); layout = QVBoxLayout(w); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        layout.addWidget(self._section("Conversion Profile")); layout.addSpacing(12)
        
        self.prof_combo = QComboBox(); self.prof_combo.addItems(["High Quality", "Balanced", "Economy"])
        self.prof_combo.setFixedWidth(140); self.prof_combo.setCurrentText(self.cfg["General"].get("conv_profile", "High Quality"))
        layout.addWidget(self.prof_combo, 0, Qt.AlignmentFlag.AlignLeft)
        
        layout.addSpacing(14)
        legend = QLabel("• High Quality: Visually lossless. Ideal for archiving, but generates\n  larger files.\n\n• Balanced: The sweet spot. Excellent quality with optimized file size.\n\n• Economy: Maximum compression. Generates the smallest files while\n  keeping good quality."); legend.setObjectName("muted"); legend.setWordWrap(True)
        layout.addWidget(legend)

        layout.addSpacing(20)
        
        # 🔻 NOVA SEÇÃO: CUSTOM PROFILE
        c_box = QFrame(); c_box.setStyleSheet(f"QFrame {{ background-color: {COLORS['card']}; border-radius: 10px; }}")
        c_lay = QVBoxLayout(c_box); c_lay.setContentsMargins(0, 10, 15, 15); c_lay.setSpacing(10)
        
        self.cb_custom = Switch("Enable custom profile")
        self.cb_custom.setChecked(self.cfg["General"].get("custom_profile", False))
        c_lay.addWidget(self.cb_custom); c_lay.addSpacing(5)
        
        # Grid para alinhar os campos direitinho
        grid = QGridLayout(); grid.setContentsMargins(0, 0, 0, 0); grid.setHorizontalSpacing(15); grid.setVerticalSpacing(10)
        
        grid.setColumnStretch(2, 1)
        
        grid.addWidget(QLabel("CRF Value (0-51):"), 0, 0)
        self.crf_entry = QLineEdit(self.cfg["General"].get("custom_crf", "18")); self.crf_entry.setFixedWidth(60)
        grid.addWidget(self.crf_entry, 0, 1, Qt.AlignmentFlag.AlignLeft)
        
        grid.addWidget(QLabel("Preset (H.264/H.265):"), 1, 0)
        self.preset_combo = QComboBox(); self.preset_combo.addItems(["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"])
        self.preset_combo.setCurrentText(self.cfg["General"].get("custom_preset", "faster"))
        grid.addWidget(self.preset_combo, 1, 1)
        
        grid.addWidget(QLabel("CPU-Used (VP9):"), 2, 0)
        self.cpu_combo = QComboBox(); self.cpu_combo.addItems(["0", "1", "2", "3", "4", "5"])
        self.cpu_combo.setCurrentText(self.cfg["General"].get("custom_cpu_used", "4"))
        grid.addWidget(self.cpu_combo, 2, 1)
        
        c_lay.addLayout(grid)
        layout.addWidget(c_box)

        # 🔻 Lógica de Ativar/Desativar os menus cruzados
        def toggle_custom_profile():
            is_custom = self.cb_custom.isChecked()
            self.prof_combo.setEnabled(not is_custom) # Escurece o perfil padrão
            self.crf_entry.setEnabled(is_custom)      # Acende o CRF
            self.preset_combo.setEnabled(is_custom)   # Acende o Preset
            self.cpu_combo.setEnabled(is_custom)      # Acende o CPU-Used
            
        self.cb_custom.toggled.connect(toggle_custom_profile)
        toggle_custom_profile() # Chama uma vez para configurar o estado inicial
        
        layout.addStretch(1); return w

    def _network_tab(self):
        w = QWidget(); layout = QVBoxLayout(w); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        layout.addWidget(self._section("Network Options")); layout.addSpacing(12)
        
        row1 = QHBoxLayout(); row1.setSpacing(10); row1.addWidget(QLabel("Max retries:"))
        self.retries = QLineEdit(self.cfg["General"].get("max_retries", "10")); self.retries.setFixedWidth(60); row1.addWidget(self.retries); row1.addStretch(1); layout.addLayout(row1)
        
        layout.addSpacing(10); row2 = QHBoxLayout(); row2.setSpacing(10); row2.addWidget(QLabel("Delay mode:"))
        self.delay = QComboBox(); self.delay.addItems(["None", "Playlist Only", "All Downloads"]); self.delay.setFixedWidth(140); self.delay.setCurrentText(self.cfg["General"].get("delay_mode", "Playlist Only")); row2.addWidget(self.delay); row2.addStretch(1); layout.addLayout(row2)
        
        layout.addSpacing(10); row3 = QHBoxLayout(); row3.setSpacing(6)
        row3.addWidget(QLabel("Sleep intervals (Sec):  Min")); self.s_min = QLineEdit(self.cfg["General"].get("sleep_min", "2")); self.s_min.setFixedWidth(40); row3.addWidget(self.s_min)
        row3.addWidget(QLabel("Max")); self.s_max = QLineEdit(self.cfg["General"].get("sleep_max", "5")); self.s_max.setFixedWidth(40); row3.addWidget(self.s_max)
        row3.addWidget(QLabel("Requests")); self.s_req = QLineEdit(self.cfg["General"].get("sleep_req", "1")); self.s_req.setFixedWidth(40); row3.addWidget(self.s_req); row3.addStretch(1); layout.addLayout(row3)
        
        # 🔻 LIMITADOR DE VELOCIDADE
        layout.addSpacing(10); row4 = QHBoxLayout(); row4.setSpacing(10); row4.addWidget(QLabel("Speed limit:"))
        self.speed_combo = QComboBox(); self.speed_combo.addItems(["Unlimited", "1 MB/s", "5 MB/s", "10 MB/s", "25 MB/s", "50 MB/s"])
        self.speed_combo.setFixedWidth(140); self.speed_combo.setCurrentText(self.cfg["General"].get("speed_limit", "Unlimited"))
        row4.addWidget(self.speed_combo); row4.addStretch(1); layout.addLayout(row4)

        # 🔻 PROXY
        layout.addSpacing(10); self.cb_proxy = Switch("Use Proxy Server"); self.cb_proxy.setChecked(self.cfg["General"].get("use_proxy", False))
        layout.addWidget(self.cb_proxy)
        
        layout.addSpacing(10)
        
        self.proxy_entry = QLineEdit(self.cfg["General"].get("proxy_url", ""))
        self.proxy_entry.setPlaceholderText("http://ip:port or socks5://ip:port")
        self.proxy_entry.setFixedWidth(350)
        self.proxy_entry.setEnabled(self.cb_proxy.isChecked()) # Começa ativado/desativado de acordo com a caixinha
        self.cb_proxy.toggled.connect(self.proxy_entry.setEnabled) # Trava/Destrava ao clicar
        layout.addWidget(self.proxy_entry)
        
        layout.addSpacing(10)
        
        c_box = QFrame(); c_box.setObjectName("cookieBox"); c_box.setStyleSheet(f"QFrame#cookieBox {{ background-color: {COLORS['card']}; border-radius: 10px; }}")
        c_lay = QVBoxLayout(c_box); c_lay.setContentsMargins(0, 10, 15, 10); c_lay.setSpacing(12)
        c_lay.addWidget(self._section("Cookies"))
        self.cb_cookies = Switch("Use cookies file")
        self.cb_cookies.setChecked(self.cfg["General"].get("use_cookies", True))
        c_lay.addWidget(self.cb_cookies)
        c_lay.addSpacing(8)
        r_row = QHBoxLayout()
        r_auto = QRadioButton("Auto-extract (Edge/Firefox/Brave)"); r_txt = QRadioButton("Import from text file"); r_auto.setChecked(True)
        r_row.addWidget(r_auto); r_row.addSpacing(10); r_row.addWidget(r_txt); r_row.addStretch(1); c_lay.addLayout(r_row)
        
        stack = QStackedWidget()
        p_auto = QWidget(); p_auto_lay = QVBoxLayout(p_auto); p_auto_lay.setContentsMargins(0, 2, 0, 0); p_auto_lay.setSpacing(8)
        n_auto = QLabel("Note: May require closing the browser or running the app as Administrator."); n_auto.setObjectName("muted"); p_auto_lay.addWidget(n_auto)
        row_ext = QHBoxLayout(); self.browser_combo = QComboBox(); self.browser_combo.addItems(["Edge", "Firefox", "Brave", "Safari"]); self.browser_combo.setFixedWidth(120)
        
        btn_ext = QPushButton("Extract cookies"); btn_ext.setObjectName("primaryButton"); btn_ext.setFixedWidth(116)
        row_ext.addWidget(self.browser_combo); row_ext.addWidget(btn_ext); row_ext.addStretch(1); p_auto_lay.addLayout(row_ext)

        def perform_extraction():
            btn_ext.setEnabled(False); btn_ext.setText("Extracting...")
            browser = self.browser_combo.currentText().lower()
            c_path = self.cookie_path.text()

            def reset_btn():
                try:
                    btn_ext.setEnabled(True); btn_ext.setText("Extract cookies"); btn_ext.setStyleSheet("")
                except RuntimeError:
                    pass

            def thread_task():
                try:
                    import rookiepy
                    self.main_app.safe_ui(self.main_app.add_to_log, f">>> Bypassing browser locks and extracting {browser.capitalize()} cookies...")
                    browsers = {"edge": getattr(rookiepy, 'edge', None), "firefox": getattr(rookiepy, 'firefox', None), "brave": getattr(rookiepy, 'brave', None), "safari": getattr(rookiepy, 'safari', None)}
                    if browser not in browsers or browsers[browser] is None: raise ValueError(f"The browser '{browser.capitalize()}' is not supported on your OS.")
                    
                    ext_args = {"domains": self.main_app.valid_domains}
                    extracted_cookies = None
                    if browser == "firefox" and not self.main_app.is_windows:
                        linux_dir = os.path.expanduser("~/.config/mozilla/firefox/")
                        if os.path.exists(linux_dir):
                            newest_db = None; newest_time = 0
                            for folder_name in os.listdir(linux_dir):
                                potential_db = os.path.join(linux_dir, folder_name, "cookies.sqlite")
                                if os.path.isfile(potential_db):
                                    mod_time = os.path.getmtime(potential_db)
                                    if mod_time > newest_time: newest_time = mod_time; newest_db = potential_db
                            if newest_db:
                                self.main_app.safe_ui(self.main_app.add_to_log, ">>> Linux custom path detected! Injecting database...")
                                extracted_cookies = rookiepy.firefox_based(db_path=newest_db, domains=self.main_app.valid_domains)
                    
                    if extracted_cookies is None: extracted_cookies = browsers[browser](**ext_args)
                    if not extracted_cookies: raise Exception("No cookies found for the target domains. Are you logged in?")

                    with open(c_path, 'w', encoding='utf-8') as f:
                        f.write("# Netscape HTTP Cookie File\n# Generated by CopynDown Native Extractor\n\n")
                        for c in extracted_cookies:
                            domain = c.get('domain', '')
                            include_sub = 'TRUE' if domain.startswith('.') else 'FALSE'
                            path = c.get('path', '/')
                            secure = 'TRUE' if c.get('secure') else 'FALSE'
                            expires = str(int(c.get('expires', 0))) if c.get('expires') else '0'
                            name = c.get('name', '')
                            value = c.get('value', '')
                            f.write(f"{domain}\t{include_sub}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")
                    
                    self.main_app.safe_ui(lambda: (btn_ext.setText("✅ Success!"), btn_ext.setStyleSheet("background-color: #2ea043; color: white; border: none;")))
                    self.main_app.safe_ui(self.main_app.add_to_log, f">>> Successfully generated valid cookies.txt at {c_path}")
                    self.main_app.safe_ui(lambda: QTimer.singleShot(3000, reset_btn))

                except Exception as e:
                    # 1. Congelamos o texto do erro imediatamente
                    err_msg = str(e)
                    
                    # 2. Passamos a mensagem congelada (m=err_msg) para blindar o lambda
                    self.main_app.safe_ui(lambda: (btn_ext.setText("❌ Error"), btn_ext.setStyleSheet("background-color: #a94442; color: white; border: none;")))
                    self.main_app.safe_ui(lambda m=err_msg: QMessageBox.critical(self.main_app, "Extraction Error", f"Failed to extract cookies.\n\nDetails: {m}"))
                    self.main_app.safe_ui(self.main_app.add_to_log, f">>> Cookie extraction error: {err_msg}")
                    self.main_app.safe_ui(lambda: QTimer.singleShot(3000, reset_btn))

            threading.Thread(target=thread_task, daemon=True).start()

        btn_ext.clicked.connect(perform_extraction)
        
        p_txt = QWidget(); p_txt_lay = QVBoxLayout(p_txt); p_txt_lay.setContentsMargins(0, 2, 0, 0); p_txt_lay.setSpacing(8)
        n_txt = QLabel("1. Install 'Get cookies.txt LOCALLY' extension in your browser.\n2. Export the file and select it below:"); n_txt.setObjectName("muted"); p_txt_lay.addWidget(n_txt)
        self.cookie_path = self._path_row(p_txt_lay, "", self.cfg["General"].get("cookies_path", "bin/cookies.txt"), False, True)
        
        stack.addWidget(p_auto); stack.addWidget(p_txt); c_lay.addWidget(stack)
        r_auto.toggled.connect(lambda c: stack.setCurrentIndex(0) if c else None); r_txt.toggled.connect(lambda c: stack.setCurrentIndex(1) if c else None)
        layout.addWidget(c_box)
        layout.addStretch(1)
        return w

    def _section(self, text):
        lbl = QLabel(text); lbl.setObjectName("sectionTitle"); return lbl

    def _path_row(self, parent_layout, label_text, path, is_dir, has_ext=False):
        if label_text: parent_layout.addWidget(QLabel(label_text)); parent_layout.addSpacing(-8)
        row = QHBoxLayout(); edit = QLineEdit(path); edit.setReadOnly(True)
        edit.setFixedWidth(350)
        btn = QPushButton("Browse"); btn.setObjectName("browseButton"); btn.setFixedWidth(75)
        
        def do_browse():
            title = "Select Output Folder" if is_dir else "Select Cookies File"
            p = QFileDialog.getExistingDirectory(self, title) if is_dir else QFileDialog.getOpenFileName(self, title, "", "Text Files (*.txt)")[0]
            if p: 
                p = p.replace("\\", "/")
                home = os.path.expanduser("~").replace("\\", "/")
                app_dir = os.path.abspath(".").replace("\\", "/")
                if p.startswith(app_dir): p = p[len(app_dir):].lstrip("/")
                elif p.startswith(home): p = "~" + p[len(home):]
                edit.setText(p)
                
        btn.clicked.connect(do_browse)
        row.addWidget(edit); row.addWidget(btn)
        
        if has_ext:
            btn_ext = QPushButton("Get extension"); btn_ext.setObjectName("primaryButton"); btn_ext.setFixedWidth(110)
            btn_ext.clicked.connect(lambda: webbrowser.open_new("https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"))
            row.addWidget(btn_ext)
            
        row.addStretch(1)
        parent_layout.addLayout(row)
        return edit

    def restore_defaults(self):
        self.vid_path.setText("~/Videos/CopynDown")
        self.aud_path.setText("~/Music/CopynDown")
        self.cookie_path.setText("bin/cookies.txt")
        self.cb_auto.setChecked(True); self.cb_hide.setChecked(False); self.cb_prefer.setChecked(False)
        self.cb_thumb.setChecked(True); self.cb_meta.setChecked(True); self.cb_native.setChecked(False); self.cb_auto_sub.setChecked(False); self.cb_embed.setChecked(False)
        self.lang_combo.setCurrentText("English"); self.trans_combo.setCurrentText("None")
        self.prof_combo.setCurrentText("High Quality"); self.tmpl_combo.setCurrentText("Title (Default)")
        self.delay.setCurrentText("Playlist Only")
        self.retries.setText("10"); self.s_min.setText("2"); self.s_max.setText("5"); self.s_req.setText("1")
        self.speed_combo.setCurrentText("Unlimited")
        self.cb_proxy.setChecked(False); self.proxy_entry.setText("")
        self.cb_custom.setChecked(False)
        self.crf_entry.setText("18")
        self.preset_combo.setCurrentText("faster")
        self.cpu_combo.setCurrentText("4")

    def save_settings(self):
        global CURRENT_THEME, COLORS
        sel_theme = self.theme_combo.currentText().lower()
        self.cfg["General"].update({
            "video_path": self.vid_path.text(), "audio_path": self.aud_path.text(), "auto_paste": self.cb_auto.isChecked(),
            "use_cookies": self.cb_cookies.isChecked(), "cookies_path": self.cookie_path.text(), "hide_options": self.cb_hide.isChecked(),
            "prefer_video": self.cb_prefer.isChecked(), "max_retries": self.retries.text(), "file_template": self.tmpl_combo.currentText(),
            "delay_mode": self.delay.currentText(), "sleep_min": self.s_min.text(), "sleep_max": self.s_max.text(), "sleep_req": self.s_req.text(),
            "conv_profile": self.prof_combo.currentText(),
            "speed_limit": self.speed_combo.currentText(),
            "use_proxy": self.cb_proxy.isChecked(),
            "proxy_url": self.proxy_entry.text(),
            "theme": sel_theme,
            "custom_profile": self.cb_custom.isChecked(),
            "custom_crf": self.crf_entry.text(),
            "custom_preset": self.preset_combo.currentText(),
            "custom_cpu_used": self.cpu_combo.currentText()
        })
        self.cfg[self.main_app.TAB_VID].update({
            "thumb": self.cb_thumb.isChecked(), "native_subs": self.cb_native.isChecked(), "auto_subs": self.cb_auto_sub.isChecked(),
            "embed_subs": self.cb_embed.isChecked(), "langs": self.rev_map.get(self.lang_combo.currentText(), "en"), "trans_langs": self.rev_map.get(self.trans_combo.currentText(), "none")
        })
        self.cfg[self.main_app.TAB_AUD].update({
            "thumb": self.cb_thumb.isChecked(), "meta": self.cb_meta.isChecked()
        })
        
        if sel_theme != CURRENT_THEME:
            CURRENT_THEME = sel_theme; COLORS = THEMES[CURRENT_THEME]
            QApplication.instance().setStyleSheet(get_app_qss())
            
            apply_theme_titlebar(self.main_app)
            apply_theme_titlebar(self)
            if getattr(self.main_app, 'queue_window', None): apply_theme_titlebar(self.main_app.queue_window)
            if getattr(self.main_app, 'log_window', None): apply_theme_titlebar(self.main_app.log_window)
            
            self.main_app.refresh_theme_colors()
            
        self.main_app.save_config()
        self.main_app.update_folder_context()
        self.main_app.evaluate_ui_state()
        self.accept()
        self.main_app.add_to_log(">>> Settings saved successfully.")
        
class CopynDownApp(QMainWindow):
    ui_signal = Signal(object, tuple, dict)
    def __init__(self):
        super().__init__()
        self.ui_signal.connect(self._execute_safe_ui)
        self.TAB_VID = "Save Video"; self.TAB_AUD = "Save Audio"; self.TAB_C_VID = "Convert Video"; self.TAB_C_AUD = "Convert Audio"
        self.tabs = [self.TAB_VID, self.TAB_AUD, self.TAB_C_VID, self.TAB_C_AUD]
        
        # 1. Primeiro definimos o sistema e os caminhos dos arquivos
        self.is_windows = os.name == 'nt'; self.exe = ".exe" if self.is_windows else ""
        self.config_file = os.path.join(bin_path, "config.txt").replace("\\", "/")
        self.ytdlp_path = os.path.join(bin_path, f"yt-dlp{self.exe}").replace("\\", "/")
        self.cookies_path_default = os.path.join(bin_path, "cookies.txt").replace("\\", "/")
        self.version_file = os.path.join(bin_path, "version.txt").replace("\\", "/")
        
        # 2. AGORA SIM lemos a versão, pois self.version_file já existe
        self.version = self.get_local_version()

        self.setWindowTitle("CopynDown")
        self.resize(850, 650); self.setMinimumSize(850, 650)

        # 🔻 Timers 100% Blindados
        self.status_timer = QTimer(self); self.status_timer.setSingleShot(True); self.status_timer.timeout.connect(self.reset_status)
        self.ui_update_timer = QTimer(self); self.ui_update_timer.setSingleShot(True); self.ui_update_timer.timeout.connect(self.evaluate_ui_state)

        self.log_window = None; self.queue_window = None
        self.current_process = None; self.current_playlist_item = ""
        self.is_cancelling = False; self.is_busy = False; self.is_updating = False
        self.download_queue = []; self.is_queue_running = False

        self.re_progress = re.compile(r'(\d+\.\d+)%')
        self.valid_domains = [
            "youtube.com", "youtu.be", "instagram.com", "tiktok.com", "twitter.com", 
            "//x.com", ".x.com", "facebook.com", "fb.watch", "twitch.tv", "clips.twitch.tv", 
            "vimeo.com", "reddit.com", "dailymotion.com", "dai.ly", "soundcloud.com",
            "linkedin.com", "pinterest.com", "snapchat.com", "bilibili.com", 
            "rumble.com", "bandcamp.com", "mixcloud.com", "kick.com", "odysee.com",
            "kwai.com", "kw.ai"
        ]
        self.full_logs_list = ["--- Program Logs ---"]

        self.config_data = {
            "General": { 
                "auto_paste": True, "use_cookies": True, "cookies_path": self.cookies_path_default, "hide_options": False, 
                "video_path": "~/Videos/CopynDown", "audio_path": "~/Music/CopynDown", "prefer_video": False, 
                "max_retries": "10", "file_template": "Title (Default)", "delay_mode": "Playlist Only", 
                "sleep_min": "2", "sleep_max": "5", "sleep_req": "1", "conv_profile": "High Quality",
                "custom_profile": False, "custom_crf": "18", "custom_preset": "faster", "custom_cpu_used": "4",
                "speed_limit": "Unlimited", "use_proxy": False, "proxy_url": ""                
            },
            self.TAB_VID: {"thumb": True, "meta": False, "native_subs": False, "auto_subs": False, "embed_subs": False, "langs": "en", "trans_langs": "none"},
            self.TAB_AUD: {"thumb": True, "meta": True}
        }
        self.load_config()
        self.last_folder = self.config_data["General"]["video_path"]
        self.current_category = self.TAB_VID
        
        global CURRENT_THEME, COLORS
        saved_theme = self.config_data.get("General", {}).get("theme", "dark")
        if saved_theme in THEMES:
            CURRENT_THEME = saved_theme
            COLORS = THEMES[CURRENT_THEME]
        QApplication.instance().setStyleSheet(get_app_qss())

        self.startupinfo = None
        if self.is_windows:
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.startupinfo.wShowWindow = subprocess.SW_HIDE

        
        self._build_ui()
        self.select_tab(self.TAB_VID)
        apply_theme_titlebar(self)
        center_window(self)

        threading.Thread(target=self.check_ytdlp_updates, daemon=True).start()
    
    def changeEvent(self, event):
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Type.ActivationChange and self.isActiveWindow():
            self.on_clipboard_change()
        super().changeEvent(event)

    def _build_ui(self):
        root = QWidget(); self.setCentralWidget(root)
        main_layout = QVBoxLayout(root); main_layout.setContentsMargins(40, 25, 40, 20); main_layout.setSpacing(20)

        top_bar = QHBoxLayout(); top_bar.setSpacing(28); main_layout.addLayout(top_bar)
        brand = QHBoxLayout(); brand.setSpacing(8); top_bar.addLayout(brand)

        logo = QLabel()
        logo.setFixedSize(32, 32)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = os.path.join(bin_path, "logo.png").replace("\\", "/")
        if os.path.exists(logo_path):
            logo.setPixmap(QPixmap(logo_path).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo.setText("⬇")
            logo.setStyleSheet(f"font-size: 23px; color: #55cdfc; background: {COLORS['blue']}; border-radius: 8px;")
        brand.addWidget(logo)

        title_box = QVBoxLayout(); title_box.setSpacing(0); title_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        brand.addLayout(title_box)
        title = QLabel("CopynDown"); title.setObjectName("title")
        version = QLabel(f"Version {self.version}"); version.setObjectName("version")
        version.setStyleSheet("font-size: 11px;")
        title_box.addWidget(title); title_box.addWidget(version)

        self.nav_frame = QFrame(); self.nav_frame.setObjectName("navFrame"); self.nav_frame.setFixedHeight(40); self.nav_frame.setMinimumWidth(455)
        nav_layout = QHBoxLayout(self.nav_frame); nav_layout.setContentsMargins(3, 3, 3, 3); nav_layout.setSpacing(3)
        top_bar.addWidget(self.nav_frame, 1, Qt.AlignmentFlag.AlignHCenter)

        self.tab_buttons = {}
        for tab in self.tabs:
            btn = PillButton(tab); btn.setObjectName("pill")
            btn.clicked.connect(lambda checked=False, name=tab: self.select_tab(name))
            nav_layout.addWidget(btn); self.tab_buttons[tab] = btn

        settings_btn = QPushButton("⚙ Settings"); settings_btn.setObjectName("smallFooter"); settings_btn.setFixedWidth(100)
        settings_btn.clicked.connect(self.show_settings); top_bar.addWidget(settings_btn, 0, Qt.AlignmentFlag.AlignRight)

        self.main_card = QFrame(); self.main_card.setObjectName("mainCard")
        main_layout.addWidget(self.main_card, 1)
        card_layout = QVBoxLayout(self.main_card); card_layout.setContentsMargins(40, 20, 40, 20); card_layout.setSpacing(20); card_layout.addSpacing(10)

        self.desc_label = QLabel("Video Downloader"); self.desc_label.setObjectName("muted"); self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.desc_label); card_layout.addSpacing(-8)

        self.input_frame = QFrame(); self.input_frame.setObjectName("inputFrame"); self.input_frame.setFixedHeight(47)
        input_layout = QHBoxLayout(self.input_frame); input_layout.setContentsMargins(8, 5, 6, 5); input_layout.setSpacing(8)
        self.main_entry = QLineEdit(); self.main_entry.setObjectName("mainEntry"); self.main_entry.setPlaceholderText("Paste URL here")
        self.main_entry.textChanged.connect(self.schedule_ui_evaluation)
        def on_entry_focus_in(event):
            QLineEdit.focusInEvent(self.main_entry, event)
            self.on_clipboard_change()
        self.main_entry.focusInEvent = on_entry_focus_in
        self.main_btn = QPushButton("Paste"); self.main_btn.setObjectName("primaryButton"); self.main_btn.setFixedSize(75, 36)
        self.main_btn.clicked.connect(self.paste_url_btn)
        input_layout.addWidget(self.main_entry, 1); input_layout.addWidget(self.main_btn)
        card_layout.addWidget(self.input_frame)

        self.lbl_1, self.menu_1 = self._field("Quality", ["2160p (4K)", "1440p (QHD)", "1080p (AV1/VP9)", "1080p (H.264)", "720p", "480p", "360p"])
        self.lbl_2, self.menu_2 = self._field("Format", ["MP4", "MKV", "WEBM"])
        self.lbl_3, self.menu_3 = self._field("Video Codec", ["Original", "H.264", "H.265", "VP9"])
        self.lbl_4, self.menu_4 = self._field("Audio Codec", ["Original", "AAC", "MP3", "FLAC", "ALAC", "Opus", "None (Video Only)"])

        self.options_frame = QWidget()
        opt_lay = QVBoxLayout(self.options_frame); opt_lay.setContentsMargins(0, 0, 0, 0); opt_lay.setSpacing(15)

        self.row1_widget = QWidget()
        row1_layout = QGridLayout(self.row1_widget); row1_layout.setContentsMargins(0, 5, 0, 0); row1_layout.setHorizontalSpacing(20); row1_layout.setVerticalSpacing(13)
        row1_layout.addWidget(self.lbl_1, 0, 0); row1_layout.addWidget(self.menu_1, 1, 0)
        row1_layout.addWidget(self.lbl_2, 0, 1); row1_layout.addWidget(self.menu_2, 1, 1)
        opt_lay.addWidget(self.row1_widget)

        self.row2_widget = QWidget()
        row2_layout = QGridLayout(self.row2_widget); row2_layout.setContentsMargins(0, 0, 0, 0); row2_layout.setHorizontalSpacing(20); row2_layout.setVerticalSpacing(13)
        row2_layout.addWidget(self.lbl_3, 0, 0); row2_layout.addWidget(self.menu_3, 1, 0)
        row2_layout.addWidget(self.lbl_4, 0, 1); row2_layout.addWidget(self.menu_4, 1, 1)
        opt_lay.addWidget(self.row2_widget)
        
        card_layout.addWidget(self.options_frame)

        switches_container = QWidget()
        switches_layout = QVBoxLayout(switches_container); switches_layout.setSpacing(16); switches_layout.setContentsMargins(0, 0, 0, 0)
        self.switch_advanced = Switch("Advanced selection")
        self.switch_advanced.clicked.connect(self.on_advanced_toggle)
        self.switch_extract_audio = Switch("Extract original audio")
        self.switch_extract_audio.toggled.connect(self.on_extract_audio_toggle)
        switches_layout.addWidget(self.switch_advanced, 0, Qt.AlignmentFlag.AlignLeft)
        switches_layout.addWidget(self.switch_extract_audio, 0, Qt.AlignmentFlag.AlignLeft)
        card_layout.addWidget(switches_container)

        self.action_frame = QWidget()
        actions = QHBoxLayout(self.action_frame); actions.setContentsMargins(0, 13, 0, 13); actions.setSpacing(20); actions.addStretch(1)
        self.btn_download = QPushButton("Download media"); self.btn_download.setObjectName("primaryButton"); self.btn_download.setFixedWidth(150); self.btn_download.setStyleSheet("min-height: 24px; font-size: 13px;")
        self.btn_download.clicked.connect(self.handle_unified_download)
        self.btn_cancel = QPushButton("Cancel"); self.btn_cancel.setObjectName("dangerButton"); self.btn_cancel.setFixedWidth(150); self.btn_cancel.setStyleSheet("min-height: 24px; font-size: 13px;"); self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_download)
        actions.addWidget(self.btn_download); actions.addWidget(self.btn_cancel); actions.addStretch(1)
        card_layout.addWidget(self.action_frame)

        self.status_frame = QWidget()
        status_lay = QVBoxLayout(self.status_frame); status_lay.setContentsMargins(0, 0, 0, 0)
        self.progress_label = QLabel("Starting..."); self.progress_label.setObjectName("muted"); self.progress_label.setStyleSheet("font-size: 11px;")
        status_lay.addWidget(self.progress_label)
        self.progress = QProgressBar(); self.progress.setRange(0, 100); self.progress.setValue(0); self.progress.setTextVisible(False); self.progress.setFixedHeight(6)
        status_lay.addWidget(self.progress)
        card_layout.addWidget(self.status_frame); card_layout.addStretch(1)

        footer = QHBoxLayout(); footer.setSpacing(10); main_layout.addLayout(footer)
        self.open_btn = self._footer_btn("📁 Open location", 140); self.open_btn.clicked.connect(self.open_folder)
        self.queue_btn = self._footer_btn("📥 Queue (0)", 110); self.queue_btn.clicked.connect(self.show_queue)
        self.logs_btn = self._footer_btn("📄 View logs", 105); self.logs_btn.clicked.connect(self.show_logs)
        self.about_btn = self._footer_btn("ℹ About", 80); self.about_btn.clicked.connect(self.show_about)
        footer.addWidget(self.open_btn); footer.addWidget(self.queue_btn); footer.addStretch(1); footer.addWidget(self.logs_btn); footer.addWidget(self.about_btn)
        
        apply_ui_ux_cursors(self)

    def _field(self, label_text, values):
        label = QLabel(label_text); label.setObjectName("fieldLabel")
        combo = QComboBox(); combo.addItems(values); combo.setMinimumHeight(35); combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return label, combo

    def _footer_btn(self, text, width):
        btn = QPushButton(text)
        btn.setObjectName("smallFooter")
        btn.setFixedWidth(width)
        return btn

    def set_combo(self, combo, values, current=None):
        combo.clear(); combo.addItems(values)
        if current: combo.setCurrentText(current)

    def select_tab(self, tab):
        self.switch_extract_audio.setChecked(False)
        self.current_category = tab
        for k, v in self.tab_buttons.items(): v.setChecked(k == tab)
        
        is_convert = tab in (self.TAB_C_VID, self.TAB_C_AUD)
        if getattr(self, 'last_tab_is_convert', None) != is_convert:
            self.main_entry.clear()
            self.main_entry.setPlaceholderText("Select source media file..." if is_convert else "Paste URL here")
        self.last_tab_is_convert = is_convert
        self.main_btn.setText("Browse" if is_convert else "Paste")
        if is_convert:
            # 🔻 Aplica a nova cor idêntica ao Drop-down
            self.main_btn.setObjectName("browseButton"); self.main_btn.setStyleSheet("")
            self.main_btn.clicked.disconnect(); self.main_btn.clicked.connect(self.browse_source)
        else:
            self.main_btn.setObjectName("primaryButton"); self.main_btn.setStyleSheet("")
            self.main_btn.clicked.disconnect(); self.main_btn.clicked.connect(self.paste_url_btn)
            
        self.main_btn.style().unpolish(self.main_btn); self.main_btn.style().polish(self.main_btn)

        desc = {self.TAB_VID: "Video Downloader", self.TAB_AUD: "Audio Downloader", self.TAB_C_VID: "Video Converter", self.TAB_C_AUD: "Audio Converter"}[tab]
        self.desc_label.setText(desc)

        if tab == self.TAB_VID:
            self.lbl_1.setText("Quality"); self.set_combo(self.menu_1, ["2160p (4K)", "1440p (QHD)", "1080p (AV1/VP9)", "1080p (H.264)", "720p", "480p", "360p"], "2160p (4K)")
            self.lbl_2.setText("Format"); self.set_combo(self.menu_2, ["MP4", "MKV", "WEBM"], "MP4")
        elif tab == self.TAB_AUD:
            self.lbl_1.setText("Quality"); self.set_combo(self.menu_1, ["Auto", "High (320 kbps)", "Medium (192 kbps)", "Low (128 kbps)"], "Auto")
            self.lbl_2.setText("Format"); self.set_combo(self.menu_2, ["M4A", "MP3", "FLAC", "WAV", "Opus"], "M4A")
        elif tab == self.TAB_C_VID:
            self.lbl_1.setText("Resolution"); self.set_combo(self.menu_1, ["Original", "2160p (4K)", "1440p (QHD)", "1080p", "720p", "480p", "360p"], "Original")
            self.lbl_2.setText("Output Format"); self.set_combo(self.menu_2, ["MP4", "MKV", "WEBM", "MOV", "AVI"], "MP4")
            self.lbl_3.setText("Video Codec"); self.set_combo(self.menu_3, ["Original", "H.264", "H.265", "VP9"], "Original")
            self.lbl_4.setText("Audio Codec"); self.set_combo(self.menu_4, ["Original", "AAC", "MP3", "FLAC", "ALAC", "Opus", "None (Video Only)"], "Original")
        else:
            self.lbl_1.setText("Bitrate"); self.set_combo(self.menu_1, ["Auto", "320 kbps", "256 kbps", "192 kbps", "128 kbps"], "Auto")
            self.lbl_2.setText("Output Format"); self.set_combo(self.menu_2, ["M4A", "MP3", "FLAC", "WAV", "Opus", "Ogg"], "M4A")
            self.lbl_3.setText("Audio Channels"); self.set_combo(self.menu_3, ["Original", "Stereo (2.0)", "Mono (1.0)"], "Original")
            self.lbl_4.setText("Sample Rate"); self.set_combo(self.menu_4, ["Original", "48000 Hz", "44100 Hz"], "Original")

        self.update_folder_context()
        self.evaluate_ui_state()

    def browse_source(self):
        filters = "Audio Files (*.m4a *.mp3 *.flac *.wav *.opus *.ogg);;Video Files (*.mp4 *.mkv *.webm *.mov *.avi)" if self.current_category == self.TAB_C_AUD else "Video Files (*.mp4 *.mkv *.webm *.mov *.avi);;Audio Files (*.m4a *.mp3 *.flac *.wav *.opus *.ogg)"
        file = QFileDialog.getOpenFileName(self, "Select Media File", "", filters)[0]
        if file: self.main_entry.setText(file.replace("\\", "/")); self.evaluate_ui_state()

    def on_advanced_toggle(self):
        self.evaluate_ui_state()
        if self.switch_advanced.isChecked(): self.handle_unified_download()

    def on_extract_audio_toggle(self):
        state = not self.switch_extract_audio.isChecked()
        self.menu_1.setEnabled(state); self.menu_3.setEnabled(state); self.menu_4.setEnabled(state)

    def evaluate_ui_state(self, *args):
        cat = self.current_category
        is_convert = cat in [self.TAB_C_VID, self.TAB_C_AUD]
        text = self.main_entry.text().strip()
        is_valid = bool(text) if is_convert else self.is_valid_media_url(text)
        is_playlist = not is_convert and is_valid and "list=" in text.lower()
        hide_mode = self.config_data.get("General", {}).get("hide_options", False)

        self.btn_download.setText("Convert media" if is_convert else "Download media")
        self.row2_widget.setVisible(is_convert)
        
        # 🔻 LÓGICA DE UPDATE RESTAURADA (Esconde tudo, mostra só a barra) 🔻
        if self.is_updating:
            self.input_frame.setVisible(False)
            self.options_frame.setVisible(False)
            self.switch_advanced.setVisible(False)
            self.switch_extract_audio.setVisible(False)
            self.action_frame.setVisible(False)
            self.status_frame.setVisible(True)
            return
            
        self.input_frame.setVisible(True)
        
        show_options = True
        if not is_convert and hide_mode and not is_valid: show_options = False
        
        show_status = show_options or getattr(self, 'is_queue_running', False)
        
        self.options_frame.setVisible(show_options)
        self.switch_advanced.setVisible(show_options and not is_convert)
        self.switch_extract_audio.setVisible(show_options and cat == self.TAB_C_AUD)
        
        self.action_frame.setVisible(show_status)
        self.status_frame.setVisible(show_status)
        
        if is_valid and not is_convert:
            self.switch_advanced.setEnabled(not is_playlist)
            if is_playlist: self.switch_advanced.setChecked(False)
        else:
            self.switch_advanced.setEnabled(False)
            self.switch_advanced.setChecked(False)

    def schedule_ui_evaluation(self, event=None):
        self.ui_update_timer.start(200)
        
    def reset_status(self, text="Ready!", color=None):
        self.status_timer.stop()
        self.progress_label.setText(text)
        
        # 🔻 Se for um Erro, pinta de vermelho. Se for normal, deixa o Tema escolher a cor "muted"!
        if color:
            self.progress_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        else:
            self.progress_label.setStyleSheet("font-size: 11px;")
            
        if self.current_category in [self.TAB_C_VID, self.TAB_C_AUD] and self.is_busy and not self.is_updating:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 100); self.progress.setValue(0)
            self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['blue']}; }}")
        self.evaluate_ui_state()

    def schedule_reset(self, time_ms=5000):
        self.status_timer.start(time_ms)

    def set_terminal_state(self, label_text, log_msg=""):
        self.progress.setRange(0, 100); self.progress.setValue(100)
        self.progress_label.setText(label_text); self.progress_label.setStyleSheet(f"color: {COLORS['danger']}; font-size: 11px;")
        self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['danger']}; }}") # 👈 BARRA VERMELHA!
        if log_msg: self.add_to_log(log_msg)

    def status_error(self, log_msg=""): self.set_terminal_state("Process Error! (Check Logs)", log_msg)
    def status_canceled(self, log_msg=">>> Process Canceled!"): self.set_terminal_state("Canceled!", log_msg)

    def safe_ui(self, func, *args, **kwargs):
        # Emite o sinal de forma 100% segura, não importa em qual Thread estejamos!
        self.ui_signal.emit(func, args, kwargs)

    def _execute_safe_ui(self, func, args, kwargs):
        # 🔻 ESCUDO BLINDADO: Impede o app de crashar se uma Thread 
        # tentar atualizar um botão ou janela que o usuário já fechou!
        try:
            func(*args, **kwargs)
        except RuntimeError:
            pass

    def is_valid_media_url(self, text_url):
        if not text_url or len(text_url) < 12: return False
        return text_url.startswith("https://") and any(d in text_url.lower() for d in self.valid_domains)

    def paste_url_btn(self):
        try:
            text = QApplication.clipboard().text()[:2000]
            self.main_entry.setText(text); self.evaluate_ui_state()
            if not self.is_busy and not self.is_updating:
                if self.is_valid_media_url(text): self.reset_status("URL Detected!"); self.schedule_reset()
                else: self.reset_status("Invalid URL!", COLORS["danger"]); self.schedule_reset()
        except Exception:
            pass

    def on_clipboard_change(self):
        try:
            if not self.config_data.get("General", {}).get("auto_paste", True) or self.current_category in [self.TAB_C_VID, self.TAB_C_AUD]: return
            text = QApplication.clipboard().text()[:2000]
            if self.is_valid_media_url(text) and self.main_entry.text() != text:
                self.main_entry.setText(text); self.evaluate_ui_state()
                if not self.is_busy and not self.is_updating:
                    self.reset_status("URL Auto-Detected!"); self.schedule_reset()
        except Exception:
            pass

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    l = json.load(f)
                    if "General" not in self.config_data: self.config_data["General"] = {}
                    for key in ["YouTube", "Video", "Save Video"]:
                        if key in l:
                            for k, v in l[key].items():
                                if k == "path": self.config_data["General"]["video_path"] = v
                                elif k in self.config_data[self.TAB_VID]: self.config_data[self.TAB_VID][k] = v
                    for key in ["Music", "Audio", "Save Audio"]:
                        if key in l:
                            for k, v in l[key].items():
                                if k == "path": self.config_data["General"]["audio_path"] = v
                                elif k in self.config_data[self.TAB_AUD]: self.config_data[self.TAB_AUD][k] = v
                    if "General" in l: self.config_data["General"].update(l["General"])
            except Exception as e: self.add_to_log(f">>> Warning: Could not read config.txt: {e}")

    def save_config(self):
        try:
            if not os.path.exists("bin"): os.makedirs("bin")
            with open(self.config_file, "w") as f: json.dump(self.config_data, f, indent=4)
        except Exception as e: self.add_to_log(f">>> ERROR: Failed to save config.txt: {e}")

    def update_folder_context(self):
        is_video = self.current_category in [self.TAB_VID, self.TAB_C_VID]
        self.last_folder = self.config_data["General"]["video_path"] if is_video else self.config_data["General"]["audio_path"]
        
    def refresh_theme_colors(self):
        txt = self.progress_label.text()
        if "Complete" in txt:
            self.progress.setStyleSheet("QProgressBar::chunk { background-color: #2ea043; }")
            self.progress_label.setStyleSheet("color: #2ea043; font-size: 11px;")
        elif "Incomplete" in txt:
            self.progress.setStyleSheet("QProgressBar::chunk { background-color: #d29922; }")
            self.progress_label.setStyleSheet("color: #d29922; font-size: 11px;")
        elif "Error" in txt or "Canceled" in txt or "Failed" in txt or "Invalid" in txt:
            self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['danger']}; }}")
            self.progress_label.setStyleSheet(f"color: {COLORS['danger']}; font-size: 11px;")
        else:
            self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['blue']}; }}")
            self.progress_label.setStyleSheet("font-size: 11px;")

    def add_to_log(self, text):
        self.full_logs_list.append(text)
        if len(self.full_logs_list) > 5000: self.full_logs_list = self.full_logs_list[-5000:]
        
        # 🔻 Usa a nova inserção rápida em vez de reescrever tudo
        if getattr(self, 'log_window', None):
            self.log_window.append_log(text)

    def clear_logs(self):
        self.full_logs_list = ["--- Program Logs ---"]
        if self.log_window: self.log_window.update_logs(self.full_logs_list)
        self.add_to_log(">>> Logs cleared.")

    def copy_logs(self):
        QApplication.clipboard().setText("\n".join(self.full_logs_list))
        self.add_to_log(">>> Logs copied to clipboard.")
    
    def toggle_buttons(self, state, is_downloading=True):
        self.is_busy = (state == "disabled")
        self.btn_cancel.setEnabled(state == "disabled" and is_downloading)
        for btn in self.tab_buttons.values(): btn.setEnabled(state == "normal")
        
        try:
            if hasattr(self, 'about_win') and self.about_win.isVisible():
                self.about_win.update_btn.setEnabled(state == "normal")
        except RuntimeError:
            pass

    def build_base_cmd(self, is_json=False, url="", silent=False):
        cmd = [self.ytdlp_path, "-i"]
        gen_cfg = self.config_data.get("General", {})
        if gen_cfg.get("use_cookies", True):
            c_path = gen_cfg.get("cookies_path", self.cookies_path_default)
            try:
                if os.path.exists(c_path) and os.path.getsize(c_path) > 0: cmd.extend(["--cookies", c_path])
                elif not silent: self.safe_ui(self.add_to_log, ">>> Warning: Cookies.txt file not found or empty. Continuing without cookies.")
            except Exception as e:
                if not silent: self.safe_ui(self.add_to_log, f">>> Warning: Error verifying cookies.txt ({e}). Continuing without cookies.")
        
        if gen_cfg.get("use_proxy", False):
            proxy_url = gen_cfg.get("proxy_url", "").strip()
            if proxy_url:
                cmd.extend(["--proxy", proxy_url])
        
        if is_json: cmd.append("-J")
        else:
            cmd.append("--newline"); cmd.extend(["--retries", str(gen_cfg.get("max_retries", "10"))])
            if gen_cfg.get("prefer_video", False): cmd.append("--no-playlist")
            delay = gen_cfg.get("delay_mode", "Playlist Only")
            apply = (delay == "All Downloads") or (delay == "Playlist Only" and "list=" in url.lower())
            if apply: cmd.extend(["--sleep-interval", str(gen_cfg.get("sleep_min", "2")), "--max-sleep-interval", str(gen_cfg.get("sleep_max", "5")), "--sleep-requests", str(gen_cfg.get("sleep_req", "1"))])
            speed_map = {"1 MB/s": "1M", "5 MB/s": "5M", "10 MB/s": "10M", "25 MB/s": "25M", "50 MB/s": "50M"}
            speed_choice = gen_cfg.get("speed_limit", "Unlimited")
            if speed_choice in speed_map:
                cmd.extend(["--limit-rate", speed_map[speed_choice]])
        return cmd

    def add_subtitle_args(self, base_cmd, cfg):
        if cfg.get("native_subs"): base_cmd.append("--write-subs")
        if cfg.get("auto_subs"): base_cmd.append("--write-auto-subs")
        if cfg.get("native_subs") or cfg.get("auto_subs"):
            src, tgt = cfg.get("langs", "en"), cfg.get("trans_langs", "none")
            s_str = f"{tgt}-{src}*" if tgt != "none" else f"{src}*"
            base_cmd.extend(["--sub-langs", s_str, "--convert-subs", "srt"])
            if cfg.get("embed_subs"): base_cmd.append("--embed-subs")
        return base_cmd

    def handle_unified_download(self):
        if self.switch_advanced.isChecked():
            self.fix_ghost_cursor()
        tab = self.current_category
        if tab == self.TAB_C_VID: self.convert_media("video"); return
        elif tab == self.TAB_C_AUD: self.convert_media("audio"); return
        url = self.main_entry.text().strip()
        if not self.is_valid_media_url(url): self.status_error("ERROR: Invalid URL."); return
        if not os.path.exists(self.ytdlp_path): self.status_error("ERROR: yt-dlp is missing! Please place it in the 'bin' folder."); return
        if tab == self.TAB_VID: self.download_video(url)
        elif tab == self.TAB_AUD: self.download_music(url)

    def download_video(self, url):
        cfg = self.config_data[self.TAB_VID]
        r_path = os.path.expanduser(self.config_data["General"]["video_path"])
        is_social = any(d in url for d in ["instagram.com", "tiktok.com", "kwai.com", "kw.ai", "twitter.com", ".x.com", "facebook.com", "fb.watch", "reddit.com", "linkedin.com", "pinterest.com", "snapchat.com"])
        
        tmpl_map = {"Title (Default)": "%(title)s.%(ext)s", "Title + Video ID": "%(title)s [%(id)s].%(ext)s", "Title + Format ID": "%(title)s [%(format_id)s].%(ext)s", "Title + Resolution": "%(title)s [%(resolution)s].%(ext)s"}
        o_tmpl = "%(uploader)s [%(id)s].%(ext)s" if is_social else tmpl_map.get(self.config_data.get("General", {}).get("file_template", "Title (Default)"), "%(title)s.%(ext)s")
        
        b_cmd = self.build_base_cmd(url=url)
        vfmt = self.menu_2.currentText().lower()
        if cfg["thumb"] and (self.switch_advanced.isChecked() or vfmt != "webm"): b_cmd.append("--embed-thumbnail")
        if cfg["meta"]: b_cmd.append("--embed-metadata")
        b_cmd = self.add_subtitle_args(b_cmd, cfg)

        if self.switch_advanced.isChecked():
            # 🔻 Salva no 'self' e usa .exec() para bloquear o fundo corretamente
            self.manual_win = ManualSelectionDialog(url, b_cmd, o_tmpl, ["MP4", "MKV", "WEBM"], self)
            self.manual_win.exec()
            self.switch_advanced.setChecked(False)
            self.evaluate_ui_state()
            return

        res_map = {"360p": "360", "480p": "480", "720p": "720", "1080p (H.264)": "1080", "1080p (AV1/VP9)": "1080", "1440p (QHD)": "1440", "2160p (4K)": "2160"}
        sq = self.menu_1.currentText()
        
        pending_logs = [] # 👈 Retém o log!
        if vfmt == "webm" and sq == "1080p (H.264)": 
            sq = "1080p (AV1/VP9)"
            pending_logs.append("[Auto-Fix] Forced VP9/Opus for WEBM.") 
        
        r = res_map[sq]
        if sq == "1080p (H.264)": s_str = f"res:{r},vcodec:avc1,aext:m4a"
        elif vfmt == "mp4": s_str = f"res:{r},aext:m4a"
        elif vfmt == "webm": s_str = f"res:{r},vcodec:vp9,aext:opus"
        elif vfmt == "mkv": s_str = f"res:{r},aext:opus"
        else: s_str = f"res:{r}"

        cmd = b_cmd + ["-S", s_str, "--merge-output-format", vfmt, "--remux-video", vfmt, "-o", f"{r_path}/{o_tmpl}", "-o", f"subtitle:{r_path}/subtitles/{o_tmpl}", url]
        self.run_command(cmd, url, pending_logs) # 👈 Passa o log para a fila!

    def download_music(self, url):
        cfg = self.config_data[self.TAB_AUD]
        r_path = os.path.expanduser(self.config_data["General"]["audio_path"])
        afmt, q = self.menu_2.currentText().lower(), self.menu_1.currentText()
        b_cmd = self.build_base_cmd(url=url) + ["-x"]
        if not self.switch_advanced.isChecked(): b_cmd.extend(["--audio-format", afmt])
        
        if cfg["thumb"] and (self.switch_advanced.isChecked() or afmt != "wav"): b_cmd.append("--embed-thumbnail")
        if cfg["meta"] and (self.switch_advanced.isChecked() or afmt != "wav"):
            b_cmd.extend(["--embed-metadata", "--parse-metadata", "%(playlist_index|)s:%(track_number)s", "--parse-metadata", "%(release_year,release_date,date,upload_date).4s:%(meta_date)s", "--parse-metadata", "%(album_artist,creator,channel|)s:%(meta_album_artist)s"])
            
        if self.switch_advanced.isChecked():
            self.manual_win = ManualSelectionDialog(url, b_cmd, "%(playlist_index&{}. |)s%(title)s.%(ext)s", ["M4A", "MP3", "FLAC", "WAV", "Opus"], self)
            self.manual_win.exec()
            self.switch_advanced.setChecked(False)
            self.evaluate_ui_state()
            return
            
        b_map = {"Low (128 kbps)": "128k", "Medium (192 kbps)": "192k", "High (320 kbps)": "320k"}
        if q != "Auto": b_cmd.extend(["--audio-quality", b_map.get(q)])
        cmd = b_cmd + ["-o", f"{r_path}/%(playlist_index&{{}}. |)s%(title)s.%(ext)s", url]
        self.run_command(cmd, url)
    
    def get_audio_codec(self, filepath):
        """Descobre o codec real lendo os metadados do arquivo."""
        ffprobe_exe = os.path.join(bin_path, f"ffprobe{self.exe}").replace("\\", "/")
        if not os.path.exists(ffprobe_exe): ffprobe_exe = "ffprobe"
        
        try:
            cmd = [ffprobe_exe, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1", filepath]
            res = subprocess.run(cmd, capture_output=True, text=True, startupinfo=self.startupinfo)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip().lower()
        except: pass
            
        try:
            ffmpeg_exe = os.path.join(bin_path, f"ffmpeg{self.exe}").replace("\\", "/")
            if not os.path.exists(ffmpeg_exe): ffmpeg_exe = "ffmpeg"
            cmd = [ffmpeg_exe, "-i", filepath]
            res = subprocess.run(cmd, capture_output=True, text=True, startupinfo=self.startupinfo)
            match = re.search(r'Audio:\s*([a-zA-Z0-9_]+)', res.stderr)
            if match: return match.group(1).lower()
        except: pass
            
        return "unknown"
    
    def convert_media(self, media_type):
        src = self.main_entry.text().strip()
        if not os.path.exists(src): self.status_error("ERROR: Source file does not exist."); return
        
        is_vid = media_type == "video"
        base = os.path.splitext(os.path.basename(src))[0]
        e_fin = self.menu_2.currentText().lower()
        s_ext = os.path.splitext(src)[1].lower()
        suf = "extracted" if not is_vid and self.switch_extract_audio.isChecked() else "converted"
        gen_cfg = self.config_data.get("General", {})
        save_dir = os.path.expanduser(gen_cfg.get("video_path") if is_vid else gen_cfg.get("audio_path"))
        
        try:
            if not os.path.exists(save_dir): os.makedirs(save_dir)
        except Exception as e:
            self.status_error(f"Folder Access Error: {e}")
            return
        dst = os.path.join(save_dir, f"{base}_{suf}.{e_fin}").replace("\\", "/")
        if src == dst: dst = os.path.join(save_dir, f"{base}_new.{e_fin}").replace("\\", "/")
        
        ff_exe = os.path.join("bin", f"ffmpeg{self.exe}").replace("\\", "/")
        if not os.path.exists(ff_exe):
            try:
                subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                ff_exe = "ffmpeg"
            except Exception:
                self.safe_ui(self.status_error, "ERROR: FFmpeg is missing! Please check your 'bin' folder.")
                return
        cmd = [ff_exe, "-y", "-i", src]
        pending_logs = []

        if is_vid:
            vc_map = {"Original": "copy", "H.264": "libx264", "H.265": "libx265", "VP9": "libvpx-vp9"}
            ac_map = {"Original": "copy", "AAC": "aac", "MP3": "libmp3lame", "FLAC": "flac", "ALAC": "alac", "Opus": "libopus", "None (Video Only)": "none"}
            vc, ac = vc_map.get(self.menu_3.currentText(), "copy"), ac_map.get(self.menu_4.currentText(), "copy")
            
            if e_fin in ["mp4", "mov"] and ac == "flac":
                ac = "alac"
                pending_logs.append(f"[Auto-Fix] Swapped FLAC for ALAC for {e_fin.upper()} lossless compatibility.")
                
            r_c = self.menu_1.currentText()
            sf = None
            if r_c != "Original" and vc != "none":
                th = {"2160p (4K)": "2160", "1440p (QHD)": "1440", "1080p": "1080", "720p": "720", "480p": "480", "360p": "360"}.get(r_c)
                if th:
                    sf = f"scale=-2:{th}"
                    if vc == "copy":
                        if e_fin == "webm":
                            vc = "libvpx-vp9"
                            pending_logs.append(f"[Auto-Fix] Forced VP9 codec to allow scaling to {th}p.")
                        else:
                            vc = "libx264"
                            pending_logs.append(f"[Auto-Fix] Forced H.264 codec to allow scaling to {th}p.")
            
            if e_fin == "avi":
                if vc in ["copy", "libvpx-vp9"]:
                    vc = "libx264"
                    pending_logs.append("[Auto-Fix] Forced H.264 codec for AVI compatibility.")
                if ac in ["copy", "aac", "flac", "alac", "libopus"]:
                    ac = "libmp3lame"
                    pending_logs.append("[Auto-Fix] Forced MP3 codec for AVI compatibility.")
                    
            elif e_fin == "webm":
                if vc in ["copy", "libx264", "libx265"]:
                    vc = "libvpx-vp9"
                    pending_logs.append("[Auto-Fix] Forced VP9 codec for WEBM compatibility.")
                if ac in ["copy", "aac", "libmp3lame", "flac", "alac"]:
                    ac = "libopus"
                    pending_logs.append("[Auto-Fix] Forced Opus codec for WEBM compatibility.")
                    
            elif e_fin in ["mp4", "mov"]:
                if vc == "libvpx-vp9":
                    vc = "libx264"
                    pending_logs.append(f"[Auto-Fix] Forced H.264 (VP9 is incompatible with {e_fin.upper()}).")
                if ac == "libopus":
                    ac = "aac"
                    pending_logs.append(f"[Auto-Fix] Forced AAC (Opus is incompatible with {e_fin.upper()}).")
                if s_ext in [".webm", ".mkv", ".ogg"]:
                    if vc == "copy":
                        vc = "libx264"
                        pending_logs.append(f"[Auto-Fix] Forced H.264 to safely put WEBM/MKV into {e_fin.upper()}.")
                    if ac == "copy":
                        ac = "aac"
                        pending_logs.append(f"[Auto-Fix] Forced AAC audio to safely put WEBM/MKV into {e_fin.upper()}.")
            
            # 🔻 LÓGICA DOS PERFIS (Padrão vs Custom)
            is_custom = gen_cfg.get("custom_profile", False)
            
            if is_custom:
                crf = gen_cfg.get("custom_crf", "18")
                v_preset = gen_cfg.get("custom_preset", "faster")
                v_cpu = gen_cfg.get("custom_cpu_used", "4")
            else:
                prof = gen_cfg.get("conv_profile", "High Quality")
                crf = "18" if prof == "High Quality" else ("20" if prof == "Balanced" else "22")
                v_preset = "faster"
                v_cpu = "4"
            
            if vc == "none": cmd.append("-vn")
            else:
                cmd.extend(["-c:v", vc])
                if sf: cmd.extend(["-vf", sf])
                
                if vc == "libvpx-vp9": cmd.extend(["-crf", crf, "-b:v", "0", "-row-mt", "1", "-cpu-used", v_cpu])
                elif vc == "libx264": cmd.extend(["-crf", crf, "-preset", v_preset, "-pix_fmt", "yuv420p"])
                elif vc == "libx265": cmd.extend(["-crf", crf, "-preset", v_preset, "-tag:v", "hvc1"])
                elif vc != "copy": cmd.extend(["-crf", crf])

            if ac == "none": cmd.append("-an")
            else:
                cmd.extend(["-c:a", ac])
                if ac not in ["copy", "flac", "alac"]: cmd.extend(["-b:a", "192k"])
        else:
            cmd.append("-vn")
            dst_fmt = self.menu_2.currentText().lower()
            
            if self.switch_extract_audio.isChecked():
                if dst_fmt in ["mp3", "wav", "flac", "ogg", "opus", "m4a"]:
                    src_codec = self.get_audio_codec(src)
                    copy_allowed = {"m4a": ["aac", "alac"], "mp3": ["mp3"], "flac": ["flac"], "wav": ["pcm_s16le"], "opus": ["opus"], "ogg": ["vorbis"]}
                    allowed_codecs = copy_allowed.get(dst_fmt, [])
                    
                    if src_codec in allowed_codecs:
                        cmd.extend(["-c:a", "copy"])
                        pending_logs.append(f">>> [Smart Extract] Source codec '{src_codec}' matches '{dst_fmt.upper()}'. Proceeding with lossless direct copy.")
                    else:
                        ac_map = {"mp3": "libmp3lame", "wav": "pcm_s16le", "flac": "flac", "ogg": "libvorbis", "opus": "libopus", "m4a": "aac"}
                        ac = ac_map.get(dst_fmt)
                        cmd.extend(["-c:a", ac])
                        if dst_fmt in ["mp3", "ogg"]: cmd.extend(["-q:a", "2"])
                        elif dst_fmt in ["m4a", "opus"]: cmd.extend(["-b:a", "192k"])
                        pending_logs.append(f">>> [Smart Extract] Source codec '{src_codec}' is incompatible with '{dst_fmt.upper()}'. Recoding safely to '{ac}'.")
                else:
                    cmd.extend(["-c:a", "copy"])
                    
            else:
                amap = {"m4a": "aac", "mp3": "libmp3lame", "flac": "flac", "wav": "pcm_s16le", "opus": "libopus", "ogg": "libvorbis"}
                ac = amap.get(dst_fmt, "copy")
                cmd.extend(["-c:a", ac])
                
                br, sr, ch = self.menu_1.currentText(), self.menu_4.currentText(), self.menu_3.currentText()
                if br != "Auto" and ac not in ["copy", "flac", "alac", "pcm_s16le"]: 
                    cmd.extend(["-b:a", br.replace(" kbps", "k")])
                elif br == "Auto":
                    if ac in ["libmp3lame", "libvorbis"]: cmd.extend(["-q:a", "2"])
                    elif ac in ["aac", "libopus"]: cmd.extend(["-b:a", "192k"])
                if sr != "Original" and ac != "copy": cmd.extend(["-ar", sr.replace(" Hz", "")])
                if ch != "Original" and ac != "copy": cmd.extend(["-ac", "2" if "Stereo" in ch else "1"])
        
        cmd.append(dst); self.run_command(cmd, base, pending_logs)

    def run_command(self, cmd, task_name="Media Task", task_logs=None):
        is_conv = self.current_category in [self.TAB_C_VID, self.TAB_C_AUD]
        # 🔻 Adicionado a chave "logs" no dicionário da tarefa
        qi = {"cmd": cmd, "name": task_name, "is_convert": is_conv, "logs": task_logs or []}
        self.download_queue.append(qi)
        
        def animate_btn():
            self.queue_animating = True
            count = len(self.download_queue)
            self.queue_btn.setText(f"✅ Added! ({count})")
            def revert():
                self.queue_animating = False
                if self.isVisible(): self.queue_btn.setText(f"📥 Queue ({len(self.download_queue)})")
            QTimer.singleShot(2000, revert)
            
        self.safe_ui(animate_btn)
        self.safe_ui(self.update_queue_ui)

        if not is_conv and task_name.startswith("http"):
            def fetch_title():
                try:
                    t_cmd = self.build_base_cmd(is_json=True, silent=True) + ["--flat-playlist", "--no-warnings", "--playlist-items", "1", task_name]
                    res = subprocess.run(t_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', startupinfo=self.startupinfo)
                    if res.returncode == 0:
                        info = json.loads(res.stdout.strip())
                        p_t = info.get('playlist_title') or info.get('playlist')
                        n_name = f"[Playlist] {p_t}" if p_t else (f"[Playlist] {info.get('title')}" if "list=" in task_name.lower() else info.get('title') or task_name)
                        qi["name"] = n_name; self.safe_ui(self.update_queue_ui)
                except: pass
            threading.Thread(target=fetch_title, daemon=True).start()

        if not self.is_queue_running: self.process_next_in_queue()

    def update_queue_ui(self):
        if self.queue_window and self.queue_window.isVisible(): 
            self.queue_window.update_list(self.download_queue, self.is_queue_running)

    def clear_entire_queue(self):
        if self.is_queue_running and self.download_queue: self.download_queue = [self.download_queue[0]]
        else: self.download_queue.clear()
        self.queue_btn.setText(f"📥 Queue ({len(self.download_queue)})"); self.update_queue_ui()

    def remove_from_queue(self, index):
        if 0 <= index < len(self.download_queue):
            self.download_queue.pop(index)
            self.queue_btn.setText(f"📥 Queue ({len(self.download_queue)})"); self.update_queue_ui()

    def move_queue_item(self, index, direction):
        n_idx = index + direction
        if 0 <= n_idx < len(self.download_queue):
            self.download_queue[index], self.download_queue[n_idx] = self.download_queue[n_idx], self.download_queue[index]
            self.update_queue_ui()
            
    def _finish_task(self, is_conv, err, d_str, t_f=None):
        if self.is_cancelling:
            self.status_canceled()
            if is_conv and t_f and os.path.exists(t_f):
                try: 
                    os.remove(t_f)
                    self.add_to_log(f">>> Incomplete file deleted: {os.path.basename(t_f)}")
                except Exception as e: 
                    self.add_to_log(f">>> Warning: Could not delete incomplete file: {e}")
            
            # 🔻 CORREÇÃO: AVISAMOS QUE A FILA PAROU ANTES DE LIMPAR! (Adeus, fantasma)
            self.is_queue_running = False
            self.clear_entire_queue()
            self.toggle_buttons("normal")
            return
            
        elif not err:
            msg = f"Conversion Complete! (Total time: {d_str})" if is_conv else f"Download Complete! (Total time: {d_str})"
            self.progress_label.setText(msg); self.progress_label.setStyleSheet("color: #2ea043; font-size: 11px;")
            self.progress.setRange(0, 100); self.progress.setValue(100)
            self.progress.setStyleSheet("QProgressBar::chunk { background-color: #2ea043; }") # 👈 VERDE SUAVE
            self.add_to_log(f">>> {msg}\n")
        else:
            is_p = getattr(self, 'current_playlist_item', '') != ""
            if is_conv or is_p:
                msg = "Conversion Incomplete (Check Logs)" if is_conv else "Download Incomplete (Check Logs)"
                self.progress_label.setText(msg); self.progress_label.setStyleSheet("color: #d29922; font-size: 11px;")
                self.progress.setRange(0, 100); self.progress.setValue(100)
                self.progress.setStyleSheet("QProgressBar::chunk { background-color: #d29922; }") # 👈 BARRA AMARELA!
                self.add_to_log(f">>> {msg}\n")
            else:
                self.status_error()
        
        if self.download_queue: self.download_queue.pop(0)
        QTimer.singleShot(2000 if err else 500, self.process_next_in_queue)

    def process_next_in_queue(self):
        if not self.download_queue:
            self.is_queue_running = False
            self.queue_start_time = None
            self.queue_btn.setText("📥 Queue (0)")
            self.update_queue_ui()
            self.toggle_buttons("normal")
            return

        if not getattr(self, 'queue_start_time', None):
            self.queue_start_time = time.time()

        # 🔻 AS DUAS LINHAS QUE FALTAVAM AQUI! 🔻
        self.is_queue_running = True
        task = self.download_queue[0]

        if not getattr(self, 'queue_animating', False):
            self.queue_btn.setText(f"📥 Queue ({len(self.download_queue)})")
        self.update_queue_ui()

        cmd = task["cmd"]; is_conv = task["is_convert"]; self.is_cancelling = False
        self.status_timer.stop()
        self.toggle_buttons("disabled"); self.current_playlist_item = ""

        if is_conv:
            self.progress.setRange(0, 0); self.progress_label.setText("Starting conversion..."); self.progress_label.setStyleSheet("font-size: 11px;")
            self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['blue']}; }}")
            self.add_to_log("\n>>> Starting conversion...")
        else:
            self.progress.setRange(0, 100); self.progress.setValue(0); self.progress_label.setText("Starting download..."); self.progress_label.setStyleSheet("font-size: 11px;")
            self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['blue']}; }}")
            self.add_to_log("\n>>> Starting download...")

        # 🔻 DESPEJA OS LOGS RETIDOS NA HORA CERTA! 🔻
        for log_msg in task.get("logs", []):
            self.add_to_log(log_msg)

        def worker():
            err = False
            try:
                kwargs = {'startupinfo': self.startupinfo}
                if not self.is_windows:
                    kwargs['preexec_fn'] = os.setsid

                self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8', errors='replace', **kwargs)
                for line in self.current_process.stdout:
                    c = line.strip()
                    if c:
                        if "ERROR:" in c or "Invalid data found" in c: err = True; self.safe_ui(self.add_to_log, c); continue
                        if is_conv and "time=" in c:
                            el = int(time.time() - getattr(self, 'queue_start_time', time.time()))
                            self.safe_ui(lambda d=f"{el//60}m {el%60}s" if el>=60 else f"{el}s": self.progress_label.setText(f"Converting... (Elapsed time: {d})"))
                        if not is_conv and "Downloading item" in c:
                            m = re.search(r"Downloading item (\d+ of \d+)", c)
                            if m: self.current_playlist_item = f" [Item {m.group(1)}]"
                        if "100%" in c or "already been downloaded" in c or "already is in target format" in c:
                            self.safe_ui(self.add_to_log, c)
                            if not is_conv: self.safe_ui(lambda: self.progress.setValue(100))
                        elif "B/s" not in c and "ETA" not in c and "time=" not in c: self.safe_ui(self.add_to_log, c)
                        if not is_conv:
                            m = self.re_progress.search(c)
                            if m and not err and not self.is_cancelling:
                                self.safe_ui(lambda v=float(m.group(1)): (self.progress.setValue(int(v)), self.progress_label.setText(f"Downloading{self.current_playlist_item}... {int(v)}%")))

                self.current_process.wait()
                if is_conv: self.safe_ui(lambda: self.progress.setRange(0, 100))
                
                el = int(time.time() - getattr(self, 'queue_start_time', time.time()))
                d_str = f"{el//60}m {el%60}s" if el>=60 else f"{el}s"
                t_f = cmd[-1] if is_conv else None
                
                self.safe_ui(lambda: self._finish_task(is_conv, err, d_str, t_f))
                
            except Exception as e:
                self.safe_ui(self.status_error, f"SYSTEM ERROR: {e}")
                # 🔻 A CORREÇÃO: Avisa a central para finalizar e remover o item defeituoso!
                self.safe_ui(lambda: self._finish_task(is_conv, True, "0s", None))
            finally:
                self.current_process = None; self.safe_ui(lambda: self.btn_cancel.setText("Cancel"))
        threading.Thread(target=worker, daemon=True).start()

    def cancel_download(self):
        proc = self.current_process
        if proc and not self.is_cancelling:
            self.btn_cancel.setEnabled(False); self.btn_cancel.setText("Cancelling...")
            self.is_cancelling = True; self.add_to_log(">>> Attempting to force close process...")
            try:
                if self.is_windows:
                    res = subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)], capture_output=True, text=True, encoding='oem', errors='replace', startupinfo=self.startupinfo, timeout=3)
                    if res.stdout: self.add_to_log(res.stdout.strip())
                    if res.stderr: self.add_to_log(res.stderr.strip())
                else: 
                    import signal
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception as e: 
                self.add_to_log(f">>> Failed to close process: {e}")
                self.is_cancelling = False

    def open_folder(self):
        try:
            p = os.path.expanduser(self.last_folder)
            if not os.path.exists(p): os.makedirs(p)
            if self.is_windows: os.startfile(os.path.realpath(p))
            elif sys.platform == "darwin": subprocess.Popen(["open", p])
            else: subprocess.Popen(["xdg-open", p])
        except Exception as e:
            QMessageBox.critical(self, "Folder Error", f"Could not open or create output folder:\n{e}")

    def fix_ghost_cursor(self):
        # Resolve o bug do cursor travado ao abrir janelas modais
        btn = self.sender()
        if btn:
            btn.setCursor(Qt.CursorShape.ArrowCursor)
            QTimer.singleShot(300, lambda: btn.setCursor(Qt.CursorShape.PointingHandCursor) if btn else None)
    
    def show_queue(self):
        self.fix_ghost_cursor()
        if not getattr(self, 'queue_window', None): self.queue_window = QueueDialog(self)
        self.queue_window.show()
        self.queue_window.raise_()
        self.update_queue_ui()

    def show_logs(self):
        self.fix_ghost_cursor()
        if not getattr(self, 'log_window', None): 
            self.log_window = LogsDialog(self)
            self.log_window.update_logs(self.full_logs_list)
        self.log_window.show()
        self.log_window.raise_()

    def show_settings(self): 
        self.fix_ghost_cursor()
        self.settings_win = SettingsDialog(self)
        self.settings_win.exec()
        
    def show_about(self): 
        self.fix_ghost_cursor()
        self.about_win = AboutDialog(self)
        self.about_win.exec()

    def check_ytdlp_updates(self):
        if not os.path.exists(self.ytdlp_path):
            self.safe_ui(self.add_to_log, ">>> Warning: yt-dlp is missing! Update check skipped. Please check your 'bin' folder.")
            return
        try:
            self.safe_ui(self.toggle_buttons, "disabled", False)
            p = subprocess.Popen([self.ytdlp_path, "-U"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', startupinfo=self.startupinfo)
            for line in p.stdout:
                if line.strip(): self.safe_ui(self.add_to_log, f"[yt-dlp update] {line.strip()}")
            p.wait()
        except Exception as e: self.safe_ui(self.add_to_log, f"ERROR: {e}")
        finally: 
            def restore_ui():
                if not self.is_queue_running:
                    self.toggle_buttons("normal")
                    self.reset_status()
            self.safe_ui(restore_ui)

    def get_local_version(self):
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, "r", encoding='utf-8') as f: 
                    return f.read().strip()
            except Exception:
                pass
        return "Unknown"

    def start_github_update(self, btn=None, dialog=None):
        self.is_updating = True
        self.safe_ui(self.toggle_buttons, "disabled", False) # Bloqueia abas
        self.reset_status("Checking for updates...")         # Força a interface a se esconder
        
        def task():
            try:
                v = self.get_local_version()
                r = requests.get("https://api.github.com/repos/DanMixerBR/CopynDown/releases/latest", timeout=10).json()
                rv = re.search(r'\d+(\.\d+)+', r['tag_name']).group()
                if rv != v:
                    def ask():
                        QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
                        ans = QMessageBox.question(self, "Update", f"Update available: {rv}\nUpdate now?")
                        QApplication.restoreOverrideCursor()
                            
                        if ans == QMessageBox.StandardButton.Yes:
                            # 1º Ação Crítica: Inicia a thread de update PRIMEIRO
                            threading.Thread(target=self.do_update, daemon=True).start()
                            # 2º Ação Visual: Tenta fechar o dialog (blindado)
                            try:
                                if dialog: dialog.accept()
                            except RuntimeError: pass
                        else:
                            self.is_updating = False
                            self.safe_ui(self.toggle_buttons, "normal") 
                            self.safe_ui(self.reset_status)
                            
                            try:
                                if btn: 
                                    btn.setEnabled(True)
                                    btn.setText("Check for updates")
                            except RuntimeError: pass
                    self.safe_ui(ask)
                else:
                    self.is_updating = False; self.safe_ui(self.reset_status)
                    def show_info():
                        QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
                        QMessageBox.information(self, "Up to date", "You are using the latest version.")
                        QApplication.restoreOverrideCursor()
                        
                        # 1º Ação Crítica: Destrava o aplicativo PRIMEIRO
                        self.safe_ui(self.toggle_buttons, "normal")
                        
                        # 2º Ação Visual: Restaura o botão (blindado)
                        try:
                            if btn: 
                                btn.setEnabled(True)
                                btn.setText("Check for updates")
                        except RuntimeError: pass
                        
                    self.safe_ui(show_info)
            except Exception as e:
                self.is_updating = False
                err_msg = str(e) # 🔻 Congela a mensagem de erro ANTES do 'e' sumir!
                
                self.safe_ui(self.set_terminal_state, "Update Failed!", f"ERROR: {err_msg}")
                self.safe_ui(self.schedule_reset)
                
                def show_api_err(msg=err_msg): # 🔻 Passa a mensagem congelada
                    QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
                    QMessageBox.critical(self, "Update Error", f"ERROR: {msg}")
                    QApplication.restoreOverrideCursor()
                self.safe_ui(show_api_err)
                
                if btn: self.safe_ui(lambda: (btn.setEnabled(True), btn.setText("Check for updates")))
                self.safe_ui(self.toggle_buttons, "normal") # Reativa as abas
        threading.Thread(target=task, daemon=True).start()

    def do_update(self):
        try:
            self.safe_ui(lambda: (
                self.progress.setRange(0, 100), 
                self.progress_label.setText("Starting update..."), 
                self.progress_label.setStyleSheet("font-size: 11px;")
            ))
            self.safe_ui(self.add_to_log, "\n>>> Downloading update file...")
            
            url = "https://github.com/DanMixerBR/CopynDown/releases/latest/download/CopynDown_Windows.zip" if self.is_windows else "https://github.com/DanMixerBR/CopynDown/releases/latest/download/CopynDown_Linux.zip"
            zip_platform = "CopynDown_Windows.zip" if self.is_windows else "CopynDown_Linux.zip"
            
            # 🔻 CORREÇÃO 1: Salvando com o nome exato que o update.bat e update.sh esperam
            z_path = os.path.join(base_dir, zip_platform) 
            hash_url = "https://raw.githubusercontent.com/DanMixerBR/CopynDown/refs/heads/main/hash_v2.txt"
            
            if os.path.exists(z_path): os.remove(z_path)

            r = requests.get(url, stream=True, timeout=30)
            r.raise_for_status()
            
            sz = int(r.headers.get('content-length', 0))
            d = 0
            last_reported = 0

            with open(z_path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk); d += len(chunk)
                        if sz > 0:
                            percent = int((d / sz) * 50) 
                            if percent - last_reported >= 1 or d == sz:
                                self.safe_ui(lambda p=percent: (
                                    self.progress.setValue(p),
                                    self.progress_label.setText(f"Downloading update... {p*2}%")
                                ))
                                last_reported = percent

            zip_size_mb = os.path.getsize(z_path) / (1024 * 1024)
            if zip_size_mb < 100.0:
                if os.path.exists(z_path): os.remove(z_path)
                raise Exception(f"ERROR: File suspiciously small ({zip_size_mb:.1f} MB). Aborted.")

            self.safe_ui(lambda: (
                self.progress_label.setText("Verifying update... 50%"),
                self.progress.setValue(50)
            ))
            self.safe_ui(self.add_to_log, "Verifying update file...")

            with zipfile.ZipFile(z_path, 'r') as zf:
                corrupt_file = zf.testzip()
            if corrupt_file is not None:
                if os.path.exists(z_path): os.remove(z_path)
                raise Exception("ERROR: The downloaded zip structure is corrupted.")
            
            self.safe_ui(self.add_to_log, "File structure verified (OK).")

            r_hash = requests.get(hash_url, timeout=10)
            if r_hash.status_code == 200:
                expected_hashes = [line.strip().lower().replace("sha256:", "") for line in r_hash.text.splitlines() if line.strip()]
                sha256_hash = hashlib.sha256()
                with open(z_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                if sha256_hash.hexdigest().lower() not in expected_hashes:
                    if os.path.exists(z_path): os.remove(z_path)
                    raise Exception("Security Error: Hash verification failed!")
                self.safe_ui(self.add_to_log, "Hash verification (OK).")
            else:
                if os.path.exists(z_path): os.remove(z_path)
                raise Exception("Security Error: Could not download hash_v2.txt.")

            self.safe_ui(lambda: (
                self.progress_label.setText("Preparing update... 75%"),
                self.progress.setValue(75)
            ))
            self.safe_ui(self.add_to_log, "Downloading update script...")

            s_ext = "bat" if self.is_windows else "sh"
            s_path = os.path.join(base_dir, f"update.{s_ext}")
            r_s = requests.get(f"https://raw.githubusercontent.com/DanMixerBR/CopynDown/refs/heads/main/update.{s_ext}", timeout=10)
            if r_s.status_code == 200:
                with open(s_path, 'wb') as f: f.write(r_s.content)
            else:
                raise Exception("Could not download update script.")

            self.safe_ui(lambda: (
                self.progress_label.setText("Update Ready! (100%)"),
                self.progress_label.setStyleSheet("color: #2ea043; font-size: 11px;"),
                self.progress.setStyleSheet("QProgressBar::chunk { background-color: #2ea043; }"),
                self.progress.setValue(100)
            ))
            self.safe_ui(self.add_to_log, ">>> Update downloaded and verified successfully!")

            def finish_update():
                QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
                QMessageBox.information(self, "Success", "Update Ready! The app will close to complete the update.")
                QApplication.restoreOverrideCursor()
                if os.path.exists(s_path):
                    # 🔻 CORREÇÃO 2: Lógica Original de Execução + cwd=base_dir
                    if self.is_windows:
                        # O cwd garante que o script rode na pasta correta, independentemente de espaços no caminho
                        subprocess.Popen(['cmd.exe', '/c', f"update.{s_ext}"], cwd=base_dir, creationflags=0x00000010)
                    else:
                        os.chmod(s_path, 0o755)
                        limpo_env = os.environ.copy()
                        limpo_env.pop("LD_LIBRARY_PATH", None)
                        limpo_env.pop("GTK_PATH", None)
                        comando_bash = f'cd "{base_dir}" && bash update.sh'
                        terminais = [['x-terminal-emulator', '-e'], ['gnome-terminal', '--'], ['konsole', '-e'], ['xfce4-terminal', '-x']]
                        
                        abriu_terminal = False
                        for term in terminais:
                            try:
                                subprocess.Popen(term + ['bash', '-c', comando_bash], env=limpo_env, start_new_session=True)
                                abriu_terminal = True
                                break
                            except Exception: continue
                                
                        if not abriu_terminal:
                            subprocess.Popen(['bash', s_path], cwd=base_dir, env=limpo_env, start_new_session=True)
                
                os._exit(0)

            self.safe_ui(finish_update)

        except Exception as e:
            self.is_updating = False
            err_msg = str(e) # 🔻 Congela a mensagem de erro!
            
            self.safe_ui(self.set_terminal_state, "Update Failed!", f"ERROR: {err_msg}")
            self.safe_ui(self.evaluate_ui_state)
            self.safe_ui(self.toggle_buttons, "normal")
            
            def show_err(msg=err_msg): # 🔻 Passa a mensagem congelada
                QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
                QMessageBox.critical(self, "Update Error", f"ERROR: {msg}")
                QApplication.restoreOverrideCursor()
            self.safe_ui(show_err)

    def closeEvent(self, event):
        proc = self.current_process
        if proc:
            try:
                if self.is_windows: 
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)], capture_output=True, startupinfo=self.startupinfo, timeout=2)
                else: 
                    import signal
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except: pass
        event.accept(); os._exit(0)

def main():
    if sys.platform.startswith("linux"):
        os.environ["QT_QPA_PLATFORMTHEME"] = "xdgdesktopportal"
    app = QApplication(sys.argv)
    app.setApplicationName("CopynDown")
    set_app_icon(app)
    app.setStyleSheet(get_app_qss())
    win = CopynDownApp()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
