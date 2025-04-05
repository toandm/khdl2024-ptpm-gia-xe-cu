# api/routes.py
from flask import Blueprint, request, jsonify, current_app
import os
import sys
import json
import sqlite3
import datetime
from config import DB_PATH
# Thêm thư mục gốc vào sys.path để có thể import các module khác
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Tạo blueprint
api_bp = Blueprint('api', __name__)

# Hàm kết nối database
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Tạo một endpoint test đơn giản
@api_bp.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "API đang hoạt động!", "message": "Kết nối thành công"})

# Lấy danh sách thương hiệu
@api_bp.route('/brands', methods=['GET'])
def get_brands():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT brand FROM motorbikes ORDER BY brand")
        brands = cursor.fetchall()
        conn.close()
        
        # Chuyển đổi kết quả thành list các thương hiệu
        result = [{"value": brand['brand'], "label": brand['brand']} for brand in brands]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lấy danh sách mẫu xe theo thương hiệu
@api_bp.route('/models/<brand>', methods=['GET'])
def get_models(brand):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT model FROM motorbikes 
            WHERE brand = ? 
            ORDER BY model
        """, (brand,))
        models = cursor.fetchall()
        conn.close()
        
        # Chuyển đổi kết quả thành list các mẫu xe
        result = [{"value": model['model'], "label": model['model']} for model in models]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lấy danh sách phiên bản theo thương hiệu và mẫu xe
@api_bp.route('/variants/<brand>/<model>', methods=['GET'])
def get_variants(brand, model):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT variant FROM motorbikes 
            WHERE brand = ? AND model = ? 
            ORDER BY variant
        """, (brand, model))
        variants = cursor.fetchall()
        conn.close()
        
        # Chuyển đổi kết quả thành list các phiên bản
        result = [{"value": variant['variant'], "label": variant['variant']} for variant in variants]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lấy thông tin chi tiết của xe
