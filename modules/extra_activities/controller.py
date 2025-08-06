from PyQt5.QtCore import QObject, pyqtSignal


class ActivityController(QObject):
    activity_requested = pyqtSignal(dict)
    activity_updated = pyqtSignal(dict)
    activity_deleted = pyqtSignal(int)
    error_occurred = pyqtSignal(str)

    def __init__(self, db_connections):
        super().__init__()
        self.db = db_connections

    def request_activity(self, activity_data):
        """Request a new activity"""
        try:
            cursor = self.db['sqlite'].cursor()
            cursor.execute('''
                           INSERT INTO extra_activities (title, type, description, status)
                           VALUES (?, ?, ?, ?)
                           ''', (
                               activity_data['title'],
                               activity_data['type'],
                               activity_data['description'],
                               activity_data['status']
                           ))
            activity_id = cursor.lastrowid
            self.db['sqlite'].commit()

            # Also insert into MongoDB
            activity_data['id'] = activity_id
            self.db['mongodb'].extra_activities.insert_one(activity_data)

            self.activity_requested.emit(activity_data)
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to request activity: {str(e)}")
            return False

    def update_activity(self, activity_id, activity_data):
        """Update an existing activity"""
        try:
            cursor = self.db['sqlite'].cursor()
            cursor.execute('''
                           UPDATE extra_activities
                           SET title=?,
                               type=?,
                               description=?,
                               status=?
                           WHERE id = ?
                           ''', (
                               activity_data['title'],
                               activity_data['type'],
                               activity_data['description'],
                               activity_data['status'],
                               activity_id
                           ))
            self.db['sqlite'].commit()

            # Also update MongoDB
            self.db['mongodb'].extra_activities.update_one(
                {'id': activity_id},
                {'$set': activity_data}
            )

            self.activity_updated.emit({'id': activity_id, **activity_data})
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to update activity: {str(e)}")
            return False

    def get_activity_list(self, filters=None):
        """Get list of activities with optional filters"""
        try:
            cursor = self.db['sqlite'].cursor()

            query = '''
                    SELECT id, title, type, status, created_at
                    FROM extra_activities
                    WHERE 1 = 1 \
                    '''

            params = []

            if filters and 'type' in filters:
                query += ' AND type = ?'
                params.append(filters['type'])

            if filters and 'status' in filters:
                query += ' AND status = ?'
                params.append(filters['status'])

            query += ' ORDER BY created_at DESC'

            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            self.error_occurred.emit(f"Failed to get activity list: {str(e)}")
            return []