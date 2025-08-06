from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDateTimeEdit, QFormLayout, QMessageBox, QGroupBox, QTextEdit
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QIcon
import datetime

class TimeTrackingView(QWidget):
    def __init__(self, db_connections, user_id, parent=None):
        super().__init__(parent)
        self.db = db_connections
        self.user_id = user_id
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()

        # Time Entry Form
        form_group = QGroupBox("Log Time")
        form_layout = QFormLayout()

        self.project_combo = QComboBox()
        self.task_combo = QComboBox()
        self.start_time = QDateTimeEdit()
        self.end_time = QDateTimeEdit()
        self.description = QTextEdit()

        self.start_time.setDateTime(QDateTime.currentDateTime())
        self.end_time.setDateTime(QDateTime.currentDateTime())

        form_layout.addRow("Project:", self.project_combo)
        form_layout.addRow("Task:", self.task_combo)
        form_layout.addRow("Start Time:", self.start_time)
        form_layout.addRow("End Time:", self.end_time)
        form_layout.addRow("Description:", self.description)

        submit_btn = QPushButton("Submit Time Entry")
        submit_btn.clicked.connect(self.submit_time_entry)
        form_layout.addRow(submit_btn)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Time Entries Table
        self.time_entries_table = QTableWidget()
        self.time_entries_table.setColumnCount(6)
        self.time_entries_table.setHorizontalHeaderLabels([
            "ID", "Project", "Task", "Start", "End", "Duration"
        ])
        self.time_entries_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.time_entries_table)

        self.setLayout(layout)

    def load_data(self):
        # Load projects
        cursor = self.db['sqlite'].cursor()
        cursor.execute("SELECT id, name FROM projects")
        projects = cursor.fetchall()
        self.project_combo.clear()
        for project_id, project_name in projects:
            self.project_combo.addItem(project_name, project_id)

        # Load time entries
        cursor.execute('''
            SELECT te.id, p.name, t.title, te.start_time, te.end_time 
            FROM time_entries te
            JOIN projects p ON te.project_id = p.id
            LEFT JOIN tasks t ON te.task_id = t.id
            WHERE te.user_id = ?
            ORDER BY te.start_time DESC
        ''', (self.user_id,))
        entries = cursor.fetchall()

        self.time_entries_table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            duration = (entry[4] - entry[3]).total_seconds() / 3600
            for col, value in enumerate(entry[:5]):
                self.time_entries_table.setItem(row, col, QTableWidgetItem(str(value)))
            self.time_entries_table.setItem(row, 5, QTableWidgetItem(f"{duration:.2f} hours"))

    # def submit_time_entry(self):
    #     project_id = self.project_combo.currentData()
    #     task_id = self.task_combo.currentData() if self.task_combo.currentData() else None
    #     start_time = self.start_time.dateTime().toString(Qt.ISODate)
    #     end_time = self.end_time.dateTime().toString(Qt.ISODate)
    #     description = self.description.toPlainText()
    #
    #     cursor = self.db['sqlite'].cursor()
    #     cursor.execute('''
    #         INSERT INTO time_entries
    #         (user_id, project_id, task_id, start_time, end_time, description)
    #         VALUES (?, ?, ?, ?, ?, ?)
    #     ''', (self.user_id, project_id, task_id, start_time, end_time, description))
    #     self.db['sqlite'].commit()
    #
    #     # Also insert into MongoDB
    #     self.db['mongodb'].time_entries.insert_one({
    #         'user_id': self.user_id,
    #         'project_id': project_id,
    #         'task_id': task_id,
    #         'start_time': start_time,
    #         'end_time': end_time,
    #         'description': description,
    #         'created_at': datetime.datetime.now().isoformat()
    #     })
    #
    #     QMessageBox.information(self, "Success", "Time entry submitted successfully")
    #     self.load_data()
    #

    def submit_time_entry(self):
        project_id = self.project_combo.currentData()
        task_id = self.task_combo.currentData() if self.task_combo.currentData() else None
        start_time = self.start_time.dateTime().toString(Qt.ISODate)
        end_time = self.end_time.dateTime().toString(Qt.ISODate)
        description = self.description.toPlainText()

        # SQLite Insert
        cursor = self.db['sqlite'].cursor()
        cursor.execute('''
            INSERT INTO time_entries 
            (user_id, project_id, task_id, start_time, end_time, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.user_id, project_id, task_id, start_time, end_time, description))
        time_entry_id = cursor.lastrowid
        self.db['sqlite'].commit()

        # MongoDB Insert (with additional flexible fields)
        mongo_entry = {
            'time_entry_id': time_entry_id,
            'user_id': self.user_id,
            'project_id': project_id,
            'task_id': task_id,
            'start_time': start_time,
            'end_time': end_time,
            'description': description,
            'calculated_duration': (QDateTime.fromString(end_time, Qt.ISODate).toSecsSinceEpoch() -
                                  QDateTime.fromString(start_time, Qt.ISODate).toSecsSinceEpoch()) / 3600,
            'tags': [],  # MongoDB can handle array fields easily
            'attachments': [],  # Can store references to files
            'created_at': datetime.datetime.now().isoformat(),
            'updated_at': datetime.datetime.now().isoformat()
        }
        self.db['mongodb'].time_entries.insert_one(mongo_entry)

        QMessageBox.information(self, "Success", "Time entry submitted successfully")
        self.load_data()