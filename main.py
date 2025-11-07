#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones, ZoneInfoNotFoundError

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QListWidget, QPushButton, 
                             QTimeEdit, QLineEdit, QStackedWidget, QMessageBox,
                             QSpacerItem, QSizePolicy, QScrollArea, QSystemTrayIcon)
from PyQt6.QtCore import QTimer, QTime, Qt
from PyQt6.QtGui import QFont, QIcon, QAction, QCloseEvent
from pygame import mixer

CONFIG_FILE = 'midnight_clock_config.json'
ALARM_SOUND_FILE = 'alarm.wav'
TRAY_ICON_FILE = 'icon.png'

class MidnightClock(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- Initializations ---
        mixer.init()
        self.alarm_sound = mixer.Sound(ALARM_SOUND_FILE) if os.path.exists(ALARM_SOUND_FILE) else None
        if not self.alarm_sound:
            print(f"Warning: Alarm sound file not found at '{ALARM_SOUND_FILE}'")

        self.config = self.load_config()
        self.is_quitting = False

        self.setWindowTitle("Midnight Clock")
        self.setWindowIcon(QIcon(TRAY_ICON_FILE))
        self.setGeometry(100, 100, 850, 500)
        self.setMinimumSize(800, 450)
        
        self.custom_font_family = "Monospace"
        self.apply_stylesheet()

        # --- System Tray Icon Setup ---
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(TRAY_ICON_FILE))
        self.tray_icon.setToolTip("Midnight Clock is active")
        
        tray_menu = self.create_tray_menu()
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        # --- Main Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Navigation ---
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(180)
        self.nav_list.addItems(["Clock", "World Clocks", "Alarm", "Timer", "Stopwatch"])
        main_layout.addWidget(self.nav_list)

        # --- Pages using QStackedWidget ---
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        self.pages = {name: QWidget() for name in ["Clock", "World Clocks", "Alarm", "Timer", "Stopwatch"]}
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)
        
        # --- Initialize UI for each page ---
        self.init_clock_ui()
        self.init_world_clocks_ui()
        self.init_alarm_ui()
        self.init_timer_ui()
        self.init_stopwatch_ui()

        # --- Connect navigation to page switching ---
        self.nav_list.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

    # --- Event Handling & System Tray ---
    def closeEvent(self, event: QCloseEvent):
        """ Overrides the window's close event. """
        if self.is_quitting:
            event.accept()  # Quit the app for good
        else:
            event.ignore()  # Ignore the window closing
            self.hide()     # Hide the window
            self.tray_icon.show()
            self.tray_icon.showMessage(
                "Midnight Clock",
                "The application is running in the background. Alarms remain active.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )

    def on_tray_icon_activated(self, reason):
        """ Called when the tray icon is activated. """
        if reason == QSystemTrayIcon.ActivationReason.Trigger: # Left-click
            self.show()
            self.activateWindow()

    def force_quit(self):
        """ Quits the application completely. """
        self.is_quitting = True
        self.close()

    def create_tray_menu(self):
        """ Creates the context menu for the tray icon. """
        menu = self.menuBar().addMenu('') # Workaround for menu styling
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.force_quit)
        
        menu.addAction(show_action)
        menu.addAction(quit_action)
        return menu

    # --- Configuration Management ---
    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"pinned_timezones": ["Europe/London", "America/New_York", "Asia/Tokyo"]}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    # --- UI Initializers ---
    def init_clock_ui(self):
        page = self.pages["Clock"]
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label = QLabel()
        self.time_label.setFont(QFont(self.custom_font_family, 100, QFont.Weight.Bold))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("color: #00d0d0;")
        self.date_label = QLabel()
        self.date_label.setFont(QFont(self.custom_font_family, 24))
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_label.setStyleSheet("color: #cccccc;")
        layout.addWidget(self.time_label)
        layout.addWidget(self.date_label)
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(500)
        self.update_clock()

    def init_world_clocks_ui(self):
        page = self.pages["World Clocks"]
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(20, 20, 20, 20)
        pinned_header = QLabel("Pinned Clocks")
        pinned_header.setFont(QFont(self.custom_font_family, 18, QFont.Weight.Bold))
        main_layout.addWidget(pinned_header)
        self.pinned_clocks_widget = QWidget()
        self.pinned_clocks_layout = QVBoxLayout(self.pinned_clocks_widget)
        self.pinned_clocks_layout.setContentsMargins(0, 5, 0, 15)
        main_layout.addWidget(self.pinned_clocks_widget)
        search_header = QLabel("Add Timezone (Double-click to pin)")
        search_header.setFont(QFont(self.custom_font_family, 18, QFont.Weight.Bold))
        main_layout.addWidget(search_header)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for a timezone...")
        self.search_bar.textChanged.connect(self.filter_timezones)
        main_layout.addWidget(self.search_bar)
        self.timezone_list = QListWidget()
        self.all_timezones = sorted(list(available_timezones()))
        self.timezone_list.addItems(self.all_timezones)
        self.timezone_list.itemDoubleClicked.connect(self.pin_timezone)
        main_layout.addWidget(self.timezone_list)
        self.update_pinned_clocks_display()
        self.world_clock_timer = QTimer(self)
        self.world_clock_timer.timeout.connect(self.update_world_clocks)
        self.world_clock_timer.start(1000)

    def init_alarm_ui(self):
        page = self.pages["Alarm"]
        main_layout = QHBoxLayout(page)
        left_panel = QVBoxLayout()
        left_panel.setContentsMargins(20, 20, 20, 20)
        left_panel.setSpacing(10)
        header = QLabel("Set New Alarm")
        header.setFont(QFont(self.custom_font_family, 18, QFont.Weight.Bold))
        self.alarm_time_edit = QTimeEdit(QTime.currentTime())
        self.alarm_time_edit.setFont(QFont(self.custom_font_family, 16))
        self.alarm_message_edit = QLineEdit()
        self.alarm_message_edit.setPlaceholderText("Alarm message (optional)")
        set_alarm_button = QPushButton("Set Alarm")
        set_alarm_button.clicked.connect(self.add_alarm)
        left_panel.addWidget(header)
        left_panel.addWidget(self.alarm_time_edit)
        left_panel.addWidget(self.alarm_message_edit)
        left_panel.addWidget(set_alarm_button)
        left_panel.addStretch()
        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(20, 20, 20, 20)
        active_header = QLabel("Active Alarms")
        active_header.setFont(QFont(self.custom_font_family, 18, QFont.Weight.Bold))
        self.active_alarms_list = QListWidget()
        right_panel.addWidget(active_header)
        right_panel.addWidget(self.active_alarms_list)
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)
        self.alarms = []
        self.alarm_check_timer = QTimer(self)
        self.alarm_check_timer.timeout.connect(self.check_alarms)
        self.alarm_check_timer.start(1000)

    def init_timer_ui(self):
        page = self.pages["Timer"]
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        self.timer_display = QLabel("00:10:00")
        self.timer_display.setFont(QFont(self.custom_font_family, 80, QFont.Weight.Bold))
        self.timer_display.setStyleSheet("color: #00d0d0;")
        self.timer_time_edit = QTimeEdit(QTime(0, 10, 0))
        self.timer_time_edit.setDisplayFormat("HH:mm:ss")
        self.timer_time_edit.setFont(QFont(self.custom_font_family, 16))
        self.timer_time_edit.timeChanged.connect(self.sync_timer_display)
        button_layout = QHBoxLayout()
        self.timer_start_button = QPushButton("Start")
        self.timer_pause_button = QPushButton("Pause")
        self.timer_reset_button = QPushButton("Reset")
        self.timer_pause_button.setEnabled(False)
        button_layout.addWidget(self.timer_start_button)
        button_layout.addWidget(self.timer_pause_button)
        button_layout.addWidget(self.timer_reset_button)
        layout.addWidget(self.timer_display)
        layout.addWidget(self.timer_time_edit)
        layout.addLayout(button_layout)
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.timer_total_seconds = 10 * 60
        self.is_timer_running = False
        self.timer_start_button.clicked.connect(self.start_timer)
        self.timer_pause_button.clicked.connect(self.pause_timer)
        self.timer_reset_button.clicked.connect(self.reset_timer)

    def init_stopwatch_ui(self):
        page = self.pages["Stopwatch"]
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)
        self.stopwatch_display = QLabel("00:00.000")
        self.stopwatch_display.setFont(QFont(self.custom_font_family, 80, QFont.Weight.Bold))
        self.stopwatch_display.setStyleSheet("color: #00d0d0;")
        button_layout = QHBoxLayout()
        self.stopwatch_start_button = QPushButton("Start")
        self.stopwatch_stop_button = QPushButton("Stop")
        self.stopwatch_reset_button = QPushButton("Reset")
        self.stopwatch_lap_button = QPushButton("Lap")
        self.stopwatch_stop_button.setEnabled(False)
        self.stopwatch_lap_button.setEnabled(False)
        button_layout.addWidget(self.stopwatch_start_button)
        button_layout.addWidget(self.stopwatch_stop_button)
        button_layout.addWidget(self.stopwatch_reset_button)
        button_layout.addWidget(self.stopwatch_lap_button)
        self.lap_list_widget = QListWidget()
        self.lap_list_widget.setMaximumHeight(200)
        layout.addWidget(self.stopwatch_display)
        layout.addLayout(button_layout)
        layout.addWidget(self.lap_list_widget)
        self.stopwatch_timer = QTimer(self)
        self.stopwatch_timer.setInterval(10)
        self.stopwatch_timer.timeout.connect(self.update_stopwatch)
        self.stopwatch_elapsed_ms = 0
        self.lap_count = 0
        self.stopwatch_start_button.clicked.connect(self.start_stopwatch)
        self.stopwatch_stop_button.clicked.connect(self.stop_stopwatch)
        self.stopwatch_reset_button.clicked.connect(self.reset_stopwatch)
        self.stopwatch_lap_button.clicked.connect(self.record_lap)

    # --- Logic & Update Functions ---
    def update_clock(self):
        now = datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%A, %B %d, %Y"))

    def play_sound(self):
        if self.alarm_sound:
            self.alarm_sound.play()

    def update_world_clocks(self):
        for i in range(self.pinned_clocks_layout.count()):
            widget = self.pinned_clocks_layout.itemAt(i).widget()
            tz_name = widget.property("timezone")
            time_label = widget.findChild(QLabel, "time_label")
            try:
                tz = ZoneInfo(tz_name)
                tz_time = datetime.now(tz)
                if time_label: time_label.setText(tz_time.strftime("%H:%M:%S"))
            except (ZoneInfoNotFoundError, AttributeError):
                pass

    def update_pinned_clocks_display(self):
        while self.pinned_clocks_layout.count():
            item = self.pinned_clocks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for tz_name in self.config["pinned_timezones"]:
            city = tz_name.split('/')[-1].replace('_', ' ')
            row_widget = QWidget()
            row_widget.setProperty("timezone", tz_name)
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0,0,0,0)
            city_label = QLabel(f"{city}:")
            city_label.setFont(QFont(self.custom_font_family, 16))
            time_label = QLabel("00:00:00")
            time_label.setObjectName("time_label")
            time_label.setFont(QFont(self.custom_font_family, 16, QFont.Weight.Bold))
            time_label.setStyleSheet("color: #00d0d0;")
            unpin_button = QPushButton("Unpin")
            # --- ADJUSTMENT: Button made larger ---
            unpin_button.setMinimumWidth(85)
            unpin_button.clicked.connect(lambda chk, tz=tz_name: self.unpin_timezone(tz))
            row.addWidget(city_label)
            row.addStretch()
            row.addWidget(time_label)
            row.addWidget(unpin_button)
            self.pinned_clocks_layout.addWidget(row_widget)
        self.update_world_clocks()
    
    def filter_timezones(self):
        filter_text = self.search_bar.text().lower()
        for i in range(self.timezone_list.count()):
            item = self.timezone_list.item(i)
            item.setHidden(filter_text not in item.text().lower())

    def pin_timezone(self, item):
        tz_name = item.text()
        if tz_name not in self.config["pinned_timezones"]:
            self.config["pinned_timezones"].append(tz_name)
            self.save_config()
            self.update_pinned_clocks_display()

    def unpin_timezone(self, tz_name):
        if tz_name in self.config["pinned_timezones"]:
            self.config["pinned_timezones"].remove(tz_name)
            self.save_config()
            self.update_pinned_clocks_display()

    def add_alarm(self):
        time = self.alarm_time_edit.time()
        message = self.alarm_message_edit.text() or "Alarm"
        alarm = {"time": time, "message": message, "active": True}
        self.alarms.append(alarm)
        self.active_alarms_list.addItem(f"{time.toString('HH:mm')} - {message}")

    def check_alarms(self):
        current_time = QTime.currentTime()
        for i, alarm in enumerate(self.alarms):
            if alarm["active"] and alarm["time"].hour() == current_time.hour() and alarm["time"].minute() == current_time.minute():
                alarm["active"] = False
                self.play_sound()
                self.show() # Show window on alarm
                self.activateWindow()
                QMessageBox.information(self, "Alarm", f"Alarm: {alarm['message']}")
                item = self.active_alarms_list.item(i)
                item.setText(f"{item.text()} (Triggered)")
                item.setForeground(Qt.GlobalColor.gray)

    def sync_timer_display(self, time):
        if not self.is_timer_running:
            self.timer_total_seconds = time.hour() * 3600 + time.minute() * 60 + time.second()
            self.timer_display.setText(time.toString("HH:mm:ss"))

    def start_timer(self):
        if self.timer_total_seconds > 0 and not self.is_timer_running:
            self.is_timer_running = True
            self.countdown_timer.start(1000)
            self.timer_start_button.setEnabled(False)
            self.timer_pause_button.setEnabled(True)
            self.timer_time_edit.setEnabled(False)

    def pause_timer(self):
        if self.is_timer_running:
            self.is_timer_running = False
            self.countdown_timer.stop()
            self.timer_start_button.setText("Resume")
            self.timer_start_button.setEnabled(True)
            self.timer_pause_button.setEnabled(False)

    def reset_timer(self):
        self.is_timer_running = False
        self.countdown_timer.stop()
        self.sync_timer_display(self.timer_time_edit.time())
        self.timer_start_button.setText("Start")
        self.timer_start_button.setEnabled(True)
        self.timer_pause_button.setEnabled(False)
        self.timer_time_edit.setEnabled(True)

    def update_countdown(self):
        if self.is_timer_running and self.timer_total_seconds > 0:
            self.timer_total_seconds -= 1
            time = QTime.fromMSecsSinceStartOfDay(self.timer_total_seconds * 1000)
            self.timer_display.setText(time.toString("HH:mm:ss"))
            if self.timer_total_seconds == 0:
                self.countdown_timer.stop()
                self.is_timer_running = False
                self.play_sound()
                self.show()
                self.activateWindow()
                QMessageBox.information(self, "Timer", "Time's up!")

    def start_stopwatch(self):
        self.stopwatch_timer.start()
        self.stopwatch_start_button.setEnabled(False)
        self.stopwatch_stop_button.setEnabled(True)
        self.stopwatch_lap_button.setEnabled(True)

    def stop_stopwatch(self):
        self.stopwatch_timer.stop()
        self.stopwatch_start_button.setEnabled(True)
        self.stopwatch_stop_button.setEnabled(False)
        self.stopwatch_lap_button.setEnabled(False)

    def reset_stopwatch(self):
        self.stop_stopwatch()
        self.stopwatch_elapsed_ms = 0
        self.lap_count = 0
        self.lap_list_widget.clear()
        self.update_stopwatch_display()

    def record_lap(self):
        self.lap_count += 1
        lap_time = self.stopwatch_display.text()
        self.lap_list_widget.insertItem(0, f"Lap {self.lap_count}: {lap_time}")

    def update_stopwatch(self):
        self.stopwatch_elapsed_ms += 10
        self.update_stopwatch_display()

    def update_stopwatch_display(self):
        minutes = self.stopwatch_elapsed_ms // 60000
        seconds = (self.stopwatch_elapsed_ms % 60000) // 1000
        milliseconds = self.stopwatch_elapsed_ms % 1000
        self.stopwatch_display.setText(f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}")
    
    # --- Styling ---
    def apply_stylesheet(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e; color: #f0f0f0; font-family: Monospace;
            }
            QListWidget {
                background-color: #2a2a2a; border: 1px solid #444; font-size: 14px; padding: 5px;
            }
            QListWidget::item { padding: 8px; }
            QListWidget::item:selected { background-color: #007acc; color: #ffffff; }
            QPushButton {
                background-color: #007acc; color: #ffffff; border: none;
                padding: 11px 16px; font-size: 15px; border-radius: 5px;
            }
            QPushButton:hover { background-color: #005f9e; }
            QPushButton:pressed { background-color: #004c7d; }
            QPushButton:disabled { background-color: #444; }
            QLineEdit, QTimeEdit {
                background-color: #2a2a2a; border: 1px solid #444; padding: 8px;
                border-radius: 4px; font-size: 14px;
            }
            QScrollBar:vertical {
                border: none; background: #2a2a2a; width: 10px; margin: 0;
            }
            QScrollBar::handle:vertical { background: #555; min-height: 20px; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QMenu { background-color: #2a2a2a; border: 1px solid #444; }
            QMenu::item:selected { background-color: #007acc; }
        """)

# --- Application Entry Point ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Prevents the app from quitting when the last window is closed
    app.setQuitOnLastWindowClosed(False) 
    
    clock = MidnightClock()
    clock.show()
    sys.exit(app.exec())
