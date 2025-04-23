import sys
import os
import logging
import streamlit as st

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Thêm thư mục gốc vào sys.path để có thể import các module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import các trang
from webpages.market_overview import show_market_overview
from webpages.price_prediction import show_price_prediction
from webpages.bike_comparison import show_bike_comparison
from webpages.bike_suggestion import show_bike_suggestion

# Import cấu hình
from config import check_database


def main():
    """Hàm chính của ứng dụng Streamlit"""

    # Cấu hình trang
    st.set_page_config(
        page_title="Dự Đoán Giá Xe Máy Cũ",
        page_icon="🏍️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Load CSS tùy chỉnh
    def load_css():
        css_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "static", "styles", "main.css"
        )
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        else:
            st.warning(f"Không tìm thấy file CSS: {css_path}")

    try:
        load_css()
    except Exception as e:
        st.warning(f"Không thể tải CSS: {str(e)}")

    # Kiểm tra database trước
    check_database()

    # Hiển thị Dự đoán giá xe
    show_price_prediction()

    # Tạm bỏ sidebar
    # # Sidebar
    # st.sidebar.title("🏍️ Dự Đoán Giá Xe Máy Cũ")
    # page = st.sidebar.radio(
    #     "Chọn trang:",
    #     [
    #         "Dự đoán giá xe",
    #         # "Tổng quan thị trường",
    #         # "So sánh xe",
    #         # "Gợi ý mua xe"
    #     ]
    # )

    # # Điều hướng trang
    # if page == "Tổng quan thị trường":
    #     show_market_overview()
    # elif page == "Dự đoán giá xe":
    #     show_price_prediction()
    # elif page == "So sánh xe":
    #     show_bike_comparison()
    # elif page == "Gợi ý mua xe":
    #     show_bike_suggestion()

    # Thêm footer
    st.markdown(
        '<div class="footer">Ứng dụng dự đoán giá xe máy cũ © 2025</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
