import sys
from PyQt5.QtWidgets import QApplication
from activity_tracker import ActivityTracker

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tracker = ActivityTracker()
    tracker.show()
    sys.exit(app.exec_())
