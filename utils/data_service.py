import streamlit as st
import sqlite3
import pandas as pd
import logging
import os
import requests
import json
import re
from config import DB_PATH

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cố gắng tải biến môi trường từ .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
except Exception as e:
    logger.warning(f"Không thể tải biến môi trường: {str(e)}")
    CLAUDE_API_KEY = None

# Thiết lập logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Kết nối đến database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Lỗi kết nối database: {str(e)}")
        raise Exception(f"Database connection error: {str(e)}")

@st.cache_data(ttl=3600)  # Cache 1 giờ
def get_similar_listings(predicted_price, brand=None, model=None, year=None, mileage=None, 
                         condition=None, origin=None):
    """
    Lấy danh sách bài đăng có giá gần với giá dự đoán từ database
    
    Args:
        predicted_price: Giá dự đoán (VND)
        brand: Thương hiệu xe (tùy chọn)
        model: Mẫu xe (tùy chọn)
        year: Năm sản xuất (tùy chọn)
        mileage: Số km đã đi (tùy chọn)
        condition: Tình trạng xe (tùy chọn)
        origin: Xuất xứ (tùy chọn)
        
    Returns:
        DataFrame chứa thông tin các bài đăng tương tự
    """
    try:
        conn = get_db_connection()
        
        # Xây dựng truy vấn SQL với điều kiện
        query = """
        SELECT 
            *,
            ABS(price_numeric - ?) AS price_diff,
            ((price_numeric - ?) / ? * 100) AS price_diff_percent
        FROM 
            motorbikes
        WHERE 
            1=1
        """
        
        # Danh sách tham số cho truy vấn
        params = [predicted_price, predicted_price, predicted_price]
        
        # Thêm điều kiện lọc theo brand
        if brand:
            query += " AND LOWER(brand) LIKE LOWER(?)"
            params.append(f"%{brand}%")
        
        # Thêm điều kiện lọc theo model
        if model:
            query += " AND LOWER(model_normalized) LIKE LOWER(?)"
            params.append(f"%{model}%")
        
   
        # Sắp xếp theo khoảng cách giá và thời gian đăng (nếu có)
        query += " ORDER BY price_diff ASC"
        if "post_date" in [col[0] for col in conn.execute("PRAGMA table_info(motorbikes)").fetchall()]:
            query += ", post_date DESC"
        elif "days_since_posted" in [col[0] for col in conn.execute("PRAGMA table_info(motorbikes)").fetchall()]:
            query += ", days_since_posted ASC"
        
        # Thực thi truy vấn
        logger.info(f"Executing query: {query}")
        logger.info(f"With parameters: {params}")
        
        # Sử dụng pandas để đọc kết quả truy vấn
        similar_listings = pd.read_sql_query(query, conn, params=params)
        
        # Đóng kết nối
        conn.close()
        
        # Xử lý kết quả
        if not similar_listings.empty:
            # Định dạng phần trăm chênh lệch giá
            similar_listings["price_diff_percent"] = similar_listings["price_diff_percent"].round(1)
            
            # Định dạng ngày đăng nếu có
            if "post_date" in similar_listings.columns:
                # Chuyển sang datetime nếu là chuỗi
                if similar_listings["post_date"].dtype == 'object':
                    similar_listings["post_date"] = pd.to_datetime(
                        similar_listings["post_date"], errors='coerce'
                    )
                # Định dạng ngày đăng thành chuỗi dễ đọc
                similar_listings["post_date_display"] = similar_listings["post_date"].dt.strftime("%d/%m/%Y")
            
            # Tạo URL đầy đủ nếu chưa có
            if "url" in similar_listings.columns and "url_full" not in similar_listings.columns:
                similar_listings["url_full"] = similar_listings["url"].apply(
                    lambda url: f"https://xe.chotot.com{url}" if url and not url.startswith(('http://', 'https://')) else url
                )
        
        logger.info(f"Tìm thấy {len(similar_listings)} bài đăng tương tự")
        return similar_listings
    
    except Exception as e:
        logger.error(f"Lỗi khi lấy danh sách bài đăng tương tự: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return pd.DataFrame()
    
@st.cache_data(ttl=3600)  # Cache 1 giờ
def get_brands():
    """Lấy danh sách thương hiệu từ database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT brand FROM motorbikes")
        brands = [row[0] for row in cursor.fetchall()]
        conn.close()
        return brands
    except Exception as e:
        logger.error(f"Lỗi khi lấy danh sách thương hiệu: {str(e)}")
        st.error(f"Không thể lấy danh sách thương hiệu: {str(e)}")
        return []

@st.cache_data(ttl=3600)  # Cache 1 giờ
def get_models(brand):
    """Lấy danh sách mẫu xe theo thương hiệu từ database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT model_normalized FROM motorbikes WHERE brand = ?", (brand,))
        models = [row[0] for row in cursor.fetchall()]
        conn.close()
        return models
    except Exception as e:
        logger.error(f"Lỗi khi lấy danh sách mẫu xe: {str(e)}")
        st.error(f"Không thể lấy danh sách mẫu xe cho {brand}: {str(e)}")
        return []

# @st.cache_data(ttl=3600)  # Cache 1 giờ
# def get_variants(brand, model):
#     """Lấy danh sách phiên bản theo thương hiệu và mẫu xe từ database"""
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute(
#             "SELECT DISTINCT variant FROM motorbikes WHERE brand = ? AND model = ?", 
#             (brand, model)
#         )
#         variants = [row[0] for row in cursor.fetchall()]
#         conn.close()
#         return variants
#     except Exception as e:
#         logger.error(f"Lỗi khi lấy danh sách phiên bản: {str(e)}")
#         st.error(f"Không thể lấy danh sách phiên bản cho {brand} {model}: {str(e)}")
#         return []
    
@st.cache_data(ttl=3600)  # Cache 1 giờ
def load_market_data():
    """Lấy dữ liệu thị trường từ database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                brand as 'Thương hiệu',
                COUNT(*) as 'Số lượng giao dịch',
                ROUND(AVG(price_numeric), 1) as 'Giá trung bình (triệu VND)'
            FROM motorbikes
            GROUP BY brand
            ORDER BY COUNT(*) DESC
        """)
        
        # Chuyển kết quả thành list of dicts
        market_data = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return pd.DataFrame(market_data)
    except Exception as e:
        logger.error(f"Lỗi khi truy vấn database để lấy dữ liệu thị trường: {str(e)}")
        st.error(f"Không thể tải dữ liệu thị trường: {str(e)}")
        # Trả về DataFrame trống
        return pd.DataFrame(columns=['Thương hiệu', 'Số lượng giao dịch', 'Giá trung bình (triệu VND)'])

def analyze_image(img_str):
    """
    Phân tích ảnh để trích xuất thông tin xe máy
    
    Args:
        img_str (str): Chuỗi base64 của hình ảnh
        
    Returns:
        dict: Thông tin xe được trích xuất từ ảnh
    """
    # Kiểm tra xem có CLAUDE_API_KEY không
    if not CLAUDE_API_KEY:
        error_msg = "Chức năng phân tích ảnh cần API key Claude. Vui lòng cấu hình trong file .env"
        logger.error(error_msg)
        st.error(error_msg)
        raise ValueError(error_msg)
    
    # Tiếp tục nếu có API key
    try:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        # Tạo payload với hình ảnh base64
        payload = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Đây là ảnh một chiếc xe máy. Hãy phân tích và cung cấp thông tin chi tiết về xe, bao gồm: thương hiệu, mẫu xe, năm sản xuất ước tính, dung tích động cơ, và tình trạng xe. Trả về kết quả dưới dạng JSON với các key sau: brand, model, year, cc, condition, và các thông tin khác nếu có."
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img_str
                            }
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(CLAUDE_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # Trích xuất và phân tích phản hồi từ Claude
        try:
            content = result.get('content', [{}])[0].get('text', '{}')
            # Tìm và trích xuất phần JSON
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content
            
            # Cố gắng parse JSON
            parsed_result = json.loads(json_str)
            
            # Chuẩn hóa keys
            normalized_result = {
                "brand": parsed_result.get("brand", parsed_result.get("Thương hiệu", "Unknown")),
                "model": parsed_result.get("model", parsed_result.get("Mẫu xe", "Unknown")),
                "year": parsed_result.get("year", parsed_result.get("Năm sản xuất", 2020)),
                "cc": parsed_result.get("cc", parsed_result.get("Dung tích động cơ", "Unknown")),
                "condition": parsed_result.get("condition", parsed_result.get("Tình trạng xe", "Tốt")),
                "confidence": 0.9  # Độ tin cậy cao vì dùng Claude
            }
            
            return normalized_result
            
        except Exception as parse_error:
            error_msg = f"Lỗi khi phân tích kết quả từ Claude: {str(parse_error)}"
            logger.error(error_msg)
            st.error(error_msg)
            raise ValueError(error_msg)
            
    except Exception as e:
        error_msg = f"Lỗi khi gọi API Claude để phân tích ảnh: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        raise ValueError(error_msg)

def analyze_description(description_text):
    """
    Phân tích mô tả để trích xuất thông tin xe máy
    
    Args:
        description_text (str): Mô tả về xe máy
        
    Returns:
        dict: Thông tin xe được trích xuất từ mô tả
    """
    # Kiểm tra xem có CLAUDE_API_KEY không
    if not CLAUDE_API_KEY:
        error_msg = "Chức năng phân tích mô tả cần API key Claude. Vui lòng cấu hình trong file .env"
        logger.error(error_msg)
        st.error(error_msg)
        raise ValueError(error_msg)
    
    # Tiếp tục nếu có API key
    try:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        # Tạo payload với mô tả
        payload = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Đây là mô tả về một chiếc xe máy: '{description_text}'. Hãy phân tích và cung cấp thông tin chi tiết về xe, bao gồm: thương hiệu, mẫu xe, năm sản xuất, dung tích động cơ, số km đã đi, và tình trạng xe. Trả về kết quả dưới dạng JSON với các key sau: brand, model, year, cc, km_driven, condition, và các thông tin khác nếu có."
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(CLAUDE_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # Trích xuất và phân tích phản hồi từ Claude
        try:
            content = result.get('content', [{}])[0].get('text', '{}')
            # Tìm và trích xuất phần JSON
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content
            
            # Cố gắng parse JSON
            parsed_result = json.loads(json_str)
            
            # Chuẩn hóa keys
            normalized_result = {
                "brand": parsed_result.get("brand", parsed_result.get("Thương hiệu", "Unknown")),
                "model": parsed_result.get("model", parsed_result.get("Mẫu xe", "Unknown")),
                "year": parsed_result.get("year", parsed_result.get("Năm sản xuất", 2020)),
                "cc": parsed_result.get("cc", parsed_result.get("Dung tích động cơ", "Unknown")),
                "km_driven": parsed_result.get("km_driven", parsed_result.get("Số km đã đi", 15000)),
                "condition": parsed_result.get("condition", parsed_result.get("Tình trạng xe", "Tốt")),
                "confidence": 0.8  # Độ tin cậy cao vì dùng Claude
            }
            
            return normalized_result
            
        except Exception as parse_error:
            error_msg = f"Lỗi khi phân tích kết quả từ Claude: {str(parse_error)}"
            logger.error(error_msg)
            st.error(error_msg)
            raise ValueError(error_msg)
            
    except Exception as e:
        error_msg = f"Lỗi khi gọi API Claude để phân tích mô tả: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        raise ValueError(error_msg)
