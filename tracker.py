import logging
import sys
import psutil
import pandas as pd
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QHBoxLayout
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
        self.activity_log = ActivityLog()

        self.last_active_window = None  # Added
        self.last_active_time = None  # Added
        self.transition_period = 1  # 1 second transition period
        self.current_logs = []
        self.pause_duration = 10  # 10 seconds for debug
        self.is_paused = False
        self.pause_start_time = None

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
        self.database_timer.start(10000)  # Alle 60 Sekunden
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
