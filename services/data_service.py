# services/data_service.py - Dịch vụ truy xuất dữ liệu (API hoặc DB)
import streamlit as st
from config import use_direct_db
import pandas as pd
from services.api_service import get_brands_api, get_models_api, get_variants_api, get_prediction_api
from services.db_service import get_brands_db, get_models_db, get_variants_db, get_prediction_db, get_market_data_db

@st.cache_data
def get_brands():
    """Lấy danh sách thương hiệu từ API hoặc database"""
    if use_direct_db:
        return get_brands_db()
    else:
        return get_brands_api()

@st.cache_data
def get_models(brand):
    """Lấy danh sách mẫu xe theo thương hiệu từ API hoặc database"""
    if use_direct_db:
        return get_models_db(brand)
    else:
        return get_models_api(brand)

@st.cache_data
def get_variants(brand, model):
    """Lấy danh sách phiên bản theo thương hiệu và mẫu xe từ API hoặc database"""
    if use_direct_db:
        return get_variants_db(brand, model)
    else:
        return get_variants_api(brand, model)

def get_prediction(payload):
    """Dự đoán giá từ API hoặc database"""
    if use_direct_db:
        return get_prediction_db(payload)
    else:
        return get_prediction_api(payload)

@st.cache_data
def load_market_data():
    """Lấy dữ liệu thị trường từ API hoặc database"""
    if use_direct_db:
        market_data = get_market_data_db()
        return pd.DataFrame(market_data)
    else:
        try:
            # Thử lấy dữ liệu từ API
            import requests
            from config import API_BASE_URL
            
            response = requests.get(f"{API_BASE_URL}/market-data")
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
            # Fallback to direct DB
            market_data = get_market_data_db()
            return pd.DataFrame(market_data)