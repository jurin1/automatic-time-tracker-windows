from PyQt5.QtWidgets import QComboBox, QMenu, QAction


class HierarchicalComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.menu = QMenu(self)
        self.setMenu(self.menu)
        self.categories = []
        self.selected_category_id = None

    def set_categories(self, categories):
        self.categories = categories
        self.menu.clear()
        self.build_menu(None, self.menu)

    def build_menu(self, parent_id, menu):
        for category in self.categories:
            if category['parent_id'] == parent_id:
                action = QAction(category['name'], self)
                action.setData(category['id'])
                if any(cat['parent_id'] == category['id'] for cat in self.categories):
                    submenu = QMenu(category['name'], self)
                    self.build_menu(category['id'], submenu)
                    action.setMenu(submenu)
                else:
                    action.triggered.connect(
                        lambda checked, cat_id=category['id']: self.select_category(cat_id))
                menu.addAction(action)

    def select_category(self, category_id):
        self.selected_category_id = category_id
        for category in self.categories:
            if category['id'] == category_id:
                self.setCurrentText(self.get_category_path(category))
                break

    def get_category_path(self, category, path=""):
        if category['parent_id'] is not None:
            for cat in self.categories:
                if cat['id'] == category['parent_id']:
                    return self.get_category_path(cat, cat['name'] + " > " + path)
        return path + category['name']

    def get_selected_category_id(self):
        return self.selected_category_id
