import os
import sys

# Thêm thư mục gốc vào sys.path để có thể import các module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api import create_app
from config import API_PORT

def main():
    """Hàm chính của Flask API"""
    # Khởi tạo ứng dụng Flask
    app = create_app()
    
    # Thông báo
    print(f"Khởi động Flask API ở cổng {API_PORT}...")
    print(f"Truy cập http://localhost:{API_PORT}/api/test để kiểm tra API")
    
    # Chạy ứng dụng
    app.run(debug=False, port=API_PORT, host='0.0.0.0')

if __name__ == '__main__':
    main()