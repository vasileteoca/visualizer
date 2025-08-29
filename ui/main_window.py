from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QLabel
)
from PySide6 import QtGui
from ui.widgets import LevelBar, WaterVisualizer
from audio_manager import (
    enumerate_devices,
    start_monitor_thread,
    audio_levels,
    audio_locks,
    selected_sources,
    get_default_output_device
)
from water_simulation import update_water_reflecting
from config import AMPLITUDE_SCALE

MIN_ACTIVITY_THRESHOLD = 0.001  # amplitude threshold to highlight active device

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Water Simulation Visualizer")
        self.setMinimumSize(1400, 960)

        container = QWidget()
        main_layout = QHBoxLayout(container)
        self.setCentralWidget(container)

        # ------------------ LEFT PANEL ------------------
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(5)

        # Start All button
        self.start_button = QPushButton("Start All")
        self.start_button.clicked.connect(self.toggle_all_sources)
        left_layout.addWidget(self.start_button)

        # Radio buttons container
        self.water_display = WaterVisualizer()
        left_layout.addWidget(self.water_display.radio_container)

        # Device table
        self.device_table = QTableWidget(0, 4)
        self.device_table.setHorizontalHeaderLabels(
            ["Device ID", "Device Name", "Monitor", "Level"]
        )
        header = self.device_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        left_layout.addWidget(QLabel("Audio Sources"))
        left_layout.addWidget(self.device_table, 1)

        self.level_bars = {}
        self.populate_device_table()

        # ------------------ RIGHT PANEL ------------------
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.water_display)
        main_layout.addWidget(left_panel, 1)
        main_layout.addLayout(right_layout, 3)

        # ------------------ TIMERS ------------------
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.start(50)

        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self.run_simulation)
        self.sim_timer.start(16)

        # Auto-start default output device
        default_out = get_default_output_device()
        if default_out:
            selected_sources.add(default_out['id'])
            start_monitor_thread(default_out)
            self.update_table_button(default_out['id'], True)

    def populate_device_table(self):
        devices = enumerate_devices()
        for dev in devices:
            row = self.device_table.rowCount()
            self.device_table.insertRow(row)
            self.device_table.setItem(row, 0, QTableWidgetItem(str(dev['id'])))
            self.device_table.setItem(row, 1, QTableWidgetItem(dev['name']))

            btn = QPushButton("Start")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, d=dev, b=btn: self.toggle_source(d, checked, b))
            self.device_table.setCellWidget(row, 2, btn)

            bar = LevelBar()
            self.device_table.setCellWidget(row, 3, bar)
            self.level_bars[dev['id']] = bar

    def toggle_source(self, device_info, checked, btn):
        device_id = device_info['id']
        if checked:
            selected_sources.add(device_id)
            btn.setText("Stop")
            start_monitor_thread(device_info)
        else:
            selected_sources.discard(device_id)
            btn.setText("Start")

    def update_table_button(self, device_id, active):
        for row in range(self.device_table.rowCount()):
            if int(self.device_table.item(row, 0).text()) == device_id:
                btn = self.device_table.cellWidget(row, 2)
                if btn:
                    btn.setChecked(active)
                    btn.setText("Stop" if active else "Start")

    def toggle_all_sources(self):
        all_started = all(
            self.device_table.cellWidget(r, 2).isChecked() for r in range(self.device_table.rowCount())
        )
        for row in range(self.device_table.rowCount()):
            btn = self.device_table.cellWidget(row, 2)
            device_id = int(self.device_table.item(row, 0).text())
            if all_started:
                btn.setChecked(False)
                selected_sources.discard(device_id)
                btn.setText("Start")
            else:
                btn.setChecked(True)
                selected_sources.add(device_id)
                dev = next(d for d in enumerate_devices() if d['id']==device_id)
                start_monitor_thread(dev)
                btn.setText("Stop")
        self.start_button.setText("Stop All" if not all_started else "Start All")

    def update_ui(self):
        for device_id, bar in self.level_bars.items():
            lock = audio_locks.get(device_id)
            if lock:
                with lock:
                    level = audio_levels.get(device_id, 0.0)
            else:
                level = 0.0
            bar.set_level(level)

            # Highlight row if device is active
            color = QtGui.QColor(200, 255, 200) if level >= MIN_ACTIVITY_THRESHOLD else QtGui.QColor(255, 255, 255)
            row = self.get_row(device_id)
            if row == -1:
                continue
            # Only color columns 0 and 1 (QTableWidgetItem), skip widget columns
            for col in range(2):
                item = self.device_table.item(row, col)
                if item:
                    item.setBackground(color)

    def get_row(self, device_id):
        for r in range(self.device_table.rowCount()):
            if int(self.device_table.item(r, 0).text()) == device_id:
                return r
        return -1

    def run_simulation(self):
        combined_amplitude = sum(
            audio_levels.get(dev_id, 0.0) for dev_id in selected_sources
        ) * AMPLITUDE_SCALE
        self.water_display.disturb(combined_amplitude)
        update_water_reflecting()
        self.water_display.update()  # force repaint
