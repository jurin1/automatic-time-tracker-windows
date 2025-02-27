import sqlite3
from datetime import datetime
import os


class ActivityLog:
    def __init__(self, db_path="activity.db"):
        self.db_path = db_path
        self._create_database()

    def _create_database(self):
        """
            Erstellt die SQLite Datenbank und die Tabellen.
            """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    window TEXT,
                    start TEXT,
                    end TEXT,
                    duration REAL,
                    type TEXT,
                    video INTEGER,
                    category_id INTEGER
                )
            """)
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level INTEGER,
                    name TEXT,
                    parent_id INTEGER,
                    FOREIGN KEY (parent_id) REFERENCES categories(id)
                )
            """)
        conn.commit()
        conn.close()

    def add_log(self, window, start, end, duration, type, video=False, category_id=None):
        """
        Fügt einen neuen Log in die SQLite Datenbank hinzu.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_log (window, start, end, duration, type, video, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (window, str(start), str(end), duration, type, int(video), category_id))
        conn.commit()
        conn.close()

    def get_logs(self):
        """
        Gibt alle Logs aus der SQLite Datenbank als Liste von Dictionaries zurück.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT window, start, end, duration, type, video, category_id FROM activity_log")
        rows = cursor.fetchall()
        conn.close()

        logs = []
        for row in rows:
            logs.append({
                'window': row[0],
                'start': datetime.fromisoformat(row[1]),
                'end': datetime.fromisoformat(row[2]) if row[2] and row[2] != 'None' else None,
                'duration': row[3],
                'type': row[4],
                'video': bool(row[5]),
                'category_id': row[6]
            })
        return logs

    def update_log_duration(self, window, duration):
        """
        Updated die Dauer eines Logs in der Datenbank.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE activity_log
            SET duration = ?
            WHERE window = ? AND end IS NULL
            """, (duration, window))
        conn.commit()
        conn.close()

    def delete_database(self):
        """
         Löscht die SQLite-Datenbankdatei.
         """
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            self._create_database()

    def add_category(self, level, name, parent_id=None):
        """
            Fügt eine neue Kategorie in die SQLite Datenbank hinzu.
            """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO categories (level, name, parent_id)
            VALUES (?, ?, ?)
        """, (level, name, parent_id))
        conn.commit()
        conn.close()

    def get_categories(self):
        """
            Gibt alle Kategorien aus der SQLite Datenbank als Liste von Dictionaries zurück.
            """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, level, name, parent_id FROM categories")
        rows = cursor.fetchall()
        conn.close()

        categories = []
        for row in rows:
            categories.append({
                'id': row[0],
                'level': row[1],
                'name': row[2],
                'parent_id': row[3]
            })
        return categories

    def update_category(self, category_id, name, parent_id=None):
        """
            Updated eine Kategorie in der Datenbank.
            """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE categories
            SET name = ?, parent_id = ?
            WHERE id = ?
            """, (name, parent_id, category_id))
        conn.commit()
        conn.close()

    def delete_category(self, category_id):
        """
            Löscht eine Kategorie aus der Datenbank.
            """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM categories
            WHERE id = ?
            """, (category_id,))
        conn.commit()
        conn.close()

    def set_log_category(self, log_id, category_id):
        """
            Setzt die Kategorie für einen Logeintrag.
            """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE activity_log
            SET category_id = ?
            WHERE id = ?
            """, (category_id, log_id))
        conn.commit()
        conn.close()

    def get_logs_without_category(self):
        """
            Gibt alle Logs ohne Kategorie aus der Datenbank zurück.
            """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, window, start, end, duration, type, video FROM activity_log WHERE category_id IS NULL"
        )
        rows = cursor.fetchall()
        conn.close()

        logs = []
        for row in rows:
            logs.append({
                'id': row[0],
                'window': row[1],
                'start': datetime.fromisoformat(row[2]),
                'end': datetime.fromisoformat(row[3]) if row[3] and row[3] != 'None' else None,
                'duration': row[4],
                'type': row[5],
                'video': bool(row[6])
            })
        return logs
