# pages/market_overview.py
import streamlit as st
import pandas as pd
from utils.data_service import load_market_data
from utils.visualization import create_market_overview, create_price_trend
from config import get_db_connection

def get_market_stats():
    """Lấy thống kê thị trường từ database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tổng số xe
        cursor.execute("SELECT COUNT(*) as total FROM motorbikes")
        total_count = cursor.fetchone()['total']
        
        # Giá trung bình
        cursor.execute("SELECT ROUND(AVG(avg_price_used), 1) as avg_price FROM motorbikes")
        avg_price = cursor.fetchone()['avg_price']
        
        # Chênh lệch giá
        cursor.execute("""
            SELECT ROUND((AVG(price_new) - AVG(avg_price_used)) / AVG(price_new) * 100, 1) as price_diff 
            FROM motorbikes
        """)
        price_diff = cursor.fetchone()['price_diff']
        
        conn.close()
        
        return total_count, avg_price, price_diff
    except Exception as e:
        st.error(f"Lỗi khi lấy thống kê thị trường: {str(e)}")
        return 3000, 27, 12

@st.cache_data
def get_detailed_market_data():
    """Lấy dữ liệu chi tiết thị trường từ database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                brand as 'Thương hiệu',
                model as 'Mẫu xe',
                variant as 'Phiên bản',
                segment as 'Phân khúc',
                engine_cc as 'Dung tích (cc)',
                price_new as 'Giá mới (triệu)',
                avg_price_used as 'Giá cũ TB (triệu)'
            FROM motorbikes
            ORDER BY brand, model, variant
        """)
        
        detailed_data = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return pd.DataFrame(detailed_data)
    except Exception as e:
        st.error(f"Lỗi khi lấy dữ liệu chi tiết: {str(e)}")
        return pd.DataFrame()

def show_market_overview():
    """Hiển thị trang tổng quan thị trường"""
    st.markdown('<div class="main-header">Tổng quan thị trường xe máy cũ</div>', unsafe_allow_html=True)
    
    # Load dữ liệu thị trường
    market_data = load_market_data()
    
    # Sử dụng dữ liệu market_data để tính toán
    total_count = market_data['Số lượng giao dịch'].sum()
    avg_price = round(market_data['Giá trung bình (triệu VND)'].mean(), 1)
    price_diff = round(market_data['Chênh lệch giá (%)'].mean(), 1)
    
    # Hiển thị các số liệu tổng quan
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Số lượng xe", f"{total_count:,}", "+5%")
    with col2:
        st.metric("Giá trung bình", f"{avg_price} triệu VND", "+2%")
    with col3:
        st.metric("Chênh lệch giá", f"{price_diff}%", "-1%")
    
    # Hiển thị biểu đồ thị trường
    st.markdown('<div class="sub-header">Phân tích thị trường theo thương hiệu</div>', unsafe_allow_html=True)
    market_chart = create_market_overview(market_data)
    st.pyplot(market_chart)
    
    # Hiển thị xu hướng giá
    st.markdown('<div class="sub-header">Xu hướng giá trong 12 tháng qua</div>', unsafe_allow_html=True)
    trend_chart = create_price_trend()
    st.pyplot(trend_chart)
    
    # Hiển thị bảng dữ liệu chi tiết
    st.markdown('<div class="sub-header">Dữ liệu thị trường chi tiết</div>', unsafe_allow_html=True)
    detailed_data = get_detailed_market_data()
    st.dataframe(detailed_data)