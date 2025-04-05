# utils/api_service.py - Dịch vụ gọi API
import requests
import streamlit as st
from config import API_BASE_URL

def analyze_image(img_str):
    """Gọi API để phân tích ảnh"""
    try:
        response = requests.post(f"{API_BASE_URL}/analyze-image", json={"image": img_str}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("Phân tích ảnh bị quá thời gian. Vui lòng thử lại sau.")
        raise Exception("API timeout")
    except requests.exceptions.ConnectionError:
        st.error(f"Không thể kết nối đến API tại {API_BASE_URL}. Vui lòng kiểm tra kết nối.")
        raise Exception("API connection error")
    except requests.exceptions.HTTPError as e:
        st.error(f"Lỗi HTTP khi gọi API phân tích ảnh: {e.response.status_code}")
        raise Exception(f"HTTP error: {e.response.status_code}")
    except Exception as e:
        st.error(f"Lỗi khi gọi API phân tích ảnh: {str(e)}")
        raise Exception(f"API error: {str(e)}")

def analyze_description(description_text):
    """Gọi API để phân tích mô tả"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze-description", 
            json={"description": description_text},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("Phân tích mô tả bị quá thời gian. Vui lòng thử lại sau.")
        raise Exception("API timeout")
    except requests.exceptions.ConnectionError:
        st.error(f"Không thể kết nối đến API tại {API_BASE_URL}. Vui lòng kiểm tra kết nối.")
        raise Exception("API connection error")
    except requests.exceptions.HTTPError as e:
        st.error(f"Lỗi HTTP khi gọi API phân tích mô tả: {e.response.status_code}")
        raise Exception(f"HTTP error: {e.response.status_code}")
    except Exception as e:
        st.error(f"Lỗi khi gọi API phân tích mô tả: {str(e)}")
        raise Exception(f"API error: {str(e)}")

def get_brands_api():
    """Lấy danh sách thương hiệu từ API"""
    try:
        response = requests.get(f"{API_BASE_URL}/brands", timeout=5)
        response.raise_for_status()
        brands_data = response.json()
        return [brand['value'] for brand in brands_data]
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách thương hiệu từ API: {str(e)}")
        raise Exception(f"API error: {str(e)}")

def get_models_api(brand):
    """Lấy danh sách mẫu xe theo thương hiệu từ API"""
    try:
        response = requests.get(f"{API_BASE_URL}/models/{brand}", timeout=5)
        response.raise_for_status()
        models_data = response.json()
        return [model['value'] for model in models_data]
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách mẫu xe từ API: {str(e)}")
        raise Exception(f"API error: {str(e)}")

def get_variants_api(brand, model):
    """Lấy danh sách phiên bản theo thương hiệu và mẫu xe từ API"""
    try:
        response = requests.get(f"{API_BASE_URL}/variants/{brand}/{model}", timeout=5)
        response.raise_for_status()
        variants_data = response.json()
        return [variant['value'] for variant in variants_data]
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách phiên bản từ API: {str(e)}")
        raise Exception(f"API error: {str(e)}")

def get_prediction_api(payload):
    """Gọi API để dự đoán giá"""
    try:
        response = requests.post(f"{API_BASE_URL}/predict", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("Dự đoán giá bị quá thời gian. Vui lòng thử lại sau.")
        raise Exception("API timeout")
    except requests.exceptions.ConnectionError:
        st.error(f"Không thể kết nối đến API tại {API_BASE_URL}. Vui lòng kiểm tra kết nối.")
        raise Exception("API connection error")
    except requests.exceptions.HTTPError as e:
        st.error(f"Lỗi HTTP khi dự đoán giá: {e.response.status_code}")
        raise Exception(f"HTTP error: {e.response.status_code}")
    except Exception as e:
        st.error(f"Lỗi khi dự đoán giá từ API: {str(e)}")
        raise Exception(f"API error: {str(e)}")