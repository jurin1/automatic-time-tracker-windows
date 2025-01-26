import argparse
import configparser
import os
import sys

CONFIG_FILE = "config.ini"


def create_config_file():
    """
        Erstellt die Konfigurationsdatei, wenn sie nicht existiert.
        """
    if not os.path.exists(CONFIG_FILE):
        config = configparser.ConfigParser()
        config["pause"] = {
            "detection_method": "inactivity",
            "inactivity_time": "10",
            "manual_start": "false",
            "manual_end": "false",
        }
        config["database"] = {
            "upload_interval": "60",
            "database_path": "activity.db",
        }
        config["startup"] = {
            "auto_start": "false",
        }
        config["notifications"] = {
            "pause_notification": "false",
        }
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)


def load_config():
    """
        Lädt die Konfiguration aus der Datei.
        """
    create_config_file()
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config


def save_config(config):
    """
        Speichert die Konfiguration in die Datei.
        """
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)


def configure_pause(args):
    """
        Konfiguriert die Pauseneinstellungen.
        """
    config = load_config()
    if args.detection_method:
        config["pause"]["detection_method"] = args.detection_method
    if args.inactivity_time:
        config["pause"]["inactivity_time"] = str(args.inactivity_time)
    if args.manual_start is not None:
        config["pause"]["manual_start"] = str(args.manual_start).lower()
    if args.manual_end is not None:
        config["pause"]["manual_end"] = str(args.manual_end).lower()
    save_config(config)
    print("Pauseneinstellungen aktualisiert.")


def configure_database(args):
    """
    Konfiguriert die Datenbankeinstellungen.
    """
    config = load_config()
    if args.upload_interval:
        config["database"]["upload_interval"] = str(args.upload_interval)
    if args.database_path:
        config["database"]["database_path"] = args.database_path
    save_config(config)
    print("Datenbankeinstellungen aktualisiert.")


def configure_startup(args):
    """
        Konfiguriert die Starteinstellungen.
        """
    config = load_config()
    if args.auto_start is not None:
        config["startup"]["auto_start"] = str(args.auto_start).lower()
    save_config(config)
    print("Starteinstellungen aktualisiert.")


def configure_notifications(args):
    """
        Konfiguriert die Benachrichtigungseinstellungen.
        """
    config = load_config()
    if args.pause_notification is not None:
        config["notifications"]["pause_notification"] = str(
            args.pause_notification).lower()
    save_config(config)
    print("Benachrichtigungseinstellungen aktualisiert.")


def main():
    parser = argparse.ArgumentParser(
        description="Konfiguriere den Activity Tracker."
    )
    subparsers = parser.add_subparsers(
        title="Konfigurationsbereiche", dest="command"
    )

    # Pause Subcommand
    pause_parser = subparsers.add_parser("pause", help="Pauseneinstellungen")
    pause_parser.add_argument(
        "--detection-method",
        type=str,
        choices=["inactivity", "manual"],
        help="Wie soll eine Pause erfasst werden?",
    )
    pause_parser.add_argument(
        "--inactivity-time", type=int, help="Ab wann soll eine Pause bei Inaktivität aktiviert werden (in Sekunden)."
    )
    pause_parser.add_argument(
        "--manual-start", type=bool, help="Option zum manuellen Starten einer Pause."
    )
    pause_parser.add_argument(
        "--manual-end", type=bool, help="Option zum manuellen Beenden einer Pause."
    )
    pause_parser.set_defaults(func=configure_pause)

    # Database Subcommand
    database_parser = subparsers.add_parser(
        "database", help="Datenbankeinstellungen")
    database_parser.add_argument(
        "--upload-interval", type=int, help="Wann soll der Upload in die Datenbank stattfinden (in Sekunden)."
    )
    database_parser.add_argument(
        "--database-path", type=str, help="Pfad zur Datenbankdatei."
    )
    database_parser.set_defaults(func=configure_database)

    # Startup Subcommand
    startup_parser = subparsers.add_parser(
        "startup", help="Starteinstellungen")
    startup_parser.add_argument(
        "--auto-start", type=bool, help="Soll das Programm beim Start des PCs automatisch im Hintergrund starten? (true/false)."
    )
    startup_parser.set_defaults(func=configure_startup)

    # Notifications Subcommand
    notifications_parser = subparsers.add_parser(
        "notifications", help="Benachrichtigungseinstellungen"
    )
    notifications_parser.add_argument(
        "--pause-notification", type=bool, help="Soll eine Benachrichtigung erstellt werden, wenn eine Pause aktiv ist? (true/false)."
    )
    notifications_parser.set_defaults(func=configure_notifications)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
