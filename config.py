# config.py - Cấu hình chung cho ứng dụng
import os
import sqlite3
import requests
import streamlit as st

# Cấu hình API endpoint
API_PORT = 5001  # Thay đổi port ở đây nếu cần
API_BASE_URL = f"http://localhost:{API_PORT}/api"

# Biến toàn cục để quyết định sử dụng API hay truy vấn trực tiếp database
use_direct_db = False

# Hàm kết nối trực tiếp đến database
def get_db_connection():
    conn = sqlite3.connect('motorbike_database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Kiểm tra database trước khi chạy ứng dụng
def check_database():
    if not os.path.exists('motorbike_database.db'):
        st.error("Không tìm thấy database 'motorbike_database.db'. Vui lòng tạo database trước khi chạy ứng dụng.")
        st.stop()

# Kiểm tra kết nối với API
def check_api_connection():
    """Kiểm tra kết nối với API"""
    global use_direct_db
    try:
        response = requests.get(f"{API_BASE_URL}/test", timeout=5)
        if response.status_code == 200:
            use_direct_db = False
            return True, "API đang hoạt động bình thường", False
        else:
            use_direct_db = True
            return False, f"API trả về mã lỗi: {response.status_code}", True
    except requests.exceptions.ConnectionError:
        use_direct_db = True
        return False, f"Không thể kết nối đến API tại {API_BASE_URL}", True
    except Exception as e:
        use_direct_db = True
        return False, f"Lỗi khi kiểm tra API: {str(e)}", True