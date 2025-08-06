from typing import Dict, Optional
import bcrypt
from PyQt5.QtCore import QObject, pyqtSignal


class AuthManager(QObject):
    login_success = pyqtSignal(dict)  # Signal emitted on successful login

    def __init__(self, db_connections):
        super().__init__()
        self.db = db_connections
        self.current_user = None

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with username and password"""
        # Try SQLite first
        cursor = self.db['sqlite'].cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user:
            # Convert SQLite row to dict
            columns = [desc[0] for desc in cursor.description]
            user_dict = dict(zip(columns, user))

            # Verify password
            if self._verify_password(password, user_dict['password_hash']):
                self.current_user = user_dict
                self.login_success.emit(user_dict)
                return user_dict

        # If not found in SQLite, try MongoDB
        mongo_user = self.db['mongodb'].users.find_one({'username': username})
        if mongo_user and self._verify_password(password, mongo_user['password_hash']):
            # Convert MongoDB ObjectId to string for serialization
            mongo_user['_id'] = str(mongo_user['_id'])
            self.current_user = mongo_user
            self.login_success.emit(mongo_user)
            return mongo_user

        return None

    def _hash_password(self, password: str) -> str:
        """Hash a password for storing"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a stored password against one provided by user"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    def create_user(self, user_data: Dict) -> bool:
        """Create a new user"""
        try:
            # Hash password before storing
            user_data['password_hash'] = self._hash_password(user_data.pop('password'))

            # Store in both databases
            cursor = self.db['sqlite'].cursor()
            cursor.execute('''
                           INSERT INTO users (username, password_hash, full_name, email, role)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (
                               user_data['username'],
                               user_data['password_hash'],
                               user_data['full_name'],
                               user_data['email'],
                               user_data.get('role', 'user')
                           ))
            self.db['sqlite'].commit()

            # Also store in MongoDB
            self.db['mongodb'].users.insert_one(user_data)

            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    def get_current_user(self) -> Optional[Dict]:
        """Get currently authenticated user"""
        return self.current_user