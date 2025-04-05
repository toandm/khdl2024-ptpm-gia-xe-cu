import subprocess
import sys
import os
import time
import requests
import logging
import socket

# Thiết lập logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_port_available(port, host='localhost'):
    """Kiểm tra xem port có đang được sử dụng không"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) != 0

def run_flask_api():
    """Chạy Flask API trong tiến trình riêng"""
    # Đọc thông tin port từ config
    try:
        from config import API_PORT
        api_port = API_PORT
    except (ImportError, AttributeError):
        api_port = 5001
    
    # Kiểm tra port
    if not check_port_available(api_port):
        logger.error(f"Port {api_port} đang được sử dụng. Không thể khởi động Flask API.")
        return None
    
    # Chạy Flask API - hiển thị output trực tiếp thay vì redirect
    logger.info(f"Đang khởi động Flask API trên port {api_port}...")
    flask_process = subprocess.Popen(
        [sys.executable, "flask_app.py"],
        # Không redirect output để dễ debug
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE
    )
    return flask_process

def check_api_health(url, max_retries=30, retry_interval=1):
    """Kiểm tra kết nối API với cơ chế retry"""
    logger.info(f"Đang kiểm tra kết nối đến API tại {url}...")
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                logger.info(f"✅ API hoạt động tốt sau {attempt + 1} lần thử!")
                return True
            else:
                logger.warning(f"API trả về mã lỗi: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.info(f"Đang thử kết nối... ({attempt + 1}/{max_retries})")
            
        # Đợi trước khi thử lại
        if attempt < max_retries - 1:
            time.sleep(retry_interval)
    
    logger.error(f"❌ Không thể kết nối đến API sau {max_retries} lần thử!")
    return False

if __name__ == "__main__":
    # Đảm bảo thư mục data tồn tại
    os.makedirs("data", exist_ok=True)
    
    # Lấy thông tin port từ config
    try:
        from config import API_PORT
        api_port = API_PORT
    except (ImportError, AttributeError):
        api_port = 5001
    
    # Khởi động Flask API
    flask_process = run_flask_api()
    
    if flask_process is None:
        logger.error("Không thể khởi động Flask API. Vui lòng kiểm tra port và thử lại.")
        sys.exit(1)
    
    # Đường dẫn API test endpoint
    api_test_url = f"http://localhost:{api_port}/api/test"
    
    # Kiểm tra API khởi động thành công
    api_available = check_api_health(api_test_url, max_retries=30, retry_interval=1)
    
    if api_available:
        try:
            # Chạy Streamlit app
            logger.info("Đang khởi động Streamlit app...")
            subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])
        except KeyboardInterrupt:
            logger.info("Đã nhận lệnh thoát từ người dùng.")
        finally:
            # Dừng Flask API
            logger.info("Đang dừng Flask API...")
            flask_process.terminate()
            flask_process.wait(timeout=5)
            logger.info("Flask API đã dừng.")
    else:
        # Nếu API không khởi động được, dừng Flask process
        logger.error("Không thể kết nối đến API. Ứng dụng sẽ thoát.")
        flask_process.terminate()
        flask_process.wait(timeout=5)
        sys.exit(1)