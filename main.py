import sys
import os
from datetime import datetime
from PyQt5.QtCore import QTimer, Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QMessageBox, QToolBar,
    QAction, QProgressDialog
)

# Core logic
from core.database import initialize_databases
from core.auth import AuthManager
from core.sync import SyncManager
from config import APP_NAME, DB_CONFIG

# Views
from modules.user_management.views import LoginWindow, UserManagementView
from modules.task_management.views import TaskManagementView
from modules.bug_management.views import BugManagementView
from modules.extra_activities.views import ExtraActivitiesView
from modules.reports.views import ReportsView
from modules.sync.views import SyncView
import traceback
import logging
from modules.time_tracking.views import TimeTrackingView
from modules.chat.views import ChatView
from modules.meetings.views import MeetingsView


# Optional: log to file
logging.basicConfig(filename='error.log', level=logging.ERROR)

def exception_hook(exctype, value, tb):
    # Print full traceback to console
    traceback_text = ''.join(traceback.format_exception(exctype, value, tb))
    print("Unhandled exception caught:\n", traceback_text)

    # Log to file
    logging.error("Unhandled exception:\n%s", traceback_text)

    # Show popup
    QMessageBox.critical(
        None,
        "Unhandled Exception",
        f"An unexpected error occurred:\n\n{value}\n\nSee error.log for details."
    )

    # Optionally: terminate the app after showing error
    sys.exit(1)


class SyncThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, sync_manager):
        super().__init__()
        self.sync_manager = sync_manager

    def run(self):
        try:
            self.sync_manager.sync_data()
            self.finished.emit(True, "Sync successful.")
        except Exception as e:
            self.finished.emit(False, str(e))


class ProjectDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(600, 200)

        self.db_connections = initialize_databases()
        self.auth_manager = AuthManager(self.db_connections)
        self.sync_manager = SyncManager(self.db_connections)

        self.setup_sync_timer()
        self.current_user_id = None

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.sync_view = SyncView(self.sync_manager)
        self.init_modules()

        self.show_login()

        self.sync_view.sync_requested.connect(self.sync_manager.sync_data)
        self.sync_view.config_updated.connect(self.sync_manager.configure)
        self.sync_manager.sync_complete.connect(self.on_sync_complete)

    def init_modules(self):
        self.login_window = LoginWindow(self.auth_manager, self)
        self.login_window.login_success.connect(self.on_login_success)

        self.user_management = UserManagementView(self.auth_manager, self.db_connections)
        self.task_management = TaskManagementView(self.db_connections)
        self.bug_management = BugManagementView(self.db_connections)
        self.extra_activities = ExtraActivitiesView(self.db_connections)
        self.reports = ReportsView(self.db_connections)

        self.stacked_widget.addWidget(self.login_window)
        self.stacked_widget.addWidget(self.user_management)
        self.stacked_widget.addWidget(self.task_management)
        self.stacked_widget.addWidget(self.bug_management)
        self.stacked_widget.addWidget(self.extra_activities)
        self.stacked_widget.addWidget(self.reports)
        self.stacked_widget.addWidget(self.sync_view)

    def show_login(self):
        self.stacked_widget.setCurrentIndex(0)

    def on_login_success(self, user_data):
        self.current_user = user_data
        if 'id' in user_data:
            self.current_user_id = user_data['id']
        if self.current_user:
            self.time_tracking_view = TimeTrackingView(self.db_connections,
                                                     self.current_user_id if self.current_user_id else 1)
            self.chat_view = ChatView(self.db_connections, self.current_user_id if self.current_user_id else 1)
            self.meetings_view = MeetingsView(self.db_connections, self.current_user_id if self.current_user_id else 1)
            self.stacked_widget.addWidget(self.time_tracking_view)  # Index 7
            self.stacked_widget.addWidget(self.chat_view)  # Index 8
            self.stacked_widget.addWidget(self.meetings_view)  # Index 9
            self.setup_navigation()

        self.resize(1200, 800)
        self.show_dashboard()

        role = user_data.get('role', 'user')
        self.user_management.set_user_role(role)
        self.task_management.set_user_role(role)
        self.bug_management.set_user_role(role)
        self.extra_activities.set_user_role(role)
        self.reports.set_user_role(role)

    def show_dashboard(self):
        index = 1 if self.current_user.get('role') == 'admin' else 2
        self.stacked_widget.setCurrentIndex(index)
        self.update_navigation(self.current_user.get('role', 'user'))

    def setup_navigation(self):
        self.nav_bar = QToolBar("Navigation")
        self.nav_bar.setIconSize(QSize(28, 28))
        self.addToolBar(Qt.LeftToolBarArea, self.nav_bar)

        def make_action(icon_path, label, index):
            action = QAction(QIcon(icon_path), label, self)
            action.triggered.connect(lambda _, i=index: self.stacked_widget.setCurrentIndex(i))
            return action

        self.user_action = make_action("ui/assets/user.svg", "Users", 1)
        self.task_action = make_action("ui/assets/task.svg", "Tasks", 2)
        self.bug_action = make_action("ui/assets/bug.svg", "Bugs", 3)
        self.activity_action = make_action("ui/assets/activity.svg", "Activities", 4)
        self.report_action = make_action("ui/assets/report.svg", "Reports", 5)
        self.sync_action = make_action("ui/assets/sync.svg", "Sync", 6)
        self.time_action = make_action("ui/assets/time.svg", "Time Tracking", 7)
        self.chat_action = make_action("ui/assets/chat.svg", "Chat", 8)
        self.meetings_action = make_action("ui/assets/meetings.svg", "Meetings", 9)

        # Add all actions to the toolbar
        actions = [
            self.user_action, self.task_action, self.bug_action,
            self.activity_action, self.report_action, self.sync_action,
            self.time_action, self.chat_action, self.meetings_action
        ]

        for action in actions:
            self.nav_bar.addAction(action)

    def update_navigation(self, role):
        self.user_action.setVisible(role == 'admin')
        self.task_action.setVisible(role in ['admin', 'manager', 'user'])
        self.bug_action.setVisible(role in ['admin', 'manager', 'user'])
        self.activity_action.setVisible(role in ['admin', 'manager', 'user'])
        self.report_action.setVisible(role in ['admin', 'manager', 'user'])
        self.sync_action.setVisible(role in ['admin', 'manager'])
        self.time_action.setVisible(role in ['admin', 'manager', 'user'])
        self.chat_action.setVisible(role in ['admin', 'manager', 'user'])
        self.meetings_action.setVisible(role in ['admin', 'manager', 'user'])

    def setup_sync_timer(self):
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.check_for_sync)
        self.sync_timer.start(300000)  # 5 minutes

    def check_for_sync(self):
        if self.sync_manager.should_sync():
            try:
                self.sync_manager.sync_data()
            except Exception as e:
                QMessageBox.warning(self, "Sync Error", f"Failed to sync data: {str(e)}")

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Exit Application",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            event.ignore()
            return

        if self.sync_manager.should_sync():
            self.progress_dialog = QProgressDialog("Syncing before exit...", "Cancel", 0, 0, self)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setCancelButton(None)
            self.progress_dialog.setWindowTitle("Please Wait")
            self.progress_dialog.show()

            event.ignore()  # Delay close
            self.sync_thread = SyncThread(self.sync_manager)
            self.sync_thread.finished.connect(lambda success, msg: self.finish_close(event, success, msg))
            self.sync_thread.start()
        else:
            self.finish_close(event)

    def finish_close(self, event, success=True, msg=""):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()

        if not success:
            QMessageBox.warning(self, "Sync Failed", f"Sync error before exit:\n{msg}")

        # Close database connections properly
        for name, conn in self.db_connections.items():
            if name == 'mongodb':
                # For MongoDB, close the client
                if hasattr(conn, 'client') and conn.client:
                    conn.client.close()
            elif hasattr(conn, 'close'):
                conn.close()

        event.accept()
        QApplication.quit()

    def on_sync_complete(self, success, message):
        last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.sync_view.update_status(last_sync, success, message)

        logs = list(self.db_connections['mongodb'].sync_logs.find().sort("timestamp", -1).limit(50))
        self.sync_view.update_logs(logs)


if __name__ == "__main__":
    sys.excepthook = exception_hook
    app = QApplication(sys.argv)

    # Apply stylesheet
    try:
        with open("ui/styles/main.css", "r") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Stylesheet load failed: {e}")

    window = ProjectDashboard()
    window.show()
    sys.exit(app.exec_())