@api_bp.route('/motorbike-details', methods=['GET'])
def get_motorbike_details():
    try:
        brand = request.args.get('brand')
        model = request.args.get('model')
        variant = request.args.get('variant')
        
        if not brand or not model:
            return jsonify({"error": "Thiếu thông tin thương hiệu hoặc mẫu xe"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if variant:
            cursor.execute("""
                SELECT * FROM motorbikes 
                WHERE brand = ? AND model = ? AND variant = ?
            """, (brand, model, variant))
        else:
            cursor.execute("""
                SELECT * FROM motorbikes 
                WHERE brand = ? AND model = ? 
                LIMIT 1
            """, (brand, model))
        
        motorbike = cursor.fetchone()
        conn.close()
        
        if motorbike:
            result = dict(motorbike)
            # Chuyển đổi chuỗi features thành JSON
            result['features'] = json.loads(result['features']) if result['features'] else {}
            return jsonify(result)
        else:
            return jsonify({"error": "Không tìm thấy thông tin xe"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lấy danh sách phân khúc xe
@api_bp.route('/segments', methods=['GET'])
def get_segments():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT segment FROM motorbikes ORDER BY segment")
        segments = cursor.fetchall()
        conn.close()
        
        # Chuyển đổi kết quả thành list các phân khúc
        result = [{"value": segment['segment'], "label": segment['segment']} for segment in segments]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lấy xe theo phân khúc
@api_bp.route('/motorbikes/segment/<segment>', methods=['GET'])
def get_motorbikes_by_segment(segment):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT brand, model, variant, engine_cc, price_new, avg_price_used
            FROM motorbikes 
            WHERE segment = ? 
            ORDER BY price_new
        """, (segment,))
        motorbikes = cursor.fetchall()
        conn.close()
        
        # Chuyển đổi kết quả thành list
        result = [dict(motorbike) for motorbike in motorbikes]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Tìm kiếm xe
@api_bp.route('/search', methods=['GET'])
def search_motorbikes():
    try:
        query = request.args.get('q', '')
        
        if not query or len(query) < 2:
            return jsonify([])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        search_param = f"%{query}%"
        
        cursor.execute("""
            SELECT brand, model, variant, engine_cc, price_new, avg_price_used
            FROM motorbikes 
            WHERE 
                brand LIKE ? OR
                model LIKE ? OR
                variant LIKE ? OR
                description LIKE ?
            ORDER BY brand, model, variant
            LIMIT 20
        """, (search_param, search_param, search_param, search_param))
        
        results = cursor.fetchall()
        conn.close()
        
        # Chuyển đổi kết quả thành list
        formatted_results = [dict(result) for result in results]
        return jsonify(formatted_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint để dự đoán giá xe máy
@api_bp.route('/predict', methods=['POST'])
def predict_price():
    """API endpoint để dự đoán giá xe máy"""
    try:
        # In thông tin debug
        print("Nhận được request tới /api/predict")
        
        # Lấy dữ liệu JSON
        data = request.get_json()
        print(f"Dữ liệu nhận được: {json.dumps(data, ensure_ascii=False)}")
        
        if not data:
            print("Không có dữ liệu")
            return jsonify({"error": "Không có dữ liệu"}), 400
        
        # Trích xuất thông tin cần thiết
        brand = data.get('brand')
        model = data.get('model')
        variant = data.get('variant', '')
        year = data.get('year', 0)
        km_driven = data.get('km_driven', 0)
        condition = data.get('condition', 'Tốt')
        
        # Kết nối database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tìm xe trong database
        if variant:
            cursor.execute("""
                SELECT * FROM motorbikes 
                WHERE brand = ? AND model = ? AND variant LIKE ?
            """, (brand, model, f"%{variant}%"))
        else:
            cursor.execute("""
                SELECT * FROM motorbikes 
                WHERE brand = ? AND model = ?
                LIMIT 1
            """, (brand, model))
        
        motorbike = cursor.fetchone()
        conn.close()
        
        if motorbike:
            print(f"Tìm thấy thông tin xe trong database: {motorbike['brand']} {motorbike['model']} {motorbike['variant']}")
            
            # Sử dụng thông tin từ database cho dự đoán
            # Tính toán dựa trên năm sản xuất, số km đã đi và tình trạng xe
            db_price = float(motorbike['avg_price_used'])
            year_diff = year - motorbike['year_start'] if year > 0 else 0
            
            # Điều chỉnh giá dựa trên năm sản xuất (giảm 5% mỗi năm)
            if year_diff < 0:
                # Nếu năm sản xuất không hợp lệ, sử dụng năm hiện tại
                year_diff = 0
            
            price = db_price * (0.95 ** year_diff)
            
            # Điều chỉnh theo số km đã đi (giảm 1% cho mỗi 10,000 km)
            km_factor = 1 - (km_driven / 10000) * 0.01
            price = price * km_factor
            
            # Điều chỉnh theo tình trạng xe
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
            
            # Thêm thông tin chi tiết
            details = {
                "model_info": {
                    "brand": motorbike['brand'],
                    "model": motorbike['model'],
                    "variant": motorbike['variant'],
                    "year_start": motorbike['year_start'],
                    "engine_cc": motorbike['engine_cc'],
                    "price_new": motorbike['price_new']
                },
                "adjustments": {
                    "year_factor": 0.95 ** year_diff,
                    "km_factor": km_factor,
                    "condition_factor": condition_factor
                }
            }
            
            result = {
                "price": final_price,
                "price_range": [round(final_price * 0.9, 1), round(final_price * 1.1, 1)],
                "confidence": 0.85,
                "source": "database",
                "details": details
            }
            
            print(f"Kết quả dự đoán: {json.dumps(result, ensure_ascii=False)}")
            return jsonify(result)
        else:
            print(f"Không tìm thấy thông tin xe trong database, sử dụng mô hình mặc định")
            
            # Nếu không tìm thấy trong database, sử dụng mô hình dự đoán mặc định
            # Giả lập kết quả dự đoán
            base_price = 20  # Giá cơ bản (triệu VND)
            
            # Điều chỉnh theo thương hiệu
            brand_factors = {
                "Honda": 1.0,
                "Yamaha": 1.2,
                "Suzuki": 0.9,
                "Piaggio": 1.8,
                "SYM": 0.8,
                "Khác": 0.7
            }
            brand_factor = brand_factors.get(brand, 1.0)
            
            # Điều chỉnh theo năm sản xuất
            year_factor = 1 - (2025 - year) * 0.05 if year > 0 else 0.5  # Giảm 5% mỗi năm
            
            # Điều chỉnh theo km đã đi
            km_factor = 1 - (km_driven / 100000)  # Giảm dần theo km đã đi
            
            # Điều chỉnh theo tình trạng
            condition_factors = {
                "Rất kém": 0.6,
                "Kém": 0.7,
                "Trung bình": 0.8,
                "Tốt": 0.9,
                "Rất tốt": 1.0
            }
            condition_factor = condition_factors.get(condition, 0.9)
            
            # Điều chỉnh theo dung tích xe
            engine_cc = data.get('cc', 125)
            cc_factor = engine_cc / 125
            
            # Tính giá cuối cùng
            final_price = base_price * brand_factor * year_factor * km_factor * condition_factor * cc_factor
            
            # Làm tròn và tạo khoảng giá
            final_price = round(final_price, 1)
            price_range = [round(final_price * 0.9, 1), round(final_price * 1.1, 1)]
            
            # Thêm thông tin chi tiết
            details = {
                "model_info": {
                    "brand": brand,
                    "model": model,
                    "variant": variant,
                    "engine_cc": engine_cc
                },
                "adjustments": {
                    "brand_factor": brand_factor,
                    "year_factor": year_factor,
                    "km_factor": km_factor,
                    "condition_factor": condition_factor,
                    "cc_factor": cc_factor
                }
            }
            
            result = {
                "price": final_price,
                "price_range": price_range,
                "confidence": 0.75,
                "source": "model",
                "details": details
            }
            
            print(f"Kết quả dự đoán: {json.dumps(result, ensure_ascii=False)}")
            return jsonify(result)
    
    except Exception as e:
        print(f"Lỗi trong predict_price: {str(e)}")
        return jsonify({"error": str(e)}), 500

# API endpoint để phân tích ảnh xe máy (giả lập)
@api_bp.route('/analyze-image', methods=['POST'])
def analyze_image():
    try:
        print("Nhận được request tới /api/analyze-image")
        
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({"error": "Không có dữ liệu ảnh"}), 400
        
        # Phân tích ảnh (giả lập)
        # Trong thực tế, ở đây sẽ gọi API Claude để phân tích ảnh
        
        # Giả lập kết quả phân tích ảnh
        result = {
            "Thương hiệu": "Honda",
            "Mẫu xe": "Wave RSX 110",
            "Năm sản xuất": "Khoảng 2018-2020",
            "Dung tích động cơ": "110cc",
            "Tình trạng xe": "Khá tốt, có một số vết xước nhỏ"
        }
        
        # Lấy thông tin chi tiết từ database (nếu có)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM motorbikes 
            WHERE brand = ? AND model LIKE ? AND variant LIKE ?
            LIMIT 1
        """, ("Honda", "%Wave%", "%RSX%"))
        
        motorbike = cursor.fetchone()
        conn.close()
        
        if motorbike:
            # Bổ sung thông tin từ database
            result["Dung tích động cơ"] = f"{motorbike['engine_cc']}cc"
            result["Công suất"] = f"{motorbike['horsepower']}hp"
            result["Trọng lượng"] = f"{motorbike['weight']}kg"
            result["Giá mới"] = f"{motorbike['price_new']} triệu VND"
            result["Giá cũ trung bình"] = f"{motorbike['avg_price_used']} triệu VND"
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Lỗi trong analyze_image: {str(e)}")
        return jsonify({"error": str(e)}), 500

# API endpoint để phân tích mô tả xe máy (giả lập)
@api_bp.route('/analyze-description', methods=['POST'])
def analyze_description():
    try:
        print("Nhận được request tới /api/analyze-description")
        
        data = request.get_json()
        if not data or 'description' not in data:
            return jsonify({"error": "Không có dữ liệu mô tả"}), 400
        
        description = data['description']
        print(f"Mô tả nhận được: {description}")
        
        # Phân tích mô tả (giả lập)
        # Trong thực tế, ở đây sẽ gọi API Claude để phân tích mô tả
        
        # Tìm một số từ khóa đơn giản trong mô tả
        brand = "Honda"
        model = "Wave"
        variant = "RSX"
        year = "2019"
        engine_cc = "110cc"
        
        if "honda" in description.lower():
            brand = "Honda"
        elif "yamaha" in description.lower():
            brand = "Yamaha"
        elif "suzuki" in description.lower():
            brand = "Suzuki"
        elif "piaggio" in description.lower() or "vespa" in description.lower():
            brand = "Piaggio"
        elif "sym" in description.lower():
            brand = "SYM"
        
        if "wave" in description.lower():
            model = "Wave"
        elif "air blade" in description.lower() or "airblade" in description.lower():
            model = "Air Blade"
        elif "vision" in description.lower():
            model = "Vision"
        elif "sh" in description.lower():
            model = "SH"
        elif "winner" in description.lower():
            model = "Winner"
        elif "exciter" in description.lower():
            model = "Exciter"
        
        # Tìm năm sản xuất (4 chữ số từ 1990-2025)
        import re
        year_match = re.search(r'(19[9][0-9]|20[0-2][0-9])', description)
        if year_match:
            year = year_match.group(0)
        
        # Tìm dung tích động cơ
        cc_match = re.search(r'(\d{2,3})cc', description.lower())
        if cc_match:
            engine_cc = cc_match.group(0)
        
        # Giả lập kết quả phân tích mô tả
        result = {
            "Thương hiệu": brand,
            "Mẫu xe": model,
            "Năm sản xuất": year,
            "Dung tích động cơ": engine_cc,
            "Số km đã đi": "Khoảng 20,000 km",
            "Màu sắc": "Đỏ đen",
            "Đặc điểm": "Phanh đĩa trước, bảo dưỡng định kỳ"
        }
        
        # Lấy thông tin chi tiết từ database (nếu có)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM motorbikes 
            WHERE brand = ? AND model LIKE ?
            LIMIT 1
        """, (brand, f"%{model}%"))
        
        motorbike = cursor.fetchone()
        conn.close()
        
        if motorbike:
            # Bổ sung thông tin từ database
            result["Dung tích động cơ"] = f"{motorbike['engine_cc']}cc"
            result["Công suất"] = f"{motorbike['horsepower']}hp"
            result["Trọng lượng"] = f"{motorbike['weight']}kg"
            result["Giá mới"] = f"{motorbike['price_new']} triệu VND"
            result["Giá cũ trung bình"] = f"{motorbike['avg_price_used']} triệu VND"
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Lỗi trong analyze_description: {str(e)}")
        return jsonify({"error": str(e)}), 500

# API endpoint để lấy dữ liệu thị trường
@api_bp.route('/market-data', methods=['GET'])
def get_market_data():
    try:
        print("Nhận được request tới /api/market-data")
        
        # Lấy thống kê từ database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tính toán thống kê theo thương hiệu
        cursor.execute("""
            SELECT 
                brand,
                COUNT(*) as count,
                AVG(price_new) as avg_price_new,
                AVG(avg_price_used) as avg_price_used,
                (AVG(price_new) - AVG(avg_price_used)) / AVG(price_new) * 100 as price_diff
            FROM motorbikes
            GROUP BY brand
            ORDER BY count DESC
        """)
        brands_stats = cursor.fetchall()
        
        # Tính toán tổng số xe
        cursor.execute("SELECT COUNT(*) as total_count FROM motorbikes")
        total_count = cursor.fetchone()['total_count']
        
        # Tính toán giá trung bình
        cursor.execute("""
            SELECT 
                AVG(price_new) as avg_price_new,
                AVG(avg_price_used) as avg_price_used,
                (AVG(price_new) - AVG(avg_price_used)) / AVG(price_new) * 100 as avg_price_diff
            FROM motorbikes
        """)
        avg_stats = cursor.fetchone()
        
        conn.close()
        
        # Chuyển đổi kết quả thành dictionary
        brands = {}
        for brand in brands_stats:
            brands[brand['brand']] = {
                'count': brand['count'],
                'avg_price': round(brand['avg_price_used'], 1),
                'price_diff': round(brand['price_diff'], 1)
            }
        
        # Tạo kết quả tổng hợp
        data = {
            'brands': brands,
            'total_count': total_count,
            'avg_price': round(avg_stats['avg_price_used'], 1),
            'avg_price_diff': round(avg_stats['avg_price_diff'], 1)
        }
        
        return jsonify(data)
    
    except Exception as e:
        print(f"Lỗi trong get_market_data: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Endpoint để lấy thống kê xe theo phân khúc
@api_bp.route('/stats/segments', methods=['GET'])
def get_segment_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                segment,
                COUNT(*) as count,
                AVG(price_new) as avg_price_new,
                AVG(avg_price_used) as avg_price_used
            FROM motorbikes
            GROUP BY segment
            ORDER BY count DESC
        """)
        
        segments = cursor.fetchall()
        conn.close()
        
        # Chuyển đổi kết quả thành list
        result = [
            {
                'segment': segment['segment'],
                'count': segment['count'],
                'avg_price_new': round(segment['avg_price_new'], 1),
                'avg_price_used': round(segment['avg_price_used'], 1)
            }
            for segment in segments
        ]
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint để lấy thống kê xe theo dung tích động cơ
@api_bp.route('/stats/engine-cc', methods=['GET'])
def get_engine_cc_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                CASE
                    WHEN engine_cc <= 110 THEN '≤ 110cc'
                    WHEN engine_cc <= 125 THEN '125cc'
                    WHEN engine_cc <= 150 THEN '150cc'
                    ELSE '> 150cc'
                END as cc_range,
                COUNT(*) as count,
                AVG(price_new) as avg_price_new,
                AVG(avg_price_used) as avg_price_used
            FROM motorbikes
            GROUP BY cc_range
            ORDER BY MIN(engine_cc)
        """)
        
        cc_ranges = cursor.fetchall()
        conn.close()
        
        # Chuyển đổi kết quả thành list
        result = [
            {
                'cc_range': cc_range['cc_range'],
                'count': cc_range['count'],
                'avg_price_new': round(cc_range['avg_price_new'], 1),
                'avg_price_used': round(cc_range['avg_price_used'], 1)
            }
            for cc_range in cc_ranges
        ]
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint để lấy so sánh giữa các xe
@api_bp.route('/compare', methods=['GET'])
def compare_motorbikes():
    try:
        # Lấy danh sách id xe cần so sánh từ query params
        id1 = request.args.get('id1')
        id2 = request.args.get('id2')
        
        if not id1 or not id2:
            return jsonify({"error": "Thiếu id xe cần so sánh"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Lấy thông tin của xe 1
        cursor.execute("SELECT * FROM motorbikes WHERE id = ?", (id1,))
        motorbike1 = cursor.fetchone()
        
        # Lấy thông tin của xe 2
        cursor.execute("SELECT * FROM motorbikes WHERE id = ?", (id2,))
        motorbike2 = cursor.fetchone()
        
        conn.close()
        
        if not motorbike1 or not motorbike2:
            return jsonify({"error": "Không tìm thấy thông tin của một hoặc cả hai xe"}), 404
        
        # Chuyển đổi kết quả thành dict để so sánh
        bike1 = dict(motorbike1)
        bike2 = dict(motorbike2)
        
        # Chuyển đổi features từ JSON string sang dict
        bike1['features'] = json.loads(bike1['features']) if bike1['features'] else {}
        bike2['features'] = json.loads(bike2['features']) if bike2['features'] else {}
        
        # Tạo so sánh chi tiết
        comparison = {
            "bike1": {
                "id": bike1['id'],
                "brand": bike1['brand'],
                "model": bike1['model'],
                "variant": bike1['variant'],
                "year_start": bike1['year_start'],
                "engine_cc": bike1['engine_cc'],
                "horsepower": bike1['horsepower'],
                "torque": bike1['torque'],
                "weight": bike1['weight'],
                "transmission": bike1['transmission'],
                "brake_front": bike1['brake_front'],
                "brake_rear": bike1['brake_rear'],
                "abs": bool(bike1['abs']),
                "price_new": bike1['price_new'],
                "avg_price_used": bike1['avg_price_used'],
                "features": bike1['features']
            },
            "bike2": {
                "id": bike2['id'],
                "brand": bike2['brand'],
                "model": bike2['model'],
                "variant": bike2['variant'],
                "year_start": bike2['year_start'],
                "engine_cc": bike2['engine_cc'],
                "horsepower": bike2['horsepower'],
                "torque": bike2['torque'],
                "weight": bike2['weight'],
                "transmission": bike2['transmission'],
                "brake_front": bike2['brake_front'],
                "brake_rear": bike2['brake_rear'],
                "abs": bool(bike2['abs']),
                "price_new": bike2['price_new'],
                "avg_price_used": bike2['avg_price_used'],
                "features": bike2['features']
            },
            "comparison": {
                "engine_cc_diff": bike1['engine_cc'] - bike2['engine_cc'],
                "horsepower_diff": bike1['horsepower'] - bike2['horsepower'],
                "torque_diff": bike1['torque'] - bike2['torque'],
                "weight_diff": bike1['weight'] - bike2['weight'],
                "price_new_diff": bike1['price_new'] - bike2['price_new'],
                "price_used_diff": bike1['avg_price_used'] - bike2['avg_price_used'],
                "power_weight_ratio1": round(bike1['horsepower'] * 1000 / bike1['weight'], 2),
                "power_weight_ratio2": round(bike2['horsepower'] * 1000 / bike2['weight'], 2)
            }
        }
        
        return jsonify(comparison)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint để lấy top xe bán chạy (giả lập)
@api_bp.route('/top-selling', methods=['GET'])
def get_top_selling():
    try:
        limit = request.args.get('limit', 5, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, brand, model, variant, engine_cc, price_new, avg_price_used
            FROM motorbikes
            ORDER BY RANDOM()
            LIMIT ?
        """, (limit,))
        
        top_bikes = cursor.fetchall()
        conn.close()
        
        # Chuyển đổi kết quả thành list
        result = [dict(bike) for bike in top_bikes]
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint để lấy xe theo dải giá
@api_bp.route('/price-range', methods=['GET'])
def get_by_price_range():
    try:
        min_price = request.args.get('min', 0, type=float)
        max_price = request.args.get('max', 1000, type=float)
        price_type = request.args.get('type', 'used')  # 'new' hoặc 'used'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if price_type == 'new':
            cursor.execute("""
                SELECT id, brand, model, variant, engine_cc, price_new, avg_price_used
                FROM motorbikes
                WHERE price_new BETWEEN ? AND ?
                ORDER BY price_new
            """, (min_price, max_price))
        else:
            cursor.execute("""
                SELECT id, brand, model, variant, engine_cc, price_new, avg_price_used
                FROM motorbikes
                WHERE avg_price_used BETWEEN ? AND ?
                ORDER BY avg_price_used
            """, (min_price, max_price))
        
        bikes = cursor.fetchall()
        conn.close()
        
        # Chuyển đổi kết quả thành list
        result = [dict(bike) for bike in bikes]
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint để lấy xe theo dung tích động cơ
@api_bp.route('/engine-cc', methods=['GET'])
def get_by_engine_cc():
    try:
        min_cc = request.args.get('min', 0, type=int)
        max_cc = request.args.get('max', 1000, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, brand, model, variant, engine_cc, price_new, avg_price_used
            FROM motorbikes
            WHERE engine_cc BETWEEN ? AND ?
            ORDER BY engine_cc
        """, (min_cc, max_cc))
        
        bikes = cursor.fetchall()
        conn.close()
        
        # Chuyển đổi kết quả thành list
        result = [dict(bike) for bike in bikes]
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint để lấy thông tin thị trường của một xe cụ thể
@api_bp.route('/market-info/<int:id>', methods=['GET'])
def get_bike_market_info(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT *
            FROM motorbikes
            WHERE id = ?
        """, (id,))
        
        bike = cursor.fetchone()
        if not bike:
            conn.close()
            return jsonify({"error": "Không tìm thấy thông tin xe"}), 404
        
        # Lấy các xe tương tự để so sánh
        cursor.execute("""
            SELECT id, brand, model, variant, engine_cc, price_new, avg_price_used
            FROM motorbikes
            WHERE brand = ? AND model = ? AND id != ?
            ORDER BY engine_cc
        """, (bike['brand'], bike['model'], id))
        
        similar_bikes = cursor.fetchall()
        
        # Lấy các xe cùng phân khúc
        cursor.execute("""
            SELECT id, brand, model, variant, engine_cc, price_new, avg_price_used
            FROM motorbikes
            WHERE segment = ? AND id != ? AND brand != ?
            ORDER BY avg_price_used
            LIMIT 5
        """, (bike['segment'], id, bike['brand']))
        
        segment_bikes = cursor.fetchall()
        
        conn.close()
        
        # Tính toán thông tin thị trường
        market_info = {
            "bike": dict(bike),
            "similar_models": [dict(b) for b in similar_bikes],
            "segment_competitors": [dict(b) for b in segment_bikes],
            "price_analysis": {
                "new_price": bike['price_new'],
                "used_price": bike['avg_price_used'],
                "depreciation_percentage": round((bike['price_new'] - bike['avg_price_used']) / bike['price_new'] * 100, 1),
                "price_range": {
                    "min": bike['min_price_used'],
                    "avg": bike['avg_price_used'],
                    "max": bike['max_price_used']
                }
            }
        }
        
        # Chuyển đổi JSON string sang dict
        if market_info['bike']['features']:
            market_info['bike']['features'] = json.loads(market_info['bike']['features'])
        else:
            market_info['bike']['features'] = {}
        
        return jsonify(market_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint để lấy các xe bán chạy theo phân khúc
@api_bp.route('/top-by-segment/<segment>', methods=['GET'])
def get_top_by_segment(segment):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, brand, model, variant, engine_cc, price_new, avg_price_used
            FROM motorbikes
            WHERE segment = ?
            ORDER BY avg_price_used
            LIMIT 5
        """, (segment,))
        
        bikes = cursor.fetchall()
        conn.close()
        
        # Chuyển đổi kết quả thành list
        result = [dict(bike) for bike in bikes]
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500