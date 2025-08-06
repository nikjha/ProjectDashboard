from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout,
    QGroupBox, QCheckBox, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
import datetime

class SyncView(QWidget):
    sync_requested = pyqtSignal()
    config_updated = pyqtSignal(dict)

    def __init__(self, sync_manager, parent=None):
        super().__init__(parent)
        self.sync_manager = sync_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Configuration Group
        config_group = QGroupBox("Sync Configuration")
        config_layout = QFormLayout()

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("localhost")
        config_layout.addRow("MySQL Host:", self.host_input)

        self.db_input = QLineEdit()
        self.db_input.setPlaceholderText("project_dashboard")
        config_layout.addRow("Database Name:", self.db_input)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("dashboard_user")
        config_layout.addRow("Username:", self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        config_layout.addRow("Password:", self.pass_input)

        self.auto_sync_check = QCheckBox("Enable Auto Sync")
        config_layout.addRow(self.auto_sync_check)

        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_config)
        config_layout.addRow(save_btn)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Sync Control Group
        control_group = QGroupBox("Sync Control")
        control_layout = QVBoxLayout()

        self.sync_btn = QPushButton("Sync Now")
        self.sync_btn.clicked.connect(self.sync_requested.emit)
        control_layout.addWidget(self.sync_btn)

        self.status_label = QLabel("Last sync: Never")
        control_layout.addWidget(self.status_label)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # Sync Logs Table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(4)
        self.logs_table.setHorizontalHeaderLabels(["Timestamp", "Status", "Tables", "Message"])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.logs_table)

        self.setLayout(layout)

    def save_config(self):
        config = {
            'mysql_host': self.host_input.text(),
            'mysql_database': self.db_input.text(),
            'mysql_user': self.user_input.text(),
            'mysql_password': self.pass_input.text(),
            'auto_sync': self.auto_sync_check.isChecked()
        }
        self.config_updated.emit(config)

    def update_status(self, last_sync, success, message):
        status = "Success" if success else "Failed"
        self.status_label.setText(f"Last sync: {last_sync} ({status}) - {message}")

    def update_logs(self, logs):
        self.logs_table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            self.logs_table.setItem(row, 0, QTableWidgetItem(str(log['timestamp'])))
            self.logs_table.setItem(row, 1, QTableWidgetItem("Success" if log['success'] else "Failed"))
            self.logs_table.setItem(row, 2, QTableWidgetItem(", ".join(log['tables_synced'])))
            self.logs_table.setItem(row, 3, QTableWidgetItem(log.get('message', '')))