import logging
import sys
import psutil
import pandas as pd
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QHBoxLayout, QSpinBox, QCheckBox, QComboBox, QDialogButtonBox, QFormLayout
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import QTimer, Qt
import matplotlib.pyplot as plt
import win32gui
import win32process
from activity_log import ActivityLog
from activity_monitor import ActivityMonitor
from video_detection import get_active_window_name
from report_window import ReportWindow
from real_time_window import RealTimeWindow
import configparser
import os


CONFIG_FILE = "config.ini"


def create_config_file():
    """
        Erstellt die Konfigurationsdatei, wenn sie nicht existiert.
        """
    if not os.path.exists(CONFIG_FILE):
        config = configparser.ConfigParser()
        config["pause"] = {
            "detection_method": "inactivity",
            "inactivity_time": "10",
            "manual_start": "false",
            "manual_end": "false",
        }
        config["database"] = {
            "upload_interval": "60",
            "database_path": "activity.db",
        }
        config["startup"] = {
            "auto_start": "false",
        }
        config["notifications"] = {
            "pause_notification": "false",
        }
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)


class SettingsWindow(QDialog):
    def __init__(self, parent, config, tracker):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 400, 300)
        self.setStyleSheet("background-color: #3b4252; color: #eceff4;")
        self.config = config
        self.tracker = tracker

        self.initUI()

    def initUI(self):
        layout = QFormLayout()

        # Pause Settings
        self.pause_detection_method = QComboBox()
        self.pause_detection_method.addItems(["inactivity", "manual"])
        self.pause_detection_method.setCurrentText(
            self.config["pause"]["detection_method"])
        layout.addRow("Pause Detection Method:", self.pause_detection_method)

        self.pause_inactivity_time = QSpinBox()
        self.pause_inactivity_time.setMinimum(1)
        self.pause_inactivity_time.setValue(
            int(self.config["pause"]["inactivity_time"]))
        layout.addRow("Inactivity Time (seconds):", self.pause_inactivity_time)

        self.pause_manual_start = QCheckBox()
        self.pause_manual_start.setChecked(
            self.config["pause"].getboolean("manual_start"))
        layout.addRow("Manual Start:", self.pause_manual_start)

        self.pause_manual_end = QCheckBox()
        self.pause_manual_end.setChecked(
            self.config["pause"].getboolean("manual_end"))
        layout.addRow("Manual End:", self.pause_manual_end)

        # Database Settings
        self.database_upload_interval = QSpinBox()
        self.database_upload_interval.setMinimum(1)
        self.database_upload_interval.setValue(
            int(self.config["database"]["upload_interval"]))
        layout.addRow("Database Upload Interval (seconds):",
                      self.database_upload_interval)

        self.database_path = QFileDialog()
        self.database_path_button = QPushButton("Select Path")
        self.database_path_button.clicked.connect(self.open_file_dialog)
        self.database_path_label = QLabel(
            self.config["database"]["database_path"])
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.database_path_label)
        path_layout.addWidget(self.database_path_button)
        layout.addRow("Database Path:", path_layout)

        # Startup Settings
        self.startup_auto_start = QCheckBox()
        self.startup_auto_start.setChecked(
            self.config["startup"].getboolean("auto_start"))
        layout.addRow("Auto Start:", self.startup_auto_start)

        # Notification Settings
        self.notifications_pause_notification = QCheckBox()
        self.notifications_pause_notification.setChecked(
            self.config["notifications"].getboolean("pause_notification"))
        layout.addRow("Pause Notification:",
                      self.notifications_pause_notification)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

    def open_file_dialog(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Select Database File", "", "DB Files (*.db);;All Files (*)")
        if filepath:
            self.database_path_label.setText(filepath)

    def save_settings(self):
        self.config["pause"]["detection_method"] = self.pause_detection_method.currentText()
        self.config["pause"]["inactivity_time"] = str(
            self.pause_inactivity_time.value())
        self.config["pause"]["manual_start"] = str(
            self.pause_manual_start.isChecked()).lower()
        self.config["pause"]["manual_end"] = str(
            self.pause_manual_end.isChecked()).lower()
        self.config["database"]["upload_interval"] = str(
            self.database_upload_interval.value())
        self.config["database"]["database_path"] = self.database_path_label.text()
        self.config["startup"]["auto_start"] = str(
            self.startup_auto_start.isChecked()).lower()
        self.config["notifications"]["pause_notification"] = str(
            self.notifications_pause_notification.isChecked()).lower()

        self.tracker.update_config(self.config)
        self.accept()


class ActivityTracker(QMainWindow):
    def __init__(self):
        super().__init__()

        # Logging Konfiguration
        logging.basicConfig(filename='app.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Application started")

        self.setWindowTitle("Activity Tracker")
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet("background-color: #2e3440; color: #eceff4;")

        self.active_window = None
        self.start_time = None

        # Load Configuration
        create_config_file()  # Stelle sicher, dass die Datei existiert
        self.config = self.load_config()

        self.activity_log = ActivityLog(
            db_path=self.config["database"]["database_path"])

        self.last_active_window = None  # Added
        self.last_active_time = None  # Added
        self.transition_period = 1  # 1 second transition period
        self.current_logs = []
        self.pause_duration = int(self.config["pause"]["inactivity_time"])
        self.is_paused = False
        self.pause_start_time = None
        self.auto_start = self.config["startup"].getboolean("auto_start")
        self.pause_notification = self.config["notifications"].getboolean(
            "pause_notification")
        self.database_upload_interval = int(
            self.config["database"]["upload_interval"])

        self.activity_monitor = ActivityMonitor()
        self.mouse_listener, self.keyboard_listener = self.activity_monitor.start()

        self.initUI()
        self.track_time()
        self.start_database_update_timer()  # Timer zum DB updaten

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel("Activity Tracker Running...", self)
        self.label.setFont(QFont("Arial", 18, QFont.Bold))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("margin-bottom: 20px;")
        layout.addWidget(self.label)

        self.button_layout = QHBoxLayout()

        self.log_report_button = self.create_button(
            "Log & Report", "icons/report_icon.png", self.show_report_window)
        self.button_layout.addWidget(self.log_report_button)

        self.realtime_tracker_button = self.create_button(
            "Real-Time Tracker", "icons/tracker_icon.png", self.show_realtime_window)
        self.button_layout.addWidget(self.realtime_tracker_button)

        self.settings_button = self.create_button(
            "Settings", "icons/settings_icon.png", self.show_settings_window)
        self.button_layout.addWidget(self.settings_button)

        layout.addLayout(self.button_layout)

        self.delete_db_button = self.create_button(
            "Delete DB", "icons/download_icon.png", self.delete_database)
        layout.addWidget(self.delete_db_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def create_button(self, text, icon_path, callback):
        button = QPushButton(text, self)
        button.setFont(QFont("Arial", 12))
        button.setStyleSheet("""
            QPushButton {
                background-color: #5e81ac;
                color: #eceff4;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #81a1c1;
            }
        """)
        button.setIcon(QIcon(QPixmap(icon_path)))  # Add your icon path here
        button.clicked.connect(callback)
        return button

    def load_config(self):
        """
            Lädt die Konfiguration aus der Datei.
            """
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        return config

    def update_config(self, config):
        """
            Aktualisiert die Konfiguration und speichert sie in der Datei.
            """
        self.config = config
        with open(CONFIG_FILE, "w") as configfile:
            self.config.write(configfile)

        self.pause_duration = int(self.config["pause"]["inactivity_time"])
        self.auto_start = self.config["startup"].getboolean("auto_start")
        self.pause_notification = self.config["notifications"].getboolean(
            "pause_notification")
        self.database_upload_interval = int(
            self.config["database"]["upload_interval"])

        self.activity_log = ActivityLog(
            db_path=self.config["database"]["database_path"])

        self.start_database_update_timer()
        logging.info("Configuration updated.")

    def show_settings_window(self):
        try:
            settings_window = SettingsWindow(self, self.config, self)
            settings_window.exec_()
            logging.info("Settings window opened.")
        except Exception as e:
            logging.error(f"Error showing settings window: {e}")

    def delete_database(self):
        """
        Löscht die SQLite Datenbank und aktualisiert die Log Tabelle
         """
        try:
            self.activity_log.delete_database()
            self.current_logs = []
            self.update_activity_log_table()
            logging.info("Database deleted and UI updated")
        except Exception as e:
            logging.error(f"Error deleting database: {e}")

    def track_time(self):
        try:
            window_info = get_active_window_name()
            self.active_window = window_info
            self.start_time = datetime.now()
            if self.active_window != "Kein aktives Fenster":
                self.current_logs.append(
                    {'window': self.active_window, 'start': self.start_time, 'end': None, 'duration': 0, 'type': "activity"})
            logging.info(f"Started tracking window: {self.active_window}")

            self.update_timer = QTimer(self)
            self.update_timer.timeout.connect(self.update_time)
            self.update_timer.start(1000)
        except Exception as e:
            logging.error(f"Error during track_time: {e}")

    def update_time(self):
        try:
            if self.is_paused:
                if self.check_for_activity():
                    self.end_pause()
                    self.track_time()
            else:
                if self.check_for_pause():
                    self.start_pause()
                else:
                    window_info = get_active_window_name()
                    new_window = window_info

                    if new_window != self.active_window:
                        # Beende die aktuelle Activity aufgrund eines Fensterwechsels
                        self.end_activity(reason="window_change")
                        self.active_window = new_window
                        self.start_time = datetime.now()

                        # Startet nur ein task, wenn auch ein fenster aktiv ist
                        if self.active_window != "Kein aktives Fenster":
                            self.current_logs.append(
                                {'window': self.active_window, 'start': self.start_time, 'end': None, 'duration': 0, 'type': "activity"})
                        logging.info(
                            f"Window changed to: {self.active_window}")

                    if self.active_window != "Kein aktives Fenster" and self.start_time:
                        duration = (datetime.now() -
                                    self.start_time).total_seconds()
                        for log in self.current_logs:
                            if log['window'] == self.active_window and log['end'] is None:
                                log['duration'] = duration
                                self.activity_log.update_log_duration(
                                    log['window'], log['duration'])  # Hier wird die duration in der datenbank geupdatet
                                break
            self.update_activity_log_table()
        except Exception as e:
            logging.error(f"Error during update_time: {e}")

    def check_for_pause(self):
        last_activity_time = self.activity_monitor.get_last_activity_time()
        if (datetime.now() - last_activity_time).total_seconds() >= self.pause_duration:
            return True
        return False

    def start_pause(self):
        self.end_activity(reason="pause_start")
        self.is_paused = True
        self.pause_start_time = datetime.now()
        logging.info("Pause started.")
        self.current_logs.append(
            {'window': 'Pause', 'start': self.pause_start_time, 'end': None, 'duration': 0, 'type': "pause"})

    def check_for_activity(self):
        last_activity_time = self.activity_monitor.get_last_activity_time()
        if (datetime.now() - last_activity_time).total_seconds() < self.pause_duration:
            return True
        return False

    def end_pause(self):
        self.is_paused = False
        pause_end_time = datetime.now()
        current_pause_log = None
        for log in reversed(self.current_logs):
            if log['window'] == "Pause" and log['end'] is None:
                current_pause_log = log
                break
        if current_pause_log:
            current_pause_log['end'] = pause_end_time
            current_pause_log['duration'] = (
                pause_end_time - current_pause_log['start']).total_seconds()
        logging.info("Pause ended.")

    def start_database_update_timer(self):
        self.database_timer = QTimer(self)
        self.database_timer.timeout.connect(self.update_database)
        self.database_timer.start(
            self.database_upload_interval * 1000)  # Alle x Sekunden
        logging.info("Database update timer started.")

    def update_database(self):
        try:
            logs_to_add = []
            for log in self.current_logs:
                if log['end'] is None:
                    self.activity_log.update_log_duration(
                        log['window'], log['duration'])
                else:
                    logs_to_add.append(log)
            for log in logs_to_add:
                self.activity_log.add_log(
                    log['window'], log['start'], log['end'], log['duration'], log['type'])
                self.current_logs.remove(log)
            logging.info("Database updated.")
        except Exception as e:
            logging.error(f"Error during database update: {e}")

    def end_activity(self, reason=""):
        end_time = datetime.now()
        try:
            # Finde den Aktuellen Log
            current_log = None
            for log in reversed(self.current_logs):
                if log['window'] == self.active_window and log['end'] is None:
                    current_log = log
                    break

            if current_log:
                current_log['end'] = end_time
                current_log['duration'] = (
                    current_log['end'] - current_log['start']).total_seconds()

            if reason == "window_change" and current_log and current_log["window"] != "Kein aktives Fenster":
                self.last_active_window = current_log["window"]
                self.last_active_time = end_time
            self.active_window = None
            self.start_time = None
            logging.info(f"Activity ended. Reason: {reason}")

        except Exception as e:
            logging.error(f"Error during end_activity: {e}")

    def show_report_window(self):
        try:
            if not self.activity_log.get_logs():
                QMessageBox.warning(self, "Log & Report",
                                    "No activity to report.")
                return

            report_window = ReportWindow(self.activity_log.get_logs())
            report_window.exec_()
            logging.info("Report window opened.")
        except Exception as e:
            logging.error(f"Error showing report window: {e}")

    def show_realtime_window(self):
        try:
            self.realtime_window = RealTimeWindow(self)
            self.realtime_window.show()
            logging.info("Real-time window opened.")
        except Exception as e:
            logging.error(f"Error showing real-time window: {e}")

    def update_activity_log_table(self):
        try:
            if hasattr(self, 'realtime_window') and self.realtime_window.isVisible():
                self.realtime_window.update_table()
        except Exception as e:
            logging.error(f"Error updating real-time table: {e}")

    def closeEvent(self, event):
        try:
            self.mouse_listener.stop()
            self.keyboard_listener.stop()
            self.update_database()  # Speichern wenn das Fenster geschlossen wird
            logging.info("Application closed.")
            event.accept()
        except Exception as e:
            logging.error(f"Error during closing application: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    tracker = ActivityTracker()
    tracker.show()
    sys.exit(app.exec_())
