import os
import sqlite3
import streamlit as st

# Đường dẫn database
DB_PATH = os.path.join('data', 'motorbike_database.db')

# Đường dẫn đến model
MODEL_PATH = os.path.join('models', 'rf.pkl')

# Hàm kết nối trực tiếp đến database
def get_db_connection():
    """Kết nối đến database với đường dẫn tuyệt đối"""
    db_path = os.path.abspath(DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Kiểm tra database trước khi chạy ứng dụng
def check_database():
    """Kiểm tra xem database có tồn tại không"""
    if not os.path.exists(DB_PATH):
        st.error(f"Không tìm thấy database '{DB_PATH}'. Vui lòng tạo database trước khi chạy ứng dụng.")
        return False
    return True

# Kiểm tra model tồn tại
def check_model():
    """Kiểm tra xem model có tồn tại không"""
    if not os.path.exists(MODEL_PATH):
        st.warning(f"Không tìm thấy model tại '{MODEL_PATH}'.")
        return False
    return True