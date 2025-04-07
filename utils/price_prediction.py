# utils/price_prediction.py
import pickle
import os
import numpy as np
import pandas as pd
import joblib
import streamlit as st
import logging
from config import MODEL_PATH
from sklearn.preprocessing import PolynomialFeatures
from model_training.data_processing import process_prediction_input

# Cấu hình logging
logger = logging.getLogger(__name__)


class MotorbikePricePredictor:
    """
    Lớp dự đoán giá xe máy cũ dựa trên các thông số
    """
    def __init__(self, model_path=MODEL_PATH):
        """
        Khởi tạo mô hình dự đoán
        
        Args:
            model_path (str, optional): Đường dẫn đến file mô hình. Mặc định sẽ dùng MODEL_PATH từ config.
        """
        self.model = None        
        logger.info(f"Khởi tạo MotorbikePricePredictor với model_path={model_path}")
        
        # Tải model từ file
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                logger.info(f"Đã tải thành công mô hình từ {model_path}")
            except Exception as e:
                error_msg = f"Lỗi khi tải mô hình từ {model_path}: {str(e)}"
                logger.error(error_msg)
                st.error(error_msg)
                raise RuntimeError(error_msg)
        else:
            error_msg = f"Không tìm thấy file mô hình tại {model_path}"
            logger.error(error_msg)
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
        logger.info(f"Bắt đầu dự đoán giá cho xe: {features}")
        
        # Kiểm tra dữ liệu đầu vào
        if not isinstance(features, dict):
            error_msg = "Features phải là dict với các thông số xe"
            logger.error(error_msg)
            st.error(error_msg)
            raise ValueError(error_msg)
            
        # Kiểm tra xem model đã được tải hay chưa
        if self.model is None:
            error_msg = "Mô hình dự đoán không được tải thành công"
            logger.error(error_msg)
            st.error(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            # Chuẩn bị dữ liệu đầu vào
            X, df_transformed = process_prediction_input(features)

            
            # Dự đoán với model đã tải
            logger.info(f"Thực hiện dự đoán với mô hình")
            log_price_pred = self.model.predict(X)[0]
            logger.info(f"Kết quả dự đoán log_price: {log_price_pred:.4f}")
            
            # Chuyển từ giá log sang giá thực tế
            predicted_price = np.exp(log_price_pred)
            logger.info(f"Giá dự đoán (nghìn đồng): {predicted_price:.2f}")
            
            # Nhân với 1000 để chuyển về đơn vị tiền tệ
            predicted_price_vnd = predicted_price * 1000
            
            # Làm tròn giá trị
            predicted_price_vnd_rounded = round(predicted_price_vnd)
            logger.info(f"Giá dự đoán (đồng, làm tròn): {predicted_price_vnd_rounded:,}")
            
            # Xác định độ tin cậy dự đoán dựa trên các yếu tố
            confidence = 0.85
            
            # Điều chỉnh độ tin cậy dựa trên tuổi xe
            age = 2025 - features["reg_year"]
            if age > 10:
                confidence -= 0.05
                logger.debug(f"Giảm độ tin cậy do xe quá cũ ({age} năm)")
            
            # Điều chỉnh độ tin cậy dựa trên số km
            mileage = features["mileage"]
            if mileage > 100000:
                confidence -= 0.05
                logger.debug(f"Giảm độ tin cậy do xe đi quá nhiều km ({mileage:,} km)")
            
            # Tạo khoảng giá dự đoán
            price_range_low = round(predicted_price_vnd_rounded * 0.9)
            price_range_high = round(predicted_price_vnd_rounded * 1.1)
            
            # Tạo kết quả dự đoán
            result = {
                "price": predicted_price_vnd_rounded,
                "price_range": [price_range_low, price_range_high],
                "confidence": round(confidence, 2),
                "unit": "VND"
            }
            
            # Log kết quả cuối cùng
            logger.info(f"Kết quả dự đoán cuối cùng: {result}")
            
            return result
            
        except Exception as e:
            error_msg = f"Lỗi khi dự đoán với model: {str(e)}"
            logger.error(error_msg)
            st.error(error_msg)
            raise RuntimeError(error_msg)