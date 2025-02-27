import logging
import time
import configparser
from datetime import datetime
from activity_log import ActivityLog

CONFIG_FILE = "config.ini"
LOG_FILE = "categorize_activities.log"

# Logging Konfiguration
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def load_config():
    """
        Lädt die Konfiguration aus der Datei.
        """
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config


def categorize_activities():
    """
        Kategorisiert die Aktivitäten in der Datenbank.
        """
    try:
        logging.info("Starting activity categorization process.")
        config = load_config()
        activity_log = ActivityLog(
            db_path=config["database"]["database_path"])
        categories = activity_log.get_categories()
        logs_without_category = activity_log.get_logs_without_category()
        categorization_start_time = config.get(
            "categorization", "start_time", fallback=None)

        if categorization_start_time:
            categorization_start_time = datetime.fromisoformat(
                categorization_start_time)

        for log in logs_without_category:
            log_start_time = log['start']
            if categorization_start_time and log_start_time < categorization_start_time:
                continue

            category_id = None
            window = log['window']

            # Hier wird die Logik für die Kategorisierung hinzugefügt
            # Beispiel: Wenn der Fenstertitel "Visual Studio Code" enthält, dann setze Kategorie "Arbeit"
            if "Visual Studio Code" in window:
                for category in categories:
                    if category['level'] == 1 and category['name'] == 'Arbeit':
                        category_id = category['id']
                        break
            elif "Google Chrome" in window:
                for category in categories:
                    if category['level'] == 1 and category['name'] == 'Privat':
                        category_id = category['id']
                        break

            if category_id:
                activity_log.set_log_category(log['id'], category_id)
                logging.info(
                    f"Categorized log with id {log['id']} to category {category_id}")
            else:
                logging.info(
                    f"No category found for log with id {log['id']}")
        logging.info("Activity categorization process finished.")
    except Exception as e:
        logging.error(f"Error during activity categorization: {e}")


def main():
    while True:
        categorize_activities()
        time.sleep(60)  # Alle 60 Sekunden


if __name__ == "__main__":
    main()
