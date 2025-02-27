from PyQt5.QtWidgets import QDialog, QVBoxLayout, QComboBox, QMenu, QAction, QDialogButtonBox, QLabel, QTableWidget, QHeaderView, QTableWidgetItem, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt
from hierarchical_combobox import HierarchicalComboBox
import logging


class AssignCategoryWindow(QDialog):
    def __init__(self, parent, tracker):
        super().__init__(parent)
        self.setWindowTitle("Assign Categories")
        self.setGeometry(200, 200, 800, 600)
        self.setStyleSheet("background-color: #3b4252; color: #eceff4;")
        self.tracker = tracker
        self.activity_log = tracker.activity_log
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(
            ["All", "Without Category", "Level 1", "Level 2", "Level 3"])
        self.filter_combo.currentIndexChanged.connect(self.load_activities)
        layout.addWidget(self.filter_combo)

        self.activities_table = QTableWidget()
        self.activities_table.setColumnCount(5)
        self.activities_table.setHorizontalHeaderLabels(
            ["ID", "Application/Website", "Start", "End", "Duration"])
        self.activities_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.activities_table.itemDoubleClicked.connect(self.assign_category)
        layout.addWidget(self.activities_table)

        self.load_activities()
        self.setLayout(layout)

    def load_activities(self):
        try:
            self.activities_table.clearContents()
            self.activities_table.setRowCount(0)

            filter_text = self.filter_combo.currentText()
            if filter_text == "Without Category":
                logs = self.activity_log.get_logs_without_category()
            else:
                logs = self.activity_log.get_logs()

            unique_logs = {}
            for log in logs:
                if log['window'] not in unique_logs:
                    unique_logs[log['window']] = log

            row_count = 0
            for log in unique_logs.values():
                if filter_text == "Level 1" or filter_text == "Level 2" or filter_text == "Level 3":
                    level = int(filter_text.split(" ")[1])
                    if log.get('category_id'):
                        category = self.get_category_by_id(log['category_id'])
                        if category and category['level'] != level:
                            continue
                    else:
                        if filter_text != "Without Category":
                            continue

                self.activities_table.insertRow(row_count)
                self.activities_table.setItem(
                    row_count, 0, QTableWidgetItem(str(log.get('id'))))
                self.activities_table.setItem(
                    row_count, 1, QTableWidgetItem(log.get('window')))
                self.activities_table.setItem(
                    row_count, 2, QTableWidgetItem(str(log.get('start'))))
                self.activities_table.setItem(row_count, 3, QTableWidgetItem(
                    str(log.get('end')) if log.get('end') else ""))
                self.activities_table.setItem(
                    row_count, 4, QTableWidgetItem(str(log.get('duration'))))
                row_count += 1
        except Exception as e:
            logging.error(
                f"Error in AssignCategoryWindow.load_activities: {e}")

    def assign_category(self, item):
        if item.column() != 0:
            return

        log_id = int(self.activities_table.item(item.row(), 0).text())

        dialog = QDialog(self)
        dialog.setWindowTitle("Assign Category")
        dialog_layout = QVBoxLayout()

        category_label = QLabel("Select Category:", dialog)
        dialog_layout.addWidget(category_label)

        category_tree = QTreeWidget(dialog)
        category_tree.setHeaderHidden(True)
        category_tree.setColumnCount(1)
        categories = self.activity_log.get_categories()
        self.load_categories_to_tree(category_tree, categories)
        dialog_layout.addWidget(category_tree)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addWidget(button_box)

        dialog.setLayout(dialog_layout)

        selected_category_id = None
        if dialog.exec_() == QDialog.Accepted:
            selected_item = category_tree.currentItem()
            if selected_item:
                selected_category_id = selected_item.data(0, Qt.UserRole)

            if selected_category_id is not None:
                self.activity_log.set_log_category(
                    log_id, selected_category_id)
            else:
                self.activity_log.set_log_category(log_id, None)
        self.load_activities()

    def load_categories_to_tree(self, tree, categories, parent_item=None):
        for key, value in categories.items():
            item = QTreeWidgetItem([key])
            if parent_item:
                parent_item.addChild(item)
            else:
                tree.addTopLevelItem(item)
            if isinstance(value, dict):
                self.load_categories_to_tree(tree, value, item)

    def get_category_path(self, item, path=""):
        if item.parent():
            return self.get_category_path(item.parent(), item.parent().text(0) + "->" + path)
        return path + item.text(0)

    def get_category_id_by_path(self, path):
        categories = self.activity_log.get_categories()
        for category in categories:
            category_path = self.get_category_path_from_category(category)
            if category_path == path:
                return category['id']
        return None

    def get_category_path_from_category(self, category, path=""):
        if category['parent_id'] is not None:
            for cat in self.activity_log.get_categories():
                if cat['id'] == category['parent_id']:
                    return self.get_category_path_from_category(cat, cat['name'] + "->" + path)
        return path + category['name']
