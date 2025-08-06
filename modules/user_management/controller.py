from PyQt5.QtCore import QObject, pyqtSignal
from core.auth import AuthManager
from utils.helpers import validate_email


class UserController(QObject):
    user_created = pyqtSignal(dict)
    user_updated = pyqtSignal(dict)
    user_deleted = pyqtSignal(int)
    error_occurred = pyqtSignal(str)

    def __init__(self, auth_manager: AuthManager, db_connections):
        super().__init__()
        self.auth_manager = auth_manager
        self.db = db_connections

    def create_user(self, user_data):
        """Create a new user account"""
        if not validate_email(user_data['email']):
            self.error_occurred.emit("Invalid email address")
            return False

        if user_data['password'] != user_data['confirm_password']:
            self.error_occurred.emit("Passwords do not match")
            return False

        if self.auth_manager.create_user(user_data):
            self.user_created.emit(user_data)
            return True
        else:
            self.error_occurred.emit("Failed to create user")
            return False

    def update_user(self, user_id, user_data):
        """Update an existing user account"""
        try:
            cursor = self.db['sqlite'].cursor()
            cursor.execute('''
                UPDATE users 
                SET username=?, full_name=?, email=?, role=?
                WHERE id=?
            ''', (
                user_data['username'],
                user_data['full_name'],
                user_data['email'],
                user_data['role'],
                user_id
            ))
            self.db['sqlite'].commit()

            # Also update MongoDB
            self.db['mongodb'].users.update_one(
                {'id': user_id},
                {'$set': {
                    'username': user_data['username'],
                    'full_name': user_data['full_name'],
                    'email': user_data['email'],
                    'role': user_data['role']
                }}
            )

            self.user_updated.emit({'id': user_id, **user_data})
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to update user: {str(e)}")
            return False

    def delete_user(self, user_id):
        """Delete a user account"""
        try:
            cursor = self.db['sqlite'].cursor()
            cursor.execute('DELETE FROM users WHERE id=?', (user_id,))
            self.db['sqlite'].commit()

            # Also delete from MongoDB
            self.db['mongodb'].users.delete_one({'id': user_id})

            self.user_deleted.emit(user_id)
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to delete user: {str(e)}")
            return False

    def get_user_list(self, search_term=None):
        """Get list of users with optional search filter"""
        try:
            cursor = self.db['sqlite'].cursor()
            if search_term:
                cursor.execute('''
                    SELECT id, username, full_name, email, role 
                    FROM users 
                    WHERE username LIKE ? OR full_name LIKE ? OR email LIKE ?
                    ORDER BY username
                ''', (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            else:
                cursor.execute('''
                    SELECT id, username, full_name, email, role 
                    FROM users 
                    ORDER BY username
                ''')
            return cursor.fetchall()
        except Exception as e:
            self.error_occurred.emit(f"Failed to get user list: {str(e)}")
            return []