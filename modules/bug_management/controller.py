from PyQt5.QtCore import QObject, pyqtSignal


class BugController(QObject):
    bug_reported = pyqtSignal(dict)
    bug_updated = pyqtSignal(dict)
    bug_deleted = pyqtSignal(int)
    error_occurred = pyqtSignal(str)

    def __init__(self, db_connections):
        super().__init__()
        self.db = db_connections

    def report_bug(self, bug_data):
        """Report a new bug"""
        try:
            cursor = self.db['sqlite'].cursor()
            cursor.execute('''
                           INSERT INTO bugs (project_id, title, description, severity, status)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (
                               bug_data['project_id'],
                               bug_data['title'],
                               bug_data['description'],
                               bug_data['severity'],
                               bug_data['status']
                           ))
            bug_id = cursor.lastrowid
            self.db['sqlite'].commit()

            # Also insert into MongoDB
            bug_data['id'] = bug_id
            self.db['mongodb'].bugs.insert_one(bug_data)

            self.bug_reported.emit(bug_data)
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to report bug: {str(e)}")
            return False

    def update_bug(self, bug_id, bug_data):
        """Update an existing bug"""
        try:
            cursor = self.db['sqlite'].cursor()
            cursor.execute('''
                           UPDATE bugs
                           SET title=?,
                               description=?,
                               severity=?,
                               status=?
                           WHERE id = ?
                           ''', (
                               bug_data['title'],
                               bug_data['description'],
                               bug_data['severity'],
                               bug_data['status'],
                               bug_id
                           ))
            self.db['sqlite'].commit()

            # Also update MongoDB
            self.db['mongodb'].bugs.update_one(
                {'id': bug_id},
                {'$set': bug_data}
            )

            self.bug_updated.emit({'id': bug_id, **bug_data})
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to update bug: {str(e)}")
            return False

    def get_bug_list(self, filters=None):
        """Get list of bugs with optional filters"""
        try:
            cursor = self.db['sqlite'].cursor()

            query = '''
                    SELECT b.id, \
                           p.name as project, \
                           b.title, \
                           b.severity,
                           b.status, \
                           b.created_at
                    FROM bugs b
                             LEFT JOIN projects p ON b.project_id = p.id
                    WHERE 1 = 1 \
                    '''

            params = []

            if filters and 'project_id' in filters:
                query += ' AND b.project_id = ?'
                params.append(filters['project_id'])

            if filters and 'status' in filters:
                query += ' AND b.status = ?'
                params.append(filters['status'])

            if filters and 'severity' in filters:
                query += ' AND b.severity = ?'
                params.append(filters['severity'])

            query += ' ORDER BY b.severity DESC, b.created_at DESC'

            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            self.error_occurred.emit(f"Failed to get bug list: {str(e)}")
            return []