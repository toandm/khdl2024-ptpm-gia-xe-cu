# run.py - Script để chạy ứng dụng
import os
import subprocess
import sys

def run_app():
    """Chạy ứng dụng Streamlit và API Flask"""
    try:
        # Kiểm tra xem đã tạo cấu trúc thư mục chưa
        if not os.path.exists('utils') or not os.path.exists('api'):
            subprocess.run([sys.executable, 'init_directories.py'])
            print("Đã khởi tạo cấu trúc thư mục.")
        
        # Chạy API Flask trong một process riêng
        try:
            flask_process = subprocess.Popen(
                [sys.executable, 'flask_app.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("API Flask đã được khởi động.")
        except Exception as e:
            print(f"Lỗi khi khởi động API Flask: {str(e)}")
            print("Ứng dụng sẽ chạy mà không có API.")
            flask_process = None
        
        # Chạy ứng dụng Streamlit
        print("Đang khởi động ứng dụng Streamlit...")
        streamlit_cmd = f"{sys.executable} -m streamlit run app.py"
        os.system(streamlit_cmd)
        
        # Kết thúc process Flask khi thoát
        if flask_process:
            flask_process.terminate()
            print("Đã kết thúc API Flask.")
        
    except KeyboardInterrupt:
        print("Đang thoát ứng dụng...")
        if 'flask_process' in locals() and flask_process:
            flask_process.terminate()
            print("Đã kết thúc API Flask.")
    except Exception as e:
        print(f"Lỗi khi chạy ứng dụng: {str(e)}")
        if 'flask_process' in locals() and flask_process:
            flask_process.terminate()
            print("Đã kết thúc API Flask.")
        sys.exit(1)

if __name__ == "__main__":
    run_app()