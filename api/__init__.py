# api/__init__.py
import os
import sys

# Thêm thư mục gốc vào sys.path để có thể import các module khác
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from flask import Flask
from flask_cors import CORS  # Thêm import này

def create_app():
    """Tạo và cấu hình Flask app"""
    app = Flask(__name__)
    CORS(app)  # Cho phép CORS
    
    # Đăng ký blueprint API
    from api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Định nghĩa route chính
    @app.route('/')
    def home():
        return "API cho dự đoán giá xe máy cũ đang hoạt động. Truy cập /api/test để kiểm tra."
    
    return app