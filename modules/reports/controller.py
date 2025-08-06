from PyQt5.QtCore import QObject, pyqtSignal
from utils.excel_generator import ExcelGenerator
from datetime import datetime


class ReportController(QObject):
    report_generated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, db_connections):
        super().__init__()
        self.db = db_connections
        self.excel_gen = ExcelGenerator()

    def generate_project_summary(self, from_date, to_date):
        """Generate project summary report"""
        try:
            cursor = self.db['sqlite'].cursor()
            cursor.execute('''
                           SELECT p.id,
                                  p.name,
                                  p.status,
                                  COUNT(DISTINCT t.id) as task_count,
                                  COUNT(DISTINCT b.id) as bug_count
                           FROM projects p
                                    LEFT JOIN tasks t ON p.project_id = t.id
                                    LEFT JOIN bugs b ON p.project_id = b.id
                           WHERE p.start_date BETWEEN ? AND ?
                           GROUP BY p.id, p.name, p.status
                           ORDER BY p.name
                           ''', (from_date, to_date))

            projects = cursor.fetchall()

            report_data = {
                'sheets': [{
                    'title': 'Project Summary',
                    'headers': ['ID', 'Project Name', 'Status', 'Tasks', 'Bugs'],
                    'data': projects
                }],
                'file_name': f"reports/project_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            }

            file_path = self.excel_gen.generate_report(report_data)
            self.report_generated.emit(file_path)
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to generate project summary: {str(e)}")
            return False

    def generate_comprehensive_report(self, from_date, to_date, include_tasks=True,
                                      include_bugs=True, include_activities=True):
        """Generate comprehensive report with multiple sheets"""
        try:
            sheets = []

            if include_tasks:
                cursor = self.db['sqlite'].cursor()
                cursor.execute('''
                               SELECT t.id,
                                      p.name     as project,
                                      t.title,
                                      t.status,
                                      t.priority,
                                      t.due_date,
                                      u.username as assigned_to
                               FROM tasks t
                                        LEFT JOIN projects p ON t.project_id = p.id
                                        LEFT JOIN users u ON t.assigned_to = u.id
                               WHERE t.created_at BETWEEN ? AND ?
                               ORDER BY t.due_date, t.priority DESC
                               ''', (from_date, to_date))
                tasks = cursor.fetchall()

                sheets.append({
                    'title': 'Tasks',
                    'headers': ['ID', 'Project', 'Title', 'Status', 'Priority', 'Due Date', 'Assigned To'],
                    'data': tasks
                })

            if include_bugs:
                cursor.execute('''
                               SELECT b.id,
                                      p.name as project,
                                      b.title,
                                      b.severity,
                                      b.status,
                                      b.created_at
                               FROM bugs b
                                        LEFT JOIN projects p ON b.project_id = p.id
                               WHERE b.created_at BETWEEN ? AND ?
                               ORDER BY b.severity DESC, b.created_at DESC
                               ''', (from_date, to_date))
                bugs = cursor.fetchall()

                sheets.append({
                    'title': 'Bugs',
                    'headers': ['ID', 'Project', 'Title', 'Severity', 'Status', 'Reported On'],
                    'data': bugs
                })

            if include_activities:
                cursor.execute('''
                               SELECT id,
                                      title,
                                      type,
                                      status,
                                      created_at
                               FROM extra_activities
                               WHERE created_at BETWEEN ? AND ?
                               ORDER BY created_at DESC
                               ''', (from_date, to_date))
                activities = cursor.fetchall()

                sheets.append({
                    'title': 'Activities',
                    'headers': ['ID', 'Title', 'Type', 'Status', 'Requested On'],
                    'data': activities
                })

            report_data = {
                'sheets': sheets,
                'file_name': f"reports/comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            }

            file_path = self.excel_gen.generate_report(report_data)
            self.report_generated.emit(file_path)
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to generate comprehensive report: {str(e)}")
            return False