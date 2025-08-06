import os
import datetime
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor


def format_date(date_str, input_format="%Y-%m-%d", output_format="%d %b %Y"):
    """Format date string from one format to another"""
    if not date_str:
        return ""
    try:
        date_obj = datetime.datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except ValueError:
        return date_str


def set_table_row_color(table, row, color):
    """Set background color for an entire row in a table"""
    for col in range(table.columnCount()):
        item = table.item(row, col)
        if item:
            item.setBackground(color)


def create_readonly_item(text):
    """Create a table widget item that's not editable"""
    item = QTableWidgetItem(str(text))
    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    return item


def clear_table(table):
    """Clear all rows from a table"""
    table.setRowCount(0)


def populate_combo_from_query(combo, query, params=None, db_conn=None, display_col=1, data_col=0):
    """Populate a combo box from a database query"""
    combo.clear()
    if db_conn:
        cursor = db_conn.cursor()
        cursor.execute(query, params or ())
        for row in cursor.fetchall():
            combo.addItem(str(row[display_col]), row[data_col])


def date_to_qdate(date_str, date_format="%Y-%m-%d"):
    """Convert date string to QDate"""
    if not date_str:
        return QDate.currentDate()
    try:
        date_obj = datetime.datetime.strptime(date_str, date_format)
        return QDate(date_obj.year, date_obj.month, date_obj.day)
    except ValueError:
        return QDate.currentDate()


def validate_email(email):
    """Simple email validation"""
    return '@' in email and '.' in email.split('@')[-1]


def ensure_directory_exists(path):
    """Ensure a directory exists, create if it doesn't"""
    os.makedirs(path, exist_ok=True)


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)