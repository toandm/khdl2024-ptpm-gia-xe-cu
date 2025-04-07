Tạo file .env trong thư mục gốc của dự án và thêm API key:
CLAUDE_API_KEY=your_api_key_here

pip install -r requirements.txt
streamlit run run.py

ptpm-project/
├── app.py # File chính để chạy ứng dụng
├── run.py # Script khởi động ứng dụng Streamlit
├── config.py # File cấu hình chung
├── requirements.txt # Dependencies
├── README.md # Tài liệu dự án
├── .gitignore # File/thư mục bỏ qua khi commit
├── .streamlit/ # Cấu hình Streamlit  
│ └── config.toml
│
├── data/ # Thư mục chứa dữ liệu
│ ├── raw/ # Dữ liệu thô từ crawl
│ ├── processed/ # Dữ liệu đã xử lý
│ └── database/
│
├── models/ # Thư mục chứa các mô hình
│
├── static/ # Tài nguyên tĩnh
│ └── styles/
│ └── main.css # CSS tùy chỉnh
│
├── utils/ # Tiện ích
│ ├── **init**.py
│ ├── data_provider.py # Cung cấp dữ liệu từ database
│ ├── price_prediction.py # Dự đoán giá xe
│ └── visualization.py # Tạo biểu đồ
│
├── webpages/ # Các trang Streamlit
│ ├── **init**.py
│ ├── market_overview.py # Trang tổng quan thị trường
│ ├── price_prediction.py # Trang dự đoán giá
│ ├── bike_comparison.py # Trang so sánh xe
│ └── bike_suggestion.py # Trang gợi ý mua xe
│
├── scrapers/ # Module crawl dữ liệu
│ ├── **init**.py
│ ├── crawler_manager.py # Quản lý các crawler
│ ├── chotot_crawler.py # Crawler cho Chợ Tốt
│ ├── webike_crawler.py # Crawler cho Webike
│ └── facebook_crawler.py # Crawler cho Facebook Marketplace
│
├── data_processing/ # Module xử lý dữ liệu
│ ├── **init**.py
│ ├── cleaner.py # Làm sạch dữ liệu
│ ├── transformer.py # Biến đổi dữ liệu
│ ├── feature_engineering.py # Tạo đặc trưng
│ └── data_validation.py # Kiểm tra tính hợp lệ
│
└── model_training/ # Module huấn luyện mô hình
├── **init**.py
└── train.py # Huấn luyện mô hình
