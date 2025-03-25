# services/db_service.py - Dịch vụ truy vấn database
import streamlit as st
from config import get_db_connection

def get_brands_db():
    """Lấy danh sách thương hiệu từ database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT brand FROM motorbikes ORDER BY brand")
        brands = [row[0] for row in cursor.fetchall()]
        conn.close()
        return brands
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách thương hiệu: {str(e)}")
        return ["Honda", "Yamaha", "Suzuki", "Piaggio", "SYM"]

def get_models_db(brand):
    """Lấy danh sách mẫu xe theo thương hiệu từ database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT model FROM motorbikes WHERE brand = ? ORDER BY model", (brand,))
        models = [row[0] for row in cursor.fetchall()]
        conn.close()
        return models
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách mẫu xe: {str(e)}")
        return []

def get_variants_db(brand, model):
    """Lấy danh sách phiên bản theo thương hiệu và mẫu xe từ database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT variant FROM motorbikes WHERE brand = ? AND model = ? ORDER BY variant", (brand, model))
        variants = [row[0] for row in cursor.fetchall()]
        conn.close()
        return variants
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách phiên bản: {str(e)}")
        return []

def get_prediction_db(payload):
    """Dự đoán giá từ database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        brand = payload.get('brand')
        model = payload.get('model')
        variant = payload.get('variant')
        
        if variant:
            # Nếu có variant cụ thể
            cursor.execute("""
                SELECT * FROM motorbikes 
                WHERE brand = ? AND model = ? AND variant = ?
                LIMIT 1
            """, (brand, model, variant))
            motorbike = cursor.fetchone()
        else:
            # Nếu không có variant cụ thể, lấy tất cả các variants và tính trung bình
            cursor.execute("""
                SELECT 
                    brand, model, 
                    AVG(engine_cc) as engine_cc, 
                    MIN(year_start) as year_start,
                    AVG(avg_price_used) as avg_price_used
                FROM motorbikes
                WHERE brand = ? AND model = ?
                GROUP BY brand, model
            """, (brand, model))
            motorbike = cursor.fetchone()
        
        conn.close()
        
        if motorbike:
            # Tính toán giá dựa trên thông tin từ database
            motorbike_dict = dict(motorbike)
            
            db_price = float(motorbike_dict['avg_price_used'])
            year = payload.get('year', 2020)
            year_diff = year - motorbike_dict['year_start'] if year > 0 else 0
            
            # Điều chỉnh giá dựa trên năm sản xuất (giảm 5% mỗi năm)
            if year_diff < 0:
                year_diff = 0
            price = db_price * (0.95 ** year_diff)
            
            # Điều chỉnh theo số km đã đi (giảm 1% cho mỗi 10,000 km)
            km_driven = payload.get('km_driven', 15000)
            km_factor = 1 - (km_driven / 10000) * 0.01
            price = price * km_factor
            
            # Điều chỉnh theo tình trạng xe
            condition = payload.get('condition', 'Tốt')
            condition_factors = {
                "Rất kém": 0.7,
                "Kém": 0.8,
                "Trung bình": 0.9,
                "Tốt": 1.0,
                "Rất tốt": 1.1
            }
            condition_factor = condition_factors.get(condition, 1.0)
            price = price * condition_factor
            
            # Làm tròn giá
            final_price = round(price, 1)
            
            return {
                "price": final_price,
                "price_range": [round(final_price * 0.9, 1), round(final_price * 1.1, 1)],
                "confidence": 0.85 if variant else 0.75  # Giảm độ tin cậy nếu không chọn variant cụ thể
            }
        else:
            return {
                "error": f"Không tìm thấy thông tin xe {brand} {model} trong database",
                "price": 0,
                "price_range": [0, 0],
                "confidence": 0
            }
    except Exception as e:
        st.error(f"Lỗi khi dự đoán giá từ database: {str(e)}")
        raise e

def get_market_data_db():
    """Lấy dữ liệu thị trường từ database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                brand as 'Thương hiệu',
                COUNT(*) as 'Số lượng giao dịch',
                ROUND(AVG(avg_price_used), 1) as 'Giá trung bình (triệu VND)',
                ROUND((AVG(price_new) - AVG(avg_price_used)) / AVG(price_new) * 100, 1) as 'Chênh lệch giá (%)'
            FROM motorbikes
            GROUP BY brand
            ORDER BY COUNT(*) DESC
        """)
        
        # Chuyển kết quả thành list of dicts
        market_data = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return market_data
    except Exception as e:
        st.error(f"Lỗi khi truy vấn database: {str(e)}")
        # Fallback to sample data as last resort
        data = [
            {'Thương hiệu': 'Honda', 'Số lượng giao dịch': 1200, 'Giá trung bình (triệu VND)': 25, 'Chênh lệch giá (%)': 10},
            {'Thương hiệu': 'Yamaha', 'Số lượng giao dịch': 800, 'Giá trung bình (triệu VND)': 30, 'Chênh lệch giá (%)': 15},
            {'Thương hiệu': 'Suzuki', 'Số lượng giao dịch': 500, 'Giá trung bình (triệu VND)': 22, 'Chênh lệch giá (%)': 8},
            {'Thương hiệu': 'Piaggio', 'Số lượng giao dịch': 300, 'Giá trung bình (triệu VND)': 40, 'Chênh lệch giá (%)': 20},
            {'Thương hiệu': 'SYM', 'Số lượng giao dịch': 200, 'Giá trung bình (triệu VND)': 18, 'Chênh lệch giá (%)': 5}
        ]
        return data