from PyQt5.QtWidgets import QDialog, QFormLayout, QComboBox, QSpinBox, QCheckBox, QPushButton, QLabel, QFileDialog, QHBoxLayout, QDialogButtonBox, QTreeWidget, QTreeWidgetItem, QDateTimeEdit, QAbstractItemView, QInputDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from datetime import datetime
import configparser
import logging
from category_manager_window import CategoryManagerWindow

CONFIG_FILE = "config.ini"


class SettingsWindow(QDialog):
    def __init__(self, parent, config, tracker):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 600, 500)
        self.setStyleSheet("background-color: #3b4252; color: #eceff4;")
        self.config = config
        self.tracker = tracker
        self.activity_log = tracker.activity_log

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

        # Manage Categories Button
        self.manage_categories_button = QPushButton("Manage Categories")
        self.manage_categories_button.clicked.connect(
            self.show_category_manager)
        layout.addRow(self.manage_categories_button)
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

    def show_category_manager(self):
        try:
            self.category_manager_window = CategoryManagerWindow(
                self, self.tracker)
            self.category_manager_window.exec_()
            logging.info("Category manager window opened.")
        except Exception as e:
            logging.error(f"Error showing category manager window: {e}")

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
        if self.categorization_start_time.dateTime().toString("yyyy-MM-dd HH:mm:ss") != "":
            self.config["categorization"]["start_time"] = self.categorization_start_time.dateTime(
            ).toString("yyyy-MM-dd HH:mm:ss")
        else:
            self.config["categorization"]["start_time"] = None
        self.config["categorization"]["update_option"] = self.categorization_update_option.currentText()

        self.tracker.update_config(self.config)
        self.accept()
