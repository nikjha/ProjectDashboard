from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTabWidget,
    QFormLayout, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from core.auth import AuthManager


class LoginWindow(QWidget):
    login_success = pyqtSignal(dict)

    def __init__(self, auth_manager: AuthManager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title = QLabel("Project Dashboard Login")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 30px;")
        layout.addWidget(title)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.username_input = QLineEdit()
        self.username_input.setAlignment(Qt.AlignLeft)
        self.username_input.setPlaceholderText("Enter your username")
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setAlignment(Qt.AlignLeft)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.password_input)

        layout.addLayout(form_layout)

        # Login button
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.handle_login)
        login_btn.setStyleSheet("padding: 8px; font-weight: bold;")
        layout.addWidget(login_btn)

        self.setLayout(layout)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password")
            return

        user = self.auth_manager.authenticate(username, password)
        if user:
            self.login_success.emit(user)
        else:
            QMessageBox.warning(self, "Error", "Invalid username or password")


class UserManagementView(QWidget):
    def __init__(self, auth_manager: AuthManager, db_connections, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.db = db_connections
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        # Create tab widget
        self.tabs = QTabWidget()

        # User list tab
        self.user_list_tab = QWidget()
        self.init_user_list_tab()
        self.tabs.addTab(self.user_list_tab, "User List")

        # Add user tab
        self.add_user_tab = QWidget()
        self.init_add_user_tab()
        self.tabs.addTab(self.add_user_tab, "Add User")

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        # Load initial data
        self.load_users()

    def init_user_list_tab(self):
        layout = QVBoxLayout()

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search users...")
        self.search_input.textChanged.connect(self.load_users)
        search_layout.addWidget(self.search_input)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_users)
        search_layout.addWidget(refresh_btn)

        layout.addLayout(search_layout)

        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(["ID", "Username", "Full Name", "Email", "Role"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.users_table)
        self.user_list_tab.setLayout(layout)

    def init_add_user_tab(self):
        layout = QFormLayout()

        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText("Enter username")
        layout.addRow("Username:", self.new_username)

        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("Enter password")
        self.new_password.setEchoMode(QLineEdit.Password)
        layout.addRow("Password:", self.new_password)

        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Confirm password")
        self.confirm_password.setEchoMode(QLineEdit.Password)
        layout.addRow("Confirm Password:", self.confirm_password)

        self.full_name = QLineEdit()
        self.full_name.setPlaceholderText("Enter full name")
        layout.addRow("Full Name:", self.full_name)

        self.email = QLineEdit()
        self.email.setPlaceholderText("Enter email")
        layout.addRow("Email:", self.email)

        self.role = QComboBox()
        self.role.addItems(["user", "admin", "manager"])
        layout.addRow("Role:", self.role)

        add_user_btn = QPushButton("Add User")
        add_user_btn.clicked.connect(self.add_user)
        layout.addRow(add_user_btn)

        self.add_user_tab.setLayout(layout)

    def load_users(self):
        search_term = self.search_input.text()

        # Load from SQLite
        cursor = self.db['sqlite'].cursor()
        if search_term:
            cursor.execute('''
                           SELECT id, username, full_name, email, role
                           FROM users
                           WHERE username LIKE ?
                              OR full_name LIKE ?
                              OR email LIKE ?
                           ''', (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        else:
            cursor.execute('SELECT id, username, full_name, email, role FROM users')

        users = cursor.fetchall()

        self.users_table.setRowCount(len(users))
        for row_idx, user in enumerate(users):
            for col_idx, value in enumerate(user):
                item = QTableWidgetItem(str(value))
                self.users_table.setItem(row_idx, col_idx, item)

    def add_user(self):
        username = self.new_username.text()
        password = self.new_password.text()
        confirm_password = self.confirm_password.text()
        full_name = self.full_name.text()
        email = self.email.text()
        role = self.role.currentText()

        if not all([username, password, confirm_password, full_name, email]):
            QMessageBox.warning(self, "Error", "All fields are required")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return

        user_data = {
            'username': username,
            'password': password,
            'full_name': full_name,
            'email': email,
            'role': role
        }

        if self.auth_manager.create_user(user_data):
            QMessageBox.information(self, "Success", "User created successfully")
            self.load_users()
            self.clear_form()
        else:
            QMessageBox.warning(self, "Error", "Failed to create user")

    def clear_form(self):
        self.new_username.clear()
        self.new_password.clear()
        self.confirm_password.clear()
        self.full_name.clear()
        self.email.clear()
        self.role.setCurrentIndex(0)
    #
    # def set_user_role(self, role):
    #     """Enable/disable features based on user role"""
    #     if role != 'admin':
    #         self.tabs.removeTab(1)  # Remove "Add User" tab for non-admins
    #


    def set_user_role(self, role):
        """Enable/disable features based on user role"""
        self.current_role = role

        # For UserManagementView, just control what user management features are available
        if role != 'admin':
            # Remove "Add User" tab for non-admins
            while self.tabs.count() > 1:
                self.tabs.removeTab(1)