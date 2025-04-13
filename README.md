# Motorcycle Price Prediction

Dự án này nhằm xây dựng một hệ thống thu thập dữ liệu, xử lý và dự đoán giá xe máy cũ tại Việt Nam, cùng với một ứng dụng web trực quan để người dùng có thể dễ dàng sử dụng mô hình.

## Nội dung

1. [Tổng quan](#tổng-quan)
2. [Cấu trúc dự án](#cấu-trúc-dự-án)
3. [Thu thập dữ liệu](#thu-thập-dữ-liệu)
4. [Tiền xử lý dữ liệu](#tiền-xử-lý-dữ-liệu)
5. [Xây dựng mô hình](#xây-dựng-mô-hình)
6. [Ứng dụng web](#ứng-dụng-web)
7. [Cài đặt](#cài-đặt)
8. [Hướng dẫn sử dụng](#hướng-dẫn-sử-dụng)
9. [Kết quả đánh giá](#kết-quả-đánh-giá)

## Tổng quan

Dự án này giải quyết bài toán dự đoán giá xe máy cũ dựa trên các đặc điểm như hãng xe, dòng xe, năm sản xuất, số km đã đi, tình trạng xe, v.v. Dự án sử dụng Random Forest Regression để dự đoán và triển khai mô hình trên ứng dụng web bằng Streamlit.

## Cấu trúc dự án

```
ptpm-project/
├── app.py                   # File chính để chạy ứng dụng
├── config.py                # File cấu hình chung
├── crawler/                 # Module crawl dữ liệu
│   ├── __init__.py
│   ├── chotot_crawler.py    # Crawler cho Chợ Tốt
│   ├── crawler_manager.py   # Quản lý các crawler
│   └── vnexpress_crawler.py # Crawler cho VnExpress
│
├── data/                    # Thư mục chứa dữ liệu
│   ├── processed/           # Dữ liệu đã xử lý
│   ├── raw/                 # Dữ liệu thô từ crawl
│   └── motorbike_database.db # Cơ sở dữ liệu SQLite
│
├── model_training/          # Module huấn luyện mô hình
│   ├── data_processing.py   # Xử lý dữ liệu cho huấn luyện
│   └── train.py             # Huấn luyện mô hình
│
├── models/                  # Thư mục chứa các mô hình đã huấn luyện
│   ├── ols.pkl              # Mô hình hồi quy tuyến tính
│   ├── ols_summary.txt      # Tóm tắt mô hình hồi quy
│   ├── rf.pkl               # Mô hình Random Forest
│   └── rf_model_metrics.json # Metrics của mô hình RF
│
├── presentation/           # Các tệp trình bày và phân tích
│   ├── eda.ipynb           # Notebook phân tích khám phá dữ liệu
│   └── model_journey.py    # Giải thích quá trình xây dựng mô hình
│
├── static/                 # Tài nguyên tĩnh
│   └── styles/
│       └── main.css        # CSS tùy chỉnh
│
├── tests/                  # Unit tests và integration tests
│   └── utils/
│       └── preprocessing/
│           └── test_unit.py # Unit test cho preprocessing
│
├── utils/                  # Tiện ích
│   ├── data_service.py     # Cung cấp dữ liệu từ database
│   ├── price_prediction.py # Dự đoán giá xe
│   └── visualization.py    # Tạo biểu đồ
│
├── webpages/              # Các trang Streamlit
│   ├── bike_comparison.py # Trang so sánh xe
│   ├── bike_suggestion.py # Trang gợi ý mua xe
│   ├── market_overview.py # Trang tổng quan thị trường
│   └── price_prediction.py # Trang dự đoán giá
│
├── README.md              # Tài liệu dự án
├── requirements.txt       # Dependencies
└── run.py                 # Script khởi động ứng dụng Streamlit
```

## Thu thập dữ liệu

Dữ liệu được thu thập từ các trang web mua bán xe máy cũ tại Việt Nam sử dụng module crawler:

- **crawler_manager.py**: Quản lý và điều phối quá trình thu thập dữ liệu từ nhiều nguồn
- **chotot_crawler.py**, **vnexpress_crawler.py**: Các crawler chuyên biệt cho từng nguồn dữ liệu

Dữ liệu thu thập bao gồm thông tin về:

- Hãng xe (Honda, Yamaha, Suzuki, Piaggio...)
- Dòng xe (Wave, Vision, Exciter, Vespa...)
- Năm sản xuất
- Số km đã đi
- Dung tích xe
- Tình trạng xe
- Vị trí bán
- Giá bán

## Tiền xử lý dữ liệu

Module model_training/data_processing.py thực hiện xử lý dữ liệu thô:

- Loại bỏ giá trị thiếu, trùng lặp, và bản ghi không hợp lệ
- Chuẩn hóa định dạng và quy chuẩn đơn vị
- Tạo các biến mới như tuổi xe, mức độ phổ biến, phân khúc giá
- Kiểm tra tính hợp lệ của dữ liệu trước khi đưa vào mô hình

## Xây dựng mô hình

Module model_training/train.py huấn luyện mô hình Random Forest Regression để dự đoán giá xe:

- Phân tích và lựa chọn đặc trưng quan trọng từ dữ liệu
- Tối ưu siêu tham số mô hình bằng RandomizedSearchCV
- Đánh giá hiệu suất bằng nhiều chỉ số: MAE, RMSE, R², MAPE
- Phân tích phần dư để đánh giá độ tin cậy của mô hình

Mô hình được lưu vào thư mục models/ để sử dụng trong ứng dụng web.

## Ứng dụng web

Ứng dụng web dựa trên Streamlit với các chức năng:

- **market_overview.py**: Phân tích tổng quan thị trường xe máy cũ
- **price_prediction.py**: Dự đoán giá xe dựa trên các thông số đầu vào
- **bike_comparison.py**: So sánh các xe có thông số tương đương
- **bike_suggestion.py**: Gợi ý xe phù hợp với ngân sách và nhu cầu

Utils cung cấp các chức năng hỗ trợ:

- **data_service.py**: Truy xuất dữ liệu từ database
- **price_prediction.py**: Xử lý logic dự đoán giá
- **visualization.py**: Tạo các biểu đồ phân tích

## Cài đặt

```bash
# Clone repository
git clone https://github.com/username/ptpm-project.git
cd ptpm-project

# Tạo môi trường ảo
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

## Hướng dẫn sử dụng

### Thu thập dữ liệu mới

```bash
# Chạy thu thập dữ liệu từ tất cả nguồn
python -m crawler.crawler_manager

# Hoặc thu thập từ nguồn cụ thể
python -m crawler.chotot_crawler
```

## Xử lý dữ liệu

```bash
# Xử lý dữ liệu thô
python -m model_training.data_processing
```

## Huấn luyện mô hình

```bash
# Huấn luyện và lưu mô hình mới
python -m model_training.train
```

## Chạy ứng dụng web

```bash
streamlit run app.py
```
