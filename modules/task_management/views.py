from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTabWidget,
    QFormLayout, QComboBox, QDateEdit, QTextEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon
import datetime


class TaskManagementView(QWidget):
    def __init__(self, db_connections, parent=None):
        super().__init__(parent)
        self.db = db_connections
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        # Create tab widget
        self.tabs = QTabWidget()

        # Task list tab
        self.task_list_tab = QWidget()
        self.init_task_list_tab()
        self.tabs.addTab(self.task_list_tab, "Task List")

        # Add task tab
        self.add_task_tab = QWidget()
        self.init_add_task_tab()
        self.tabs.addTab(self.add_task_tab, "Add Task")

        # Correction form tab
        self.correction_tab = QWidget()
        self.init_correction_tab()
        self.tabs.addTab(self.correction_tab, "Corrections")

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        # Load initial data
        self.load_projects()
        self.load_tasks()

    def init_task_list_tab(self):
        layout = QVBoxLayout()

        # Filter controls
        filter_layout = QHBoxLayout()

        self.project_filter = QComboBox()
        self.project_filter.addItem("All Projects", None)
        self.project_filter.currentIndexChanged.connect(self.load_tasks)
        filter_layout.addWidget(QLabel("Filter by Project:"))
        filter_layout.addWidget(self.project_filter)

        self.status_filter = QComboBox()
        self.status_filter.addItem("All Statuses", None)
        self.status_filter.addItems(["Pending", "In Progress", "Completed", "Blocked"])
        self.status_filter.currentIndexChanged.connect(self.load_tasks)
        filter_layout.addWidget(QLabel("Filter by Status:"))
        filter_layout.addWidget(self.status_filter)

        layout.addLayout(filter_layout)

        # Tasks table
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(7)
        self.tasks_table.setHorizontalHeaderLabels([
            "ID", "Project", "Title", "Status", "Priority", "Due Date", "Assigned To"
        ])
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tasks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tasks_table.doubleClicked.connect(self.view_task_details)

        layout.addWidget(self.tasks_table)
        self.task_list_tab.setLayout(layout)

    def init_add_task_tab(self):
        layout = QFormLayout()

        self.task_project = QComboBox()
        layout.addRow("Project:", self.task_project)

        self.task_title = QLineEdit()
        self.task_title.setPlaceholderText("Enter task title")
        layout.addRow("Title:", self.task_title)

        self.task_description = QTextEdit()
        self.task_description.setPlaceholderText("Enter task description")
        layout.addRow("Description:", self.task_description)

        self.task_status = QComboBox()
        self.task_status.addItems(["Pending", "In Progress", "Completed", "Blocked"])
        layout.addRow("Status:", self.task_status)

        self.task_priority = QComboBox()
        self.task_priority.addItems(["Low", "Medium", "High", "Critical"])
        layout.addRow("Priority:", self.task_priority)

        self.task_due_date = QDateEdit()
        self.task_due_date.setDate(QDate.currentDate().addDays(7))
        self.task_due_date.setCalendarPopup(True)
        layout.addRow("Due Date:", self.task_due_date)

        self.task_assigned_to = QComboBox()
        self.load_users_to_combo(self.task_assigned_to)
        layout.addRow("Assigned To:", self.task_assigned_to)

        add_task_btn = QPushButton("Add Task")
        add_task_btn.clicked.connect(self.add_task)
        layout.addRow(add_task_btn)

        self.add_task_tab.setLayout(layout)

    def set_user_role(self, role):
        """Enable/disable features based on user role"""
        self.current_role = role

        # # For UserManagementView, just control what user management features are available
        # if role != 'admin':
        #     # Remove "Add User" tab for non-admins
        #     while self.tabs.count() > 1:
        #         self.tabs.removeTab(1)

    def init_correction_tab(self):
        layout = QFormLayout()

        self.correction_project = QComboBox()
        self.correction_project.currentIndexChanged.connect(self.load_project_tasks)
        layout.addRow("Project:", self.correction_project)

        self.correction_task = QComboBox()
        layout.addRow("Task:", self.correction_task)

        self.correction_description = QTextEdit()
        self.correction_description.setPlaceholderText("Describe the correction needed")
        layout.addRow("Correction Description:", self.correction_description)

        submit_correction_btn = QPushButton("Submit Correction")
        submit_correction_btn.clicked.connect(self.submit_correction)
        layout.addRow(submit_correction_btn)

        self.correction_tab.setLayout(layout)

    def load_projects(self):
        """Load projects into combo boxes"""
        cursor = self.db['sqlite'].cursor()
        cursor.execute('SELECT id, name FROM projects ORDER BY name')
        projects = cursor.fetchall()

        self.project_filter.clear()
        self.project_filter.addItem("All Projects", None)

        self.task_project.clear()
        self.correction_project.clear()

        for project_id, project_name in projects:
            self.project_filter.addItem(project_name, project_id)
            self.task_project.addItem(project_name, project_id)
            self.correction_project.addItem(project_name, project_id)

    def load_users_to_combo(self, combo):
        """Load users into a combo box"""
        cursor = self.db['sqlite'].cursor()
        cursor.execute('SELECT id, username FROM users ORDER BY username')
        users = cursor.fetchall()

        combo.clear()
        combo.addItem("Unassigned", None)

        for user_id, username in users:
            combo.addItem(username, user_id)

    def load_tasks(self):
        """Load tasks based on current filters"""
        project_id = self.project_filter.currentData()
        status = self.status_filter.currentText() if self.status_filter.currentIndex() > 0 else None

        query = '''
                SELECT t.id, p.name, t.title, t.status, t.priority, t.due_date, u.username
                FROM tasks t
                         LEFT JOIN projects p ON t.project_id = p.id
                         LEFT JOIN users u ON t.assigned_to = u.id
                WHERE 1 = 1 \
                '''

        params = []

        if project_id:
            query += ' AND t.project_id = ?'
            params.append(project_id)

        if status:
            query += ' AND t.status = ?'
            params.append(status)

        query += ' ORDER BY t.due_date, t.priority DESC'

        cursor = self.db['sqlite'].cursor()
        cursor.execute(query, params)
        tasks = cursor.fetchall()

        self.tasks_table.setRowCount(len(tasks))
        for row_idx, task in enumerate(tasks):
            for col_idx, value in enumerate(task):
                item = QTableWidgetItem(str(value) if value else "")
                self.tasks_table.setItem(row_idx, col_idx, item)

    def load_project_tasks(self):
        """Load tasks for a specific project (for corrections)"""
        project_id = self.correction_project.currentData()

        if not project_id:
            self.correction_task.clear()
            return

        cursor = self.db['sqlite'].cursor()
        cursor.execute('''
                       SELECT id, title
                       FROM tasks
                       WHERE project_id = ?
                       ORDER BY title
                       ''', (project_id,))

        tasks = cursor.fetchall()

        self.correction_task.clear()
        for task_id, task_title in tasks:
            self.correction_task.addItem(task_title, task_id)

    def add_task(self):
        """Add a new task to the database"""
        project_id = self.task_project.currentData()
        title = self.task_title.text()
        description = self.task_description.toPlainText()
        status = self.task_status.currentText()
        priority = self.task_priority.currentText()
        due_date = self.task_due_date.date().toString("yyyy-MM-dd")
        assigned_to = self.task_assigned_to.currentData()

        if not all([project_id, title]):
            QMessageBox.warning(self, "Error", "Project and Title are required")
            return

        try:
            cursor = self.db['sqlite'].cursor()
            cursor.execute('''
                           INSERT INTO tasks (project_id, title, description, status, priority,
                                              due_date, assigned_to)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
                           ''', (
                               project_id, title, description, status, priority,
                               due_date, assigned_to
                           ))
            self.db['sqlite'].commit()

            # Also insert into MongoDB
            self.db['mongodb'].tasks.insert_one({
                'project_id': project_id,
                'title': title,
                'description': description,
                'status': status,
                'priority': priority,
                'due_date': due_date,
                'assigned_to': assigned_to,
                'created_at': datetime.datetime.now().isoformat()
            })

            QMessageBox.information(self, "Success", "Task added successfully")
            self.load_tasks()
            self.clear_task_form()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add task: {str(e)}")

    def submit_correction(self):
        """Submit a correction for a task"""
        task_id = self.correction_task.currentData()
        description = self.correction_description.toPlainText()

        if not all([task_id, description]):
            QMessageBox.warning(self, "Error", "Task and Description are required")
            return

        try:
            # In a real app, you'd have a corrections table
            # For now we'll just update the task description
            cursor = self.db['sqlite'].cursor()
            cursor.execute('''
                           UPDATE tasks
                           SET description = description || '\n\nCORRECTION: ' || ?
                           WHERE id = ?
                           ''', (description, task_id))
            self.db['sqlite'].commit()

            QMessageBox.information(self, "Success", "Correction submitted")
            self.correction_description.clear()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to submit correction: {str(e)}")

    def view_task_details(self, index):
        """View details of a selected task"""
        task_id = self.tasks_table.item(index.row(), 0).text()

        cursor = self.db['sqlite'].cursor()
        cursor.execute('''
                       SELECT t.*, p.name as project_name, u.username as assigned_username
                       FROM tasks t
                                LEFT JOIN projects p ON t.project_id = p.id
                                LEFT JOIN users u ON t.assigned_to = u.id
                       WHERE t.id = ?
                       ''', (task_id,))

        task = cursor.fetchone()

        if task:
            columns = [desc[0] for desc in cursor.description]
            task_dict = dict(zip(columns, task))

            details = f"""
            <h2>{task_dict['title']}</h2>
            <p><b>Project:</b> {task_dict['project_name']}</p>
            <p><b>Status:</b> {task_dict['status']}</p>
            <p><b>Priority:</b> {task_dict['priority']}</p>
            <p><b>Due Date:</b> {task_dict['due_date']}</p>
            <p><b>Assigned To:</b> {task_dict['assigned_username'] or 'Unassigned'}</p>
            <hr>
            <h3>Description:</h3>
            <p>{task_dict['description'] or 'No description provided'}</p>
            """

            msg = QMessageBox()
            msg.setWindowTitle("Task Details")
            msg.setTextFormat(Qt.RichText)
            msg.setText(details)
            msg.exec_()

    def clear_task_form(self):
        """Clear the add task form"""
        self.task_title.clear()
        self.task_description.clear()
        self.task_status.setCurrentIndex(0)
        self.task_priority.setCurrentIndex(1)  # Medium
        self.task_due_date.setDate(QDate.currentDate().addDays(7))
        self.task_assigned_to.setCurrentIndex(0)