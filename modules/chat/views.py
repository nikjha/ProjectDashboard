from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QTextEdit,
    QPushButton, QLabel, QListWidgetItem, QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont


class ChatView(QWidget):
    message_sent = pyqtSignal(str, int, str)  # message, recipient_id, recipient_name

    def __init__(self, db_connections, current_user_id, parent=None):
        super().__init__(parent)
        self.db = db_connections
        self.current_user_id = current_user_id
        self.init_ui()
        self.load_contacts()

    def init_ui(self):
        layout = QHBoxLayout()

        # Contacts List
        self.contacts_list = QListWidget()
        self.contacts_list.setFixedWidth(200)
        self.contacts_list.itemClicked.connect(self.load_conversation)
        layout.addWidget(self.contacts_list)

        # Chat Area
        chat_layout = QVBoxLayout()

        self.chat_header = QLabel("Select a contact to chat")
        self.chat_header.setAlignment(Qt.AlignCenter)
        self.chat_header.setFont(QFont("Arial", 12, QFont.Bold))
        chat_layout.addWidget(self.chat_header)

        self.messages_display = QTextEdit()
        self.messages_display.setReadOnly(True)
        chat_layout.addWidget(self.messages_display)

        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        chat_layout.addWidget(self.message_input)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)
        chat_layout.addWidget(send_btn)

        layout.addLayout(chat_layout)
        self.setLayout(layout)

        self.current_contact = None

    def load_contacts(self):
        cursor = self.db['sqlite'].cursor()
        cursor.execute("SELECT id, username FROM users WHERE id != ?", (self.current_user_id,))
        contacts = cursor.fetchall()

        self.contacts_list.clear()
        for user_id, username in contacts:
            item = QListWidgetItem(username)
            item.setData(Qt.UserRole, user_id)
            self.contacts_list.addItem(item)

    def load_conversation(self, item):
        self.current_contact = {
            'id': item.data(Qt.UserRole),
            'name': item.text()
        }
        self.chat_header.setText(f"Chat with {item.text()}")

        cursor = self.db['sqlite'].cursor()
        cursor.execute('''
                       SELECT sender_id, message, timestamp
                       FROM messages
                       WHERE (sender_id = ?
                         AND receiver_id = ?)
                          OR (sender_id = ?
                         AND receiver_id = ?)
                       ORDER BY timestamp
                       ''', (self.current_user_id, self.current_contact['id'],
                             self.current_contact['id'], self.current_user_id))

        self.messages_display.clear()
        for sender_id, message, timestamp in cursor.fetchall():
            alignment = Qt.AlignLeft if sender_id != self.current_user_id else Qt.AlignRight
            self.messages_display.append(f"<div style='text-align:{alignment};'>"
                                         f"<b>{'You' if sender_id == self.current_user_id else self.current_contact['name']}</b><br>"
                                         f"{message}<br>"
                                         f"<small>{timestamp}</small></div>")
    #
    # def send_message(self):
    #     if not self.current_contact:
    #         QMessageBox.warning(self, "Warning", "Please select a contact first")
    #         return
    #
    #     message = self.message_input.toPlainText()
    #     if not message.strip():
    #         return
    #
    #     cursor = self.db['sqlite'].cursor()
    #     cursor.execute('''
    #                    INSERT INTO messages (sender_id, receiver_id, message)
    #                    VALUES (?, ?, ?)
    #                    ''', (self.current_user_id, self.current_contact['id'], message))
    #     self.db['sqlite'].commit()
    #
    #     # Also store in MongoDB
    #     self.db['mongodb'].messages.insert_one({
    #         'sender_id': self.current_user_id,
    #         'receiver_id': self.current_contact['id'],
    #         'message': message,
    #         'timestamp': datetime.datetime.now().isoformat()
    #     })
    #
    #     self.message_sent.emit(message, self.current_contact['id'], self.current_contact['name'])
    #     self.message_input.clear()
    #     self.load_conversation(self.contacts_list.currentItem())
    #

    def send_message(self):
        if not self.current_contact:
            QMessageBox.warning(self, "Warning", "Please select a contact first")
            return

        message = self.message_input.toPlainText()
        if not message.strip():
            return

        # SQLite Insert (for structured data)
        cursor = self.db['sqlite'].cursor()
        cursor.execute('''
                       INSERT INTO messages (sender_id, receiver_id, message)
                       VALUES (?, ?, ?)
                       ''', (self.current_user_id, self.current_contact['id'], message))
        message_id = cursor.lastrowid
        self.db['sqlite'].commit()

        # MongoDB Insert (for rich message features)
        mongo_message = {
            'message_id': message_id,
            'sender_id': self.current_user_id,
            'receiver_id': self.current_contact['id'],
            'message': message,
            'formatted_message': f"<b>{self.current_user.name}</b>: {message}",
            'timestamp': datetime.datetime.now().isoformat(),
            'status': 'delivered',
            'read_receipt': False,
            'metadata': {
                'device': 'desktop',
                'ip_address': '127.0.0.1'  # Would be real IP in production
            }
        }
        self.db['mongodb'].messages.insert_one(mongo_message)

        self.message_sent.emit(message, self.current_contact['id'], self.current_contact['name'])
        self.message_input.clear()
        self.load_conversation(self.contacts_list.currentItem())