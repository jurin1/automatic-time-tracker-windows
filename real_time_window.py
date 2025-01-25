from PyQt5.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QFileDialog, QMessageBox
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import QTimer
import pandas as pd
import matplotlib.pyplot as plt


class RealTimeWindow(QMainWindow):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Real-Time Activity Tracker")
        self.setGeometry(150, 150, 800, 600)
        self.setStyleSheet("background-color: #3b4252; color: #eceff4;")
        self.main_window = main_window

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.table = QTableWidget(self)
        self.table.setRowCount(0)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Application/Website", "Start", "End", "Duration (seconds)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #4c566a;
                color: #eceff4;
                border: 1px solid #5e81ac;
            }
            QHeaderView::section {
                background-color: #5e81ac;
                border: 1px solid #4c566a;
            }
        """)

        layout.addWidget(self.table)

        button_layout = QHBoxLayout()

        self.download_log_button = QPushButton("Download Log", self)
        self.download_log_button.setFont(QFont("Arial", 12))
        self.download_log_button.setStyleSheet("""
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
        self.download_log_button.setIcon(
            QIcon(QPixmap("icons/download_icon.png")))  # Add your icon path here
        self.download_log_button.clicked.connect(self.download_log)
        button_layout.addWidget(self.download_log_button)

        self.download_report_button = QPushButton("Download Report", self)
        self.download_report_button.setFont(QFont("Arial", 12))
        self.download_report_button.setStyleSheet("""
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
        self.download_report_button.setIcon(
            QIcon(QPixmap("icons/download_report_icon.png")))  # Add your icon path here
        self.download_report_button.clicked.connect(self.download_report)
        button_layout.addWidget(self.download_report_button)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_table)
        self.update_timer.start(1000)

    def update_table(self):
        activity_log = self.main_window.current_logs
        df = pd.DataFrame(activity_log)

        # Die Daten werden nun so angezeigt, dass nur die aktuellste Aktivität angezeigt wird, und darunter alle Pausen

        # Aktuell laufender Task
        current_tasks = df[df['end'].isnull()]

        # Abgeschlossene Tasks
        completed_tasks = df[df['end'].notnull()]

        # Erstelle Tabelle
        self.table.setRowCount(len(current_tasks) + len(completed_tasks))

        row_counter = 0

        for index, log in completed_tasks.iterrows():
            self.table.setItem(row_counter, 0, QTableWidgetItem(log['window']))
            self.table.setItem(
                row_counter, 1, QTableWidgetItem(str(log['start'])))
            self.table.setItem(
                row_counter, 2, QTableWidgetItem(str(log['end'])))
            self.table.setItem(
                row_counter, 3, QTableWidgetItem(str(log['duration'])))
            row_counter += 1

        for index, log in current_tasks.iterrows():
            self.table.setItem(row_counter, 0, QTableWidgetItem(log['window']))
            self.table.setItem(
                row_counter, 1, QTableWidgetItem(str(log['start'])))
            self.table.setItem(row_counter, 2, QTableWidgetItem(
                str(log['end']) if log['end'] else None))
            self.table.setItem(
                row_counter, 3, QTableWidgetItem(str(log['duration'])))
            row_counter += 1

    def download_log(self):
        options = QFileDialog.Options()
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Log", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if filepath:
            df = pd.DataFrame(self.main_window.activity_log.get_logs())

            # Aggregating time usage by application/website
            summary = df.groupby('window')['duration'].sum().reset_index()
            summary.sort_values(by='duration', ascending=False, inplace=True)

            # Save detailed log and summary to CSV
            with open(filepath, 'w') as file:
                file.write("Detailed Logs\n")
                df.to_csv(file, index=False)
                file.write("\nFinal Time Usage Summary\n")
                summary.to_csv(file, index=False)

            QMessageBox.information(
                self, "Save Log", f"Log saved to {filepath}")

    def download_report(self):
        if not self.main_window.activity_log.get_logs():
            QMessageBox.warning(self, "Generate Report",
                                "No activity to report.")
            return

        df = pd.DataFrame(self.main_window.activity_log.get_logs())

        # Aggregate time usage by application/website
        summary = df.groupby('window')['duration'].sum().reset_index()
        summary.sort_values(by='duration', ascending=False, inplace=True)

        # Plotting
        plt.figure(figsize=(10, 5))
        plt.bar(summary['window'], summary['duration'])
        plt.xlabel('Applications/Websites')
        plt.ylabel('Time Spent (seconds)')
        plt.title('Time Usage Report')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        options = QFileDialog.Options()
        report_filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "", "PNG Files (*.png);;All Files (*)", options=options)
        if report_filepath:
            plt.savefig(report_filepath)
            plt.close()
            QMessageBox.information(
                self, "Generate Report", f"Report saved to {report_filepath}")
