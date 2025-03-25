# flask_app.py
import os
import sys

# Thêm thư mục gốc vào sys.path để có thể import các module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api import create_app

if __name__ == '__main__':
    app = create_app()
    port = 5001
    print(f"Khởi động Flask API ở cổng {port}...")
    print(f"Truy cập http://localhost:{port}/api/test để kiểm tra API")
    app.run(debug=True, port=port, host='0.0.0.0')