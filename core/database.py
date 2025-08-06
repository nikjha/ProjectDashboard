import sqlite3
from pymongo import MongoClient
from config import DB_CONFIG
from typing import Dict, Any
import datetime
from pymongo.server_api import ServerApi

def initialize_databases() -> Dict[str, Any]:
    """Initialize and return database connections"""
    connections = {}

    # Initialize SQLite
    sqlite_conn = sqlite3.connect(DB_CONFIG['sqlite']['path'])
    connections['sqlite'] = sqlite_conn

    # Initialize MongoDB
    #mongo_client = MongoClient(DB_CONFIG['mongodb']['uri'])
    # Initialize MongoDB Atlas with TLS
    mongo_client = MongoClient(
        DB_CONFIG['mongodb']['uri'],
        server_api=ServerApi('1'),
        tls=True,
        tlsAllowInvalidCertificates=False  # Set to True only for testing
    )

    # Verify connection
    try:
        mongo_client.admin.command('ping')
        print("Pinged your Atlas deployment. Successfully connected!")
    except Exception as e:
        print("Failed to connect to MongoDB Atlas:", e)
        raise

    mongo_db = mongo_client[DB_CONFIG['mongodb']['db_name']]
    connections['mongodb'] = mongo_db

    # Create tables/collections if they don't exist
    initialize_sqlite_tables(sqlite_conn)
    initialize_mongo_collections(mongo_db)

    return connections


def initialize_sqlite_tables(conn):
    """Create SQLite tables if they don't exist"""
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS users
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       username
                       TEXT
                       UNIQUE
                       NOT
                       NULL,
                       password_hash
                       TEXT
                       NOT
                       NULL,
                       full_name
                       TEXT
                       NOT
                       NULL,
                       email
                       TEXT
                       UNIQUE
                       NOT
                       NULL,
                       role
                       TEXT
                       NOT
                       NULL
                       DEFAULT
                       'user',
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       last_login
                       TIMESTAMP
                   )
                   ''')

    # Projects table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS projects
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       description
                       TEXT,
                       status
                       TEXT
                       NOT
                       NULL
                       DEFAULT
                       'active',
                       start_date
                       DATE,
                       end_date
                       DATE,
                       created_by
                       INTEGER,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       created_by
                   ) REFERENCES users
                   (
                       id
                   )
                       )
                   ''')

    # Tasks table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS tasks
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       project_id
                       INTEGER
                       NOT
                       NULL,
                       title
                       TEXT
                       NOT
                       NULL,
                       description
                       TEXT,
                       status
                       TEXT
                       NOT
                       NULL
                       DEFAULT
                       'pending',
                       priority
                       TEXT
                       NOT
                       NULL
                       DEFAULT
                       'medium',
                       assigned_to
                       INTEGER,
                       due_date
                       DATE,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       project_id
                   ) REFERENCES projects
                   (
                       id
                   ),
                       FOREIGN KEY
                   (
                       assigned_to
                   ) REFERENCES users
                   (
                       id
                   )
                       )
                   ''')

    # Bugs table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS bugs
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       project_id
                       INTEGER
                       NOT
                       NULL,
                       title
                       TEXT
                       NOT
                       NULL,
                       description
                       TEXT,
                       severity
                       TEXT
                       NOT
                       NULL
                       DEFAULT
                       'medium',
                       status
                       TEXT
                       NOT
                       NULL
                       DEFAULT
                       'open',
                       reported_by
                       INTEGER,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       project_id
                   ) REFERENCES projects
                   (
                       id
                   ),
                       FOREIGN KEY
                   (
                       reported_by
                   ) REFERENCES users
                   (
                       id
                   )
                       )
                   ''')

    # Extra activities table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS extra_activities
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       title
                       TEXT
                       NOT
                       NULL,
                       description
                       TEXT,
                       type
                       TEXT
                       NOT
                       NULL,
                       requested_by
                       INTEGER,
                       status
                       TEXT
                       NOT
                       NULL
                       DEFAULT
                       'pending',
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       requested_by
                   ) REFERENCES users
                   (
                       id
                   )
                       )
                   ''')

    # Extra activities table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS time_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    project_id INTEGER NOT NULL,
                    task_id INTEGER,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                     )
                   ''')

    # Extra activities table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    receiver_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (sender_id) REFERENCES users(id),
                    FOREIGN KEY (receiver_id) REFERENCES users(id)
                )
                   ''')

    # Extra activities table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS meetings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organizer_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    meeting_time DATETIME NOT NULL,
                    duration TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (organizer_id) REFERENCES users(id)
                )
                   ''')
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS meeting_participants (
                        meeting_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        PRIMARY KEY (meeting_id, user_id),
                        FOREIGN KEY (meeting_id) REFERENCES meetings(id),
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                   ''')

    conn.commit()

    # Check if admin user exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    admin_exists = cursor.fetchone()

    if not admin_exists:
        # Create admin user
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            'admin',
            # Hash for 'admin123'
            '$2b$12$oMi80sv9dinR7vxcE11SUOoZPINSZZ8sFRjFbwXSli7dPf8OEoa/2',
            'Administrator',
            'admin@projectdashboard.com',
            'admin'
        ))
        conn.commit()


def initialize_mongo_collections(db):
    """Ensure MongoDB collections exist"""
    collections = ['users', 'projects', 'tasks', 'bugs', 'extra_activities', 'sync_logs', 'time_entries', 'messages', 'meetings', 'meeting_participants']

    for collection in collections:
        if collection not in db.list_collection_names():
            db.create_collection(collection)

    # Check if admin user exists
    if db.users.count_documents({'username': 'admin'}) == 0:
        db.users.insert_one({
            'username': 'admin',
            'password_hash': '$2b$12$oMi80sv9dinR7vxcE11SUOoZPINSZZ8sFRjFbwXSli7dPf8OEoa/2',
            'full_name': 'Administrator',
            'email': 'admin@projectdashboard.com',
            'role': 'admin',
            'created_at': datetime.datetime.now(),
            'last_login': None
        })

    db.sync_logs.create_index("timestamp")
