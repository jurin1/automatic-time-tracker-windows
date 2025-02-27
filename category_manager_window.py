from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QListWidget, QInputDialog, QMessageBox, QHBoxLayout
from PyQt5.QtCore import Qt
import json
import logging

CONFIG_FILE = "config.ini"


class CategoryManagerWindow(QDialog):
    def __init__(self, parent, tracker):
        super().__init__(parent)
        self.setWindowTitle("Manage Categories")
        self.setGeometry(200, 200, 400, 400)
        self.setStyleSheet("background-color: #3b4252; color: #eceff4;")
        self.tracker = tracker
        self.categories = tracker.categories
        self.current_path = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()  # Hier wird layout definiert

        self.path_label = QLabel("Current Path: ")
        layout.addWidget(self.path_label)

        self.category_list = QListWidget()
        self.category_list.itemDoubleClicked.connect(self.load_subcategories)
        layout.addWidget(self.category_list)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_category)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_category)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_category)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.go_back)
        layout.addWidget(self.back_button)

        self.load_categories()
        self.setLayout(layout)  # Hier wird das Layout gesetzt

    def load_categories(self):
        self.category_list.clear()
        current = self.tracker.categories
        for part in self.current_path:
            current = current[part]
        for key in current.keys():
            self.category_list.addItem(key)
        self.update_path_label()

    def load_subcategories(self, item):
        self.current_path.append(item.text())
        self.load_categories()

    def go_back(self):
        if self.current_path:
            self.current_path.pop()
            self.load_categories()

    def add_category(self):
        name, ok = QInputDialog.getText(self, "Add Category", "Category Name:")
        if ok and name:
            current = self.tracker.categories
            for part in self.current_path:
                current = current[part]
            current[name] = {}
            with open(self.tracker.categories_path, "w") as f:
                json.dump(self.tracker.categories, f, indent=4)
            self.load_categories()

    def edit_category(self):
        selected_item = self.category_list.currentItem()
        if selected_item:
            current_name = selected_item.text()
            name, ok = QInputDialog.getText(
                self, "Edit Category", "Category Name:", text=current_name)
            if ok and name:
                current = self.tracker.categories
                for part in self.current_path:
                    current = current[part]
                value = current.pop(current_name)
                current[name] = value
                with open(self.tracker.categories_path, "w") as f:
                    json.dump(self.tracker.categories, f, indent=4)
                self.load_categories()

    def delete_category(self):
        selected_item = self.category_list.currentItem()
        if selected_item:
            current_name = selected_item.text()
            reply = QMessageBox.question(self, 'Delete Category',
                                         'Are you sure you want to delete this category?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                current = self.tracker.categories
                for part in self.current_path:
                    current = current[part]
                current.pop(current_name)
                with open(self.tracker.categories_path, "w") as f:
                    json.dump(self.tracker.categories, f, indent=4)
                self.load_categories()

    def update_path_label(self):
        path_text = "Current Path: " + "->".join(self.current_path)
        self.path_label.setText(path_text)
