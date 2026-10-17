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
from PySide6.QtGui import QFont, QFontDatabase, QIcon, QPainter, QColor, QImage, QPixmap, QTextCursor, QFontMetrics

def qt_message_handler(mode, context, message):
    filtros = [
        "QThreadStorage", 
        "QFont::setPointSize", 
        "zwp_text_input_v3_leave",
        "must be a top level window"
    ]

    if not any(f in message for f in filtros):
        sys.stdout.write(f"{message}\n")

qInstallMessageHandler(qt_message_handler)

from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton,
    QProgressBar, QRadioButton, QScrollArea, QSizePolicy, QStackedWidget,
    QTextEdit, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QSystemTrayIcon
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
        "success": "#2ea043", "warning": "#d29922",
    },
    "light": {
        "bg": "#ffffff", "card": "#f0f2f5", "input": "#ffffff", "input2": "#e4e6eb",
        "border": "#ccd0d5", "blue": "#3ba1ff", "blue_hover": "#288ce6", "blue_dark": "#1d4ed8",
        "button": "#f0f2f5", "button_hover": "#e4e6eb", "combo_button": "#e4e6eb", 
        "text": "#1c1e21", "muted": "#606770", "muted2": "#8d949e", "danger": "#ff5252",
        "success": "#2ecc71", "warning": "#f4b740",
    }
}
COLORS = THEMES[CURRENT_THEME]

APP_FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Sans Serif"

def apply_theme_titlebar(window):
    if sys.platform == "win32":
        try:
            hwnd = window.winId().__int__()
            if CURRENT_THEME == "dark":
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(ctypes.c_int(0x001F1A18)), 4)
            else:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(0)), 4)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(ctypes.c_int(0x00FFFFFF)), 4) 
        except Exception: pass

def center_window(window):
    screen_center = QApplication.primaryScreen().availableGeometry().center()
    frame_geo = window.frameGeometry()
    frame_geo.moveCenter(screen_center)
    window.move(frame_geo.topLeft())

def set_app_icon(app):
    for icon_name in ("icon.ico", "icon.png", "logo.png"):
        icon_path = os.path.join(bin_path, "icons", icon_name).replace("\\", "/")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            break

def load_app_font(app):
    global APP_FONT_FAMILY
    if sys.platform == "win32":
        APP_FONT_FAMILY = "Segoe UI"
        app.setFont(QFont(APP_FONT_FAMILY, 9))
        print("Using Windows system font:", APP_FONT_FAMILY)
        return

    font_path = os.path.join(bin_path, "Inter.ttf").replace("\\", "/")
    font_id = QFontDatabase.addApplicationFont(font_path) if os.path.exists(font_path) else -1

    if font_id != -1:
        families = QFontDatabase.applicationFontFamilies(font_id)
        APP_FONT_FAMILY = families[0] if families else APP_FONT_FAMILY
        print("External font loaded:", APP_FONT_FAMILY)
    else:
        print("External font not loaded. Using fallback font:", APP_FONT_FAMILY)

    app.setFont(QFont(APP_FONT_FAMILY, 9))

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
* {{ font-family: '{APP_FONT_FAMILY}'; font-size: 12px; color: {COLORS['text']}; outline: none; }}
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
QPushButton#browseButton:hover {{ background-color: {COLORS['blue']}; color: white; }}
QPushButton#pill {{ background-color: transparent; color: {COLORS['muted']}; border-radius: 18px; padding: 8px 12px; font-weight: 700; min-width: 82px; min-height: 19px; }}
QPushButton#pill:hover {{ background-color: {COLORS['button_hover']}; }}
QPushButton#pill:checked {{ background-color: {COLORS['blue']}; color: white; }}
QPushButton#smallFooter {{ background-color: {COLORS['card']}; border-radius: 10px; padding: 8px 18px; }}
QPushButton#smallFooter:hover {{ background-color: {COLORS['button_hover']}; }}
QLineEdit {{ background-color: {COLORS['input']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 6px 8px; selection-background-color: {COLORS['blue']}; }}
QLineEdit#mainEntry {{ border: none; background-color: transparent; padding-left: 13px; }}
QComboBox {{ background-color: {COLORS['input']}; border: none; border-radius: 8px; padding: 8px 10px; min-height: 18px; }}
QComboBox#subtitleCombo {{ background-color: transparent; min-height: 16px; max-height: 16px; padding: 7px 10px; }}
QComboBox#subtitleCombo::drop-down {{ width: 34px; }}
QComboBox#cardCombo {{ background-color: {COLORS['card']}; }}
QComboBox:disabled {{ background-color: {COLORS['input2']}; color: {COLORS['muted2']}; }}
QComboBox::drop-down:disabled {{ background-color: {COLORS['input2']}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 34px; border: none; border-top-right-radius: 8px; border-bottom-right-radius: 8px; background-color: {COLORS['combo_button']}; }}
QComboBox::drop-down:hover, QComboBox::drop-down:on {{ background-color: {COLORS['blue']}; }}
QComboBox::down-arrow {{ image: none; width: 0; height: 0; }}
QComboBox QAbstractItemView {{ background-color: {COLORS['input']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; outline: 0; }}
QComboBox QAbstractItemView::item:selected {{ background-color: {COLORS['blue']}; color: white; }}
QComboBox QAbstractItemView::item:hover {{ background-color: {COLORS['input2'] if CURRENT_THEME == 'light' else "#303030"}; color: {COLORS['text']}; }}
QCheckBox {{ spacing: 8px; color: {COLORS['text']}; }}
QCheckBox#fieldCheck {{ color: {COLORS['text']}; }}
QCheckBox#fieldCheck::indicator:unchecked {{ border: 2px solid {COLORS['muted2']}; background-color: transparent; }}
QCheckBox#fieldCheck::indicator {{ width: 16px; height: 16px; border-radius: 4px; border: 2px solid {COLORS['muted2']}; background-color: transparent; }}
QCheckBox#fieldCheck::indicator:unchecked:hover {{ border: 2px solid {COLORS['muted']}; background-color: {COLORS['input2']}; }}
QCheckBox#fieldCheck::indicator:checked {{ background-color: {COLORS['blue']}; border: 2px solid {COLORS['blue']}; }}
QCheckBox#fieldCheck::indicator:checked:hover {{ background-color: {COLORS['blue_hover']}; border: 2px solid {COLORS['blue_hover']}; }}
QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 5px; border: 2px solid {COLORS['muted']}; background-color: transparent; }}
QCheckBox::indicator:hover {{ border-color: {COLORS['text']}; }}
QCheckBox::indicator:checked {{ background-color: {COLORS['blue']}; border: 2px solid {COLORS['blue']}; }}
QCheckBox::indicator:checked:hover {{ background-color: {COLORS['blue_hover']}; border: 2px solid {COLORS['blue_hover']}; }}
QCheckBox:disabled {{ color: {COLORS['muted2']}; }}
QCheckBox::indicator:disabled {{ border-color: {COLORS['muted2']}; }}
QRadioButton {{ spacing: 8px; color: {COLORS['text']}; }}
QRadioButton::indicator {{ width: 14px; height: 14px; border-radius: 9px; border: 2px solid {COLORS['muted']}; background-color: transparent; }}
QRadioButton::indicator:hover {{ border-color: {COLORS['text']}; }}
QRadioButton::indicator:checked {{ width: 8px; height: 8px; border-radius: 9px; border: 5px solid {COLORS['blue']}; background-color: transparent; }}
QCheckBox#switch {{ spacing: 9px; color: {COLORS['muted']}; }}
QCheckBox#switch::indicator {{ width: 34px; height: 18px; border-radius: 9px; border: none; background-color: {COLORS['muted2']}; }}
QCheckBox#switch::indicator:unchecked {{ background-color: {COLORS['muted2']}; }}
QCheckBox#switch::indicator:unchecked:hover {{ background-color: {COLORS['muted']}; }}
QCheckBox#switch::indicator:checked {{ background-color: {COLORS['blue']}; }}
QCheckBox#switch::indicator:checked:hover {{ background-color: {COLORS['blue_hover']}; }}
QProgressBar {{ background-color: {COLORS['input']}; border: none; border-radius: 3px; height: 6px; text-align: center; }}
QProgressBar::chunk {{ background-color: {COLORS['blue']}; border-radius: 3px; }}
QTextEdit {{ background-color: {COLORS['input']}; color: {COLORS['text']}; border: none; border-radius: 6px; padding: 10px; font-family: 'Consolas'; font-size: 11px; selection-background-color: {COLORS['blue']}; }}
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

class ElidedLabel(QLabel):
    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), Qt.TextElideMode.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)

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
        font = QFont(APP_FONT_FAMILY, 9)
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
        cursor = self.text_box.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text + "\n")
        self.text_box.setTextCursor(cursor)
        self.text_box.verticalScrollBar().setValue(self.text_box.verticalScrollBar().maximum())

    def closeEvent(self, event):
        self.hide(); event.ignore()

