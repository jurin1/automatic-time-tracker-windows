import sys
import psutil
import pandas as pd
from datetime import datetime
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
        self.setWindowTitle("Activity Tracker")
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet("background-color: #2e3440; color: #eceff4;")

        self.active_window = None
        self.start_time = None
        self.activity_log = ActivityLog()
        self.inactivity_threshold = 10  # 30 Sekunden für Debugging

        self.last_active_window = None  # Added
        self.last_active_time = None  # Added
        self.transition_period = 1  # 1 second transition period
        self.current_logs = []

        self.activity_monitor = ActivityMonitor()
        self.mouse_listener, self.keyboard_listener = self.activity_monitor.start()

        self.initUI()
        self.track_time()
        self.start_inactivity_timer()  # Inactivity Timer starten
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

        self.break_reminder_label = QLabel("", self)
        self.break_reminder_label.setAlignment(Qt.AlignCenter)
        self.break_reminder_label.setFont(QFont("Arial", 12))
        self.break_reminder_label.setStyleSheet("margin-top: 20px;")
        layout.addWidget(self.break_reminder_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.break_timer = QTimer(self)
        self.break_timer.timeout.connect(self.remind_break)
        self.break_timer.start(3600000)  # Remind every hour

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
        self.activity_log.delete_database()
        self.current_logs = []
        self.update_activity_log_table()

    def track_time(self):
        window_info = get_active_window_name()
        self.active_window = window_info
        self.start_time = datetime.now()
        if self.active_window != "Kein aktives Fenster":
            self.current_logs.append(
                {'window': self.active_window, 'start': self.start_time, 'end': None, 'duration': 0, 'type': "activity"})

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_time)
        self.update_timer.start(1000)


    def update_time(self):
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

        if self.active_window != "Kein aktives Fenster" and self.start_time:
                duration = (datetime.now() - self.start_time).total_seconds()
                for log in self.current_logs:
                    if log['window'] == self.active_window and log['end'] is None:
                        log['duration'] = duration
                        self.activity_log.update_log_duration(log['window'], log['duration'])  # Hier wird die duration in der datenbank geupdatet
                        break

        self.update_activity_log_table()


    def start_inactivity_timer(self):
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self.check_inactivity)
        self.inactivity_timer.start(5000)  # Check alle 5 Sekunden

    def is_video_active(self):
        """
        Erkennt, ob ein Video im aktiven Fenster/Tab abgespielt wird.
        (Platzhalter - wird später implementiert)
        """
        return False


    def check_inactivity(self):
        if self.is_video_active():
                # Wenn ein Video läuft, Inaktivität ignorieren
                self.activity_monitor.last_activity = datetime.now()
                return

        time_since_last_activity = (
                datetime.now() - self.activity_monitor.last_activity).total_seconds()
        if time_since_last_activity > self.inactivity_threshold:
                if self.active_window != "Pause" and self.active_window != None:  # Nur wenn keine Pause aktiv ist
                    self.end_activity(reason="inactivity") # Beende die aktuelle Activity aufgrund von Inaktivität
                elif self.active_window == "Pause":
                    self.activity_monitor.last_activity = datetime.now()

    def start_database_update_timer(self):
        self.database_timer = QTimer(self)
        self.database_timer.timeout.connect(self.update_database)
        self.database_timer.start(60000)  # Alle 60 Sekunden


    def update_database(self):
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

    def end_activity(self, reason=""):
        end_time = datetime.now()

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

        if reason == "inactivity":
            # Neuen "Pause"-Log erstellen
            pause_start_time = self.activity_monitor.last_activity
            self.current_logs.append(
                {"window": "Pause", 'start': pause_start_time, 'end': None, 'duration': 0, 'type': "pause"})
            self.active_window = "Pause"
            self.start_time = pause_start_time
        else:
            if reason == "window_change" and current_log and current_log["window"] != "Kein aktives Fenster":
                self.last_active_window = current_log["window"]
                self.last_active_time = end_time
            self.active_window = None
            self.start_time = None

    def start_pause_tracking(self):
        self.pause_timer = QTimer(self)
        self.pause_timer.timeout.connect(self.track_pause)
        self.pause_timer.start(5000)  # Alle 5 Sekunden

    def track_pause(self):
        if self.active_window != "Pause":
            self.pause_timer.stop()  # Stop wenn neue Aktivität
            return

        window_info = get_active_window_name()
        if window_info != "Kein aktives Fenster" and window_info != "Pause":
            self.end_activity(reason="window_change")  # Beendet die Pause
            self.active_window = window_info
            self.start_time = datetime.now()
            self.current_logs.append(
                {'window': self.active_window, 'start': self.start_time, 'end': None, 'duration': 0, 'type': "activity"})
        else:
           if self.active_window == "Pause" and self.start_time:
               duration = (datetime.now() - self.start_time).total_seconds()
               for log in self.current_logs:
                   if log['window'] == self.active_window and log['end'] is None:
                       log['duration'] = duration
                       # Hier wird die duration in der datenbank geupdatet
                       self.activity_log.update_log_duration(
                           log['window'], log['duration'])
                       break

    def show_report_window(self):
        if not self.activity_log.get_logs():
            QMessageBox.warning(self, "Log & Report", "No activity to report.")
            return

        report_window = ReportWindow(self.activity_log.get_logs())
        report_window.exec_()

    def show_realtime_window(self):
        self.realtime_window = RealTimeWindow(self)
        self.realtime_window.show()

    def remind_break(self):
        self.break_reminder_label.setText("Time to take a break!")
        QTimer.singleShot(10000, lambda: self.break_reminder_label.setText(""))

    def update_activity_log_table(self):
        if hasattr(self, 'realtime_window') and self.realtime_window.isVisible():
            self.realtime_window.update_table()

    def closeEvent(self, event):
        self.mouse_listener.stop()
        self.keyboard_listener.stop()
        self.update_database()  # Speichern wenn das Fenster geschlossen wird
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    tracker = ActivityTracker()
    tracker.show()
    sys.exit(app.exec_())
