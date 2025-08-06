from PyQt5.QtCore import QObject, pyqtSignal


class TaskController(QObject):
    task_created = pyqtSignal(dict)
    task_updated = pyqtSignal(dict)
    task_deleted = pyqtSignal(int)
    correction_submitted = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, db_connections):
        super().__init__()
        self.db = db_connections

    def create_task(self, task_data):
        """Create a new task"""
        try:
            cursor = self.db['sqlite'].cursor()
            cursor.execute('''
                           INSERT INTO tasks (project_id, title, description, status, priority,
                                              due_date, assigned_to)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
                           ''', (
                               task_data['project_id'],
                               task_data['title'],
                               task_data['description'],
                               task_data['status'],
                               task_data['priority'],
                               task_data['due_date'],
                               task_data['assigned_to']
                           ))
            task_id = cursor.lastrowid
            self.db['sqlite'].commit()

            # Also insert into MongoDB
            task_data['id'] = task_id
            self.db['mongodb'].tasks.insert_one(task_data)

            self.task_created.emit(task_data)
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to create task: {str(e)}")
            return False

    def update_task(self, task_id, task_data):
        """Update an existing task"""
        try:
            cursor = self.db['sqlite'].cursor()
            cursor.execute('''
                           UPDATE tasks
                           SET title=?,
                               description=?,
                               status=?,
                               priority=?,
                               due_date=?,
                               assigned_to=?
                           WHERE id = ?
                           ''', (
                               task_data['title'],
                               task_data['description'],
                               task_data['status'],
                               task_data['priority'],
                               task_data['due_date'],
                               task_data['assigned_to'],
                               task_id
                           ))
            self.db['sqlite'].commit()

            # Also update MongoDB
            self.db['mongodb'].tasks.update_one(
                {'id': task_id},
                {'$set': task_data}
            )

            self.task_updated.emit({'id': task_id, **task_data})
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to update task: {str(e)}")
            return False

    def submit_correction(self, task_id, correction_data):
        """Submit a correction for a task"""
        try:
            cursor = self.db['sqlite'].cursor()
            cursor.execute('''
                           UPDATE tasks
                           SET description = description || '\n\nCORRECTION: ' || ?
                           WHERE id = ?
                           ''', (correction_data['description'], task_id))
            self.db['sqlite'].commit()

            # Also update MongoDB
            self.db['mongodb'].tasks.update_one(
                {'id': task_id},
                {'$push': {'corrections': correction_data}}
            )

            self.correction_submitted.emit({'task_id': task_id, **correction_data})
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to submit correction: {str(e)}")
            return False

    def get_task_list(self, filters=None):
        """Get list of tasks with optional filters"""
        try:
            cursor = self.db['sqlite'].cursor()

            query = '''
                    SELECT t.id, \
                           p.name     as project, \
                           t.title, \
                           t.status,
                           t.priority, \
                           t.due_date, \
                           u.username as assigned_to
                    FROM tasks t
                             LEFT JOIN projects p ON t.project_id = p.id
                             LEFT JOIN users u ON t.assigned_to = u.id
                    WHERE 1 = 1 \
                    '''

            params = []

            if filters and 'project_id' in filters:
                query += ' AND t.project_id = ?'
                params.append(filters['project_id'])

            if filters and 'status' in filters:
                query += ' AND t.status = ?'
                params.append(filters['status'])

            query += ' ORDER BY t.due_date, t.priority DESC'

            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            self.error_occurred.emit(f"Failed to get task list: {str(e)}")
            return []