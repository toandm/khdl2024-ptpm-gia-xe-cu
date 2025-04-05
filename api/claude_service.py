import requests
import json
import os
from dotenv import load_dotenv

# Load biến môi trường từ .env file
load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

def analyze_image(image_base64):
    """
    Gửi ảnh đến API Claude để phân tích
    
    Args:
        image_base64 (str): Ảnh được mã hóa base64
        
    Returns:
        dict: Kết quả phân tích từ Claude
    """
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
                        "text": "Đây là ảnh một chiếc xe máy. Hãy phân tích và cung cấp thông tin chi tiết về xe, bao gồm: thương hiệu, mẫu xe, năm sản xuất ước tính, dung tích động cơ, và tình trạng xe. Định dạng kết quả dưới dạng JSON."
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(CLAUDE_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Trích xuất phản hồi từ Claude (giả lập)
        return {
            "Thương hiệu": "Honda",
            "Mẫu xe": "Wave RSX 110",
            "Năm sản xuất": "Khoảng 2018-2020",
            "Dung tích động cơ": "110cc",
            "Tình trạng xe": "Khá tốt, có một số vết xước nhỏ"
        }
    except Exception as e:
        print(f"Lỗi khi gọi API Claude: {e}")
        return {"error": str(e)}

def analyze_description(description_text):
    """
    Gửi mô tả đến API Claude để phân tích
    
    Args:
        description_text (str): Mô tả về xe máy
        
    Returns:
        dict: Kết quả phân tích từ Claude
    """
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
                        "text": f"Đây là mô tả về một chiếc xe máy: '{description_text}'. Hãy phân tích và cung cấp thông tin chi tiết về xe, bao gồm: thương hiệu, mẫu xe, năm sản xuất, dung tích động cơ, số km đã đi, màu sắc, và các đặc điểm khác. Định dạng kết quả dưới dạng JSON."
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(CLAUDE_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Trích xuất phản hồi từ Claude (giả lập)
        return {
            "Thương hiệu": "Honda",
            "Mẫu xe": "Wave RSX",
            "Năm sản xuất": "2019",
            "Dung tích động cơ": "110cc",
            "Số km đã đi": "Khoảng 20,000 km",
            "Màu sắc": "Đỏ đen",
            "Đặc điểm": "Phanh đĩa trước, bảo dưỡng định kỳ"
        }
    except Exception as e:
        print(f"Lỗi khi gọi API Claude: {e}")
        return {"error": str(e)}