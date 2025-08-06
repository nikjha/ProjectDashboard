from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTabWidget,
    QFormLayout, QComboBox, QTextEdit
)
from PyQt5.QtCore import Qt
import datetime


class ExtraActivitiesView(QWidget):
    def __init__(self, db_connections, parent=None):
        super().__init__(parent)
        self.db = db_connections

        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        # Create tab widget
        self.tabs = QTabWidget()

        # Activities list tab
        self.activities_list_tab = QWidget()
        self.init_activities_list_tab()
        self.tabs.addTab(self.activities_list_tab, "Activities List")

        # Request activity tab
        self.request_activity_tab = QWidget()
        self.init_request_activity_tab()
        self.tabs.addTab(self.request_activity_tab, "Request Activity")

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        # Load initial data
        self.load_activities()

    def init_activities_list_tab(self):
        layout = QVBoxLayout()

        # Filter controls
        filter_layout = QHBoxLayout()

        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types", None)
        self.type_filter.addItems(["Script", "Automation", "Research", "Other"])
        self.type_filter.currentIndexChanged.connect(self.load_activities)
        filter_layout.addWidget(QLabel("Filter by Type:"))
        filter_layout.addWidget(self.type_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses", None)
        self.status_filter.addItems(["Pending", "Approved", "In Progress", "Completed", "Rejected"])
        self.status_filter.currentIndexChanged.connect(self.load_activities)
        filter_layout.addWidget(QLabel("Filter by Status:"))
        filter_layout.addWidget(self.status_filter)

        layout.addLayout(filter_layout)

        # Activities table
        self.activities_table = QTableWidget()
        self.activities_table.setColumnCount(5)
        self.activities_table.setHorizontalHeaderLabels([
            "ID", "Title", "Type", "Status", "Requested On"
        ])
        self.activities_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.activities_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.activities_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.activities_table.doubleClicked.connect(self.view_activity_details)

        layout.addWidget(self.activities_table)
        self.activities_list_tab.setLayout(layout)

    def set_user_role(self, role):
        """Enable/disable features based on user role"""
        self.current_role = role

        # # For UserManagementView, just control what user management features are available
        # if role != 'admin':
        #     # Remove "Add User" tab for non-admins
        #     while self.tabs.count() > 1:
        #         self.tabs.removeTab(1)

    def init_request_activity_tab(self):
        layout = QFormLayout()

        self.activity_title = QLineEdit()
        self.activity_title.setPlaceholderText("Enter activity title")
        layout.addRow("Title:", self.activity_title)

        self.activity_type = QComboBox()
        self.activity_type.addItems(["Script", "Automation", "Research", "Other"])
        layout.addRow("Type:", self.activity_type)

        self.activity_description = QTextEdit()
        self.activity_description.setPlaceholderText("Describe the activity in detail")
        layout.addRow("Description:", self.activity_description)

        request_activity_btn = QPushButton("Request Activity")
        request_activity_btn.clicked.connect(self.request_activity)
        layout.addRow(request_activity_btn)

        self.request_activity_tab.setLayout(layout)

    def load_activities(self):
        """Load activities based on current filters"""
        activity_type = self.type_filter.currentText() if self.type_filter.currentIndex() > 0 else None
        status = self.status_filter.currentText() if self.status_filter.currentIndex() > 0 else None

        query = '''
                SELECT id, title, type, status, created_at
                FROM extra_activities
                WHERE 1 = 1 \
                '''

        params = []

        if activity_type:
            query += ' AND type = ?'
            params.append(activity_type)

        if status:
            query += ' AND status = ?'
            params.append(status)

        query += ' ORDER BY created_at DESC'

        cursor = self.db['sqlite'].cursor()
        cursor.execute(query, params)
        activities = cursor.fetchall()

        self.activities_table.setRowCount(len(activities))
        for row_idx, activity in enumerate(activities):
            for col_idx, value in enumerate(activity):
                item = QTableWidgetItem(str(value) if value else "")
                self.activities_table.setItem(row_idx, col_idx, item)

    def request_activity(self):
        """Request a new activity"""
        title = self.activity_title.text()
        activity_type = self.activity_type.currentText()
        description = self.activity_description.toPlainText()

        if not all([title, description]):
            QMessageBox.warning(self, "Error", "Title and Description are required")
            return

        try:
            cursor = self.db['sqlite'].cursor()
            cursor.execute('''
                           INSERT INTO extra_activities (title, type, description, status)
                           VALUES (?, ?, ?, ?)
                           ''', (
                               title, activity_type, description, "Pending"
                           ))
            self.db['sqlite'].commit()

            # Also insert into MongoDB
            self.db['mongodb'].extra_activities.insert_one({
                'title': title,
                'type': activity_type,
                'description': description,
                'status': "Pending",
                'created_at': datetime.datetime.now().isoformat()
            })

            QMessageBox.information(self, "Success", "Activity requested successfully")
            self.load_activities()
            self.clear_activity_form()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to request activity: {str(e)}")

    def view_activity_details(self, index):
        """View details of a selected activity"""
        activity_id = self.activities_table.item(index.row(), 0).text()

        cursor = self.db['sqlite'].cursor()
        cursor.execute('''
                       SELECT *
                       FROM extra_activities
                       WHERE id = ?
                       ''', (activity_id,))

        activity = cursor.fetchone()

        if activity:
            columns = [desc[0] for desc in cursor.description]
            activity_dict = dict(zip(columns, activity))

            details = f"""
            <h2>{activity_dict['title']}</h2>
            <p><b>Type:</b> {activity_dict['type']}</p>
            <p><b>Status:</b> {activity_dict['status']}</p>
            <p><b>Requested On:</b> {activity_dict['created_at']}</p>
            <hr>
            <h3>Description:</h3>
            <p>{activity_dict['description']}</p>
            """

            msg = QMessageBox()
            msg.setWindowTitle("Activity Details")
            msg.setTextFormat(Qt.RichText)
            msg.setText(details)

            # Add buttons for status changes if needed
            if activity_dict['status'] == "Pending":
                msg.addButton("Approve", QMessageBox.AcceptRole)
                msg.addButton("Reject", QMessageBox.RejectRole)

            msg.exec_()

    def clear_activity_form(self):
        """Clear the request activity form"""
        self.activity_title.clear()
        self.activity_type.setCurrentIndex(0)
        self.activity_description.clear()