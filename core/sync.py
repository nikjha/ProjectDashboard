import threading
import time
from typing import Dict, Any
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal


class SyncManager(QObject):
    sync_complete = pyqtSignal(bool, str)  # success, message

    def __init__(self, db_connections):
        super().__init__()
        self.db = db_connections
        self.sync_config = {
            'mysql_host': 'localhost',
            'mysql_database': 'project_dashboard',
            'mysql_user': 'root',
            'mysql_password': '',
            'sync_interval': 3600,  # 1 hour
            'last_sync': None
        }
        self.sync_thread = None
        self.running = False
        self.lock = threading.Lock()  # For thread safety

    def should_sync(self) -> bool:
        """Check if it's time to sync based on last sync time and interval"""
        if not self.sync_config['last_sync']:
            return True

        next_sync = self.sync_config['last_sync'] + timedelta(
            seconds=self.sync_config['sync_interval']
        )
        return datetime.now() >= next_sync

    def sync_data(self):
        """Perform data synchronization with MySQL"""
        if self.running:
            return False

        with self.lock:
            if self.running:  # Double-check locking
                return False
            self.running = True

        self.sync_thread = threading.Thread(target=self._sync_data_thread, daemon=True)
        self.sync_thread.start()
        return True

    def _sync_data_thread(self):
        """Thread function for syncing data"""
        success = False
        message = ""

        try:
            # Connect to MySQL
            mysql_conn = mysql.connector.connect(
                host=self.sync_config['mysql_host'],
                database=self.sync_config['mysql_database'],
                user=self.sync_config['mysql_user'],
                password=self.sync_config['mysql_password']
            )

            if mysql_conn.is_connected():
                # Sync tables
                tables_to_sync = [
                    'users', 'projects', 'tasks', 'bugs',
                    'extra_activities', 'meetings', 'messages',
                    'time_entries', 'meeting_participants'
                ]

                for table in tables_to_sync:
                    self._sync_table(mysql_conn, table)

                # Update last sync time
                self.sync_config['last_sync'] = datetime.now()

                # Log sync
                self._log_sync(True, "Sync completed successfully")

                success = True
                message = "Sync completed successfully"
            else:
                message = "Failed to connect to MySQL"

        except Error as e:
            message = f"MySQL Error: {str(e)}"
            self._log_sync(False, message)
        except Exception as e:
            message = f"Error: {str(e)}"
            self._log_sync(False, message)
        finally:
            if 'mysql_conn' in locals() and mysql_conn.is_connected():
                mysql_conn.close()

            with self.lock:
                self.running = False
            self.sync_complete.emit(success, message)

    def _sync_table(self, mysql_conn, table_name):
        """Sync data for a specific table"""
        try:
            # Get data from SQLite
            sqlite_cursor = self.db['sqlite'].cursor()
            sqlite_cursor.execute(f'SELECT * FROM {table_name}')
            sqlite_data = sqlite_cursor.fetchall()

            if not sqlite_data:
                return

            columns = [desc[0] for desc in sqlite_cursor.description]
            column_types = [desc[1] for desc in sqlite_cursor.description]

            # Prepare MySQL cursor
            mysql_cursor = mysql_conn.cursor()

            # Check if table exists in MySQL
            mysql_cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            table_exists = mysql_cursor.fetchone()

            if not table_exists:
                # Create table in MySQL with proper schema
                create_table_sql = self._get_create_table_sql(table_name, columns, column_types)
                mysql_cursor.execute(create_table_sql)

            # Get existing records from MySQL
            mysql_cursor.execute(f'SELECT * FROM {table_name}')
            mysql_data = mysql_cursor.fetchall()

            # Convert MySQL data to dict for comparison
            mysql_records = {row[0]: row for row in mysql_data}  # Assuming first column is ID

            # Insert or update records
            for record in sqlite_data:
                record_id = record[0]
                if record_id in mysql_records:
                    # Update existing record if different
                    if record != mysql_records[record_id]:
                        update_sql = self._get_update_sql(table_name, columns)
                        mysql_cursor.execute(update_sql, record[1:] + (record_id,))
                else:
                    # Insert new record
                    insert_sql = self._get_insert_sql(table_name, columns)
                    mysql_cursor.execute(insert_sql, record)

            mysql_conn.commit()

        except Exception as e:
            mysql_conn.rollback()
            raise e

    def _get_create_table_sql(self, table_name, columns, column_types):
        """Generate proper CREATE TABLE SQL based on SQLite schema"""
        type_mapping = {
            'INTEGER': 'INT',
            'TEXT': 'TEXT',
            'REAL': 'FLOAT',
            'BLOB': 'BLOB',
            'NUMERIC': 'DECIMAL'
        }

        column_defs = []
        for col, col_type in zip(columns, column_types):
            mysql_type = type_mapping.get(col_type.upper(), 'TEXT')
            if col == columns[0]:  # Assuming first column is primary key
                column_defs.append(f"{col} {mysql_type} PRIMARY KEY")
            else:
                column_defs.append(f"{col} {mysql_type}")

        return f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"

    def _get_update_sql(self, table_name, columns):
        """Generate UPDATE SQL"""
        set_clause = ", ".join([f"{col} = %s" for col in columns[1:]])
        return f"UPDATE {table_name} SET {set_clause} WHERE {columns[0]} = %s"

    def _get_insert_sql(self, table_name, columns):
        """Generate INSERT SQL"""
        columns_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        return f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

    def _log_sync(self, success, message):
        """Log sync operation to MongoDB"""
        log_entry = {
            'timestamp': datetime.now(),
            'success': success,
            'message': message,
            'tables_synced': [
                'users', 'projects', 'tasks', 'bugs',
                'extra_activities', 'meetings', 'messages',
                'time_entries', 'meeting_participants'
            ]
        }

        self.db['mongodb'].sync_logs.insert_one(log_entry)

    def configure(self, config):
        """Update sync configuration"""
        with self.lock:
            self.sync_config.update(config)