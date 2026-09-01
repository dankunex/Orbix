import sys
import os
import ctypes
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, 
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QIcon, QPixmap, QPainter

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def update_central_widget_style(self):
    self.central_widget.setStyleSheet(f"""
        QWidget#CentralWidget {{
            background-color: {self.COLOR_BG};
            border-radius: 8px;
        }}
    """)

class ScrollingLabel(QLabel):
    def __init__(self, text, style, parent=None):
        super().__init__(parent)
        self.full_text = text
        self.setStyleSheet(f"{style} border: none; background: transparent;")
        self.x_offset = 0
        self.scroll_speed = 1
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scroll)
        self.setContentsMargins(0, 0, 0, 0)
        
    def update_scroll(self):
        text_width = self.fontMetrics().horizontalAdvance(self.full_text)
        if text_width > self.width():
            self.x_offset -= self.scroll_speed
            if abs(self.x_offset) >= text_width + 20:
                self.x_offset = 0
            self.update()
        else:
            self.timer.stop()
            self.x_offset = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        text_width = self.fontMetrics().horizontalAdvance(self.full_text)
        ascent = self.fontMetrics().ascent()
        
        if text_width > self.width():
            if not self.timer.isActive():
                self.timer.start(40)
            painter.drawText(self.x_offset, ascent, self.full_text)
            painter.drawText(self.x_offset + text_width + 20, ascent, self.full_text)
        else:
            painter.drawText(0, ascent, self.full_text)


class CustomTitleBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {parent.COLOR_BG};
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 10, 0)

        self.icon_label = QLabel()
        if parent.img_top_pix:
            self.icon_label.setPixmap(parent.img_top_pix.scaled(
                20, 20, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))
        layout.addWidget(self.icon_label)
        
        self.title_label = QLabel("QUEST")
        self.title_label.setStyleSheet(f"color: {parent.COLOR_TEXT}; font-weight: 900; font-size: 14px; border: none;")
        layout.addWidget(self.title_label)
        
        layout.addStretch()

        self.btn_min = QPushButton("-")
        self.btn_min.setFixedSize(30, 30)
        self.btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_min.setStyleSheet(f"""
            QPushButton {{
                border: none;
                font-size: 28px;
                color: {parent.COLOR_TEXT};
                background: transparent;
            }}
            QPushButton:hover {{
                color: {parent.COLOR_IDLE};
            }}
        """)
        self.btn_min.clicked.connect(self.parent.showMinimized)
        layout.addWidget(self.btn_min)

        self.drag_position = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.parent.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()


class OrbixquestWindow(QMainWindow):
    def __init__(self, process_name, quest_name):
        super().__init__()
        self.process_name = process_name.upper()
        self.quest_name = quest_name.upper()
        
        self.COLOR_BG = "#1A1A1A"
        self.COLOR_TEXT = "#F0F0F0"
        self.COLOR_SUBTEXT = "#6A7480"
        self.COLOR_ACCENT = "#C58DCA"
        self.COLOR_BORDER = "#333333"
        self.COLOR_IDLE = "#FFB02E"
        self.seconds_elapsed = 0

        self.load_icons()

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowSystemMenuHint | 
            Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setFixedSize(300, 125)

        self.central_widget = QWidget()
        self.central_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.COLOR_BG};
                border: 1px solid {self.COLOR_BORDER};
            }}
        """)
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self)
        self.main_layout.addWidget(self.title_bar)

        self.content_area = QFrame()
        self.content_area.setStyleSheet("border: none; background: transparent;")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(25, 0, 25, 12)
        self.content_layout.setSpacing(0)

        self.text_status = QLabel("00:00:00")
        self.text_status.setStyleSheet(f"color: {self.COLOR_ACCENT}; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        
        self.text_main = ScrollingLabel(self.quest_name, f"color: {self.COLOR_TEXT}; font-size: 22px; font-weight: 900;")
        self.text_main.setFixedHeight(35)
        
        self.text_brand = ScrollingLabel(self.process_name, f"color: {self.COLOR_SUBTEXT}; font-size: 11px; font-weight: bold;")
        self.text_brand.setFixedHeight(20)

        self.content_layout.addWidget(self.text_status)
        self.content_layout.addWidget(self.text_main)
        self.content_layout.addStretch()
        self.content_layout.addWidget(self.text_brand)
        
        self.main_layout.addWidget(self.content_area)

        self.chrono_timer = QTimer(self)
        self.chrono_timer.timeout.connect(self.update_timer)
        self.chrono_timer.start(1000)

        self.apply_w11_corners()

    def load_icons(self):
        try:
            ico_path = resource_path("img/orbicon-activ.ico")
            if os.path.exists(ico_path):
                app_icon = QIcon(ico_path)
                self.setWindowIcon(app_icon)
                self.img_top_pix = app_icon.pixmap(32, 32)
            else:
                self.img_top_pix = None
        except Exception:
            self.img_top_pix = None

    def apply_w11_corners(self):
        try:
            hWnd = int(self.winId())
            dwm = ctypes.windll.dwmapi
            corner_preference = ctypes.c_int(2)
            dwm.DwmSetWindowAttribute(
                hWnd, 
                33, 
                ctypes.byref(corner_preference), 
                ctypes.sizeof(corner_preference)
            )
        except Exception:
            pass

    def update_timer(self):
        self.seconds_elapsed += 1
        hours = self.seconds_elapsed // 3600
        minutes = (self.seconds_elapsed % 3600) // 60
        seconds = self.seconds_elapsed % 60
        self.text_status.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")


def main():
    if len(sys.argv) >= 3:
        process_name = sys.argv[1]
        quest_name = sys.argv[2].replace("Custom: ", "")
    elif len(sys.argv) == 2:
        process_name = sys.argv[1]
        quest_name = sys.argv[1].replace("Custom: ", "")
    else:
        file_name = os.path.basename(sys.executable)
        process_name = file_name
        quest_name = file_name[:-4] if file_name.lower().endswith(".exe") else "Orbix Quest"

    if quest_name.lower() in ["motor", "python", "pythonw", "orbix", "orbix.exe"]:
        quest_name = "Orbix Quest"
    
    if process_name.lower() in ["motor.exe", "python.exe", "pythonw.exe", "orbix.exe"]:
        process_name = "ORBIX_PROCESS"

    app = QApplication(sys.argv)

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ivandfx.orbix.quest')
    except AttributeError:
        pass
    
    window = OrbixquestWindow(process_name, quest_name)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()