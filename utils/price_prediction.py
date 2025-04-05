# utils/price_prediction.py
import pickle
import os
import numpy as np
import streamlit as st

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
        self.model = None
        
        # Đường dẫn mặc định nếu không có model_path được cung cấp
        if model_path is None:
            model_path = os.path.join('data', 'rf_model.pkl')
        
        # Tải model từ file
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print(f"Đã tải mô hình thành công từ {model_path}")
            except Exception as e:
                error_msg = f"Lỗi khi tải mô hình từ {model_path}: {str(e)}"
                print(error_msg)
                st.error(error_msg)
                raise RuntimeError(error_msg)
        else:
            error_msg = f"Không tìm thấy file mô hình tại {model_path}"
            print(error_msg)
            st.error(error_msg)
            raise FileNotFoundError(error_msg)
    
    def predict(self, features):
        """
        Dự đoán giá xe dựa trên các thông số
        
        Args:
            features (dict): Thông số của xe
            
        Returns:
            dict: Kết quả dự đoán bao gồm giá, khoảng giá, độ tin cậy
        """
        # Kiểm tra dữ liệu đầu vào
        if not isinstance(features, dict):
            error_msg = "Features phải là dict với các thông số xe"
            st.error(error_msg)
            raise ValueError(error_msg)
            
        # Kiểm tra xem model đã được tải hay chưa
        if self.model is None:
            error_msg = "Mô hình dự đoán không được tải thành công"
            st.error(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            # Chuẩn bị dữ liệu đầu vào
            model_features = np.array([
                [
                    features.get('reg_year', 2020),  # Năm đăng ký
                    features.get('mileage', 15000),  # Số km đã đi
                    features.get('cc', 125)           # Dung tích động cơ
                ]
            ])
                
            # Dự đoán với model đã tải
            predicted_price = self.model.predict(model_features)[0]
            
            # Đảm bảo kết quả là số
            predicted_price = float(predicted_price)
            
            # Tạo kết quả dự đoán
            result = {
                "price": round(predicted_price, 1),
                "price_range": [round(predicted_price * 0.9, 1), round(predicted_price * 1.1, 1)],
                "confidence": 0.85,
                "source": "model_prediction"
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Lỗi khi dự đoán với model: {str(e)}"
            print(error_msg)
            st.error(error_msg)
            raise RuntimeError(error_msg)