class ManualSelectionDialog(QDialog):
    def __init__(self, url, base_cmd, out_tmpl, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.url = url
        self.base_cmd = base_cmd
        self.out_tmpl = out_tmpl
        self.is_video = (self.main_app.current_category == self.main_app.TAB_VID)
        self.allowed_formats = ["MP4", "MKV", "WEBM"] if self.is_video else ["M4A", "MP3", "FLAC", "WAV", "Opus"]
        self.setWindowTitle("Manual Format Selection")
        self.setFixedSize(750, 550)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self._build_ui()
        apply_theme_titlebar(self)
        center_window(self)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # --- PÁGINA 1: PRESETS RÁPIDOS ---
        page_presets = QWidget()
        preset_lay = QVBoxLayout(page_presets)
        
        lbl_title = QLabel("Select Format")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        preset_lay.addWidget(lbl_title, 0, Qt.AlignmentFlag.AlignCenter)
        preset_lay.addSpacing(20)
        
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(15)
        
        self.menu_quality = QComboBox()
        self.menu_format = QComboBox()
        
        if self.is_video:
            self.menu_quality.addItems(["2160p (4K)", "1440p (QHD)", "1080p (AV1/VP9)", "1080p (H.264)", "720p", "480p", "360p"])
            self.menu_quality.setCurrentText(self.main_app.menu_1.currentText())
            self.menu_format.addItems(["MP4", "MKV", "WEBM"])
            self.menu_format.setCurrentText(self.main_app.menu_2.currentText())
        else:
            self.menu_quality.addItems(["Auto", "High (320 kbps)", "Medium (192 kbps)", "Low (128 kbps)"])
            self.menu_quality.setCurrentText(self.main_app.menu_1.currentText())
            self.menu_format.addItems(["M4A", "MP3", "FLAC", "WAV", "Opus"])
            self.menu_format.setCurrentText(self.main_app.menu_2.currentText())
            
        grid.addWidget(QLabel("Quality"), 0, 0)
        grid.addWidget(self.menu_quality, 1, 0)
        grid.addWidget(QLabel("Format"), 0, 1)
        grid.addWidget(self.menu_format, 1, 1)
        preset_lay.addLayout(grid)
        preset_lay.addSpacing(20)
        
        if self.is_video:
            sub_w = QWidget()
            sub_lay = QHBoxLayout(sub_w)
            sub_lay.setContentsMargins(0, 0, 0, 0)
            sub_lay.setSpacing(10)
            
            self.sw_sub = Switch("Download subtitles")
            self.sw_sub.setChecked(self.main_app.switch_subtitles.isChecked())
            
            self.cb_embed = QCheckBox("Embed subtitles")
            self.cb_embed.setObjectName("fieldCheck")
            self.cb_embed.setChecked(self.main_app.subs_embed_check.isChecked())
            
            self.cb_lang = QComboBox()
            self.cb_lang.addItems(list(self.main_app.lang_map.values())[1:])
            self.cb_lang.setCurrentText(self.main_app.subs_lang_combo.currentText())
            
            self.cb_trans = QComboBox()
            self.cb_trans.addItems(list(self.main_app.lang_map.values()))
            self.cb_trans.setCurrentText(self.main_app.subs_trans_combo.currentText())
            
            sub_lay.addWidget(self.sw_sub)
            sub_lay.addWidget(self.cb_embed)
            sub_lay.addWidget(QLabel("Lang:"))
            sub_lay.addWidget(self.cb_lang)
            sub_lay.addWidget(QLabel("Translate:"))
            sub_lay.addWidget(self.cb_trans)
            sub_lay.addStretch(1)
            preset_lay.addWidget(sub_w)
            preset_lay.addSpacing(20)
            
            def on_sub_toggle():
                state = self.sw_sub.isChecked()
                self.cb_embed.setVisible(state)
                self.cb_lang.setVisible(state)
                self.cb_trans.setVisible(state)
            self.sw_sub.toggled.connect(on_sub_toggle)
            on_sub_toggle()
            
        self.sw_adv = Switch("Advanced selection (Fetch all streams)")
        self.sw_adv.toggled.connect(self.load_advanced_formats)
        preset_lay.addWidget(self.sw_adv)
        
        preset_lay.addSpacing(15)
        out_lbl = QLabel("Output Folder (This file only):")
        out_lbl.setStyleSheet("font-size: 11px; font-weight: bold;")
        preset_lay.addWidget(out_lbl)
        
        row_dir = QHBoxLayout()
        default_dir = os.path.expanduser(self.main_app.config_data["General"].get("video_path" if self.is_video else "audio_path"))
        self.custom_out_dir = QLineEdit(default_dir)
        self.custom_out_dir.setReadOnly(True)
        btn_browse_dir = QPushButton("Browse")
        btn_browse_dir.setAutoDefault(False)
        btn_browse_dir.setObjectName("browseButton")
        btn_browse_dir.setFixedWidth(75)
        btn_browse_dir.clicked.connect(self._browse_custom_dir)
        
        row_dir.addWidget(self.custom_out_dir)
        row_dir.addWidget(btn_browse_dir)
        preset_lay.addLayout(row_dir)
        
        preset_lay.addStretch(1)
        
        btn_quick_down = QPushButton("Download")
        btn_quick_down.setObjectName("primaryButton")
        btn_quick_down.setFixedSize(145, 35)
        btn_quick_down.clicked.connect(self.start_quick_download)
        
        row_btn = QHBoxLayout()
        row_btn.addStretch(1)
        row_btn.addWidget(btn_quick_down)
        preset_lay.addLayout(row_btn)
        
        self.stack.addWidget(page_presets)

        # --- PÁGINA 2: LOADING ---
        page_loading = QWidget()
        load_layout = QVBoxLayout(page_loading)
        load_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_loading = QLabel("Fetching formats and thumbnail...")
        lbl_loading.setStyleSheet("font-size: 13px;")
        load_layout.addWidget(lbl_loading, 0, Qt.AlignmentFlag.AlignCenter)
        self.spinner = QProgressBar()
        self.spinner.setRange(0, 0)
        self.spinner.setFixedSize(300, 6)
        load_layout.addWidget(self.spinner, 0, Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(page_loading)

        # --- PÁGINA 3: ADVANCED CONTENT ---
        self.page_content = QWidget()
        self.content_layout = QVBoxLayout(self.page_content)
        self.stack.addWidget(self.page_content)

        apply_ui_ux_cursors(self)

    def _browse_custom_dir(self):
        start_path = self.custom_out_dir.text()
        p = QFileDialog.getExistingDirectory(self, "Select Output Folder", start_path)
        if p:
            self.custom_out_dir.setText(p.replace("\\", "/"))

    def start_quick_download(self):
        self.main_app.menu_1.setCurrentText(self.menu_quality.currentText())
        self.main_app.menu_2.setCurrentText(self.menu_format.currentText())
        
        # Sobe o diretório customizado temporário para o escopo do app para uso imediato
        self.main_app._temp_manual_dir = self.custom_out_dir.text()
        
        if self.is_video:
            self.main_app.switch_subtitles.setChecked(self.sw_sub.isChecked())
            self.main_app.subs_embed_check.setChecked(self.cb_embed.isChecked())
            self.main_app.subs_lang_combo.setCurrentText(self.cb_lang.currentText())
            self.main_app.subs_trans_combo.setCurrentText(self.cb_trans.currentText())
            
        self.accept()
        
        if self.is_video:
            self.main_app.download_video(self.url)
        else:
            self.main_app.download_music(self.url)

    def load_advanced_formats(self, checked):
        if checked:
            self.stack.setCurrentIndex(1)
            self.fetch_data_task()

    def fetch_data_task(self):
        def task():
            try:
                cmd_json = self.main_app.build_base_cmd(is_json=True, silent=True) + [
                    "--no-warnings", "--no-playlist", self.url
                ]
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
        self.main_app.add_to_log(f"ERROR: {msg}")
        QMessageBox.critical(self, "Error", f"Failed to fetch data:\n{msg}")
        self.reject()

    def build_content(self, data):
        self.setUpdatesEnabled(False)
        try:
            self.spinner.setRange(0, 100)
            self.spinner.setValue(100)
            
            header_frame = QHBoxLayout()
            self.img_label = QLabel("Loading\nThumbnail...")
            self.img_label.setFixedSize(160, 90)
            self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.img_label.setStyleSheet(f"background-color: {COLORS['card']}; border-radius: 8px;")
            header_frame.addWidget(self.img_label)
            
            self.title_label = QLabel(data.get('title', 'Unknown Video'))
            self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            self.title_label.setWordWrap(True)
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

            lists_frame = QHBoxLayout()
            lists_frame.setSpacing(15)
            
            self.vid_group = QButtonGroup(self)
            self.aud_group = QButtonGroup(self)
            
            def create_list(title, group):
                card = QFrame()
                card.setStyleSheet(f"QFrame {{ background-color: {COLORS['card']}; border-radius: 10px; }}")
                lay = QVBoxLayout(card)
                lbl = QLabel(title)
                lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
                lay.addWidget(lbl, 0, Qt.AlignmentFlag.AlignCenter)
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setFixedHeight(274)
                content = QWidget()
                content.setStyleSheet("background-color: transparent;")
                scroll_lay = QVBoxLayout(content)
                scroll_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
                rb_none = QRadioButton("None")
                rb_none.setProperty("fmt_id", "none")
                rb_none.setStyleSheet("font-size: 13px; padding: 4px 0px;")
                group.addButton(rb_none)
                scroll_lay.addWidget(rb_none)
                scroll.setWidget(content)
                lay.addWidget(scroll)
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
                    rb.setProperty("fmt_id", fmt_id)
                    self.aud_group.addButton(rb)
                    aud_lay.addWidget(rb)
                elif vc != 'none':
                    res = f.get('resolution', 'Unknown')
                    if res == 'Unknown': res = f"{f.get('width', '?')}x{f.get('height', '?')}"
                    t_note = "[Video+Audio]" if ac != 'none' else "[Video Only]"
                    rb = QRadioButton(f"ID: {fmt_id} | {res} | {ext.upper()} | {vc} {t_note} | {size_str}")
                    rb.setStyleSheet("font-size: 13px; padding: 4px 0px;")
                    rb.setProperty("fmt_id", fmt_id)
                    self.vid_group.addButton(rb)
                    vid_lay.addWidget(rb)

            lists_frame.addWidget(vid_card, 1)
            lists_frame.addWidget(aud_card, 1)
            self.content_layout.addLayout(lists_frame, 1)

            footer_box = QVBoxLayout()
            footer_box.setSpacing(8)

            footer = QHBoxLayout()
            footer.addWidget(QLabel("Output Format:"))

            self.format_combo = QComboBox()
            self.format_combo.setObjectName("cardCombo")
            self.format_combo.addItems(self.allowed_formats)
            self.format_combo.setFixedWidth(140)

            if len(self.allowed_formats) == 1:
                self.format_combo.setEnabled(False)

            footer.addWidget(self.format_combo)
            footer.addStretch(1)

            btn_down = QPushButton("Download selected")
            btn_down.setObjectName("primaryButton")
            btn_down.setFixedSize(145, 35)
            btn_down.clicked.connect(self.start_download)
            footer.addWidget(btn_down)

            manual_subs_widget = QWidget()
            manual_subs_widget.setFixedHeight(30)

            manual_subs_row = QHBoxLayout(manual_subs_widget)
            manual_subs_row.setContentsMargins(0, 0, 0, 0)
            manual_subs_row.setSpacing(8)
            manual_subs_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            video_cfg = self.main_app.config_data[self.main_app.TAB_VID]

            self.manual_switch_subtitles = Switch("Download subtitles")
            self.manual_switch_subtitles.setChecked(video_cfg.get("native_subs", False) or video_cfg.get("auto_subs", False))
            self.manual_switch_subtitles.setVisible(self.is_video)
            manual_subs_row.addWidget(self.manual_switch_subtitles, 0, Qt.AlignmentFlag.AlignLeft)

            manual_subs_row.addSpacing(8)

            self.manual_embed_check = QCheckBox("Embed subtitles")
            self.manual_embed_check.setObjectName("fieldCheck")
            self.manual_embed_check.setChecked(video_cfg.get("embed_subs", False))
            manual_subs_row.addWidget(self.manual_embed_check)

            manual_subs_row.addSpacing(8)

            manual_lang_label = QLabel("Language:")
            manual_lang_label.setObjectName("fieldLabel")
            manual_subs_row.addWidget(manual_lang_label)

            self.manual_subs_lang_combo = QComboBox()
            self.manual_subs_lang_combo.setObjectName("subtitleCombo")
            self.manual_subs_lang_combo.addItems(list(self.main_app.lang_map.values())[1:])
            self.manual_subs_lang_combo.setFixedWidth(120)
            self.manual_subs_lang_combo.setCurrentText(self.main_app.lang_map.get(video_cfg.get("langs", "en"), "English"))
            manual_subs_row.addWidget(self.manual_subs_lang_combo)

            manual_subs_row.addSpacing(8)

            manual_trans_label = QLabel("Translate to:")
            manual_trans_label.setObjectName("fieldLabel")
            manual_subs_row.addWidget(manual_trans_label)

            self.manual_subs_trans_combo = QComboBox()
            self.manual_subs_trans_combo.setObjectName("subtitleCombo")
            self.manual_subs_trans_combo.addItems(list(self.main_app.lang_map.values()))
            self.manual_subs_trans_combo.setFixedWidth(120)
            self.manual_subs_trans_combo.setCurrentText(self.main_app.lang_map.get(video_cfg.get("trans_langs", "none"), "None"))
            manual_subs_row.addWidget(self.manual_subs_trans_combo)

            manual_subs_row.addStretch(1)

            self.manual_subs_widgets = [self.manual_embed_check, manual_lang_label, self.manual_subs_lang_combo, manual_trans_label, self.manual_subs_trans_combo]

            def update_manual_subs():
                show_sub_options = self.is_video and self.manual_switch_subtitles.isChecked()
                for widget in self.manual_subs_widgets: widget.setVisible(show_sub_options)

            self.manual_switch_subtitles.toggled.connect(update_manual_subs)
            update_manual_subs()

            footer_box.addWidget(manual_subs_widget)
            footer_box.addLayout(footer)
            self.content_layout.addLayout(footer_box)
            self.stack.setCurrentIndex(2)
            
            apply_ui_ux_cursors(self)
            
        finally:
            self.setUpdatesEnabled(True)

    def get_manual_subtitle_cfg(self):
        cfg = self.main_app.config_data[self.main_app.TAB_VID].copy()
        if not self.manual_switch_subtitles.isChecked():
            cfg["native_subs"] = False
            cfg["auto_subs"] = False
            cfg["embed_subs"] = False
            return cfg
        cfg["native_subs"] = True
        cfg["auto_subs"] = True
        cfg["langs"] = self.main_app.rev_lang_map.get(self.manual_subs_lang_combo.currentText(), "en")
        cfg["trans_langs"] = self.main_app.rev_lang_map.get(self.manual_subs_trans_combo.currentText(), "none")
        cfg["embed_subs"] = self.manual_embed_check.isChecked()
        return cfg

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
        
        is_video = self.main_app.current_category in [self.main_app.TAB_VID, self.main_app.TAB_C_VID]
        gen_cfg = self.main_app.config_data.get("General", {})
        base_path = os.path.expanduser(gen_cfg.get("video_path") if is_video else gen_cfg.get("audio_path"))
        full_out_tmpl = f"{base_path}/{self.out_tmpl}"
        
        cmd = self.base_cmd.copy()
        
        if self.main_app.current_category == self.main_app.TAB_VID:
            cmd = self.main_app.add_subtitle_args(cmd, self.get_manual_subtitle_cfg())        
        
        if ext_final == "webm":
            cmd = [arg for arg in cmd if arg not in ("--embed-thumbnail", "--embed-subs")]
        elif ext_final == "wav":
            cmd = [arg for arg in cmd if arg not in ("--embed-thumbnail", "--embed-metadata", "--parse-metadata", "%(playlist_index|)s:%(track_number)s", "%(release_year,release_date,date,upload_date).4s:%(meta_date)s", "%(album_artist,creator,channel|)s:%(meta_album_artist)s")]

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
        
        github = QPushButton(" GitHub")
        github.setFixedWidth(120)
        self.main_app.set_button_icon(github, "github")
        github.clicked.connect(lambda: webbrowser.open_new("https://github.com/DanMixerBR/CopynDown"))
        
        btn_state = False if self.main_app.is_busy else True
        self.update_btn = QPushButton("Check for updates"); self.update_btn.setObjectName("primaryButton"); self.update_btn.setFixedWidth(140); self.update_btn.setEnabled(btn_state)
        def do_check():
            self.update_btn.setEnabled(False)
            self.update_btn.setText("Checking...")
            self.main_app.start_github_update(self.update_btn, self, is_startup=False, check_ytdlp_after=True)
            
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
        
        scroll = QScrollArea()
        scroll.setObjectName("settingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setWidget(stack)
        
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
        
        self.cb_auto = QCheckBox("Auto-paste URLs")
        self.cb_auto.setChecked(self.cfg["General"].get("auto_paste", True))
        layout.addWidget(self.cb_auto)

        self.cb_prefer = QCheckBox("Prefer video over playlist (If URL contains both)")
        self.cb_prefer.setChecked(self.cfg["General"].get("prefer_video", False))
        layout.addWidget(self.cb_prefer)
        self.cb_notify = QCheckBox("Enable desktop notifications")
        self.cb_notify.setChecked(self.cfg["General"].get("notifications", True))
        layout.addWidget(self.cb_notify)
        self.cb_updates_startup = QCheckBox("Check for updates on startup")
        self.cb_updates_startup.setChecked(self.cfg["General"].get("check_updates_startup", True))
        layout.addWidget(self.cb_updates_startup)
        
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
        layout.addWidget(self._section("Embed thumbnail (Cover art)"))
        layout.addSpacing(12)

        thumb_row = QHBoxLayout()
        thumb_row.setSpacing(18)

        self.cb_vid_thumb = QCheckBox("Video")
        self.cb_vid_thumb.setChecked(
            self.cfg[self.main_app.TAB_VID].get("thumb", True)
        )

        self.cb_aud_thumb = QCheckBox("Audio")
        self.cb_aud_thumb.setChecked(
            self.cfg[self.main_app.TAB_AUD].get("thumb", True)
        )

        thumb_row.addWidget(self.cb_vid_thumb)
        thumb_row.addWidget(self.cb_aud_thumb)
        thumb_row.addStretch(1)

        layout.addLayout(thumb_row)

        layout.addSpacing(24)
        layout.addWidget(self._section("Embed metadata (Artist, Title, etc)"))
        layout.addSpacing(12)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(18)

        self.cb_vid_meta = QCheckBox("Video")
        self.cb_vid_meta.setChecked(
            self.cfg[self.main_app.TAB_VID].get("meta", False)
        )

        self.cb_aud_meta = QCheckBox("Audio")
        self.cb_aud_meta.setChecked(
            self.cfg[self.main_app.TAB_AUD].get("meta", True)
        )

        meta_row.addWidget(self.cb_vid_meta)
        meta_row.addWidget(self.cb_aud_meta)
        meta_row.addStretch(1)

        layout.addLayout(meta_row)

        layout.addSpacing(24)
        layout.addWidget(self._section("Subtitles"))
        layout.addSpacing(12)

        self.cb_subs = QCheckBox("Always download subtitles")
        self.cb_subs.setChecked(
            self.cfg[self.main_app.TAB_VID].get("native_subs", False) or
            self.cfg[self.main_app.TAB_VID].get("auto_subs", False)
        )

        self.cb_embed = QCheckBox("Always embed subtitles")
        self.cb_embed.setChecked(self.cfg[self.main_app.TAB_VID].get("embed_subs", False))

        def update_subs():
            self.cb_embed.setEnabled(self.cb_subs.isChecked())
            if not self.cb_embed.isEnabled():
                self.cb_embed.setChecked(False)

        self.cb_subs.stateChanged.connect(update_subs)
        update_subs()

        layout.addWidget(self.cb_subs)
        layout.addSpacing(8)
        layout.addWidget(self.cb_embed)
        
        lang_map = self.main_app.lang_map
        self.rev_map = self.main_app.rev_lang_map
        
        layout.addSpacing(20); lang_row = QHBoxLayout(); lang_row.setSpacing(8)
        lang_col = QVBoxLayout(); lang_col.addWidget(QLabel("Language:"))
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
        
        c_box = QFrame(); c_box.setStyleSheet(f"QFrame {{ background-color: {COLORS['card']}; border-radius: 10px; }}")
        c_lay = QVBoxLayout(c_box); c_lay.setContentsMargins(0, 10, 15, 15); c_lay.setSpacing(10)
        
        self.cb_custom = Switch("Enable custom profile")
        self.cb_custom.setChecked(self.cfg["General"].get("custom_profile", False))
        c_lay.addWidget(self.cb_custom); c_lay.addSpacing(5)
        
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

        def toggle_custom_profile():
            is_custom = self.cb_custom.isChecked()
            self.prof_combo.setEnabled(not is_custom) 
            self.crf_entry.setEnabled(is_custom)      
            self.preset_combo.setEnabled(is_custom)   
            self.cpu_combo.setEnabled(is_custom)      
            
        self.cb_custom.toggled.connect(toggle_custom_profile)
        toggle_custom_profile()
        
        layout.addStretch(1); return w

    def _network_tab(self):
        w = QWidget(); layout = QVBoxLayout(w); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        layout.addWidget(self._section("Network Options")); layout.addSpacing(12)
        
        row4 = QHBoxLayout(); row4.setSpacing(10); row4.addWidget(QLabel("Speed limit:"))
        self.speed_combo = QComboBox(); self.speed_combo.addItems(["Unlimited", "1 MB/s", "5 MB/s", "10 MB/s", "25 MB/s", "50 MB/s"])
        self.speed_combo.setFixedWidth(140); self.speed_combo.setCurrentText(self.cfg["General"].get("speed_limit", "Unlimited"))
        row4.addWidget(self.speed_combo); row4.addStretch(1); layout.addLayout(row4)

        layout.addSpacing(10); self.cb_proxy = Switch("Use Proxy Server"); self.cb_proxy.setChecked(self.cfg["General"].get("use_proxy", False))
        layout.addWidget(self.cb_proxy)
        
        layout.addSpacing(10)
        
        self.proxy_entry = QLineEdit(self.cfg["General"].get("proxy_url", ""))
        self.proxy_entry.setPlaceholderText("http://ip:port or socks5://ip:port")
        self.proxy_entry.setFixedWidth(350)
        self.proxy_entry.setEnabled(self.cb_proxy.isChecked())
        self.cb_proxy.toggled.connect(self.proxy_entry.setEnabled) 
        layout.addWidget(self.proxy_entry)
        
        layout.addSpacing(10); row1 = QHBoxLayout(); row1.setSpacing(10); row1.addWidget(QLabel("Max retries:"))
        self.retries = QLineEdit(self.cfg["General"].get("max_retries", "10")); self.retries.setFixedWidth(60); row1.addWidget(self.retries); row1.addStretch(1); layout.addLayout(row1)
        
        layout.addSpacing(10); row2 = QHBoxLayout(); row2.setSpacing(10); row2.addWidget(QLabel("Delay mode:"))
        self.delay = QComboBox(); self.delay.addItems(["None", "Playlist Only", "All Downloads"]); self.delay.setFixedWidth(140); self.delay.setCurrentText(self.cfg["General"].get("delay_mode", "Playlist Only")); row2.addWidget(self.delay); row2.addStretch(1); layout.addLayout(row2)
        
        layout.addSpacing(10); row3 = QHBoxLayout(); row3.setSpacing(6)
        row3.addWidget(QLabel("Sleep intervals (Sec):  Min")); self.s_min = QLineEdit(self.cfg["General"].get("sleep_min", "2")); self.s_min.setFixedWidth(40); row3.addWidget(self.s_min)
        row3.addWidget(QLabel("Max")); self.s_max = QLineEdit(self.cfg["General"].get("sleep_max", "5")); self.s_max.setFixedWidth(40); row3.addWidget(self.s_max)
        row3.addWidget(QLabel("Requests")); self.s_req = QLineEdit(self.cfg["General"].get("sleep_req", "1")); self.s_req.setFixedWidth(40); row3.addWidget(self.s_req); row3.addStretch(1); layout.addLayout(row3)
        
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
        
        btn_ext = QPushButton("Extract cookies"); btn_ext.setObjectName("primaryButton"); btn_ext.setFixedWidth(120)
        row_ext.addWidget(self.browser_combo); row_ext.addWidget(btn_ext); row_ext.addStretch(1); p_auto_lay.addLayout(row_ext)

        def perform_extraction():
            btn_ext.setEnabled(False); btn_ext.setText("Extracting...")
            browser = self.browser_combo.currentText().lower()
            c_path = self.cookie_path.text()

            def reset_btn():
                try:
                    btn_ext.setEnabled(True)
                    btn_ext.setText("Extract cookies")
                    btn_ext.setIcon(QIcon())
                    btn_ext.setStyleSheet("")
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
                    
                    self.main_app.safe_ui(lambda: (
                        btn_ext.setText(" Success!"),
                        self.main_app.set_button_icon(btn_ext, "success"),
                        btn_ext.setStyleSheet(f"background-color: {COLORS['success']}; color: white; border: none;")
                    ))
                    self.main_app.safe_ui(self.main_app.add_to_log, f">>> Successfully generated valid cookies.txt at {c_path}")
                    self.main_app.safe_ui(lambda: QTimer.singleShot(3000, reset_btn))

                except Exception as e:
                    err_msg = str(e)
                    self.main_app.safe_ui(lambda: (
                        btn_ext.setText(" Error"),
                        self.main_app.set_button_icon(btn_ext, "error"),
                        btn_ext.setStyleSheet(f"background-color: {COLORS['danger']}; color: white; border: none;")
                    ))
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

            start_path = os.path.expanduser(edit.text() or "~")
            if not os.path.isabs(start_path):
                start_path = os.path.join(base_dir, start_path)

            if not is_dir:
                start_path = os.path.dirname(start_path)

            p = QFileDialog.getExistingDirectory(self, title, start_path) if is_dir else QFileDialog.getOpenFileName(self, title, start_path, "Text Files (*.txt)")[0]

            if p:
                p = p.replace("\\", "/")
                home = os.path.expanduser("~").replace("\\", "/")
                app_dir = os.path.abspath(".").replace("\\", "/")

                if p.startswith(app_dir):
                    p = p[len(app_dir):].lstrip("/")
                elif p.startswith(home):
                    p = "~" + p[len(home):]

                edit.setText(p)

        btn.clicked.connect(do_browse)
        row.addWidget(edit); row.addWidget(btn)
        
        if has_ext:
            btn_ext = QPushButton("Get extension"); btn_ext.setObjectName("primaryButton"); btn_ext.setFixedWidth(120)
            btn_ext.clicked.connect(lambda: webbrowser.open_new("https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"))
            row.addWidget(btn_ext)
            
        row.addStretch(1)
        parent_layout.addLayout(row)
        return edit

    def restore_defaults(self):
        self.vid_path.setText("~/Videos/CopynDown")
        self.aud_path.setText("~/Music/CopynDown")
        self.cookie_path.setText("bin/cookies.txt")
        self.cb_auto.setChecked(True); self.cb_prefer.setChecked(False)
        self.cb_updates_startup.setChecked(True)
        self.cb_notify.setChecked(True)
        self.cb_vid_thumb.setChecked(True)
        self.cb_aud_thumb.setChecked(True)
        self.cb_vid_meta.setChecked(False)
        self.cb_aud_meta.setChecked(True)
        self.cb_subs.setChecked(False)
        self.cb_embed.setChecked(False)
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
            "use_cookies": self.cb_cookies.isChecked(), "cookies_path": self.cookie_path.text(),
            "prefer_video": self.cb_prefer.isChecked(), "check_updates_startup": self.cb_updates_startup.isChecked(),
            "notifications": self.cb_notify.isChecked(),
            "max_retries": self.retries.text(), "file_template": self.tmpl_combo.currentText(),
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
            "thumb": self.cb_vid_thumb.isChecked(),
            "meta": self.cb_vid_meta.isChecked(),
            "native_subs": self.cb_subs.isChecked(),
            "auto_subs": self.cb_subs.isChecked(),
            "embed_subs": self.cb_embed.isChecked(),
            "langs": self.rev_map.get(self.lang_combo.currentText(), "en"),
            "trans_langs": self.rev_map.get(self.trans_combo.currentText(), "none")
        })

        self.cfg[self.main_app.TAB_AUD].update({
            "thumb": self.cb_aud_thumb.isChecked(),
            "meta": self.cb_aud_meta.isChecked()
        })
        
        if sel_theme != CURRENT_THEME:
            CURRENT_THEME = sel_theme; COLORS = THEMES[CURRENT_THEME]
            QApplication.instance().setStyleSheet(get_app_qss())
            
            apply_theme_titlebar(self.main_app)
            apply_theme_titlebar(self)
                
            if getattr(self.main_app, 'log_window', None):
                apply_theme_titlebar(self.main_app.log_window)
            
            self.main_app.refresh_theme_colors()
            
        self.main_app.save_config()
        self.main_app.update_folder_context()
        self.main_app.subs_embed_check.setChecked(self.cb_embed.isChecked())
        self.main_app.subs_lang_combo.setCurrentText(self.lang_combo.currentText())
        self.main_app.subs_trans_combo.setCurrentText(self.trans_combo.currentText())
        self.main_app.switch_subtitles.setChecked(self.cb_subs.isChecked())
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
        
        self.is_windows = os.name == 'nt'; self.exe = ".exe" if self.is_windows else ""
        self.config_file = os.path.join(bin_path, "config.txt").replace("\\", "/")
        self.ytdlp_path = os.path.join(bin_path, f"yt-dlp{self.exe}").replace("\\", "/")
        self.cookies_path_default = os.path.join(bin_path, "cookies.txt").replace("\\", "/")
        self.version_file = os.path.join(bin_path, "version.txt").replace("\\", "/")
        
        self.version = self.get_local_version()

        self.setWindowTitle("CopynDown")
        self.resize(850, 650); self.setMinimumSize(850, 650)

        self.status_timer = QTimer(self); self.status_timer.setSingleShot(True); self.status_timer.timeout.connect(self.reset_status)
        self.ui_update_timer = QTimer(self); self.ui_update_timer.setSingleShot(True); self.ui_update_timer.timeout.connect(self.evaluate_ui_state)

        self.log_window = None
        self.current_process = None; self.current_playlist_item = ""
        self.is_cancelling = False; self.is_busy = False; self.is_updating = False
        self.download_queue = []; self.is_queue_running = False
        
        self.title_fetch_semaphore = threading.Semaphore(3)
        self.queue_generation = 0
        self.queue_update_timer = QTimer(self)
        self.queue_update_timer.setSingleShot(True)
        self.queue_update_timer.timeout.connect(self._do_update_queue_ui)
        
        self.history_timer = QTimer(self)
        self.history_timer.setSingleShot(True)
        self.history_timer.timeout.connect(self._do_save_history)

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
                "auto_paste": True, "use_cookies": True, "cookies_path": self.cookies_path_default,
                "video_path": "~/Videos/CopynDown", "audio_path": "~/Music/CopynDown", "prefer_video": False, 
                "check_updates_startup": True,
                "notifications": True,
                "max_retries": "10", "file_template": "Title (Default)", "delay_mode": "Playlist Only", 
                "sleep_min": "2", "sleep_max": "5", "sleep_req": "1", "conv_profile": "High Quality",
                "custom_profile": False, "custom_crf": "18", "custom_preset": "faster", "custom_cpu_used": "4",
                "speed_limit": "Unlimited", "use_proxy": False, "proxy_url": ""                
            },
            self.TAB_VID: {"thumb": True, "meta": False, "native_subs": False, "auto_subs": False, "embed_subs": False, "langs": "en", "trans_langs": "none"},
            self.TAB_AUD: {"thumb": True, "meta": True}
        }
        self.load_config()

        self.lang_map = {
            "none": "None", "zh-Hans": "Chinese (S)", "zh-Hant": "Chinese (T)", "nl": "Dutch",
            "en": "English", "fr": "French", "de": "German", "id": "Indonesian",
            "it": "Italian", "ja": "Japanese", "ko": "Korean", "pl": "Polish",
            "pt": "Portuguese", "ru": "Russian", "es": "Spanish", "th": "Thai",
            "tr": "Turkish", "vi": "Vietnamese"
        }
        self.rev_lang_map = {v: k for k, v in self.lang_map.items()}
        self.lang_variants = {
            "zh-Hans": ["zh-Hans"], "zh-Hant": ["zh-Hant"], "nl": ["nl", "nl-NL"],
            "en": ["en", "en-US", "en-GB"], "fr": ["fr", "fr-FR", "fr-CA"], "de": ["de", "de-DE"],
            "id": ["id", "id-ID"], "it": ["it", "it-IT"], "ja": ["ja", "ja-JP"],
            "ko": ["ko", "ko-KR"], "pl": ["pl", "pl-PL"], "pt": ["pt", "pt-BR", "pt-PT"],
            "ru": ["ru", "ru-RU"], "es": ["es", "es-ES", "es-419"], "th": ["th", "th-TH"],
            "tr": ["tr", "tr-TR"], "vi": ["vi", "vi-VN"]
        }

        self.last_folder = self.config_data["General"]["video_path"]
        self.current_category = self.TAB_VID
        self.init_notifications()
        
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
        
        self.history_file = os.path.join(bin_path, "history.txt").replace("\\", "/")
        self.load_history()
        self._build_ui()
        self.select_tab(self.TAB_VID)
        apply_theme_titlebar(self)
        center_window(self)

        if self.config_data["General"].get("check_updates_startup", True):
            QTimer.singleShot(500, lambda: self.start_github_update(is_startup=True))

    def init_notifications(self):
        self.tray_icon = None
        if not QSystemTrayIcon.isSystemTrayAvailable(): return
        icon = QApplication.windowIcon()
        if icon.isNull():
            for icon_name in ("icon.ico", "icon.png", "logo.png"):
                icon_path = os.path.join(bin_path, "icons", icon_name).replace("\\", "/")
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    break
        if icon.isNull(): return
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("CopynDown")
        self.tray_icon.show()
        self.tray_icon.messageClicked.connect(self.restore_from_notification)
        self.tray_icon.activated.connect(self.restore_from_tray_icon)

    def notify_user(self, title, message, icon_type=None):
        if not self.config_data.get("General", {}).get("notifications", True): return
        if not getattr(self, "tray_icon", None): return
        if icon_type is None: icon_type = QSystemTrayIcon.MessageIcon.Information
        self.tray_icon.showMessage(title, message, icon_type, 5000)    
    
    def restore_from_notification(self):
        self.showNormal(); self.raise_(); self.activateWindow()

    def restore_from_tray_icon(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.restore_from_notification()
    
    def changeEvent(self, event):
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Type.ActivationChange and self.isActiveWindow():
            self.on_clipboard_change()
        super().changeEvent(event)

    def open_manual_selection(self):
        self.fix_ghost_cursor()
        url = self.main_entry.text().strip()
        if not self.is_valid_media_url(url):
            self.reset_status("Invalid URL.", COLORS["danger"])
            self.schedule_reset()
            return
            
        b_cmd = self.build_base_cmd(url=url)
        o_tmpl = "%(title)s.%(ext)s"
        
        self.manual_win = ManualSelectionDialog(url, b_cmd, o_tmpl, self)
        self.manual_win.exec()

    def _create_queue_row(self):
        f = QFrame()
        # f.setMinimumHeight(65)
        f.setStyleSheet(f"QFrame {{ background-color: {COLORS['input']}; border-radius: 8px; }}")
        
        f.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        f.customContextMenuRequested.connect(lambda pos, frame=f: self._show_queue_context_menu(pos, frame))

        f_lay = QHBoxLayout(f)
        f_lay.setContentsMargins(12, 12, 12, 12)

        # Botão de Ação (Play / Pause / Restart)
        btn_action = QPushButton("▶")
        btn_action.setFixedSize(32, 32)
        btn_style = (f"QPushButton {{ background-color: {COLORS['button']}; color: {COLORS['text']}; border-radius: 4px; padding: 0px; font-weight: bold; font-size: 15px; }}"
                     f"QPushButton:hover {{ background-color: {COLORS['button_hover']}; }}")
        btn_action.setStyleSheet(btn_style)
        btn_action.clicked.connect(lambda checked=False, btn=btn_action: self.toggle_queue_item_state(btn.property("queue_index")))

        info_lay = QVBoxLayout()
        info_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        top_row = QHBoxLayout()
        
        name_lbl = ElidedLabel("")
        name_lbl.setMinimumWidth(50)
        name_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        
        link_lbl = ElidedLabel("")
        link_lbl.hide() # Mantido invisível para não dar erro na atualização
        
        status_lbl = QLabel("")
        status_lbl.setStyleSheet("font-size: 11px; font-weight: bold;")
        
        top_row.addWidget(name_lbl, 1) # O "1" faz o título empurrar o status
        top_row.addWidget(status_lbl)
        
        item_progress = QProgressBar()
        item_progress.setRange(0, 100)
        item_progress.setValue(0)
        item_progress.setTextVisible(False)
        item_progress.setFixedHeight(4)
        item_progress.setVisible(False)
        sp = item_progress.sizePolicy(); sp.setRetainSizeWhenHidden(True); item_progress.setSizePolicy(sp)

        info_lay.addLayout(top_row)
        info_lay.addWidget(item_progress)

        btn_up = QPushButton("▲"); btn_down = QPushButton("▼"); btn_remove = QPushButton("X")
        btn_up.setFixedSize(30, 24); btn_down.setFixedSize(30, 24); btn_remove.setFixedSize(30, 24)
        
        btn_sub_style = (f"QPushButton {{ background-color: {COLORS['button']}; color: {COLORS['text']}; border-radius: 4px; padding: 0px; font-weight: bold; font-size: 13px; }}"
                         f"QPushButton:hover {{ background-color: {COLORS['button_hover']}; }}"
                         f"QPushButton:disabled {{ background-color: {COLORS['input2']}; color: {COLORS['muted2']}; }}")
        btn_remove_style = (f"QPushButton {{ background-color: {COLORS['button']}; color: {COLORS['text']}; border-radius: 4px; padding: 0px; font-weight: bold; font-size: 13px; }}"
                            f"QPushButton:hover {{ background-color: {COLORS['danger']}; color: white; }}"
                            f"QPushButton:disabled {{ background-color: {COLORS['input2']}; color: {COLORS['muted2']}; }}")
        
        btn_up.setStyleSheet(btn_sub_style); btn_down.setStyleSheet(btn_sub_style); btn_remove.setStyleSheet(btn_remove_style)

        btn_remove.clicked.connect(lambda checked=False, btn=btn_remove: self.remove_from_queue(btn.property("queue_index")))
        btn_up.clicked.connect(lambda checked=False, btn=btn_up: self.move_queue_item(btn.property("queue_index"), -1))
        btn_down.clicked.connect(lambda checked=False, btn=btn_down: self.move_queue_item(btn.property("queue_index"), 1))

        f_lay.addWidget(btn_action)
        f_lay.addLayout(info_lay, 1)
        f_lay.addWidget(btn_up); f_lay.addWidget(btn_down); f_lay.addWidget(btn_remove)
        
        self.history_layout.addWidget(f) # <--- Trocado de insertWidget(0) para addWidget()

        return {"frame": f, "name": name_lbl, "link": link_lbl, "status": status_lbl, "progress": item_progress, "action": btn_action, "up": btn_up, "down": btn_down, "remove": btn_remove}

    def _show_queue_context_menu(self, pos, frame):
        index = frame.property("queue_index")
        if index is not None and 0 <= index < len(self.download_queue):
            task = self.download_queue[index]
            url = task.get("url", "")
            dest_folder = task.get("dest_folder", "")
            
            from PySide6.QtWidgets import QMenu
            menu = QMenu(self)
            open_action = menu.addAction("Open folder")
            menu.addSeparator()
            copy_action = menu.addAction("Copy link")
            delete_action = menu.addAction("Delete")
            
            if not dest_folder:
                open_action.setEnabled(False)
            
            action = menu.exec(frame.mapToGlobal(pos))
            if action == copy_action and url:
                QApplication.clipboard().setText(url)
            elif action == open_action:
                self.open_specific_folder(dest_folder)
            elif action == delete_action:
                self.delete_queue_item(index)

    def delete_queue_item(self, index):
        if 0 <= index < len(self.download_queue):
            task = self.download_queue[index]
            if task["status"] == "Running":
                task["status"] = "Canceled"
                self.cancel_download()
                # Exclui pela identidade do objeto, prevenindo exclusão acidental se a lista mudar
                QTimer.singleShot(1500, lambda t=task: self.remove_task_by_ref(t))
            else:
                self.remove_task_by_ref(task)

    def remove_task_by_ref(self, task):
        if task in self.download_queue:
            self.download_queue.remove(task)
            self.save_history()
            self.update_queue_ui()

    def open_specific_folder(self, folder_path):
        try:
            p = os.path.realpath(os.path.expanduser(folder_path))
            if os.path.exists(p):
                if self.is_windows: os.startfile(p)
                elif sys.platform == "darwin": subprocess.Popen(["open", p])
                else: subprocess.Popen(["xdg-open", p])
        except Exception as e:
            self.add_to_log(f">>> Failed to open folder: {e}")

    def toggle_queue_item_state(self, index):
        if 0 <= index < len(self.download_queue):
            if self.download_queue[index]["status"] == "Running":
                self.pause_queue_item(index)
            else:
                self.restart_queue_item(index)

    def pause_queue_item(self, index):
        if 0 <= index < len(self.download_queue):
            if self.download_queue[index]["status"] == "Running":
                self.download_queue[index]["status"] = "Paused" # Força o novo status
                self.cancel_download()
            elif self.download_queue[index]["status"] == "Pending":
                self.download_queue[index]["status"] = "Paused"
                self.update_queue_ui()
                self.save_history()

    def restart_queue_item(self, index):
        if 0 <= index < len(self.download_queue):
            self.download_queue[index]["status"] = "Pending"
            self.download_queue[index]["progress"] = 0
            self.update_queue_ui()
            self.save_history()
            if not getattr(self, 'is_queue_running', False):
                self.process_next_in_queue()

    def cancel_queue_item(self, index):
        if 0 <= index < len(self.download_queue):
            if self.download_queue[index]["status"] == "Running":
                self.download_queue[index]["status"] = "Canceled"
                self.cancel_download()
            else:
                self.download_queue[index]["status"] = "Canceled"
                self.update_queue_ui()
                self.save_history()
    
    def _update_queue_row(self, row, index, task, queue_len):
        status = task.get("status", "Pending")
        is_active = (status == "Running")

        # Texto do título limpo, sem número de índice
        row["name"].setText(task.get("name", "Media Task"))
        # row["link"].setText(task.get("url", ""))
        
        if is_active:
            row["progress"].setVisible(True)
            row["progress"].setValue(task.get("progress", 0))
            row["progress"].setRange(0, 0 if task.get("is_convert") else 100)
            row["status"].setText(task.get("progress_text", "Downloading..." if not task.get("is_convert") else "Converting..."))
            row["status"].setStyleSheet(f"color: {COLORS['blue']}; font-size: 11px; font-weight: bold;")
            row["action"].setText("⏸")
        else:
            row["progress"].setVisible(False)
            if status == "Completed":
                row["status"].setText("Completed")
                row["status"].setStyleSheet(f"color: {COLORS['muted']}; font-size: 11px; font-weight: bold;") # Cor removida
                row["action"].setText("↺")
            elif status == "Failed":
                row["status"].setText("Failed")
                row["status"].setStyleSheet(f"color: {COLORS['danger']}; font-size: 11px; font-weight: bold;")
                row["action"].setText("↺")
            elif status == "Paused":
                row["status"].setText("Paused")
                row["status"].setStyleSheet(f"color: {COLORS['muted']}; font-size: 11px; font-weight: bold;") # Cor removida
                row["action"].setText("▶")
            elif status == "Canceled":
                row["status"].setText("Canceled")
                row["status"].setStyleSheet(f"color: {COLORS['muted2']}; font-size: 11px; font-weight: bold;")
                row["action"].setText("↺")
            else:
                row["status"].setText("Pending")
                row["status"].setStyleSheet(f"color: {COLORS['muted']}; font-size: 11px;")
                row["action"].setText("▶")

        row["frame"].setProperty("queue_index", index)
        row["action"].setProperty("queue_index", index)
        row["up"].setProperty("queue_index", index)
        row["down"].setProperty("queue_index", index)
        row["remove"].setProperty("queue_index", index)

        row["frame"].setVisible(True)
        row["remove"].setEnabled(not is_active)
        
        # Verifica se há itens do MESMO TIPO acima ou abaixo para habilitar as setas
        task_type = task.get("is_convert", False)
        has_up = any(t.get("is_convert", False) == task_type for t in self.download_queue[:index])
        has_down = any(t.get("is_convert", False) == task_type for t in self.download_queue[index+1:])
        
        row["up"].setEnabled(not is_active and has_up)
        row["down"].setEnabled(not is_active and has_down)
        
        weight = "bold" if is_active else "normal"
        color = COLORS['blue'] if is_active else COLORS['text']
        row["name"].setStyleSheet(f"font-size: 13px; font-weight: {weight}; color: {color};")

    def update_queue_ui(self):
        self.queue_update_timer.start(200)
        
    def update_single_queue_row(self):
        """Atualiza apenas os textos e a barra de progresso do item ativo, buscando-o dinamicamente."""
        if not hasattr(self, "queue_rows"):
            return
        
        for i, task in enumerate(self.download_queue):
            if task.get("status") == "Running":
                if i < len(self.queue_rows):
                    row = self.queue_rows[i]
                    row["progress"].setValue(task.get("progress", 0))
                    row["status"].setText(task.get("progress_text", "Downloading..." if not task.get("is_convert") else "Converting..."))
                break

    def _do_update_queue_ui(self):
        if not hasattr(self, "queue_rows"): self.queue_rows = []
        if not hasattr(self, "empty_label"):
            self.empty_label = QLabel("List is empty.")
            self.empty_label.setObjectName("muted")
            self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_layout.addWidget(self.empty_label)

        self.setUpdatesEnabled(False)
        try:
            queue_data = self.download_queue
            if not queue_data:
                self.history_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.empty_label.setVisible(True)
                for row in self.queue_rows: row["frame"].setVisible(False)
                return

            self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.empty_label.setVisible(False)

            while len(self.queue_rows) < len(queue_data):
                self.queue_rows.append(self._create_queue_row())
                
            # Para que os itens fiquem na ordem correta na interface
            itens_visiveis = 0
            is_tab_convert = self.current_category in [self.TAB_C_VID, self.TAB_C_AUD]

            for i, task in enumerate(self.download_queue):
                self._update_queue_row(self.queue_rows[i], i, task, len(self.download_queue))
                
            # Filtro visual: exibe a linha apenas se o tipo do item bater com a aba atual
                if task.get("is_convert", False) == is_tab_convert:
                    self.queue_rows[i]["frame"].setVisible(True)
                    itens_visiveis += 1
                else:
                    self.queue_rows[i]["frame"].setVisible(False)

            # Só exibe "Lista vazia" se não houver nenhum item visível para esta aba
            self.empty_label.setVisible(itens_visiveis == 0)

            for index in range(len(self.download_queue), len(self.queue_rows)):
                self.queue_rows[index]["frame"].setVisible(False)
            self.setUpdatesEnabled(True)

        finally:
            self.setUpdatesEnabled(True)

    def clear_entire_queue(self):
        self.queue_generation += 1
        if getattr(self, 'is_queue_running', False) and self.download_queue:
            running_idx = None
            for i, t in enumerate(self.download_queue):
                if t["status"] == "Running": running_idx = i; break
            if running_idx is not None: self.download_queue = [self.download_queue[running_idx]]
            else: self.download_queue.clear()
        else:
            self.download_queue.clear()
        self.save_history()
        self.update_queue_ui()

    def remove_from_queue(self, index):
        if 0 <= index < len(self.download_queue):
            self.download_queue.pop(index)
            self.save_history()
            self.update_queue_ui()

    def move_queue_item(self, index, direction):
        if 0 <= index < len(self.download_queue):
            task_type = self.download_queue[index].get("is_convert", False)
            target_idx = None
            
            # Procura o item visível (do mesmo tipo) mais próximo para realizar a troca
            if direction == -1: # Move Up
                for i in range(index - 1, -1, -1):
                    if self.download_queue[i].get("is_convert", False) == task_type:
                        target_idx = i; break
            else: # Move Down
                for i in range(index + 1, len(self.download_queue)):
                    if self.download_queue[i].get("is_convert", False) == task_type:
                        target_idx = i; break
                        
            if target_idx is not None:
                self.download_queue[index], self.download_queue[target_idx] = self.download_queue[target_idx], self.download_queue[index]
                self.save_history()
                self.update_queue_ui()

    def _build_ui(self):
        root = QWidget(); self.setCentralWidget(root)
        main_layout = QVBoxLayout(root); main_layout.setContentsMargins(40, 25, 40, 20); main_layout.setSpacing(20)

        # CABEÇALHO
        top_bar = QHBoxLayout(); top_bar.setSpacing(28); main_layout.addLayout(top_bar)
        brand = QHBoxLayout(); brand.setSpacing(8); top_bar.addLayout(brand)

        logo = QLabel(); logo.setFixedSize(32, 32); logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = os.path.join(bin_path, "icons", "logo.png").replace("\\", "/")
        if os.path.exists(logo_path): logo.setPixmap(QPixmap(logo_path).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        brand.addWidget(logo)

        title_box = QVBoxLayout(); title_box.setSpacing(0); title_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title = QLabel("CopynDown"); title.setObjectName("title")
        version = QLabel(f"Version {self.version}"); version.setObjectName("version"); version.setStyleSheet("font-size: 11px;")
        title_box.addWidget(title); title_box.addWidget(version); brand.addLayout(title_box)

        self.nav_frame = QFrame(); self.nav_frame.setObjectName("navFrame"); self.nav_frame.setFixedHeight(40); self.nav_frame.setMinimumWidth(455)
        nav_layout = QHBoxLayout(self.nav_frame); nav_layout.setContentsMargins(3, 3, 3, 3); nav_layout.setSpacing(3)
        top_bar.addWidget(self.nav_frame, 1, Qt.AlignmentFlag.AlignHCenter)

        self.tab_buttons = {}
        for tab in self.tabs:
            btn = PillButton(tab); btn.setObjectName("pill")
            btn.clicked.connect(lambda checked=False, name=tab: self.select_tab(name))
            nav_layout.addWidget(btn); self.tab_buttons[tab] = btn

        self.settings_btn = self._footer_btn(" Settings", 100, "settings"); self.settings_btn.clicked.connect(self.show_settings)
        top_bar.addWidget(self.settings_btn, 0, Qt.AlignmentFlag.AlignRight)

        # ÁREA CENTRAL
        self.main_card = QFrame(); self.main_card.setObjectName("mainCard")
        main_layout.addWidget(self.main_card, 1)
        card_layout = QVBoxLayout(self.main_card); card_layout.setContentsMargins(40, 20, 40, 20); card_layout.setSpacing(15)

        self.desc_label = QLabel("Video Downloader"); self.desc_label.setObjectName("muted"); self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.desc_label); card_layout.addSpacing(-8)

        self.input_frame = QFrame(); self.input_frame.setObjectName("inputFrame"); self.input_frame.setFixedHeight(47)
        input_layout = QHBoxLayout(self.input_frame); input_layout.setContentsMargins(8, 5, 6, 5); input_layout.setSpacing(8)
        self.main_entry = QLineEdit(); self.main_entry.setObjectName("mainEntry"); self.main_entry.setPlaceholderText("Paste URL here")
        
        self.main_btn = QPushButton("Search"); self.main_btn.setObjectName("primaryButton"); self.main_btn.setFixedSize(75, 36)
        self.main_btn.clicked.connect(self.open_manual_selection) 
        
        def on_entry_focus_in(event):
            QLineEdit.focusInEvent(self.main_entry, event)
            self.on_clipboard_change()
        self.main_entry.focusInEvent = on_entry_focus_in
        self.main_entry.returnPressed.connect(self.trigger_download_from_url_entry)
        
        input_layout.addWidget(self.main_entry, 1); input_layout.addWidget(self.main_btn)
        card_layout.addWidget(self.input_frame)

        # VARIÁVEIS INVISÍVEIS PARA MANTER A LÓGICA DAS ABAS DE CONVERSÃO
        self.lbl_1, self.menu_1 = self._field("Quality", ["2160p (4K)", "1440p (QHD)", "1080p (AV1/VP9)", "1080p (H.264)", "720p", "480p", "360p"])
        self.lbl_2, self.menu_2 = self._field("Format", ["MP4", "MKV", "WEBM"])
        self.lbl_3, self.menu_3 = self._field("Video Codec", ["Original", "H.264", "H.265", "VP9"])
        self.lbl_4, self.menu_4 = self._field("Audio Codec", ["Original", "AAC", "MP3", "FLAC", "ALAC", "Opus", "None (Video Only)"])

        self.options_frame = QWidget()
        opt_lay = QVBoxLayout(self.options_frame); opt_lay.setContentsMargins(0, 0, 0, 0); opt_lay.setSpacing(10)
        self.row1_widget = QWidget()
        row1_layout = QGridLayout(self.row1_widget); row1_layout.setContentsMargins(0, 5, 0, 0); row1_layout.setHorizontalSpacing(20); row1_layout.setVerticalSpacing(10)
        row1_layout.addWidget(self.lbl_1, 0, 0); row1_layout.addWidget(self.menu_1, 1, 0)
        row1_layout.addWidget(self.lbl_2, 0, 1); row1_layout.addWidget(self.menu_2, 1, 1)
        opt_lay.addWidget(self.row1_widget)
        self.row2_widget = QWidget()
        row2_layout = QGridLayout(self.row2_widget); row2_layout.setContentsMargins(0, 0, 0, 0); row2_layout.setHorizontalSpacing(20); row2_layout.setVerticalSpacing(10)
        row2_layout.addWidget(self.lbl_3, 0, 0); row2_layout.addWidget(self.menu_3, 1, 0)
        row2_layout.addWidget(self.lbl_4, 0, 1); row2_layout.addWidget(self.menu_4, 1, 1)
        opt_lay.addWidget(self.row2_widget)
        card_layout.addWidget(self.options_frame)

        self.switches_container = QWidget()
        switches_layout = QVBoxLayout(self.switches_container); switches_layout.setSpacing(12); switches_layout.setContentsMargins(0, 0, 0, 0)
        
        self.switch_advanced = Switch("Advanced selection")
        self.switch_extract_audio = Switch("Extract original audio")
        self.switch_extract_audio.toggled.connect(self.on_extract_audio_toggle)
        
        self.switch_subtitles = Switch("Download subtitles")
        self.switch_subtitles.setChecked(self.config_data[self.TAB_VID].get("native_subs", False) or self.config_data[self.TAB_VID].get("auto_subs", False))
        
        self.subtitles_row_widget = QWidget(); self.subtitles_row_widget.setFixedHeight(30)
        subtitles_row = QHBoxLayout(self.subtitles_row_widget); subtitles_row.setContentsMargins(0, 0, 0, 0); subtitles_row.setSpacing(8); subtitles_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.switch_subtitles.setFixedHeight(20)
        subtitles_row.addWidget(self.switch_subtitles, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        subtitles_row.addSpacing(8)
        self.subs_embed_check = QCheckBox("Embed subtitles"); self.subs_embed_check.setObjectName("fieldCheck"); self.subs_embed_check.setFixedHeight(20); self.subs_embed_check.setChecked(self.config_data[self.TAB_VID].get("embed_subs", False))
        subtitles_row.addWidget(self.subs_embed_check, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        subtitles_row.addSpacing(8)
        subs_lang_label = QLabel("Language:"); subs_lang_label.setObjectName("fieldLabel"); subtitles_row.addWidget(subs_lang_label)
        self.subs_lang_combo = QComboBox(); self.subs_lang_combo.setObjectName("subtitleCombo")
        self.subs_lang_combo.addItems(list(self.lang_map.values())[1:])
        self.subs_lang_combo.setFixedWidth(120)
        self.subs_lang_combo.setCurrentText(self.lang_map.get(self.config_data[self.TAB_VID].get("langs", "en"), "English"))
        subtitles_row.addWidget(self.subs_lang_combo)
        subtitles_row.addSpacing(8)
        subs_trans_label = QLabel("Translate to:"); subs_trans_label.setObjectName("fieldLabel"); subtitles_row.addWidget(subs_trans_label)
        self.subs_trans_combo = QComboBox(); self.subs_trans_combo.setObjectName("subtitleCombo")
        self.subs_trans_combo.addItems(list(self.lang_map.values()))
        self.subs_trans_combo.setFixedWidth(120)
        self.subs_trans_combo.setCurrentText(self.lang_map.get(self.config_data[self.TAB_VID].get("trans_langs", "none"), "None"))
        subtitles_row.addWidget(self.subs_trans_combo)
        subtitles_row.addStretch(1)

        self.subs_extra_widgets = [self.subs_embed_check, subs_lang_label, self.subs_lang_combo, subs_trans_label, self.subs_trans_combo]
        for widget in self.subs_extra_widgets: widget.setVisible(False)

        switches_layout.addWidget(self.subtitles_row_widget)
        switches_layout.addWidget(self.switch_advanced, 0, Qt.AlignmentFlag.AlignLeft)
        switches_layout.addWidget(self.switch_extract_audio, 0, Qt.AlignmentFlag.AlignLeft)
        card_layout.addWidget(self.switches_container)

        self.action_frame = QWidget()
        actions = QHBoxLayout(self.action_frame); actions.setContentsMargins(0, 5, 0, 5); actions.setSpacing(20); actions.addStretch(1)
        self.btn_download = QPushButton("Download media"); self.btn_download.setObjectName("primaryButton"); self.btn_download.setFixedWidth(150); self.btn_download.setStyleSheet("min-height: 24px; font-size: 13px;")
        self.btn_download.clicked.connect(self.handle_unified_download)
        self.btn_cancel = QPushButton("Cancel"); self.btn_cancel.setObjectName("dangerButton"); self.btn_cancel.setFixedWidth(150); self.btn_cancel.setStyleSheet("min-height: 24px; font-size: 13px;"); self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_download)
        actions.addWidget(self.btn_download); actions.addWidget(self.btn_cancel); actions.addStretch(1)
        card_layout.addWidget(self.action_frame)

        self.status_frame = QWidget()
        self.status_frame.setMinimumWidth(200)
        status_lay = QVBoxLayout(self.status_frame)
        status_lay.setContentsMargins(15, 0, 15, 0) # Margem lateral para não colar nos botões
        status_lay.setSpacing(2)
        self.progress_label = QLabel("Ready!")
        self.progress_label.setObjectName("muted")
        self.progress_label.setStyleSheet("font-size: 11px;")
        status_lay.addWidget(self.progress_label, 0, Qt.AlignmentFlag.AlignCenter)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        status_lay.addWidget(self.progress)

        # HISTÓRICO ROLÁVEL
        self.history_scroll = QScrollArea(); self.history_scroll.setWidgetResizable(True); self.history_scroll.setObjectName("settingsScroll")
        self.history_content = QWidget(); self.history_content.setStyleSheet("background-color: transparent;")
        self.history_layout = QVBoxLayout(self.history_content); self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop); self.history_layout.setSpacing(8)
        self.history_scroll.setWidget(self.history_content)
        card_layout.addWidget(self.history_scroll, 1)

        # RODAPÉ
        footer = QHBoxLayout(); footer.setSpacing(10); main_layout.addLayout(footer)
        self.open_btn = self._footer_btn(" Open location", 140, "folder"); self.open_btn.clicked.connect(self.open_folder)
        self.logs_btn = self._footer_btn(" View logs", 110, "log"); self.logs_btn.clicked.connect(self.show_logs)
        self.about_btn = self._footer_btn(" About", 110, "about"); self.about_btn.clicked.connect(self.show_about)
        
        footer.addWidget(self.open_btn)
        footer.addWidget(self.status_frame, 1)  # <--- Adicionado ao meio do rodapé, ocupando o espaço vazio
        footer.addWidget(self.logs_btn)
        footer.addWidget(self.about_btn)
        
        apply_ui_ux_cursors(self)

    def _field(self, label_text, values):
        label = QLabel(label_text); label.setObjectName("fieldLabel")
        combo = QComboBox(); combo.addItems(values); combo.setMinimumHeight(35); combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return label, combo

    def _footer_btn(self, text, width, icon_name=None):
        btn = QPushButton(text)
        btn.setObjectName("smallFooter")
        btn.setFixedWidth(width)
        if icon_name:
            btn.setProperty("icon_name", icon_name)
            self.set_button_icon(btn, icon_name)
        return btn

    def set_button_icon(self, btn, icon_name):
        icon_path = os.path.join(bin_path, "icons", CURRENT_THEME, f"{icon_name}.svg").replace("\\", "/")
        if os.path.exists(icon_path):
            from PySide6.QtCore import QSize
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(16, 16))

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
        
        if is_convert:
            self.main_btn.setText("Browse")
            self.main_btn.setObjectName("browseButton"); self.main_btn.setStyleSheet("")
            self.main_btn.clicked.disconnect(); self.main_btn.clicked.connect(self.browse_source)
        else:
            self.main_btn.setText("Search")
            self.main_btn.setObjectName("primaryButton"); self.main_btn.setStyleSheet("")
            self.main_btn.clicked.disconnect(); self.main_btn.clicked.connect(self.open_manual_selection)
            
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
        ext_video = "*.mp4 *.mkv *.webm *.mov *.avi"
        ext_audio = "*.m4a *.mp3 *.flac *.wav *.opus *.ogg"
        if self.current_category == self.TAB_C_AUD: filters = f"Audio Files ({ext_audio});;Video Files ({ext_video})"
        else: filters = f"Video Files ({ext_video});;Audio Files ({ext_audio})"
            
        start_dir = getattr(self, "last_source_browse_dir", "")
        if not start_dir or not os.path.isdir(start_dir):
            gen_cfg = self.config_data.get("General", {})
            raw_path = gen_cfg.get("audio_path") if self.current_category == self.TAB_C_AUD else gen_cfg.get("video_path")
            start_dir = os.path.expanduser(raw_path or "~")

        file = QFileDialog.getOpenFileName(self, "Select Media File", start_dir, filters)[0]
        if file:
            self.last_source_browse_dir = os.path.dirname(file)
            self.main_entry.setText(file.replace("\\", "/"))
            self.evaluate_ui_state()

    def on_extract_audio_toggle(self):
        state = not self.switch_extract_audio.isChecked()
        self.menu_1.setEnabled(state); self.menu_3.setEnabled(state); self.menu_4.setEnabled(state)

    def evaluate_ui_state(self, *args):
        cat = self.current_category
        is_convert = cat in [self.TAB_C_VID, self.TAB_C_AUD]

        # Exibe a barra de progresso apenas durante atualizações de software
        self.progress.setVisible(self.is_updating)

        if self.is_updating:
            self.input_frame.setVisible(False)
            self.options_frame.setVisible(False)
            self.switches_container.setVisible(False)      
            self.action_frame.setVisible(False)
            return
            
        self.input_frame.setVisible(True)
        
        self.options_frame.setVisible(is_convert)
        self.switches_container.setVisible(is_convert)
        self.history_scroll.setVisible(True)  # <--- Alterado para True para aparecer na aba de Conversão
        
        self._do_update_queue_ui()
        
        if is_convert:
            self.btn_download.setText("Convert media")
            self.row2_widget.setVisible(True)
            self.switch_advanced.setVisible(False)
            self.switch_extract_audio.setVisible(cat == self.TAB_C_AUD)
            self.subtitles_row_widget.setVisible(False)
            self.switch_subtitles.setVisible(False)
        
        self.action_frame.setVisible(is_convert)

    def schedule_ui_evaluation(self, event=None):
        self.ui_update_timer.start(200)
        
    def reset_status(self, text="Ready!", color=None):
        self.status_timer.stop()
        self.progress_label.setText(text)
        if color: self.progress_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        else: self.progress_label.setStyleSheet("font-size: 11px;")
            
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
        self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['danger']}; }}") 
        if log_msg: self.add_to_log(log_msg)

    def status_error(self, log_msg=""): self.set_terminal_state("Process Error! (Check Logs)", log_msg)
    def status_canceled(self, log_msg=">>> Process Canceled!", label_text="Canceled!"):
        self.progress.setRange(0, 100); self.progress.setValue(100)
        self.progress_label.setText(label_text)
        if label_text == "Paused":
            self.progress_label.setStyleSheet("font-size: 11px;") # Cor removida para Pausado
        else:
            self.progress_label.setStyleSheet(f"color: {COLORS['muted']}; font-size: 11px;")
        self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['warning'] if label_text == 'Paused' else COLORS['muted']}; }}")
        if log_msg: self.add_to_log(log_msg)
        self.schedule_reset(3000)

    def safe_ui(self, func, *args, **kwargs):
        self.ui_signal.emit(func, args, kwargs)

    def _execute_safe_ui(self, func, args, kwargs):
        try: func(*args, **kwargs)
        except RuntimeError: pass
        except Exception as e:
            try: self.add_to_log(f">>> UI Execution Error Suppressed: {e}")
            except Exception: sys.stdout.write(f"UI Execution Error Suppressed: {e}\n")

    def is_valid_media_url(self, text_url):
        if not text_url or len(text_url) < 12: return False
        return text_url.startswith("https://") and any(d in text_url.lower() for d in self.valid_domains)

    def on_clipboard_change(self):
        try:
            if not self.config_data.get("General", {}).get("auto_paste", True) or self.current_category in [self.TAB_C_VID, self.TAB_C_AUD]: return
            text = QApplication.clipboard().text()[:2000]
            if self.is_valid_media_url(text) and self.main_entry.text() != text:
                self.main_entry.setText(text); self.evaluate_ui_state()
                if not self.is_busy and not self.is_updating:
                    self.reset_status("URL Auto-Detected!"); self.schedule_reset()
        except Exception: pass

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
        
    # MÉTODOS DE HISTÓRICO:
    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        if item.get("status") == "Running":
                            item["status"] = "Paused" # Previne travamentos de itens antigos
                        self.download_queue.append(item)
            except Exception as e: 
                self.add_to_log(f">>> Failed to load queue history: {e}")

    def save_history(self):
        # Apenas (re)inicia o timer. Se for chamado 50x em 1 segundo, ele só executará 1 vez no final.
        self.history_timer.start(1000)

    def _do_save_history(self):
        # Esta é a função que realmente escreve no disco
        try:
            # Filtra a fila para salvar APENAS os itens que não são conversões
            itens_para_salvar = [item for item in self.download_queue if not item.get("is_convert", False)]
            
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(itens_para_salvar, f, indent=4)
        except Exception as e: 
            self.add_to_log(f">>> Erro ao salvar histórico: {e}")
        
    def refresh_theme_colors(self):
        txt = self.progress_label.text()
        if "Complete" in txt:
            self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['blue']}; }}") # Barra de progresso azul padrão
            self.progress_label.setStyleSheet("font-size: 11px;") # Texto com cor padrão
        elif "Incomplete" in txt:
            self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['warning']}; }}")
            self.progress_label.setStyleSheet(f"color: {COLORS['warning']}; font-size: 11px;")
        elif "Error" in txt or "Failed" in txt or "Invalid" in txt:
            self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['danger']}; }}")
            self.progress_label.setStyleSheet(f"color: {COLORS['danger']}; font-size: 11px;")
        elif "Canceled" in txt: 
            self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['muted']}; }}")
            self.progress_label.setStyleSheet("font-size: 11px;")
        else:
            self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['blue']}; }}")
            self.progress_label.setStyleSheet("font-size: 11px;")
            
        icon_buttons = [getattr(self, 'settings_btn', None), getattr(self, 'open_btn', None), getattr(self, 'logs_btn', None), getattr(self, 'about_btn', None)]
        for btn in icon_buttons:
            if btn and btn.property("icon_name"): self.set_button_icon(btn, btn.property("icon_name"))
            
        if hasattr(self, 'queue_rows'):
            for row in self.queue_rows:
                # Atualiza o fundo do card
                row["frame"].setStyleSheet(f"QFrame {{ background-color: {COLORS['input']}; border-radius: 8px; }}")
                
                # Atualiza o botão de Ação (Play/Pause/Restart)
                btn_style = (f"QPushButton {{ background-color: {COLORS['button']}; color: {COLORS['text']}; border-radius: 4px; padding: 0px; font-weight: bold; font-size: 15px; }}"
                             f"QPushButton:hover {{ background-color: {COLORS['button_hover']}; }}")
                row["action"].setStyleSheet(btn_style)

                # Atualiza os botões Sub (Setas)
                btn_sub_style = (f"QPushButton {{ background-color: {COLORS['button']}; color: {COLORS['text']}; border-radius: 4px; padding: 0px; font-weight: bold; font-size: 13px; }}"
                                 f"QPushButton:hover {{ background-color: {COLORS['button_hover']}; }}"
                                 f"QPushButton:disabled {{ background-color: {COLORS['input2']}; color: {COLORS['muted2']}; }}")
                row["up"].setStyleSheet(btn_sub_style)
                row["down"].setStyleSheet(btn_sub_style)

                # Atualiza o botão de Remoção (X)
                btn_remove_style = (f"QPushButton {{ background-color: {COLORS['button']}; color: {COLORS['text']}; border-radius: 4px; padding: 0px; font-weight: bold; font-size: 13px; }}"
                                    f"QPushButton:hover {{ background-color: {COLORS['danger']}; color: white; }}"
                                    f"QPushButton:disabled {{ background-color: {COLORS['input2']}; color: {COLORS['muted2']}; }}")
                row["remove"].setStyleSheet(btn_remove_style)
                
            # Força a interface a re-aplicar as novas cores nos textos (Nome, Status, etc)
            self.update_queue_ui()

    def add_to_log(self, text):
        self.full_logs_list.append(text)
        if len(self.full_logs_list) > 5000: self.full_logs_list = self.full_logs_list[-5000:]
        if getattr(self, 'log_window', None): self.log_window.append_log(text)

    def clear_logs(self):
        self.full_logs_list = ["--- Program Logs ---"]
        if self.log_window: self.log_window.update_logs(self.full_logs_list)
        self.add_to_log(">>> Logs cleared.")

    def copy_logs(self):
        QApplication.clipboard().setText("\n".join(self.full_logs_list))
        self.add_to_log(">>> Logs copied to clipboard.")
    
    def toggle_buttons(self, state, is_downloading=True):
        self.is_busy = (state == "disabled")
        if getattr(self, 'btn_cancel', None):
            self.btn_cancel.setEnabled(state == "disabled" and is_downloading)
        for btn in self.tab_buttons.values(): btn.setEnabled(state == "normal")
        try:
            if hasattr(self, 'about_win') and self.about_win.isVisible():
                self.about_win.update_btn.setEnabled(state == "normal")
        except RuntimeError: pass

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
            if proxy_url: cmd.extend(["--proxy", proxy_url])
        
        if is_json: cmd.append("-J")
        else:
            cmd.append("--newline"); cmd.extend(["--retries", str(gen_cfg.get("max_retries", "10"))])
            if gen_cfg.get("prefer_video", False): cmd.append("--no-playlist")
            delay = gen_cfg.get("delay_mode", "Playlist Only")
            apply = (delay == "All Downloads") or (delay == "Playlist Only" and "list=" in url.lower())
            if apply: cmd.extend(["--sleep-interval", str(gen_cfg.get("sleep_min", "2")), "--max-sleep-interval", str(gen_cfg.get("sleep_max", "5")), "--sleep-requests", str(gen_cfg.get("sleep_req", "1"))])
            speed_map = {"1 MB/s": "1M", "5 MB/s": "5M", "10 MB/s": "10M", "25 MB/s": "25M", "50 MB/s": "50M"}
            speed_choice = gen_cfg.get("speed_limit", "Unlimited")
            if speed_choice in speed_map: cmd.extend(["--limit-rate", speed_map[speed_choice]])
        return cmd

    def add_subtitle_args(self, base_cmd, cfg):
        if cfg.get("native_subs"): base_cmd.append("--write-subs")
        if cfg.get("auto_subs"): base_cmd.append("--write-auto-subs")
        if cfg.get("native_subs") or cfg.get("auto_subs"):
            src = cfg.get("langs", "en")
            tgt = cfg.get("trans_langs", "none")
            def get_variants(lang): return self.lang_variants.get(lang, [lang])
            def exact_patterns(items): return [rf"^{re.escape(item)}$" for item in items]
            
            if tgt != "none":
                translated = [f"{target}-{source}" for target in get_variants(tgt) for source in get_variants(src)]
                patterns = exact_patterns(translated)
                if cfg.get("auto_subs"):
                    target_group = "|".join(re.escape(item) for item in get_variants(tgt))
                    source_group = "|".join(re.escape(item) for item in get_variants(src))
                    patterns.append(rf"^(?:{target_group})-(?:{source_group})-(?!(?:en|pt|es|fr|de|it|ja|ko|ru|zh|nl|id|pl|th|tr|vi)(?:-|$))[A-Za-z0-9_-]+$")
            else:
                patterns = exact_patterns(get_variants(src))
            s_str = ",".join(patterns)
            base_cmd.extend(["--sub-langs", s_str, "--convert-subs", "srt"])
            if cfg.get("embed_subs"): base_cmd.append("--embed-subs")
        return base_cmd

    def trigger_download_from_url_entry(self):
        try:
            if hasattr(self, 'manual_win') and self.manual_win.isVisible(): 
                return
        except RuntimeError:
            # Captura a exceção caso o objeto C++ da janela já tenha sido destruído
            self.manual_win = None 

        if self.current_category in [self.TAB_VID, self.TAB_AUD]:
            self.open_manual_selection()
        elif self.btn_download.isVisible() and self.btn_download.isEnabled():
            self.btn_download.click()

    def handle_unified_download(self):
        tab = self.current_category
        if tab == self.TAB_C_VID: self.convert_media("video"); return
        elif tab == self.TAB_C_AUD: self.convert_media("audio"); return

    def download_video(self, url):
        cfg = self.config_data[self.TAB_VID].copy()
        if not self.switch_subtitles.isChecked():
            cfg["native_subs"] = False
            cfg["auto_subs"] = False
            cfg["embed_subs"] = False
        else:
            cfg["native_subs"] = True
            cfg["auto_subs"] = True
            cfg["langs"] = self.rev_lang_map.get(self.subs_lang_combo.currentText(), "en")
            cfg["trans_langs"] = self.rev_lang_map.get(self.subs_trans_combo.currentText(), "none")
            cfg["embed_subs"] = self.subs_embed_check.isChecked()
            
        r_path = getattr(self, '_temp_manual_dir', None)
        if not r_path: r_path = os.path.expanduser(self.config_data["General"]["video_path"])
        self._temp_manual_dir = None
        is_social = any(d in url for d in ["instagram.com", "tiktok.com", "kwai.com", "kw.ai", "twitter.com", ".x.com", "facebook.com", "fb.watch", "reddit.com", "linkedin.com", "pinterest.com", "snapchat.com"])
        
        tmpl_map = {"Title (Default)": "%(title)s.%(ext)s", "Title + Video ID": "%(title)s [%(id)s].%(ext)s", "Title + Format ID": "%(title)s [%(format_id)s].%(ext)s", "Title + Resolution": "%(title)s [%(resolution)s].%(ext)s"}
        o_tmpl = "%(uploader)s [%(id)s].%(ext)s" if is_social else tmpl_map.get(self.config_data.get("General", {}).get("file_template", "Title (Default)"), "%(title)s.%(ext)s")
        
        b_cmd = self.build_base_cmd(url=url)
        vfmt = self.menu_2.currentText().lower()
        if cfg["thumb"] and vfmt != "webm": b_cmd.append("--embed-thumbnail")
        if cfg["meta"]:
            b_cmd.extend(["--embed-metadata", "--parse-metadata", "%(playlist_index|)s:%(track_number)s", "--parse-metadata", "%(release_year,release_date,date,upload_date).4s:%(meta_date)s", "--parse-metadata", "%(album_artist,creator,channel|)s:%(meta_album_artist)s"])

        b_cmd = self.add_subtitle_args(b_cmd, cfg)

        res_map = {"360p": "360", "480p": "480", "720p": "720", "1080p (H.264)": "1080", "1080p (AV1/VP9)": "1080", "1440p (QHD)": "1440", "2160p (4K)": "2160"}
        sq = self.menu_1.currentText()
        
        pending_logs = []
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
        self.run_command(cmd, url, pending_logs, dest_folder=r_path)

    def download_music(self, url):
        cfg = self.config_data[self.TAB_AUD]
        r_path = getattr(self, '_temp_manual_dir', None)
        if not r_path: r_path = os.path.expanduser(self.config_data["General"]["audio_path"])
        self._temp_manual_dir = None
        afmt, q = self.menu_2.currentText().lower(), self.menu_1.currentText()
        b_cmd = self.build_base_cmd(url=url) + ["-x", "--audio-format", afmt]
        
        if cfg["thumb"] and afmt != "wav": b_cmd.append("--embed-thumbnail")
        if cfg["meta"] and afmt != "wav":
            b_cmd.extend(["--embed-metadata", "--parse-metadata", "%(playlist_index|)s:%(track_number)s", "--parse-metadata", "%(release_year,release_date,date,upload_date).4s:%(meta_date)s", "--parse-metadata", "%(album_artist,creator,channel|)s:%(meta_album_artist)s"])
            
        b_map = {"Low (128 kbps)": "128k", "Medium (192 kbps)": "192k", "High (320 kbps)": "320k"}
        if q != "Auto": b_cmd.extend(["--audio-quality", b_map.get(q)])
        cmd = b_cmd + ["-o", f"{r_path}/%(playlist_index&{{}}. |)s%(title)s.%(ext)s", url]
        self.run_command(cmd, url, dest_folder=r_path)
    
    def get_audio_codec(self, filepath):
        ffprobe_exe = os.path.join(bin_path, f"ffprobe{self.exe}").replace("\\", "/")
        if not os.path.exists(ffprobe_exe): ffprobe_exe = "ffprobe"
        try:
            cmd = [ffprobe_exe, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "default=noprint_wrappers=1:nokey=1", filepath]
            res = subprocess.run(cmd, capture_output=True, text=True, startupinfo=self.startupinfo)
            if res.returncode == 0 and res.stdout.strip(): return res.stdout.strip().lower()
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
        if not os.path.exists(src): self.reset_status("Source file does not exist.", COLORS["danger"]); self.schedule_reset(); return
        
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
        
        cmd.append(dst); self.run_command(cmd, base, pending_logs, dest_folder=save_dir)

    def _revert_queue_btn(self):
        pass # Sem botão footer mais
    
    def run_command(self, cmd, task_name="Media Task", task_logs=None, dest_folder=""):
        is_conv = self.current_category in [self.TAB_C_VID, self.TAB_C_AUD]
        qi = {"cmd": cmd, "name": task_name, "is_convert": is_conv, "logs": task_logs or [], "status": "Pending", "url": task_name, "dest_folder": dest_folder}
        self.download_queue.insert(0, qi) # <--- Alterado de append para insert
        self.save_history() # <--- Adicionado
        self.safe_ui(self.update_queue_ui)

        if not is_conv and task_name.startswith("http"):
            def fetch_title():
                gen = self.queue_generation
                self.title_fetch_semaphore.acquire()
                try:
                    if gen != self.queue_generation: return
                    t_cmd = self.build_base_cmd(is_json=True, silent=True) + ["--flat-playlist", "--no-warnings", "--playlist-items", "1", task_name]
                    res = subprocess.run(t_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', startupinfo=self.startupinfo, timeout=30)
                    if gen != self.queue_generation: return
                    if res.returncode == 0:    
                        info = json.loads(res.stdout.strip())
                        p_t = info.get('playlist_title') or info.get('playlist')
                        n_name = f"[Playlist] {p_t}" if p_t else (f"[Playlist] {info.get('title')}" if "list=" in task_name.lower() else info.get('title') or task_name)
                        qi["name"] = n_name
                        self.safe_ui(self.update_queue_ui)
                except Exception as e:
                    if gen == self.queue_generation: self.safe_ui(self.add_to_log, f"Could not fetch title: {e}")
                finally:
                    self.title_fetch_semaphore.release()
            threading.Thread(target=fetch_title, daemon=True).start()
            
        if getattr(self, 'current_process', None) is None and not self.is_updating:
            self.process_next_in_queue()

    def _finish_task(self, is_conv, err, d_str, t_f=None):
        
        if t_f and (err or self.is_cancelling):
            try:
                if os.path.exists(t_f):
                    os.remove(t_f)
                    self.add_to_log(f">>> Lixo residual removido: {os.path.basename(t_f)}")
            except Exception as e:
                self.add_to_log(f">>> Aviso: Não foi possível remover o arquivo incompleto: {e}")
        
        if self.is_cancelling:
            # Assume que foi pausado (o botão ⏸ já renomeia o status para Paused antes de cancelar)
            status_val = "Paused" 
            
            for t in self.download_queue:
                if t["status"] == "Running":
                    t["status"] = "Canceled"
                    status_val = "Canceled" # Confirma que foi um Cancelamento global
                    break
            
            if status_val == "Paused":
                self.status_canceled(">>> Process Paused!", "Paused")
            else:
                self.status_canceled()
            
            self.is_queue_running = False
            self.update_queue_ui()
            self.toggle_buttons("normal")
            self.save_history()
            
            QTimer.singleShot(500, self.process_next_in_queue)
            return
            
        elif not err:
            msg = f"Conversion Complete! (Total time: {d_str})" if is_conv else f"Download Complete! (Total time: {d_str})"
            self.progress_label.setText(msg); self.progress_label.setStyleSheet("font-size: 11px;") # Cor removida
            self.progress.setRange(0, 100); self.progress.setValue(100)
            self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['success']}; }}") 
            self.add_to_log(f">>> {msg}\n")
            self.notify_user("CopynDown", msg)
            
            # Aplica o Completed no item correto, ignorando em qual linha ele está
            for t in self.download_queue:
                if t["status"] == "Running":
                    t["status"] = "Completed"
                    break
        else:
            is_p = getattr(self, 'current_playlist_item', '') != ""
            if is_conv or is_p:
                msg = "Conversion Incomplete (Check Logs)" if is_conv else "Download Incomplete (Check Logs)"
                self.progress_label.setText(msg); self.progress_label.setStyleSheet(f"color: {COLORS['warning']}; font-size: 11px;")
                self.progress.setRange(0, 100); self.progress.setValue(100)
                self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['warning']}; }}") 
                self.add_to_log(f">>> {msg}\n")
                self.notify_user("CopynDown", msg, QSystemTrayIcon.MessageIcon.Warning)
            else:
                self.status_error()
                self.notify_user("CopynDown", "Process Error! Check logs for details.", QSystemTrayIcon.MessageIcon.Critical)
                
            for t in self.download_queue:
                if t["status"] == "Running":
                    t["status"] = "Failed"
                    break
        
        self.update_queue_ui()
        self.save_history()
        QTimer.singleShot(2000 if err else 500, self.process_next_in_queue)

    def process_next_in_queue(self):
        if getattr(self, 'current_process', None) is not None: 
            return
        next_task_idx = None
        
        # Lê a fila de trás para frente (de baixo para cima na interface)
        for i in range(len(self.download_queue) - 1, -1, -1):
            if self.download_queue[i]["status"] == "Pending":
                next_task_idx = i
                break

        if next_task_idx is None:
            self.is_queue_running = False
            self.queue_start_time = None
            self.update_queue_ui()
            self.toggle_buttons("normal")
            return

        if not getattr(self, 'queue_start_time', None):
            self.queue_start_time = time.time()

        self.is_queue_running = True
        
        task = self.download_queue[next_task_idx]
        task["status"] = "Running"
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

        for log_msg in task.get("logs", []): self.add_to_log(log_msg)

        def worker():
            err = False
            last_reported_progress = -1   # <-- ADICIONE ISTO AQUI
            last_reported_time = -1       # <-- ADICIONE ISTO AQUI
            try:
                kwargs = {'startupinfo': self.startupinfo}
                if not self.is_windows: kwargs['preexec_fn'] = os.setsid
                self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8', errors='replace', **kwargs)
                
                for line in self.current_process.stdout:
                    c = line.strip()
                    if c:
                        if "ERROR:" in c or "Invalid data found" in c: err = True; self.safe_ui(self.add_to_log, c); continue
                        if is_conv and "time=" in c:
                            el = int(time.time() - getattr(self, 'queue_start_time', time.time()))
                            if el != last_reported_time:  # <-- Só atualiza a tela se o segundo mudou!
                                last_reported_time = el
                                task["progress_text"] = f"Converting... (Elapsed time: {el//60}m {el%60}s)" if el>=60 else f"Converting... (Elapsed time: {el}s)"
                                self.safe_ui(self.update_single_queue_row)
                            
                        if not is_conv and "Downloading item" in c:
                            m = re.search(r"Downloading item (\d+ of \d+)", c)
                            if m: self.current_playlist_item = f" [{m.group(1)}]"
                            
                        if "100%" in c or "already been downloaded" in c or "already is in target format" in c:
                            self.safe_ui(self.add_to_log, c)
                            if not is_conv:
                                task["progress"] = 100
                                self.safe_ui(self.update_queue_ui)
                                
                        elif "B/s" not in c and "ETA" not in c and "time=" not in c: 
                            self.safe_ui(self.add_to_log, c)
                            
                        if not is_conv:
                            m = self.re_progress.search(c)
                            if m and not err and not self.is_cancelling:
                                new_progress = int(float(m.group(1)))
                                if new_progress != last_reported_progress:  # <-- Só atualiza a tela se a porcentagem (número inteiro) mudou!
                                    last_reported_progress = new_progress
                                    task["progress"] = new_progress
                                    task["progress_text"] = f"Downloading{self.current_playlist_item}... {task['progress']}%"
                                    self.safe_ui(self.update_single_queue_row)

                return_code = self.current_process.wait()

                if return_code != 0 and not self.is_cancelling:
                    err = True
                    self.safe_ui(self.add_to_log, f">>> Process finished with error code: {return_code}")

                if is_conv: self.safe_ui(lambda: self.progress.setRange(0, 100))

                el = int(time.time() - getattr(self, 'queue_start_time', time.time()))
                d_str = f"{el//60}m {el%60}s" if el >= 60 else f"{el}s"
                t_f = cmd[-1] if is_conv else None

                self.safe_ui(lambda err=err, d_str=d_str, t_f=t_f: self._finish_task(is_conv, err, d_str, t_f))
                
            except Exception as e:
                self.safe_ui(self.status_error, f"SYSTEM ERROR: {e}")
                self.safe_ui(lambda: self._finish_task(is_conv, True, "0s", None))
            finally:
                self.current_process = None; 
                if getattr(self, 'btn_cancel', None): self.safe_ui(lambda: self.btn_cancel.setText("Cancel"))
        threading.Thread(target=worker, daemon=True).start()

    def cancel_download(self):
        proc = self.current_process
        if proc and not self.is_cancelling:
            if getattr(self, 'btn_cancel', None):
                self.btn_cancel.setEnabled(False)
                self.btn_cancel.setText("Cancelling...")
            self.is_cancelling = True
            self.add_to_log(">>> Attempting to force close process...")
            try:
                if self.is_windows:
                    res = subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)], capture_output=True, text=True, encoding='oem', errors='replace', startupinfo=self.startupinfo, timeout=3)
                    if res.stdout: self.add_to_log(res.stdout.strip())
                    if res.stderr: self.add_to_log(res.stderr.strip())
                else: 
                    import signal
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                
                # NOVO: Fecha a via de comunicação para liberar a memória do Python e abortar a Thread instantaneamente
                try:
                    if proc.stdout:
                        proc.stdout.close()
                except Exception:
                    pass
                    
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
        btn = self.sender()
        # Verifica se o remetente existe e se é um botão antes de mexer no cursor
        if isinstance(btn, QPushButton):
            btn.setCursor(Qt.CursorShape.ArrowCursor)
            QTimer.singleShot(300, lambda: btn.setCursor(Qt.CursorShape.PointingHandCursor) if btn else None)

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

    def check_ytdlp_updates(self, force=False, show_message=False, btn_to_restore=None):
        last_check_file = os.path.join(bin_path, ".last_ytdlp_check").replace("\\", "/")
        def finish_ui():
            self.is_updating = False
            if btn_to_restore:
                try:
                    btn_to_restore.setEnabled(True)
                    btn_to_restore.setText("Check for updates")
                except RuntimeError: pass
            if not self.is_queue_running:
                self.toggle_buttons("normal")
                self.reset_status()
                if self.download_queue and not self.is_updating:
                    self.process_next_in_queue()

        if not os.path.exists(self.ytdlp_path):
            self.safe_ui(self.add_to_log, ">>> Warning: yt-dlp is missing! Update check skipped. Please check your 'bin' folder.")
            self.safe_ui(finish_ui)
            return

        if not force and os.path.exists(last_check_file):
            try:
                elapsed = time.time() - os.path.getmtime(last_check_file)
                if elapsed < 3600:
                    self.safe_ui(self.add_to_log, ">>> yt-dlp update check skipped. It was checked less than 60 minutes ago.")
                    self.safe_ui(finish_ui)
                    return
            except Exception: pass

        try:
            self.is_updating = True
            self.safe_ui(self.toggle_buttons, "disabled", False)
            self.safe_ui(self.reset_status, "Checking yt-dlp updates...")
            result = subprocess.run([self.ytdlp_path, "-U"], capture_output=True, text=True, encoding="utf-8", errors="replace", startupinfo=self.startupinfo, timeout=60)
            output = (result.stdout or "") + "\n" + (result.stderr or "")
            if output.strip():
                for line in output.splitlines():
                    if line.strip(): self.safe_ui(self.add_to_log, f"[yt-dlp update] {line.strip()}")
            if result.returncode != 0 and not output.strip():
                self.safe_ui(self.add_to_log, f">>> yt-dlp update check failed with exit code {result.returncode}.")
            with open(last_check_file, "w", encoding="utf-8") as f: f.write(str(time.time()))
            if show_message:
                final_msg = "yt-dlp update check completed."
                if result.returncode == 0:
                    for line in reversed(output.splitlines()):
                        clean_line = line.strip()
                        clean_lower = clean_line.lower()
                        if "up to date" in clean_lower or "updated yt-dlp to" in clean_lower:
                            final_msg = clean_line
                            break
                def show_ytdlp_result(msg=final_msg, code=result.returncode):
                    QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
                    if code == 0: QMessageBox.information(self, "yt-dlp update", msg)
                    else: QMessageBox.warning(self, "yt-dlp update", "yt-dlp update check failed. See logs for details.")
                    QApplication.restoreOverrideCursor()
                    finish_ui()
                self.safe_ui(show_ytdlp_result)
        except subprocess.TimeoutExpired:
            self.safe_ui(self.add_to_log, ">>> yt-dlp update check timed out after 60 seconds.")
            with open(last_check_file, "w", encoding="utf-8") as f: f.write(str(time.time()))
            if show_message:
                def show_ytdlp_timeout():
                    QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
                    QMessageBox.warning(self, "yt-dlp update", "yt-dlp update check timed out.")
                    QApplication.restoreOverrideCursor()
                    finish_ui()
                self.safe_ui(show_ytdlp_timeout)
        except Exception as e:
            err_msg = str(e) 
            self.safe_ui(self.add_to_log, f">>> yt-dlp update check error: {err_msg}")
            with open(last_check_file, "w", encoding="utf-8") as f: f.write(str(time.time()))
            if show_message:
                def show_ytdlp_err(msg=err_msg):
                    QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
                    QMessageBox.warning(self, "yt-dlp update", f"yt-dlp update check failed:\n{msg}")
                    QApplication.restoreOverrideCursor()
                    finish_ui()
                self.safe_ui(show_ytdlp_err)
        finally:
            if not show_message: self.safe_ui(finish_ui)

    def get_local_version(self):
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, "r", encoding='utf-8') as f: return f.read().strip()
            except Exception: pass
        return "Unknown"

    def start_github_update(self, btn=None, dialog=None, is_startup=False, check_ytdlp_after=False):
        self.is_updating = True
        self.safe_ui(self.toggle_buttons, "disabled", False)
        self.safe_ui(self.reset_status, "Checking program updates...")
        if is_startup: self.safe_ui(self.add_to_log, ">>> Checking for updates on startup...")
        def task():
            def restore_ui():
                self.is_updating = False
                if btn:
                    try:
                        btn.setEnabled(True)
                        btn.setText("Check for updates")
                    except RuntimeError: pass
                self.toggle_buttons("normal")
                self.reset_status()

            def start_ytdlp_check(force, show_message):
                threading.Thread(target=lambda: self.check_ytdlp_updates(force=force, show_message=show_message, btn_to_restore=btn), daemon=True).start()

            def continue_after_github():
                if is_startup: start_ytdlp_check(False, False)
                elif check_ytdlp_after: start_ytdlp_check(True, True)
                else: restore_ui()

            try:
                v = self.get_local_version()
                r = requests.get("https://api.github.com/repos/DanMixerBR/CopynDown/releases/latest", timeout=10)
                if r.status_code == 403: raise Exception("GitHub API rate limit exceeded.")
                r.raise_for_status()
                r_json = r.json()
                rv = re.search(r'\d+(\.\d+)+', r_json["tag_name"]).group()

                if rv != v:
                    self.safe_ui(self.add_to_log, f">>> Update available: {rv}. Please update the program.")
                    def ask_update():
                        QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
                        ans = QMessageBox.question(self, "Update", f"Update available: {rv}\nUpdate now?")
                        QApplication.restoreOverrideCursor()
                        if ans == QMessageBox.StandardButton.Yes:
                            threading.Thread(target=self.do_update, daemon=True).start()
                            try:
                                if dialog: dialog.accept()
                            except RuntimeError: pass
                        else: continue_after_github()
                    self.safe_ui(ask_update)
                else:
                    self.safe_ui(self.add_to_log, f">>> Program is up to date (Version {v}).")
                    if is_startup: continue_after_github()
                    else:
                        def show_up_to_date():
                            QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
                            QMessageBox.information(self, "Up to date", "You are using the latest version.")
                            QApplication.restoreOverrideCursor()
                            continue_after_github()
                        self.safe_ui(show_up_to_date)
            except Exception as e:
                err_msg = str(e)
                if is_startup:
                    self.safe_ui(self.add_to_log, f">>> Startup update check failed: {err_msg}")
                    self.safe_ui(restore_ui)
                else:
                    def show_update_error(msg=err_msg):
                        self.set_terminal_state("Update Failed!", f"ERROR: {msg}")
                        QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
                        QMessageBox.critical(self, "Update Error", f"ERROR: {msg}")
                        QApplication.restoreOverrideCursor()
                        restore_ui()
                    self.safe_ui(show_update_error)
        threading.Thread(target=task, daemon=True).start()

    def do_update(self):
        try:
            self.safe_ui(lambda: (
                self.progress.setRange(0, 100), 
                self.progress_label.setText("Starting update..."), 
                self.progress_label.setStyleSheet("font-size: 11px;")
            ))
            self.safe_ui(self.add_to_log, "\n>>> Starting update...")
            
            url = "https://github.com/DanMixerBR/CopynDown/releases/latest/download/CopynDown_Windows.zip" if self.is_windows else "https://github.com/DanMixerBR/CopynDown/releases/latest/download/CopynDown_Linux.zip"
            zip_platform = "CopynDown_Windows.zip" if self.is_windows else "CopynDown_Linux.zip"
            z_path = os.path.join(base_dir, zip_platform) 
            hash_url = "https://raw.githubusercontent.com/DanMixerBR/CopynDown/refs/heads/main/hash_v2.txt"
            
            if os.path.exists(z_path): os.remove(z_path)

            self.safe_ui(self.add_to_log, "Downloading update file...")
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
                                self.safe_ui(lambda p=percent: (self.progress.setValue(p), self.progress_label.setText(f"Downloading update... {p}%")))
                                last_reported = percent

            zip_size_mb = os.path.getsize(z_path) / (1024 * 1024)
            if zip_size_mb < 100.0:
                if os.path.exists(z_path): os.remove(z_path)
                raise Exception(f"ERROR: File suspiciously small ({zip_size_mb:.1f} MB). Aborted.")

            self.safe_ui(lambda: (self.progress_label.setText("Verifying update... 50%"), self.progress.setValue(50)))
            self.safe_ui(self.add_to_log, "Verifying update file...")

            with zipfile.ZipFile(z_path, 'r') as zf: corrupt_file = zf.testzip()
            if corrupt_file is not None:
                if os.path.exists(z_path): os.remove(z_path)
                raise Exception("ERROR: The downloaded zip structure is corrupted.")
            
            self.safe_ui(self.add_to_log, "File structure verified (OK).")

            r_hash = requests.get(hash_url, timeout=10)
            if r_hash.status_code == 200:
                expected_hashes = [line.strip().lower().replace("sha256:", "") for line in r_hash.text.splitlines() if line.strip()]
                sha256_hash = hashlib.sha256()
                with open(z_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""): sha256_hash.update(byte_block)
                if sha256_hash.hexdigest().lower() not in expected_hashes:
                    if os.path.exists(z_path): os.remove(z_path)
                    raise Exception(f"Hash verification failed for {zip_platform}!")
                self.safe_ui(self.add_to_log, f"Hash verification (OK): {zip_platform}")
            else:
                if os.path.exists(z_path): os.remove(z_path)
                raise Exception("Could not download hash_v2.txt.")

            self.safe_ui(lambda: (self.progress_label.setText("Preparing update... 75%"), self.progress.setValue(75)))
            self.safe_ui(self.add_to_log, "Downloading update script...")

            s_ext = "bat" if self.is_windows else "sh"
            s_name = f"update.{s_ext}"
            s_path = os.path.join(base_dir, s_name)
            r_s = requests.get(f"https://raw.githubusercontent.com/DanMixerBR/CopynDown/refs/heads/main/{s_name}", timeout=10)
            if r_s.status_code != 200: raise Exception("Could not download update script.")

            script_hash = hashlib.sha256(r_s.content).hexdigest().lower()
            if script_hash not in expected_hashes: raise Exception(f"Hash verification failed for {s_name}!")
            with open(s_path, 'wb') as f: f.write(r_s.content)
            self.safe_ui(self.add_to_log, f"Hash verification (OK): {s_name}")

            self.safe_ui(lambda: (
                self.progress_label.setText("Update Ready! (100%)"),
                self.progress_label.setStyleSheet(f"color: {COLORS['success']}; font-size: 11px;"),
                self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {COLORS['success']}; }}"),
                self.progress.setValue(100)
            ))
            self.safe_ui(self.add_to_log, ">>> Update downloaded and verified successfully!")

            def finish_update():
                QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
                QMessageBox.information(self, "Success", "Update Ready! The app will close to complete the update.")
                QApplication.restoreOverrideCursor()
                if os.path.exists(s_path):
                    if self.is_windows:
                        subprocess.Popen(["cmd.exe", "/c", "start", "", f"update.{s_ext}", str(os.getpid())], cwd=base_dir, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True, creationflags=0x00000010)
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
                        if not abriu_terminal: subprocess.Popen(['bash', s_path], cwd=base_dir, env=limpo_env, start_new_session=True)
                os._exit(0)

            self.safe_ui(finish_update)

        except Exception as e:
            self.is_updating = False
            err_msg = str(e)
            self.safe_ui(self.set_terminal_state, "Update Failed!", f"ERROR: {err_msg}")
            self.safe_ui(self.evaluate_ui_state)
            self.safe_ui(self.toggle_buttons, "normal")
            def show_err(msg=err_msg): 
                QApplication.setOverrideCursor(Qt.CursorShape.ArrowCursor)
                QMessageBox.critical(self, "Update Error", f"ERROR: {msg}")
                QApplication.restoreOverrideCursor()
            self.safe_ui(show_err)

    def closeEvent(self, event):
        proc = self.current_process
        if proc:
            # 1. MATA O PROCESSO PRIMEIRO (Crucial para soltar o "Lock" do arquivo no SO Windows)
            try:
                if self.is_windows: 
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)], capture_output=True, startupinfo=self.startupinfo, timeout=2)
                else: 
                    import signal
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except: 
                pass

            # 2. OTIMIZAÇÃO: Pequeno delay para garantir que o Sistema Operacional devolva o controle do arquivo
            time.sleep(0.1)

            # 3. BLOCO ISOLADO: Tenta remover o arquivo residual de forma segura
            try:
                for task in self.download_queue:
                    if task["status"] == "Running":
                        # Garante que a exclusão pelo índice cmd[-1] ocorra apenas em conversões
                        if task.get("is_convert", False):
                            target_file = task["cmd"][-1]
                            if target_file and os.path.exists(target_file):
                                os.remove(target_file)
                        break
            except: 
                pass
        
        event.accept()
        os._exit(0)

def main():
    if sys.platform.startswith("linux"):
        os.environ["QT_QPA_PLATFORMTHEME"] = "xdgdesktopportal"
    app = QApplication(sys.argv)
    app.setApplicationName("CopynDown")
    set_app_icon(app)
    load_app_font(app)
    app.setStyleSheet(get_app_qss())
    win = CopynDownApp()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()