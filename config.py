import os
import sqlite3
import streamlit as st
import requests

# Cấu hình API endpoint
API_PORT = 5001
API_BASE_URL = f"http://localhost:{API_PORT}/api"

# Biến toàn cục để quyết định sử dụng API hay truy vấn trực tiếp database
use_direct_db = False

# Đường dẫn database
DB_PATH = os.path.join('data', 'motorbike_database.db')

# Hàm kết nối trực tiếp đến database
def get_db_connection():
    """Kết nối đến database với đường dẫn tuyệt đối"""
    db_path = os.path.abspath(DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Kiểm tra database trước khi chạy ứng dụng
def check_database():
    if not os.path.exists(DB_PATH):
        st.error(f"Không tìm thấy database '{DB_PATH}'. Vui lòng tạo database trước khi chạy ứng dụng.")
        st.stop()