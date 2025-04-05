# utils/data_service.py - Dịch vụ truy xuất dữ liệu (API hoặc DB)
import streamlit as st
from config import use_direct_db
import pandas as pd
import requests
from config import API_BASE_URL
import logging

# Import các service
from utils.api_service import get_brands_api, get_models_api, get_variants_api, get_prediction_api
from utils.db_service import get_brands_db, get_models_db, get_variants_db, get_prediction_db, get_market_data_db

@st.cache_data(ttl=3600)  # Cache 1 giờ
def get_brands():
    """Lấy danh sách thương hiệu từ API hoặc database"""
    try:
        if use_direct_db:
            return get_brands_db()
        else:
            return get_brands_api()
    except Exception as e:
        logging.error(f"Lỗi khi lấy thương hiệu: {str(e)}")
        st.error("Không thể lấy danh sách thương hiệu. Vui lòng làm mới trang và thử lại.")
        return []

@st.cache_data(ttl=3600)  # Cache 1 giờ
def get_models(brand):
    """Lấy danh sách mẫu xe theo thương hiệu từ API hoặc database"""
    try:
        if use_direct_db:
            return get_models_db(brand)
        else:
            return get_models_api(brand)
    except Exception as e:
        logging.error(f"Lỗi khi lấy mẫu xe: {str(e)}")
        st.error(f"Không thể lấy danh sách mẫu xe cho {brand}. Vui lòng thử lại sau.")
        return []

@st.cache_data(ttl=3600)  # Cache 1 giờ
def get_variants(brand, model):
    """Lấy danh sách phiên bản theo thương hiệu và mẫu xe từ API hoặc database"""
    try:
        if use_direct_db:
            return get_variants_db(brand, model)
        else:
            return get_variants_api(brand, model)
    except Exception as e:
        logging.error(f"Lỗi khi lấy phiên bản: {str(e)}")
        st.error(f"Không thể lấy danh sách phiên bản cho {brand} {model}. Vui lòng thử lại sau.")
        return []

def get_prediction(payload):
    """Dự đoán giá từ API hoặc database"""
    try:
        if use_direct_db:
            return get_prediction_db(payload)
        else:
            return get_prediction_api(payload)
    except Exception as e:
        logging.error(f"Lỗi khi dự đoán giá: {str(e)}")
        st.error("Không thể dự đoán giá với các thông số đã nhập. Vui lòng kiểm tra lại thông tin và thử lại.")
        return {
            "error": str(e),
            "price": None,
            "price_range": None,
            "confidence": None
        }

@st.cache_data(ttl=3600)  # Cache 1 giờ
def load_market_data():
    """Lấy dữ liệu thị trường từ API hoặc database"""
    try:
        if use_direct_db:
            market_data = get_market_data_db()
            return pd.DataFrame(market_data)
        else:
            try:
                # Thử lấy dữ liệu từ API
                response = requests.get(f"{API_BASE_URL}/market-data", timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Chuyển đổi dữ liệu thành DataFrame
                market_data = []
                for brand, values in data['brands'].items():
                    market_data.append({
                        'Thương hiệu': brand,
                        'Số lượng giao dịch': values['count'],
                        'Giá trung bình (triệu VND)': values['avg_price'],
                        'Chênh lệch giá (%)': values['price_diff']
                    })
                return pd.DataFrame(market_data)
            except Exception as e:
                st.warning(f"Không thể lấy dữ liệu thị trường từ API: {str(e)}")
                logging.warning(f"Chuyển từ API sang DB vì lỗi: {str(e)}")
                # Fallback to direct DB
                market_data = get_market_data_db()
                return pd.DataFrame(market_data)
    except Exception as e:
        logging.error(f"Lỗi khi lấy dữ liệu thị trường: {str(e)}")
        st.error("Không thể tải dữ liệu thị trường. Vui lòng làm mới trang và thử lại.")
        # Trả về DataFrame trống thay vì dữ liệu mẫu
        return pd.DataFrame(columns=['Thương hiệu', 'Số lượng giao dịch', 'Giá trung bình (triệu VND)', 'Chênh lệch giá (%)'])