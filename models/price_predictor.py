# models/price_predictor.py
import pandas as pd
import joblib
import os

class MotorbikePricePredictor:
    """
    Lớp dự đoán giá xe máy cũ dựa trên các thông số
    """
    def __init__(self, model_path=None):
        """
        Khởi tạo mô hình dự đoán
        
        Args:
            model_path (str, optional): Đường dẫn đến file mô hình. Mặc định là None.
        """
        if model_path and os.path.exists(model_path):
            self.model = joblib.load(model_path)
        else:
            # Nếu không có mô hình, tạo một mô hình giả lập đơn giản
            self.model = None
    
    def predict(self, features):
        """
        Dự đoán giá xe dựa trên các thông số
        
        Args:
            features (dict): Dictionary chứa các thông số của xe
            
        Returns:
            dict: Kết quả dự đoán bao gồm giá, khoảng giá, độ tin cậy
        """
        if self.model:
            # Sử dụng mô hình nếu có
            # Chuyển đổi features thành DataFrame
            features_df = pd.DataFrame([features])
            
            # Dự đoán giá
            predicted_price = self.model.predict(features_df)[0]
            
            return {
                "price": predicted_price,
                "price_range": [predicted_price * 0.9, predicted_price * 1.1],
                "confidence": 0.85
            }
        else:
            # Giả lập kết quả dự đoán dựa trên quy tắc đơn giản
            base_price = 0
            
            # Giá cơ bản dựa trên thương hiệu và dung tích
            brand_prices = {
                "Honda": 20,
                "Yamaha": 25,
                "Suzuki": 18,
                "Piaggio": 35,
                "SYM": 15
            }
            
            # Lấy giá cơ bản theo thương hiệu
            base_price = brand_prices.get(features.get("brand", ""), 15)
            
            # Điều chỉnh theo dung tích động cơ
            cc_factor = features.get("cc", 100) / 100
            base_price = base_price * cc_factor
            
            # Điều chỉnh theo năm sản xuất (giảm 5% mỗi năm)
            year_diff = 2025 - features.get("year", 2020)
            base_price = base_price * (0.95 ** year_diff)
            
            # Điều chỉnh theo số km đã đi (giảm 1% cho mỗi 10,000 km)
            km_driven = features.get("km_driven", 0)
            km_factor = 1 - (km_driven / 10000) * 0.01
            base_price = base_price * km_factor
            
            # Điều chỉnh theo tình trạng xe
            condition_factors = {
                "Rất kém": 0.7,
                "Kém": 0.8,
                "Trung bình": 0.9,
                "Tốt": 1.0,
                "Rất tốt": 1.1
            }
            condition = features.get("condition", "Trung bình")
            condition_factor = condition_factors.get(condition, 1.0)
            base_price = base_price * condition_factor
            
            # Điều chỉnh theo khu vực
            location_factors = {
                "Hà Nội": 1.05,
                "TP. Hồ Chí Minh": 1.1,
                "Đà Nẵng": 1.0,
                "Khác": 0.95
            }
            location = features.get("location", "Khác")
            location_factor = location_factors.get(location, 1.0)
            base_price = base_price * location_factor
            
            # Làm tròn giá
            final_price = round(base_price, 1)
            
            return {
                "price": final_price,
                "price_range": [round(final_price * 0.9, 1), round(final_price * 1.1, 1)],
                "confidence": 0.85
            }
    
    def train(self, data):
        """
        Huấn luyện mô hình (chức năng dự kiến cho tương lai)
        
        Args:
            data (DataFrame): Dữ liệu huấn luyện
            
        Returns:
            bool: True nếu huấn luyện thành công, False nếu thất bại
        """
        # Chức năng huấn luyện mô hình sẽ được triển khai trong tương lai
        pass