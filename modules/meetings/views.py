from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QDateTimeEdit, QTextEdit,
    QListWidget, QInputDialog, QMessageBox, QFormLayout, QGroupBox, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QIcon


class MeetingsView(QWidget):
    def __init__(self, db_connections, current_user_id, parent=None):
        super().__init__(parent)
        self.db = db_connections
        self.current_user_id = current_user_id
        self.init_ui()
        self.load_meetings()

    def init_ui(self):
        layout = QHBoxLayout()

        # Meetings List
        self.meetings_table = QTableWidget()
        self.meetings_table.setColumnCount(5)
        self.meetings_table.setHorizontalHeaderLabels([
            "ID", "Title", "Date", "Duration", "Participants"
        ])
        self.meetings_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.meetings_table.doubleClicked.connect(self.view_meeting_details)
        layout.addWidget(self.meetings_table, 60)

        # Meeting Details/Form
        right_panel = QVBoxLayout()

        # Meeting Form
        form_group = QGroupBox("Schedule Meeting")
        form_layout = QFormLayout()

        self.meeting_title = QLineEdit()
        self.meeting_date = QDateTimeEdit()
        self.meeting_duration = QComboBox()
        self.meeting_description = QTextEdit()
        self.participants_list = QListWidget()

        self.meeting_date.setDateTime(QDateTime.currentDateTime())
        self.meeting_duration.addItems(["30 mins", "1 hour", "1.5 hours", "2 hours"])

        add_participant_btn = QPushButton("Add Participant")
        add_participant_btn.clicked.connect(self.add_participant)

        submit_btn = QPushButton("Schedule Meeting")
        submit_btn.clicked.connect(self.schedule_meeting)

        form_layout.addRow("Title:", self.meeting_title)
        form_layout.addRow("Date & Time:", self.meeting_date)
        form_layout.addRow("Duration:", self.meeting_duration)
        form_layout.addRow("Description:", self.meeting_description)
        form_layout.addRow("Participants:", self.participants_list)
        form_layout.addRow(add_participant_btn)
        form_layout.addRow(submit_btn)

        form_group.setLayout(form_layout)
        right_panel.addWidget(form_group)

        layout.addLayout(right_panel, 40)
        self.setLayout(layout)

        self.load_participants()

    def load_participants(self):
        cursor = self.db['sqlite'].cursor()
        cursor.execute("SELECT id, username FROM users WHERE id != ?", (self.current_user_id,))
        self.available_participants = cursor.fetchall()

    def load_meetings(self):
        cursor = self.db['sqlite'].cursor()
        cursor.execute('''
                       SELECT m.id,
                              m.title,
                              m.meeting_time,
                              m.duration,
                              GROUP_CONCAT(u.username, ', ') as participants
                       FROM meetings m
                                JOIN meeting_participants mp ON m.id = mp.meeting_id
                                JOIN users u ON mp.user_id = u.id
                       WHERE m.organizer_id = ?
                          OR mp.user_id = ?
                       GROUP BY m.id
                       ORDER BY m.meeting_time DESC
                       ''', (self.current_user_id, self.current_user_id))

        meetings = cursor.fetchall()
        self.meetings_table.setRowCount(len(meetings))
        for row, meeting in enumerate(meetings):
            for col, value in enumerate(meeting):
                self.meetings_table.setItem(row, col, QTableWidgetItem(str(value)))

    def add_participant(self):
        items = [f"{user_id}: {username}" for user_id, username in self.available_participants]
        item, ok = QInputDialog.getItem(
            self, "Add Participant", "Select user:", items, 0, False
        )
        if ok and item:
            user_id = int(item.split(':')[0])
            username = item.split(':')[1].strip()

            # Check if already added
            if not any(self.participants_list.item(i).data(Qt.UserRole) == user_id
                       for i in range(self.participants_list.count())):
                item = QListWidgetItem(username)
                item.setData(Qt.UserRole, user_id)
                self.participants_list.addItem(item)

    # def schedule_meeting(self):
    #     title = self.meeting_title.text()
    #     meeting_time = self.meeting_date.dateTime().toString(Qt.ISODate)
    #     duration = self.meeting_duration.currentText()
    #     description = self.meeting_description.toPlainText()
    #
    #     if not title:
    #         QMessageBox.warning(self, "Warning", "Meeting title is required")
    #         return
    #
    #     participant_ids = []
    #     for i in range(self.participants_list.count()):
    #         participant_ids.append(self.participants_list.item(i).data(Qt.UserRole))
    #
    #     cursor = self.db['sqlite'].cursor()
    #     cursor.execute('''
    #                    INSERT INTO meetings (organizer_id, title, meeting_time, duration, description)
    #                    VALUES (?, ?, ?, ?, ?)
    #                    ''', (self.current_user_id, title, meeting_time, duration, description))
    #     meeting_id = cursor.lastrowid
    #
    #     # Add participants
    #     for user_id in participant_ids:
    #         cursor.execute('''
    #                        INSERT INTO meeting_participants (meeting_id, user_id)
    #                        VALUES (?, ?)
    #                        ''', (meeting_id, user_id))
    #
    #     # Also insert into MongoDB
    #     self.db['mongodb'].meetings.insert_one({
    #         'meeting_id': meeting_id,
    #         'organizer_id': self.current_user_id,
    #         'title': title,
    #         'meeting_time': meeting_time,
    #         'duration': duration,
    #         'description': description,
    #         'participants': participant_ids,
    #         'created_at': datetime.datetime.now().isoformat()
    #     })
    #
    #     self.db['sqlite'].commit()
    #     QMessageBox.information(self, "Success", "Meeting scheduled successfully")
    #     self.load_meetings()

    def schedule_meeting(self):
        title = self.meeting_title.text()
        meeting_time = self.meeting_date.dateTime().toString(Qt.ISODate)
        duration = self.meeting_duration.currentText()
        description = self.meeting_description.toPlainText()

        if not title:
            QMessageBox.warning(self, "Warning", "Meeting title is required")
            return

        participant_ids = []
        for i in range(self.participants_list.count()):
            participant_ids.append(self.participants_list.item(i).data(Qt.UserRole))

        # SQLite Transaction
        cursor = self.db['sqlite'].cursor()
        try:
            cursor.execute('''
                           INSERT INTO meetings (organizer_id, title, meeting_time, duration, description)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (self.current_user_id, title, meeting_time, duration, description))
            meeting_id = cursor.lastrowid

            # Add participants
            for user_id in participant_ids:
                cursor.execute('''
                               INSERT INTO meeting_participants (meeting_id, user_id)
                               VALUES (?, ?)
                               ''', (meeting_id, user_id))

            self.db['sqlite'].commit()
        except Exception as e:
            self.db['sqlite'].rollback()
            QMessageBox.critical(self, "Error", f"Failed to schedule meeting: {str(e)}")
            return

        # MongoDB Document
        mongo_meeting = {
            'meeting_id': meeting_id,
            'organizer_id': self.current_user_id,
            'title': title,
            'meeting_time': meeting_time,
            'duration': duration,
            'description': description,
            'participants': participant_ids,
            'agenda_items': [],  # Flexible array field
            'attachments': [],  # Can store file references
            'status': 'scheduled',
            'created_at': datetime.datetime.now().isoformat(),
            'updated_at': datetime.datetime.now().isoformat(),
            'timezone': 'UTC',  # Additional metadata
            'recurrence': None  # Could store recurrence rules
        }
        self.db['mongodb'].meetings.insert_one(mongo_meeting)

        QMessageBox.information(self, "Success", "Meeting scheduled successfully")
        self.load_meetings()

    def view_meeting_details(self, index):
        meeting_id = int(self.meetings_table.item(index.row(), 0).text())

        cursor = self.db['sqlite'].cursor()
        cursor.execute('''
                       SELECT m.title,
                              m.meeting_time,
                              m.duration,
                              m.description,
                              u.username                      as organizer,
                              GROUP_CONCAT(u2.username, ', ') as participants
                       FROM meetings m
                                JOIN users u ON m.organizer_id = u.id
                                JOIN meeting_participants mp ON m.id = mp.meeting_id
                                JOIN users u2 ON mp.user_id = u2.id
                       WHERE m.id = ?
                       GROUP BY m.id
                       ''', (meeting_id,))

        meeting = cursor.fetchone()

        details = f"""
        <h2>{meeting[0]}</h2>
        <p><b>Organizer:</b> {meeting[4]}</p>
        <p><b>Time:</b> {meeting[1]} ({meeting[2]})</p>
        <p><b>Participants:</b> {meeting[5]}</p>
        <hr>
        <h3>Description:</h3>
        <p>{meeting[3]}</p>
        """

        msg = QMessageBox()
        msg.setWindowTitle("Meeting Details")
        msg.setTextFormat(Qt.RichText)
        msg.setText(details)
        msg.exec_()