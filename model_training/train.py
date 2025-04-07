import os
import argparse
import logging
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import json
import yaml
import statsmodels.api as sm

from data_processing import process_training_data

def setup_logging():
    """Cấu hình logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('model_training')


def train_model(data_path, output_path):
    """
    Huấn luyện các mô hình dự đoán giá xe máy (OLS và RandomForest)
    
    Args:
        data_path (str): Đường dẫn đến file CSV chứa dữ liệu huấn luyện
        output_path (str): Đường dẫn cơ sở để lưu các mô hình đã huấn luyện
    
    Returns:
        tuple: Mô hình RandomForest đã huấn luyện và các chỉ số đánh giá
    """
    # Thiết lập logging
    logger = setup_logging()
    logger.info("Bắt đầu quá trình huấn luyện mô hình...")
    
    # === BƯỚC 1: TẢI VÀ XỬ LÝ DỮ LIỆU ===
    # Tải dữ liệu từ file CSV
    logger.info(f"Đang tải dữ liệu từ {data_path}")
    try:
        df = pd.read_csv(data_path)
        logger.info(f"Đã tải thành công {len(df)} hàng dữ liệu")
    except Exception as e:
        logger.error(f"Lỗi khi tải dữ liệu: {e}")
        raise
    
    # Xử lý dữ liệu thông qua các hàm trong module data_processing
    logger.info("Đang xử lý và chuyển đổi dữ liệu...")
    try:
        X, y = process_training_data(df)
        logger.info(f"Đã xử lý dữ liệu thành công. Ma trận đặc trưng có kích thước: {X.shape}")
    except Exception as e:
        logger.error(f"Lỗi khi xử lý dữ liệu: {e}")
        raise
    
    # === BƯỚC 2: HUẤN LUYỆN MÔ HÌNH OLS ===
    logger.info("Bắt đầu huấn luyện mô hình hồi quy tuyến tính OLS...")
    try:
        # Fit mô hình OLS (Ordinary Least Squares)
        ols_model = sm.OLS(y, X).fit()
        
        # In tóm tắt mô hình
        logger.info("Tóm tắt mô hình OLS:")
        logger.info(f"R-squared: {ols_model.rsquared:.4f}")
        logger.info(f"Adjusted R-squared: {ols_model.rsquared_adj:.4f}")
        
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Lưu tóm tắt mô hình vào file
        ols_summary_path = os.path.join(os.path.dirname(output_path), 'ols_summary.txt')
        with open(ols_summary_path, 'w') as f:
            f.write(str(ols_model.summary()))
        logger.info(f"Đã lưu tóm tắt mô hình OLS vào {ols_summary_path}")
        
        # Lưu mô hình OLS
        ols_model_path = output_path + "ols.pkl"
        joblib.dump(ols_model, ols_model_path)
        logger.info(f"Đã lưu mô hình OLS vào {ols_model_path}")
    except Exception as e:
        logger.error(f"Lỗi khi huấn luyện mô hình OLS: {e}")
        logger.warning("Tiếp tục với mô hình RandomForest...")

    # === BƯỚC 3: CHIA DỮ LIỆU CHO RANDOM FOREST ===
    logger.info("Chia dữ liệu thành tập huấn luyện và tập kiểm tra...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    logger.info(f"Kích thước tập huấn luyện: {X_train.shape}, Kích thước tập kiểm tra: {X_test.shape}")

    # === BƯỚC 4: HUẤN LUYỆN MÔ HÌNH RANDOM FOREST ===
    logger.info("Bắt đầu huấn luyện mô hình RandomForest...")
    try:
        # Khởi tạo mô hình với các tham số đã chọn
        rf_model = RandomForestRegressor(
            n_estimators=100,    # Số lượng cây
            max_depth=10,        # Độ sâu tối đa của cây
            random_state=42,     # Seed ngẫu nhiên để đảm bảo kết quả có thể tái tạo
            n_jobs=-1            # Sử dụng tất cả các lõi CPU có sẵn
        )
        
        # Fit mô hình với dữ liệu huấn luyện
        logger.info("Đang huấn luyện mô hình RandomForest...")
        rf_model.fit(X_train, y_train)
        logger.info("Đã hoàn thành huấn luyện mô hình RandomForest")
    except Exception as e:
        logger.error(f"Lỗi khi huấn luyện mô hình RandomForest: {e}")
        raise

    # === BƯỚC 5: ĐÁNH GIÁ MÔ HÌNH RANDOM FOREST ===
    logger.info("Đánh giá mô hình RandomForest trên tập kiểm tra...")
    try:
        # Dự đoán trên tập kiểm tra (vẫn ở dạng logarit)
        y_pred_log = rf_model.predict(X_test)

        
        # Tính toán các chỉ số đánh giá trên thang đo gốc
        mse = mean_squared_error(y_test, y_pred_log)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred_log)
        mape = np.mean(np.abs((y_test - y_pred_log) / y_test)) * 100
        
        # Đóng gói các chỉ số đánh giá
        metrics = {
            "mse": float(mse),           # Sai số bình phương trung bình
            "rmse": float(rmse),         # Căn bậc hai của MSE
            "r2": float(r2),             # Hệ số xác định
            "mape": float(mape)          # Phần trăm sai số tuyệt đối trung bình
        }
        
        # Hiển thị các chỉ số đánh giá
        logger.info("Kết quả đánh giá mô hình RandomForest:")
        logger.info(f"  MSE: {mse:,.2f}")
        logger.info(f"  RMSE: {rmse:,.2f}")
        logger.info(f"  R²: {r2:.4f}")
        logger.info(f"  MAPE: {mape:.2f}%")
        
        # Lưu các chỉ số đánh giá vào file JSON
        metrics_path = os.path.join(os.path.dirname(output_path), 'rf_model_metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=4)
        logger.info(f"Đã lưu chỉ số đánh giá vào {metrics_path}")
    except Exception as e:
        logger.error(f"Lỗi khi đánh giá mô hình RandomForest: {e}")
        raise

    # === BƯỚC 6: LƯU MÔ HÌNH RANDOM FOREST ===
    try:
        # Lưu mô hình RandomForest
        logger.info(f"Đang lưu mô hình RandomForest vào {output_path}")
        joblib.dump(rf_model, output_path+"rf.pkl")
        logger.info("Đã lưu mô hình RandomForest thành công")
    except Exception as e:
        logger.error(f"Lỗi khi lưu mô hình RandomForest: {e}")
        raise
    
    logger.info("Quá trình huấn luyện mô hình hoàn tất thành công!")
    
def main():
    """Hàm chính để huấn luyện mô hình dự đoán giá xe máy"""
    # Phân tích đối số dòng lệnh
    parser = argparse.ArgumentParser(description='Huấn luyện mô hình dự đoán giá xe máy')
    parser.add_argument('--data', default='data/processed/input_xe_cu.csv',
                        help='Đường dẫn đến dữ liệu huấn luyện')
    parser.add_argument('--output', default='models/',
                        help='Đường dẫn để lưu mô hình đã huấn luyện')
    args = parser.parse_args()
    
    # Huấn luyện mô hình
    train_model(args.data, args.output)

if __name__ == "__main__":
    main()