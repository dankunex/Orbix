import sys
import os
import subprocess
import webbrowser
import ctypes
import shutil
import urllib.request
import locale
import tempfile
import winreg

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QComboBox, QPushButton,
    QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QFont, QIntValidator


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class CustomTitleBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.update_style()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 10, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.icon_label = QLabel()
        if parent.img_top_pix:
            self.icon_label.setPixmap(
                parent.img_top_pix.scaled(
                    20, 20, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        layout.addWidget(self.icon_label)
        
        self.title_label = QLabel(parent.ui_strings[parent.current_lang]["title"].upper())
        self.title_label.setStyleSheet(f"color: {parent.COLOR_TEXT}; font-weight: 600; font-size: 14px; border: none;")
        layout.addWidget(self.title_label)
        
        layout.addStretch()

        self.btn_min = QPushButton("-")
        self.btn_min.setFixedSize(30, 30)
        self.btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_min.clicked.connect(parent.showMinimized)
        layout.addWidget(self.btn_min)
        
        self.btn_close = QPushButton("×")
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(parent.close)
        layout.addWidget(self.btn_close)

        self.update_button_styles()
        self.startPos = None

    def update_style(self):
        self.setStyleSheet(f"background-color: {self.parent.COLOR_BG}; border: none; border-top-left-radius: 8px; border-top-right-radius: 8px;")

    def update_button_styles(self):
        btn_style = f"""
            QPushButton {{
                border: none;
                font-size: 28px;
                color: {self.parent.COLOR_TEXT};
                background: transparent;
                padding-bottom: 3px;
            }}
        """
        self.btn_min.setStyleSheet(btn_style + "QPushButton:hover { color: #FFB02E; }")
        self.btn_close.setStyleSheet(btn_style + "QPushButton:hover { color: #FF4655; }")
        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"color: {self.parent.COLOR_TEXT}; font-weight: 900; font-size: 15px; border: none;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.startPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.startPos:
            delta = event.globalPosition().toPoint() - self.startPos
            self.parent.move(self.parent.pos() + delta)
            self.startPos = event.globalPosition().toPoint()


class Orbix(QMainWindow):
    ORBIX_VERSION = "1.5.1"

    def __init__(self):
        super().__init__()
        self.ui_strings = {
            "ENG": {
                "title": "Orbix", "sel": "QUEST SELECT", "start": "START", "stop": "STOP",
                "idle": "Idle", "run": "Active: ", "add": "NEW QUEST", "conf": "SAVE",
                "src": "Download", "err_list": "Error",
                "upd_banner": "{v} is available!",
                "changelog_banner": "Changelog",
                "custom_default": "Custom",
                "up_to_date": "Orbix is up to date", "input_ph": "Executable name", "placeholder": "None selected",
                "search_ph": "Search quests...", "timer_ph": "0 min"
            },
            "ESP": {
                "title": "Orbix", "sel": "ELIGE UNA MISIÓN", "start": "INICIAR", "stop": "DETENER",
                "idle": "En espera", "run": "Activo: ", "add": "NUEVA MISIÓN", "conf": "GUARDAR",
                "src": "Descargar", "err_list": "Error",
                "upd_banner": "¡{v} ya disponible!",
                "changelog_banner": "Cambios",
                "custom_default": "Personalizado",
                "up_to_date": "Orbix está actualizado", "input_ph": "Nombre del ejecutable", "placeholder": "Ninguna seleccionada",
                "search_ph": "Buscar misiones...", "timer_ph": "0 min"
            },
            "VAL": {
                "title": "Orbix", "sel": "TRIA UNA MISSIÓ", "start": "INICIAR", "stop": "ATURAR",
                "idle": "En espera", "run": "Actiu: ", "add": "NOVA MISSIÓ", "conf": "GUARDAR",
                "src": "Descarregar", "err_list": "Error",
                "upd_banner": "{v} ja disponible!",
                "changelog_banner": "Canvis",
                "custom_default": "Personalitzat",
                "up_to_date": "Orbix està actualitzat", "input_ph": "Nom d'executable", "placeholder": "Cap seleccionada",
                "search_ph": "Buscar missió...", "timer_ph": "0 min"
            }
        }
        self.current_lang = self.detect_system_lang()
        self.is_dark = self.check_system_dark_mode()
        self.setup_colors()
        self.load_icons()
        
        self.active_display_name = None
        self.motor_process = None
        self.temp_exe_path = None
        self.created_paths = []
        self.games_db = {}
        self.remote_version = self.ORBIX_VERSION
        self.custom_input = None

        self.selected_minutes = 0
        self.remaining_seconds = 0
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowSystemMenuHint | 
            Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.setFixedSize(300, 320)
        
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.update_central_widget_style()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)
        
        self.setup_ui()
        self.load_remote_list()
                
        QTimer.singleShot(1000, self.check_for_updates)

    def update_central_widget_style(self):
        self.central_widget.setStyleSheet(f"""
            QWidget#CentralWidget {{
                background-color: {self.COLOR_BG};
                border: 1px solid {self.COLOR_BORDER};
            }}
        """)

    def setup_colors(self):
        if self.is_dark:
            self.COLOR_BG, self.COLOR_CARD, self.COLOR_INPUT, self.COLOR_TEXT, self.COLOR_SUBTEXT = "#1A1A1A", "#2A2A2A", "#3F3F3F", "#F0F0F0", "#FFFFFF"
            self.COLOR_BORDER = "#333333"
            self.HOVER_BRIGHTNESS = "rgba(255, 255, 255, 0.1)"
            self.ARROW_COLOR = "#F0F0F0"
        else:
            self.COLOR_BG, self.COLOR_CARD, self.COLOR_INPUT, self.COLOR_TEXT, self.COLOR_SUBTEXT = "#F5F5F7", "#FFFFFF", "#EBEBED", "#1D1D1F", "#51585F"
            self.COLOR_BORDER = "#E0E0E2"
            self.HOVER_BRIGHTNESS = "rgba(0, 0, 0, 0.03)"
            self.ARROW_COLOR = "#1D1D1F"
        self.COLOR_ACCENT, self.COLOR_DANGER, self.COLOR_GOOD, self.COLOR_IDLE = "#C58DCA", "#FF4655", "#59E659", "#FFB02E"

    def load_icons(self):
        try:
            ico_path = resource_path("img/orbicon.ico")
            if os.path.exists(ico_path):
                app_icon = QIcon(ico_path)
                self.setWindowIcon(app_icon)
                self.img_top_pix = app_icon.pixmap(32, 32)
            else:
                self.img_top_pix = None
        except Exception:
            self.img_top_pix = None

    def check_system_dark_mode(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
        except Exception:
            return True

    def detect_system_lang(self):
        try:
            lang_code, _ = locale.getlocale()
            if lang_code:
                lang = lang_code.lower()
                if lang.startswith("es"): return "ESP"
                if lang.startswith("ca") or lang.startswith("val"): return "VAL"
        except Exception:
            pass
        return "ENG"

    def setup_ui(self):
        t = self.ui_strings[self.current_lang]
        self.title_bar = CustomTitleBar(self)
        self.main_layout.addWidget(self.title_bar)
        
        self.banners_container = QWidget()
        self.banners_layout = QHBoxLayout(self.banners_container)
        self.banners_layout.setContentsMargins(12, 0, 12, 0)
        self.banners_layout.setSpacing(6)

        self.update_banner = QPushButton()
        self.update_banner.setFixedHeight(20)
        self.update_banner.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_banner.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.COLOR_CARD};
                font-size: 12px;
                border-radius: 6px;
                color: #fff;
            }}
            QPushButton:hover {{
                background-color: #906594;
            }}
        """)
        self.update_banner.clicked.connect(lambda: webbrowser.open("https://ivandfx.com/labs/orbix"))

        self.changelog_banner = QPushButton(t["changelog_banner"])
        self.changelog_banner.setFixedHeight(20)
        self.changelog_banner.setFixedWidth(75)
        self.changelog_banner.setCursor(Qt.CursorShape.PointingHandCursor)
        self.changelog_banner.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.COLOR_CARD};
                font-size: 12px;
                border-radius: 6px;
                color: #fff;
            }}
            QPushButton:hover {{
                background-color: #906594;
            }}
        """)
        self.changelog_banner.clicked.connect(lambda: webbrowser.open("https://github.com/ivandfx/Orbix/releases/latest"))

        self.banners_layout.addWidget(self.update_banner, 1)
        self.banners_layout.addWidget(self.changelog_banner)

        self.banners_container.hide()
        self.main_layout.addWidget(self.banners_container)

        self.container = QFrame()
        self.container.setStyleSheet(f"background-color: {self.COLOR_BG}; border: none;")
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(25, 10, 25, 10)
        self.content_layout.setSpacing(8)
        
        header_actions = QHBoxLayout()
        
        self.lang_btn = QPushButton(self.current_lang)
        self.lang_btn.setFixedSize(40, 22)
        self.lang_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_btn.setStyleSheet(f"""
            QPushButton {{ color: {self.COLOR_SUBTEXT}; border: 2px solid {self.COLOR_CARD}; font-weight: bold; border-radius: 6px; }}
            QPushButton:hover {{ background-color: {self.HOVER_BRIGHTNESS}; border-color: {self.COLOR_ACCENT}; }}
        """)
        self.lang_btn.clicked.connect(self.switch_lang)
        
        self.ver_btn = QPushButton(self.ORBIX_VERSION)
        self.ver_btn.setFixedSize(40, 22)
        self.ver_btn.setStyleSheet(self.lang_btn.styleSheet())
        self.ver_btn.clicked.connect(self.handle_ver_click)
        self.ver_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        header_actions.addStretch()
        header_actions.addWidget(self.lang_btn)
        header_actions.addWidget(self.ver_btn)
        self.content_layout.addLayout(header_actions)

        self.sel_lbl = QLabel(t["sel"])
        self.sel_lbl.setStyleSheet(f"color: {self.COLOR_SUBTEXT}; font-weight: bold; font-size: 12px;")
        self.content_layout.addWidget(self.sel_lbl)

        self.search_input = QLineEdit()
        self.search_input.setFixedHeight(32)
        self.search_input.setPlaceholderText(t["search_ph"])
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.COLOR_INPUT};
                color: {self.COLOR_TEXT};
                border-radius: 5px;
                padding-left: 10px;
                padding-right: 10px;
                border: 1px solid {self.COLOR_CARD};
            }}
            QLineEdit:focus {{
                border: 1px solid {self.COLOR_ACCENT};
            }}
        """)
        self.search_input.textChanged.connect(self.filter_activities)
        self.search_input.returnPressed.connect(self.toggle_quest)
        self.content_layout.addWidget(self.search_input)

        selector_layout = QHBoxLayout()
        self.selector = QComboBox()
        self.selector.setFixedHeight(38)
        self.selector.setPlaceholderText(t["placeholder"])
        self.selector.setCurrentIndex(-1)

        self.selector.setStyleSheet(f"""
            QComboBox {{ 
                background-color: {self.COLOR_INPUT}; 
                color: {self.COLOR_TEXT}; 
                border-radius: 5px; 
                padding-left: 8px; 
                padding-right: 25px;
                font-size: 12px;
                border: none; 
            }}
            QComboBox:hover {{ 
                background-color: {self.COLOR_CARD}; 
            }}
            QComboBox::drop-down {{ 
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border: none;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
                width: 0px;
                height: 0px;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {self.ARROW_COLOR};
                background: none;
            }}
            QAbstractItemView {{ 
                color: {self.COLOR_TEXT}; 
                selection-background-color: {self.COLOR_ACCENT}; 
                selection-color: white; 
                outline: none; 
                border: 1px solid {self.COLOR_CARD}; 
                border-radius: 5px; 
                background-color: {self.COLOR_BG}; 
            }}
            QScrollBar:vertical {{ border: none; background: {self.COLOR_BG}; width: 8px; margin: 0px; }}
            QScrollBar::handle:vertical {{ background: {self.COLOR_CARD}; min-height: 20px; border-radius: 4px; }}
            QScrollBar::handle:vertical:hover {{ background: {self.COLOR_ACCENT}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ border: none; background: none; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        """)

        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(38, 38)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {self.COLOR_CARD}; color: {self.COLOR_ACCENT}; font-size: 18px; font-weight: bold; border-radius: 5px; border: none; }}
            QPushButton:hover {{ background-color: #906594; color: {self.COLOR_SUBTEXT}; }}
        """)
        self.add_btn.clicked.connect(self.show_add_custom)
        
        selector_layout.addWidget(self.selector)
        selector_layout.addWidget(self.add_btn)
        self.content_layout.addLayout(selector_layout)

        self.main_btn = QPushButton(t["start"])
        self.main_btn.setFixedHeight(50)
        self.main_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_main_button_style(self.COLOR_ACCENT)
        self.main_btn.clicked.connect(self.toggle_quest)
        self.content_layout.addWidget(self.main_btn)
        
        self.content_layout.addStretch()
        self.main_layout.addWidget(self.container)

        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(30)
        self.status_bar.setStyleSheet(f"background-color: {self.COLOR_CARD}; border: none; border-top: 1px solid {self.COLOR_BORDER}; border-top-left-radius: 8px; border-top-right-radius: 8px;")
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(10, 0, 10, 0)
        self.status_dot = QFrame()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet(f"background-color: {self.COLOR_IDLE}; border-radius: 4px; border: none;")
        self.status_msg = QLabel(t["idle"])
        self.status_msg.setStyleSheet(f"color: {self.COLOR_SUBTEXT}; font-size: 11px; border: none;")
        
        self.timer_input = QLineEdit()
        self.timer_input.setFixedSize(50, 20)
        self.timer_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_input.setPlaceholderText(t["timer_ph"])
        self.timer_input.setValidator(QIntValidator(1, 999))
        self.timer_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.COLOR_INPUT};
                font-size: 12px;
                border-radius: 6px;
                border: 1px solid {self.COLOR_BORDER};
                color: {self.COLOR_TEXT};
            }}
            QLineEdit:focus {{
                border: 1px solid {self.COLOR_ACCENT};
            }}
        """)
        
        status_layout.addWidget(self.status_dot)
        status_layout.addWidget(self.status_msg)
        status_layout.addStretch()
        status_layout.addWidget(self.timer_input)
        self.main_layout.addWidget(self.status_bar)

        self.overlay = QFrame(self.central_widget)
        self.refresh_overlay_geometry()
        self.overlay.setStyleSheet(f"background-color: {self.COLOR_BG}; border: none; border-radius: 8px;")
        self.overlay.hide()
        
        self.overlay_layout = QVBoxLayout(self.overlay)
        self.overlay_layout.setContentsMargins(25, 10, 25, 20)
        self.overlay_layout.setSpacing(15)

    def refresh_overlay_geometry(self):
        self.overlay.setGeometry(1, 1, self.width() - 2, self.height() - 2)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.toggle_quest()
        else:
            super().keyPressEvent(event)

    def filter_activities(self, query):
        query = query.strip().lower()
        self.selector.clear()
        
        filtered = [name for name in sorted(self.games_db.keys()) if query in name.lower()]
        if filtered:
            self.selector.addItems(filtered)
            self.selector.setCurrentIndex(0)
        else:
            self.selector.setCurrentIndex(-1)

    def update_main_button_style(self, color):
        self.main_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {color}; color: #1f1f1f; font-weight: 900; font-size: 18px; border-radius: 8px; margin-top: 5px; border: none; }}
            QPushButton:hover {{ background-color: #906594; color: {self.COLOR_TEXT};}}
        """)

    def handle_ver_click(self):
        self.show_about()

    def load_remote_list(self):
        url = "https://raw.githubusercontent.com/ivandfx/Orbix/refs/heads/main/activities.txt"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                content = response.read().decode('utf-8')
                for line in content.splitlines():
                    if "=" in line:
                        label, exe = line.split("=", 1)
                        self.games_db[label.strip()] = exe.strip()
            self.refresh_combo()
        except Exception: 
            self.selector.addItem(self.ui_strings[self.current_lang]["err_list"])

    def refresh_combo(self):
        self.selector.clear()
        self.selector.addItems(sorted(self.games_db.keys()))
        self.adjust_combo_popup_height()

    def adjust_combo_popup_height(self):
        view = self.selector.view()
        margin = 35
        space_above = self.selector.mapTo(self, self.selector.rect().topLeft()).y() - margin
        space_below = self.height() - self.selector.mapTo(self, self.selector.rect().bottomLeft()).y() - margin
        max_available_space = max(space_above, space_below, 50)
        
        count = self.selector.count()
        item_height = view.sizeHintForRow(0) if count > 0 else 25
        if item_height <= 0:
            item_height = 25
        
        needed_height = count * item_height + 10
        final_height = min(needed_height, max_available_space)
        
        self.selector.setMaxVisibleItems(max(1, int(final_height // item_height)))
        view.setMaximumHeight(int(final_height))

    def switch_lang(self):
        langs = ["ENG", "ESP", "VAL"]
        self.current_lang = langs[(langs.index(self.current_lang) + 1) % len(langs)]
        t = self.ui_strings[self.current_lang]
        self.selector.setPlaceholderText(t["placeholder"])
        self.search_input.setPlaceholderText(t["search_ph"])
        self.timer_input.setPlaceholderText(t["timer_ph"])
        self.sel_lbl.setText(t["sel"])
        self.title_bar.title_label.setText(t["title"].upper())
        self.main_btn.setText(t["stop"] if self.active_display_name else t["start"])
        self.status_msg.setText(f"{t['run']} {self.active_display_name}" if self.active_display_name else t["idle"])
        self.lang_btn.setText(self.current_lang)
        if hasattr(self, 'banners_container') and self.banners_container.isVisible():
            self.update_banner.setText(t["upd_banner"].format(v=self.remote_version))
            self.changelog_banner.setText(t["changelog_banner"])
        if self.custom_input:
            self.custom_input.setPlaceholderText(t["input_ph"])

    def toggle_quest(self):
        t = self.ui_strings[self.current_lang]
        if not self.active_display_name:
            selected = self.selector.currentText()
            if not selected or selected in [t["placeholder"], t["err_list"]]: return
            raw_path = self.games_db[selected]
            if "/" in raw_path or "\\" in raw_path:
                process_name = os.path.basename(raw_path)
                folder_path = os.path.dirname(raw_path)
                full_local_path = os.path.join(os.getcwd(), folder_path)
                if not os.path.exists(full_local_path):
                    os.makedirs(full_local_path)
                    self.created_paths.append(full_local_path)
                target_dir = full_local_path
            else:
                process_name = raw_path
                target_dir = tempfile.gettempdir()
            
            motor_source = resource_path("motor.exe")
            try:
                if os.path.exists(motor_source):
                    self.temp_exe_path = os.path.join(target_dir, f"{process_name}.exe")
                    shutil.copy2(motor_source, self.temp_exe_path)
                    self.motor_process = subprocess.Popen([self.temp_exe_path, process_name, selected], cwd=target_dir)
                
                self.active_display_name = selected
                self.main_btn.setText(t["stop"])
                self.update_main_button_style(self.COLOR_DANGER)
                self.status_msg.setText(f"{t['run']} {selected}")
                self.status_dot.setStyleSheet(f"background-color: {self.COLOR_GOOD}; border-radius: 4px; border: none;")
                self.selector.setEnabled(False)
                self.search_input.setEnabled(False)

                timer_str = self.timer_input.text().strip()
                if timer_str.isdigit() and int(timer_str) > 0:
                    self.selected_minutes = int(timer_str)
                    self.remaining_seconds = self.selected_minutes * 60
                    self.timer_input.setEnabled(False)
                    QTimer.singleShot(5000, self.start_countdown)
                else:
                    self.selected_minutes = 0

                self.monitor_timer = QTimer()
                self.monitor_timer.timeout.connect(self.monitor_process_check)
                self.monitor_timer.start(1000)
            except Exception:
                pass
        else:
            self.stop_quest()

    def start_countdown(self):
        if self.active_display_name:
            self.countdown_timer.start(1000)

    def update_countdown(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            mins, secs = divmod(self.remaining_seconds, 60)
            self.timer_input.setText(f"{mins:02d}:{secs:02d}")
        else:
            self.countdown_timer.stop()
            self.stop_quest()
            QTimer.singleShot(500, self.close)

    def stop_quest(self):
        t = self.ui_strings[self.current_lang]
        self.countdown_timer.stop()
        self.timer_input.setEnabled(True)
        self.timer_input.setText("")
        
        if self.motor_process:
            try: 
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.motor_process.pid)], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception: 
                self.motor_process.kill()
        
        self.motor_process = None
        QTimer.singleShot(800, self.cleanup_files)
        self.active_display_name = None
        self.main_btn.setText(t["start"])
        self.update_main_button_style(self.COLOR_ACCENT)
        self.status_msg.setText(t["idle"])
        self.status_dot.setStyleSheet(f"background-color: {self.COLOR_IDLE}; border-radius: 4px; border: none;")
        self.selector.setEnabled(True)
        self.search_input.setEnabled(True)

    def cleanup_files(self):
        if self.temp_exe_path and os.path.exists(self.temp_exe_path):
            try: os.remove(self.temp_exe_path)
            except Exception: pass
        for path in reversed(self.created_paths):
            try:
                if os.path.exists(path) and not os.listdir(path): os.rmdir(path)
            except Exception: pass
        self.created_paths = []

    def monitor_process_check(self):
        if self.motor_process and self.motor_process.poll() is not None:
            self.stop_quest()
            self.monitor_timer.stop()

    def add_close_overlay_btn(self):
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        close_btn = QPushButton("‹")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"QPushButton {{ color: {self.COLOR_SUBTEXT}; margin-top: 0px; font-size: 32px; border: none; background: transparent; }}")
        close_btn.clicked.connect(self.overlay.hide)
        btn_container.addWidget(close_btn)
        self.overlay_layout.addLayout(btn_container)

    def show_about(self):
        self.clear_overlay()
        self.refresh_overlay_geometry()
        self.add_close_overlay_btn()
        
        orbix_text = QLabel("Developed by")
        orbix_text.setStyleSheet(f"color: {self.COLOR_TEXT}; font-size: 14px;")
        
        logo_label = QLabel()
        logo_pix = QPixmap(resource_path("img/logo.png"))
        if not logo_pix.isNull():
            logo_label.setPixmap(logo_pix.scaled(100, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo_label.setText("IVANDFX")
            logo_label.setStyleSheet(f"color: {self.COLOR_ACCENT}; font-size: 18px; font-weight: bold;")
        
        gh_btn = QPushButton("WEB")
        gh_btn.setFixedHeight(45)
        gh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gh_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {self.COLOR_ACCENT}; color: #1f1f1f; font-weight: 900; font-size: 18px; border-radius: 8px; border: none; }}
            QPushButton:hover {{ background-color: #906594; }}
        """)
        gh_btn.clicked.connect(lambda: webbrowser.open("https://ivandfx.com/labs/orbix"))
        
        self.overlay_layout.addWidget(orbix_text, 0, Qt.AlignmentFlag.AlignCenter)
        self.overlay_layout.addWidget(logo_label, 0, Qt.AlignmentFlag.AlignCenter)
        self.overlay_layout.addStretch()
        self.overlay_layout.addWidget(gh_btn)
        self.overlay.show()

    def show_add_custom(self):
        self.clear_overlay()
        self.refresh_overlay_geometry()
        t = self.ui_strings[self.current_lang]
        self.add_close_overlay_btn()
        lbl = QLabel(t["add"])
        lbl.setStyleSheet(f"color: {self.COLOR_TEXT}; font-weight: 900; font-size: 16px; border: none;")
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText(t["input_ph"])
        self.custom_input.setFixedHeight(45)
        self.custom_input.setStyleSheet(f"background: {self.COLOR_INPUT}; color: {self.COLOR_TEXT}; border-radius: 8px; padding: 10px; border: 1px solid {self.COLOR_CARD};")
        self.custom_input.returnPressed.connect(self.save_custom)
        save_btn = QPushButton(t["conf"])
        save_btn.setFixedHeight(45)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"QPushButton {{ background: {self.COLOR_ACCENT}; color: white; font-weight: bold; border-radius: 8px; border: none; }} QPushButton:hover {{ background-color: #906594; }}")
        save_btn.clicked.connect(self.save_custom)
        self.overlay_layout.addWidget(lbl)
        self.overlay_layout.addWidget(self.custom_input)
        self.overlay_layout.addStretch()
        self.overlay_layout.addWidget(save_btn)
        self.overlay.show()

    def save_custom(self):
        if self.custom_input:
            name = self.custom_input.text().strip()
            if name:
                process_name = "".join(x for x in name if x.isalnum() or x in "._-").replace(" ", "")
                self.games_db[name] = process_name 
                self.refresh_combo()
                self.selector.setCurrentText(name)
                self.overlay.hide()

    def clear_overlay(self):
        while self.overlay_layout.count():
            child = self.overlay_layout.takeAt(0)
            if child.widget(): 
                child.widget().deleteLater()
            elif child.layout():
                while child.layout().count():
                    inner = child.layout().takeAt(0)
                    if inner.widget(): 
                        inner.widget().deleteLater()

    def check_for_updates(self):
        url = "https://raw.githubusercontent.com/ivandfx/Orbix/refs/heads/main/updat.txt"
        t = self.ui_strings[self.current_lang]
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                remote = response.read().decode('utf-8').strip()
                self.remote_version = remote
                if remote != self.ORBIX_VERSION:
                    self.ver_btn.setStyleSheet(f"""
                        QPushButton {{ color: {self.COLOR_SUBTEXT}; font-weight: bold; border: 2px solid orange; border-radius: 6px; }}
                        QPushButton:hover {{ background-color: {self.HOVER_BRIGHTNESS}; border-color: orange; }}
                    """)
                    self.update_banner.setText(t["upd_banner"].format(v=remote))
                    self.changelog_banner.setText(t["changelog_banner"])
                    self.banners_container.show()
        except Exception:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Orbix()
    window.show()
    sys.exit(app.exec())