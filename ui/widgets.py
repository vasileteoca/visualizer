from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QProgressBar, QVBoxLayout, QHBoxLayout, QRadioButton, QButtonGroup, QLabel
from PySide6.QtGui import QPainter, QImage, QColor
import numpy as np
import random
from water_simulation import (
    disturb_water_point,
    disturb_water_circle,
    disturb_water_blue_shadow,
    map_to_blue_gradient,
    current,
)

LEVEL_BAR_SCALE = 200.0
VIS_WIDTH, VIS_HEIGHT = 1200, 960


class LevelBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, int(LEVEL_BAR_SCALE))
        self.setTextVisible(False)
        self.setFixedHeight(25)

    def set_level(self, level_float):
        val = int(min(level_float * LEVEL_BAR_SCALE, LEVEL_BAR_SCALE))
        self.setValue(val)
        if val < LEVEL_BAR_SCALE * 0.4:
            color = "#28a745"
        elif val < LEVEL_BAR_SCALE * 0.75:
            color = "#ffc107"
        else:
            color = "#dc3545"

        self.setStyleSheet(f"""
            QProgressBar {{border:1px solid #333; border-radius:2px;background:#111;}}
            QProgressBar::chunk {{background-color:{color};}}
        """)


class WaterVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_amplitude = 0

        # Default disturbance mode
        self.disturb_water = disturb_water_point

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Radio buttons
        self.radio_container = QWidget()
        radio_layout = QVBoxLayout(self.radio_container)
        radio_layout.setContentsMargins(5, 5, 5, 5)
        radio_layout.setSpacing(5)

        self.mode_group = QButtonGroup(self)

        self.point_radio = QRadioButton("Point Disturbance")
        self.circle_radio = QRadioButton("Circle Ripples")
        self.shadow_radio = QRadioButton("Blue Shadow")

        self.mode_group.addButton(self.point_radio, 0)
        self.mode_group.addButton(self.circle_radio, 1)
        self.mode_group.addButton(self.shadow_radio, 2)
        self.point_radio.setChecked(True)

        for radio in [self.point_radio, self.circle_radio, self.shadow_radio]:
            radio_layout.addWidget(radio)

        self.mode_group.buttonClicked.connect(self.change_mode)
        main_layout.addWidget(self.radio_container)

    def change_mode(self, button):
        mode = self.mode_group.id(button)
        if mode == 0:
            self.disturb_water = disturb_water_point
        elif mode == 1:
            self.disturb_water = disturb_water_circle
        else:
            self.disturb_water = disturb_water_blue_shadow

    def disturb(self, amplitude):
        self.disturb_water(amplitude)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            rgb = map_to_blue_gradient(current)
            h, w, _ = rgb.shape
            img = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888)
            painter.drawImage(self.rect(), img)

            painter.setPen(QColor(0, 0, 50, 200))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
        finally:
            painter.end()

    def sizeHint(self):
        return QSize(VIS_WIDTH, VIS_HEIGHT)
