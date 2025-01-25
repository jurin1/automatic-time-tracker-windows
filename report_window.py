from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt
import pandas as pd
import matplotlib.pyplot as plt


class ReportWindow(QDialog):
    def __init__(self, activity_log):
        super().__init__()
        self.setWindowTitle("Activity Log & Report")
        self.setGeometry(150, 150, 800, 600)
        self.setStyleSheet("background-color: #3b4252; color: #eceff4;")
        self.activity_log = activity_log

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.table = QTableWidget(self)
        self.table.setRowCount(len(self.activity_log))
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

        for row, log in enumerate(self.activity_log):
            self.table.setItem(row, 0, QTableWidgetItem(log['window']))
            self.table.setItem(row, 1, QTableWidgetItem(str(log['start'])))
            self.table.setItem(row, 2, QTableWidgetItem(str(log['end'])))
            self.table.setItem(row, 3, QTableWidgetItem(str(log['duration'])))

        layout.addWidget(self.table)

        self.download_log_button = self.create_button(
            "Download Log", "icons/download_icon.png", self.download_log)
        layout.addWidget(self.download_log_button)

        self.download_report_button = self.create_button(
            "Download Report", "icons/download_report_icon.png", self.download_report)
        layout.addWidget(self.download_report_button)

        self.setLayout(layout)

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

    def download_log(self):
        options = QFileDialog.Options()
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Log", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if filepath:
            df = pd.DataFrame(self.activity_log)
            summary = df.groupby('window')['duration'].sum().reset_index()
            summary.sort_values(by='duration', ascending=False, inplace=True)
            with open(filepath, 'w') as file:
                file.write("Detailed Logs\n")
                df.to_csv(file, index=False)
                file.write("\nFinal Time Usage Summary\n")
                summary.to_csv(file, index=False)
            QMessageBox.information(
                self, "Save Log", f"Log saved to {filepath}")

    def download_report(self):
        if not self.activity_log:
            QMessageBox.warning(self, "Generate Report",
                                "No activity to report.")
            return

        df = pd.DataFrame(self.activity_log)
        summary = df.groupby('window')['duration'].sum().reset_index()
        summary.sort_values(by='duration', ascending=False, inplace=True)

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
