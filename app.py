# app.py - File chính cho Streamlit
import streamlit as st
import os
import sys

# Thêm thư mục gốc vào sys.path để có thể import các module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import các trang
from webpages.market_overview import show_market_overview
from webpages.price_prediction import show_price_prediction
from webpages.bike_comparison import show_bike_comparison
from webpages.bike_suggestion import show_bike_suggestion

# Import cấu hình và dịch vụ
from config import check_database, check_api_connection

# Cấu hình trang
st.set_page_config(
    page_title="Dự Đoán Giá Xe Máy Cũ",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS tùy chỉnh
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'styles', 'main.css')
    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    else:
        st.warning(f"Không tìm thấy file CSS: {css_path}")

try:
    load_css()
except Exception as e:
    st.warning(f"Không thể tải CSS: {str(e)}")

# Kiểm tra database trước
check_database()

# Kiểm tra kết nối API
api_status, api_message, _ = check_api_connection()
if not api_status:
    # Nếu API không hoạt động, thông báo sẽ dùng database trực tiếp
    st.warning(f"Không thể kết nối đến API: {api_message}")
    st.info("Ứng dụng sẽ sử dụng database trực tiếp thay vì thông qua API.")
else:
    st.success(f"Kết nối API thành công: {api_message}")

# Sidebar
st.sidebar.title("🏍️ Dự Đoán Giá Xe Máy Cũ")
page = st.sidebar.radio(
    "Chọn trang:",
    ["Tổng quan thị trường", "Dự đoán giá xe", "So sánh xe", "Gợi ý mua xe"]
)

# Điều hướng trang
if page == "Tổng quan thị trường":
    show_market_overview()
elif page == "Dự đoán giá xe":
    show_price_prediction()
elif page == "So sánh xe":
    show_bike_comparison()
elif page == "Gợi ý mua xe":
    show_bike_suggestion()

# Thêm footer
def add_footer():
    st.markdown('<div class="footer">Ứng dụng dự đoán giá xe máy cũ © 2025</div>', unsafe_allow_html=True)

# Thêm footer vào cuối trang
add_footer()

if __name__ == "__main__":
    st.markdown(f'<div class="info-box">Ứng dụng đang chạy trên Streamlit.</div>', unsafe_allow_html=True)