import sqlite3
from datetime import datetime
import os


class ActivityLog:
    def __init__(self, db_path="activity.db"):
        self.db_path = db_path
        self._create_database()

    def _create_database(self):
        """
            Erstellt die SQLite Datenbank und die Tabelle.
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
                    video INTEGER
                )
            """)
        conn.commit()
        conn.close()

    def add_log(self, window, start, end, duration, type, video=False):
        """
        Fügt einen neuen Log in die SQLite Datenbank hinzu.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_log (window, start, end, duration, type, video)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (window, str(start), str(end), duration, type, int(video)))
        conn.commit()
        conn.close()

    def get_logs(self):
        """
        Gibt alle Logs aus der SQLite Datenbank als Liste von Dictionaries zurück.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT window, start, end, duration, type, video FROM activity_log")
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
                'video': bool(row[5])
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
