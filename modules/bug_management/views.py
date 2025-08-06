from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTabWidget,
    QFormLayout, QComboBox, QTextEdit
)
from PyQt5.QtCore import Qt
import datetime


class BugManagementView(QWidget):
    def __init__(self, db_connections, parent=None):
        super().__init__(parent)
        self.db = db_connections
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        # Create tab widget
        self.tabs = QTabWidget()

        # Bug list tab
        self.bug_list_tab = QWidget()
        self.init_bug_list_tab()
        self.tabs.addTab(self.bug_list_tab, "Bug List")

        # Report bug tab
        self.report_bug_tab = QWidget()
        self.init_report_bug_tab()
        self.tabs.addTab(self.report_bug_tab, "Report Bug")

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        # Load initial data
        self.load_projects()
        self.load_bugs()

    def init_bug_list_tab(self):
        layout = QVBoxLayout()

        # Filter controls
        filter_layout = QHBoxLayout()

        self.project_filter = QComboBox()
        self.project_filter.addItem("All Projects", None)
        self.project_filter.currentIndexChanged.connect(self.load_bugs)
        filter_layout.addWidget(QLabel("Filter by Project:"))
        filter_layout.addWidget(self.project_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses", None)
        self.status_filter.addItems(["Open", "In Progress", "Resolved", "Closed", "Rejected"])
        self.status_filter.currentIndexChanged.connect(self.load_bugs)
        filter_layout.addWidget(QLabel("Filter by Status:"))
        filter_layout.addWidget(self.status_filter)

        self.severity_filter = QComboBox()
        self.severity_filter.addItem("All Severities", None)
        self.severity_filter.addItems(["Low", "Medium", "High", "Critical"])
        self.severity_filter.currentIndexChanged.connect(self.load_bugs)
        filter_layout.addWidget(QLabel("Filter by Severity:"))
        filter_layout.addWidget(self.severity_filter)

        layout.addLayout(filter_layout)

        # Bugs table
        self.bugs_table = QTableWidget()
        self.bugs_table.setColumnCount(6)
        self.bugs_table.setHorizontalHeaderLabels([
            "ID", "Project", "Title", "Severity", "Status", "Reported On"
        ])
        self.bugs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bugs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.bugs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.bugs_table.doubleClicked.connect(self.view_bug_details)

        layout.addWidget(self.bugs_table)
        self.bug_list_tab.setLayout(layout)

    def set_user_role(self, role):
        """Enable/disable features based on user role"""
        self.current_role = role

        # For UserManagementView, just control what user management features are available
        # if role != 'admin':
        #     # Remove "Add User" tab for non-admins
        #     while self.tabs.count() > 1:
        #         self.tabs.removeTab(1)

    def init_report_bug_tab(self):
        layout = QFormLayout()

        self.bug_project = QComboBox()
        layout.addRow("Project:", self.bug_project)

        self.bug_title = QLineEdit()
        self.bug_title.setPlaceholderText("Enter bug title")
        layout.addRow("Title:", self.bug_title)

        self.bug_description = QTextEdit()
        self.bug_description.setPlaceholderText("Describe the bug in detail")
        layout.addRow("Description:", self.bug_description)

        self.bug_severity = QComboBox()
        self.bug_severity.addItems(["Low", "Medium", "High", "Critical"])
        layout.addRow("Severity:", self.bug_severity)

        report_bug_btn = QPushButton("Report Bug")
        report_bug_btn.clicked.connect(self.report_bug)
        layout.addRow(report_bug_btn)

        self.report_bug_tab.setLayout(layout)

    def load_projects(self):
        """Load projects into combo boxes"""
        cursor = self.db['sqlite'].cursor()
        cursor.execute('SELECT id, name FROM projects ORDER BY name')
        projects = cursor.fetchall()

        self.project_filter.clear()
        self.project_filter.addItem("All Projects", None)

        self.bug_project.clear()

        for project_id, project_name in projects:
            self.project_filter.addItem(project_name, project_id)
            self.bug_project.addItem(project_name, project_id)

    def load_bugs(self):
        """Load bugs based on current filters"""
        project_id = self.project_filter.currentData()
        status = self.status_filter.currentText() if self.status_filter.currentIndex() > 0 else None
        severity = self.severity_filter.currentText() if self.severity_filter.currentIndex() > 0 else None

        query = '''
                SELECT b.id, p.name, b.title, b.severity, b.status, b.created_at
                FROM bugs b
                         LEFT JOIN projects p ON b.project_id = p.id
                WHERE 1 = 1 \
                '''

        params = []

        if project_id:
            query += ' AND b.project_id = ?'
            params.append(project_id)

        if status:
            query += ' AND b.status = ?'
            params.append(status)

        if severity:
            query += ' AND b.severity = ?'
            params.append(severity)

        query += ' ORDER BY b.severity DESC, b.created_at DESC'

        cursor = self.db['sqlite'].cursor()
        cursor.execute(query, params)
        bugs = cursor.fetchall()

        self.bugs_table.setRowCount(len(bugs))
        for row_idx, bug in enumerate(bugs):
            for col_idx, value in enumerate(bug):
                item = QTableWidgetItem(str(value) if value else "")
                self.bugs_table.setItem(row_idx, col_idx, item)

    def report_bug(self):
        """Report a new bug"""
        project_id = self.bug_project.currentData()
        title = self.bug_title.text()
        description = self.bug_description.toPlainText()
        severity = self.bug_severity.currentText()

        if not all([project_id, title, description]):
            QMessageBox.warning(self, "Error", "Project, Title and Description are required")
            return

        try:
            cursor = self.db['sqlite'].cursor()
            cursor.execute('''
                           INSERT INTO bugs (project_id, title, description, severity, status)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (
                               project_id, title, description, severity, "Open"
                           ))
            self.db['sqlite'].commit()

            # Also insert into MongoDB
            self.db['mongodb'].bugs.insert_one({
                'project_id': project_id,
                'title': title,
                'description': description,
                'severity': severity,
                'status': "Open",
                'created_at': datetime.datetime.now().isoformat()
            })

            QMessageBox.information(self, "Success", "Bug reported successfully")
            self.load_bugs()
            self.clear_bug_form()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to report bug: {str(e)}")

    def view_bug_details(self, index):
        """View details of a selected bug"""
        bug_id = self.bugs_table.item(index.row(), 0).text()

        cursor = self.db['sqlite'].cursor()
        cursor.execute('''
                       SELECT b.*, p.name as project_name
                       FROM bugs b
                                LEFT JOIN projects p ON b.project_id = p.id
                       WHERE b.id = ?
                       ''', (bug_id,))

        bug = cursor.fetchone()

        if bug:
            columns = [desc[0] for desc in cursor.description]
            bug_dict = dict(zip(columns, bug))

            details = f"""
            <h2>{bug_dict['title']}</h2>
            <p><b>Project:</b> {bug_dict['project_name']}</p>
            <p><b>Status:</b> {bug_dict['status']}</p>
            <p><b>Severity:</b> {bug_dict['severity']}</p>
            <p><b>Reported On:</b> {bug_dict['created_at']}</p>
            <hr>
            <h3>Description:</h3>
            <p>{bug_dict['description']}</p>
            """

            msg = QMessageBox()
            msg.setWindowTitle("Bug Details")
            msg.setTextFormat(Qt.RichText)
            msg.setText(details)

            # Add buttons for status changes if needed
            if bug_dict['status'] == "Open":
                msg.addButton("Start Work", QMessageBox.AcceptRole)
                msg.addButton("Reject", QMessageBox.RejectRole)

            msg.exec_()

    def clear_bug_form(self):
        """Clear the report bug form"""
        self.bug_title.clear()
        self.bug_description.clear()
        self.bug_severity.setCurrentIndex(1)  # Medium