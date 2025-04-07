# utils/__init__.py
# File khởi tạo cho package utils
import os
import sys

# Thêm thư mục gốc vào sys.path để có thể import các module khác
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)