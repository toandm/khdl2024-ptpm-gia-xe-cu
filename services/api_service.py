# services/api_service.py - Dịch vụ gọi API
import requests
import streamlit as st
import base64
from config import API_BASE_URL

def analyze_image(img_str):
    """Gọi API để phân tích ảnh"""
    try:
        response = requests.post(f"{API_BASE_URL}/analyze-image", json={"image": img_str})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Lỗi khi gọi API phân tích ảnh: {str(e)}")
        # Trả về dữ liệu giả lập nếu có lỗi
        return {
            "Thương hiệu": "Honda",
            "Mẫu xe": "Wave RSX 110",
            "Năm sản xuất": "Khoảng 2018-2020",
            "Dung tích động cơ": "110cc",
            "Tình trạng xe": "Khá tốt, có một số vết xước nhỏ"
        }

def analyze_description(description_text):
    """Gọi API để phân tích mô tả"""
    try:
        response = requests.post(f"{API_BASE_URL}/analyze-description", json={"description": description_text})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Lỗi khi gọi API phân tích mô tả: {str(e)}")
        # Trả về dữ liệu giả lập nếu có lỗi
        return {
            "Thương hiệu": "Honda",
            "Mẫu xe": "Wave RSX",
            "Năm sản xuất": "2019",
            "Dung tích động cơ": "110cc",
            "Số km đã đi": "Khoảng 20,000 km",
            "Màu sắc": "Đỏ đen",
            "Đặc điểm": "Phanh đĩa trước, bảo dưỡng định kỳ"
        }

def get_brands_api():
    """Lấy danh sách thương hiệu từ API"""
    try:
        response = requests.get(f"{API_BASE_URL}/brands")
        response.raise_for_status()
        brands_data = response.json()
        return [brand['value'] for brand in brands_data]
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách thương hiệu từ API: {str(e)}")
        return ["Honda", "Yamaha", "Suzuki", "Piaggio", "SYM"]

def get_models_api(brand):
    """Lấy danh sách mẫu xe theo thương hiệu từ API"""
    try:
        response = requests.get(f"{API_BASE_URL}/models/{brand}")
        response.raise_for_status()
        models_data = response.json()
        return [model['value'] for model in models_data]
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách mẫu xe từ API: {str(e)}")
        return []

def get_variants_api(brand, model):
    """Lấy danh sách phiên bản theo thương hiệu và mẫu xe từ API"""
    try:
        response = requests.get(f"{API_BASE_URL}/variants/{brand}/{model}")
        response.raise_for_status()
        variants_data = response.json()
        return [variant['value'] for variant in variants_data]
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách phiên bản từ API: {str(e)}")
        return []

def get_prediction_api(payload):
    """Gọi API để dự đoán giá"""
    try:
        response = requests.post(f"{API_BASE_URL}/predict", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Lỗi khi dự đoán giá từ API: {str(e)}")
        raise e