import pandas as pd
import numpy as np
import logging
import os
import re
from datetime import datetime

# Thiết lập logger
logger = logging.getLogger("data_preprocessing")
logger.setLevel(logging.INFO)
if not logger.handlers:
    # Tạo console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # Tạo formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    # Thêm handler vào logger
    logger.addHandler(ch)

def clean_price(price_str):
    """
    Chuyển đổi chuỗi giá thành số nguyên
    
    Args:
        price_str: Chuỗi giá (ví dụ: "33.000.000 đ")
        
    Returns:
        Giá dạng số nguyên (VND)
    """
    if pd.isna(price_str):
        return None
    
    try:
        # Loại bỏ "đ" và các dấu chấm, sau đó chuyển đổi sang số
        price_numeric = price_str.replace("đ", "").replace(".", "").strip()
        return int(price_numeric)
    except (ValueError, AttributeError):
        logger.warning(f"Không thể chuyển đổi giá: {price_str}")
        return None

def extract_reg_year(reg_year_str):
    """
    Trích xuất năm đăng ký từ chuỗi
    
    Args:
        reg_year_str: Chuỗi năm đăng ký
        
    Returns:
        Năm đăng ký dạng số nguyên
    """
    if pd.isna(reg_year_str):
        return None
    
    try:
        # Xử lý trường hợp "trước năm 1980"
        if "trước năm" in str(reg_year_str).lower():
            return 1980
        return int(reg_year_str)
    except (ValueError, TypeError):
        logger.warning(f"Không thể chuyển đổi năm đăng ký: {reg_year_str}")
        return None

def clean_mileage(mileage_str):
    """
    Chuyển đổi chuỗi số km thành số nguyên
    
    Args:
        mileage_str: Chuỗi số km
        
    Returns:
        Số km dạng số nguyên
    """
    if pd.isna(mileage_str):
        return None
    
    try:
        return int(mileage_str)
    except (ValueError, TypeError):
        logger.warning(f"Không thể chuyển đổi số km: {mileage_str}")
        return None

def normalize_origin(origin_str):
    """
    Chuẩn hóa xuất xứ
    
    Args:
        origin_str: Chuỗi xuất xứ
        
    Returns:
        Chuỗi xuất xứ đã chuẩn hóa
    """
    if pd.isna(origin_str) or origin_str.lower() in ["đang cập nhật", "nước khác"]:
        return "Việt Nam"  # Giả định mặc định là Việt Nam
    
    # Ánh xạ các tên gọi khác nhau
    origin_mapping = {
        "nhat ban": "Nhật Bản",
        "nhat": "Nhật Bản",
        "japan": "Nhật Bản",
        "thai lan": "Thái Lan",
        "thai": "Thái Lan",
        "viet nam": "Việt Nam",
        "vn": "Việt Nam",
        "vietnam": "Việt Nam",
        "taiwan": "Đài Loan",
        "dai loan": "Đài Loan",
        "china": "Trung Quốc",
        "trung quoc": "Trung Quốc",
        "an do": "Ấn Độ",
        "an": "Ấn Độ",
        "india": "Ấn Độ",
        "duc": "Đức",
        "germany": "Đức",
        "italia": "Ý",
        "italy": "Ý",
        "han quoc": "Hàn Quốc",
        "korea": "Hàn Quốc",
    }
    
    # Chuẩn hóa
    origin_lower = origin_str.lower().strip()
    for key, value in origin_mapping.items():
        if key in origin_lower:
            return value
    
    return origin_str

def extract_province(location_str):
    """
    Trích xuất tỉnh/thành phố từ chuỗi địa điểm
    
    Args:
        location_str: Chuỗi địa điểm (ví dụ: "Phường Phú Hòa, Thành phố Thủ Dầu Một, Bình Dương")
        
    Returns:
        Tên tỉnh/thành phố
    """
    if pd.isna(location_str):
        return None
    
    try:
        # Lấy phần tử cuối cùng sau dấu phẩy
        parts = location_str.split(",")
        province = parts[-1].strip()
        
        # Chuẩn hóa tên tỉnh/thành phố
        province_mapping = {
            "tp hồ chí minh": "TP. Hồ Chí Minh",
            "tp. hồ chí minh": "TP. Hồ Chí Minh",
            "tphcm": "TP. Hồ Chí Minh",
            "hồ chí minh": "TP. Hồ Chí Minh",
            "hcm": "TP. Hồ Chí Minh",
            "ha noi": "Hà Nội",
            "hà nội": "Hà Nội",
            "hanoi": "Hà Nội",
            "đa nang": "Đà Nẵng",
            "đà nẵng": "Đà Nẵng",
            "can tho": "Cần Thơ",
            "cần thơ": "Cần Thơ",
            "hai phong": "Hải Phòng",
            "hải phòng": "Hải Phòng",
        }
        
        province_lower = province.lower()
        for key, value in province_mapping.items():
            if key == province_lower:
                return value
        
        return province
    except Exception as e:
        logger.warning(f"Không thể trích xuất tỉnh/thành phố từ {location_str}: {str(e)}")
        return None

def normalize_model(model_str, brand_str=None):
    """
    Chuẩn hóa tên model
    
    Args:
        model_str: Chuỗi tên model
        brand_str: Chuỗi tên thương hiệu (tùy chọn)
        
    Returns:
        Tên model đã chuẩn hóa
    """
    if pd.isna(model_str) or model_str.lower() in ["dòng khác", "không xác định"]:
        return None
    
    # Ánh xạ các tên gọi khác nhau
    model_mapping = {
        "airblade": "Air Blade",
        "air blade": "Air Blade",
        "sh mode": "SH Mode",
        "shmode": "SH Mode",
        "vision": "Vision",
        "wave alpha": "Wave Alpha",
        "wave a": "Wave Alpha",
        "wave rsx": "Wave RSX",
        "wave rs": "Wave RSX",
        "winner": "Winner",
        "winner x": "Winner X",
        "exciter": "Exciter",
        "sirius": "Sirius",
        "jupiter": "Jupiter",
        "vario": "Vario",
        "click": "Click",
        "lead": "Lead",
        "sh": "SH",
        "pcx": "PCX",
        "liberty": "Liberty",
        "lx": "LX",
        "vespa": "Vespa",
        "blade": "Blade",
        "future": "Future",
        "dream": "Dream",
        "cub": "Cub",
        "raider": "Raider",
        "satria": "Satria",
        "sport": "Sport",
        "xipo": "Xipo",
        "attila": "Attila",
        "galaxy": "Galaxy",
        "fly": "Fly",
        "elite": "Elite",
        "luvias": "Luvias",
        "nouvo": "Nouvo",
        "grande": "Grande",
        "janus": "Janus",
        "freego": "Freego",
        "giorno": "Giorno",
        "px": "PX",
        "medley": "Medley",
        "primavera": "Primavera",
        "sprint": "Sprint",
    }
    
    # Chuẩn hóa
    model_lower = model_str.lower().strip()
    for key, value in model_mapping.items():
        if key == model_lower or key in model_lower.split():
            return value
    
    # Xử lý trường hợp model là brand
    if brand_str and model_str.lower() == brand_str.lower():
        brand_model_mapping = {
            "honda": "Wave Alpha",
            "yamaha": "Exciter",
            "suzuki": "Raider",
            "piaggio": "Vespa",
            "sym": "Attila",
            "kawasaki": "Z",
            "ducati": "Monster",
            "bmw": "S1000RR",
            "ktm": "Duke",
            "royal enfield": "Classic",
            "benelli": "TRK",
            "triumph": "Trident",
            "daelim": "Daystar",
        }
        brand_lower = brand_str.lower()
        if brand_lower in brand_model_mapping:
            return brand_model_mapping[brand_lower]
    
    return model_str

def normalize_condition(condition_str):
    """
    Chuẩn hóa tình trạng xe
    
    Args:
        condition_str: Chuỗi tình trạng xe
        
    Returns:
        Chuỗi tình trạng xe đã chuẩn hóa
    """
    if pd.isna(condition_str):
        return "Đã sử dụng"  # Giá trị mặc định
    
    condition_mapping = {
        "đã sử dụng": "Đã sử dụng",
        "đã qua sử dụng": "Đã sử dụng",
        "cũ": "Đã sử dụng",
        "mới": "Mới",
        "mới 99%": "Đã sử dụng",
        "95%": "Đã sử dụng",
        "90%": "Đã sử dụng",
    }
    
    condition_lower = condition_str.lower().strip()
    for key, value in condition_mapping.items():
        if key in condition_lower:
            return value
    
    return condition_str

def extract_engine_capacity(engine_str):
    """
    Trích xuất dung tích động cơ từ chuỗi
    
    Args:
        engine_str: Chuỗi dung tích động cơ (ví dụ: "100 - 175 cc")
        
    Returns:
        Giá trị trung bình của dung tích động cơ (cc)
    """
    if pd.isna(engine_str):
        return None
    
    try:
        # Trích xuất các số từ chuỗi
        matches = re.findall(r'\d+', engine_str)
        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return int(matches[0])
        else:
            # Lấy giá trị trung bình nếu có dải giá trị
            values = [int(m) for m in matches]
            return sum(values) / len(values)
    except Exception as e:
        logger.warning(f"Không thể trích xuất dung tích động cơ từ {engine_str}: {str(e)}")
        return None

def normalize_vehicle_type(type_str):
    """
    Chuẩn hóa loại xe
    
    Args:
        type_str: Chuỗi loại xe
        
    Returns:
        Chuỗi loại xe đã chuẩn hóa
    """
    if pd.isna(type_str):
        return None
    
    type_mapping = {
        "tay ga": "Tay ga",
        "xe ga": "Tay ga",
        "xe số": "Xe số",
        "số": "Xe số",
        "tay côn": "Tay côn/Moto",
        "côn tay": "Tay côn/Moto",
        "moto": "Tay côn/Moto",
        "phân khối lớn": "Tay côn/Moto",
        "pkl": "Tay côn/Moto",
    }
    
    type_lower = type_str.lower().strip()
    for key, value in type_mapping.items():
        if key in type_lower:
            return value
    
    return type_str

def process_post_time(post_time_str):
    """
    Xử lý thời gian đăng bài
    
    Args:
        post_time_str: Chuỗi thời gian đăng (ví dụ: "Đăng 15 ngày trước")
        
    Returns:
        Số ngày kể từ khi đăng
    """
    if pd.isna(post_time_str):
        return None
    
    try:
        # Trích xuất số ngày/giờ/phút
        match_days = re.search(r'(\d+) ngày', post_time_str)
        match_hours = re.search(r'(\d+) giờ', post_time_str)
        match_minutes = re.search(r'(\d+) phút', post_time_str)
        match_months = re.search(r'(\d+) tháng', post_time_str)
        
        if match_months:
            return int(match_months.group(1)) * 30  # Ước tính 30 ngày/tháng
        elif match_days:
            return int(match_days.group(1))
        elif match_hours:
            return float(match_hours.group(1)) / 24  # Chuyển giờ thành ngày
        elif match_minutes:
            return float(match_minutes.group(1)) / (24 * 60)  # Chuyển phút thành ngày
        else:
            return None
    except Exception as e:
        logger.warning(f"Không thể xử lý thời gian đăng từ {post_time_str}: {str(e)}")
        return None

def normalize_url(url_str, base_url="https://xe.chotot.com"):
    """
    Chuẩn hóa URL
    
    Args:
        url_str: Chuỗi URL gốc
        base_url: URL gốc của trang web
        
    Returns:
        URL đầy đủ
    """
    if pd.isna(url_str):
        return None
    
    # Nếu URL đã có http/https, giữ nguyên
    if url_str.startswith(("http://", "https://")):
        return url_str
    
    # Nếu không, thêm base_url vào trước
    return f"{base_url}{url_str}"
def extract_post_date(post_time_str):
    """
    Trích xuất ngày đăng từ chuỗi thời gian đăng
    
    Args:
        post_time_str: Chuỗi thời gian đăng (ví dụ: "Đăng 15 ngày trước")
        
    Returns:
        Ngày đăng dạng datetime
    """
    if pd.isna(post_time_str):
        return None
    
    try:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Trích xuất số ngày/giờ/phút
        match_days = re.search(r'(\d+) ngày', post_time_str)
        match_hours = re.search(r'(\d+) giờ', post_time_str)
        match_minutes = re.search(r'(\d+) phút', post_time_str)
        match_months = re.search(r'(\d+) tháng', post_time_str)
        
        if match_months:
            days = int(match_months.group(1)) * 30  # Ước tính 30 ngày/tháng
            return today - pd.Timedelta(days=days)
        elif match_days:
            days = int(match_days.group(1))
            return today - pd.Timedelta(days=days)
        elif match_hours:
            hours = int(match_hours.group(1))
            return today - pd.Timedelta(hours=hours)
        elif match_minutes:
            minutes = int(match_minutes.group(1))
            return today - pd.Timedelta(minutes=minutes)
        else:
            return None
    except Exception as e:
        logger.warning(f"Không thể trích xuất ngày đăng từ {post_time_str}: {str(e)}")
        return None
    
def filter_raw_data(csv_file_path, output_file_path=None):
    """
    Đọc và lọc dữ liệu raw từ file CSV
    
    Args:
        csv_file_path: Đường dẫn đến file CSV chứa dữ liệu raw
        output_file_path: Đường dẫn để lưu dữ liệu đã lọc (tùy chọn)
        
    Returns:
        DataFrame chứa dữ liệu đã lọc
    """
    try:
        # Đọc file CSV
        logger.info(f"Đang đọc dữ liệu từ {csv_file_path}...")
        df = pd.read_csv(csv_file_path)
        logger.info(f"Đã đọc {len(df)} bản ghi từ file CSV")
        
        # Lưu lại bản sao của dữ liệu gốc
        df_original = df.copy()
        
        # Các cột bắt buộc cần có
        required_columns = ["price", "model", "origin", "location", "reg_year", "mileage"]
        
        # Kiểm tra xem các cột bắt buộc có tồn tại không
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Thiếu các cột bắt buộc: {missing_columns}")
            return pd.DataFrame()
        
        # Chuyển đổi và làm sạch dữ liệu
        logger.info("Đang làm sạch và chuyển đổi dữ liệu...")
        
        # Chuyển đổi giá
        df["price_numeric"] = df["price"].apply(clean_price)
        
        # Chuyển đổi năm đăng ký
        df["reg_year_numeric"] = df["reg_year"].apply(extract_reg_year)
        
        # Chuyển đổi số km
        df["mileage_numeric"] = df["mileage"].apply(clean_mileage)
        
        # Chuẩn hóa xuất xứ
        df["origin_normalized"] = df["origin"].apply(normalize_origin)
        
        # Trích xuất tỉnh/thành phố
        df["province"] = df["location"].apply(extract_province)
        
        # Chuẩn hóa model
        df["model_normalized"] = df.apply(lambda row: normalize_model(row["model"], row["brand"]), axis=1)
        
        # Chuẩn hóa tình trạng xe
        if "condition" in df.columns:
            df["condition_normalized"] = df["condition"].apply(normalize_condition)
        
        # Trích xuất dung tích động cơ
        if "engine_capacity" in df.columns:
            df["engine_capacity_numeric"] = df["engine_capacity"].apply(extract_engine_capacity)
        
        # Chuẩn hóa loại xe
        if "vehicle_type" in df.columns:
            df["vehicle_type_normalized"] = df["vehicle_type"].apply(normalize_vehicle_type)
        
        # Xử lý thời gian đăng
        if "post_time" in df.columns:
            df["days_since_posted"] = df["post_time"].apply(process_post_time)
        
        # Chuẩn hóa URL
        if "url" in df.columns:
            df["url_full"] = df["url"].apply(normalize_url)
        
        if "post_time" in df.columns:
            df["days_since_posted"] = df["post_time"].apply(process_post_time)
            df["post_date"] = df["post_time"].apply(extract_post_date)
        
        # Lọc các bản ghi có giá trị hợp lệ cho các cột bắt buộc
        df_filtered = df[
            df["price_numeric"].notna() &
            df["model_normalized"].notna() &
            df["origin_normalized"].notna() &
            df["province"].notna() &
            df["reg_year_numeric"].notna() &
            df["mileage_numeric"].notna()
        ]
        
        # Lọc ra các mức giá hợp lý (từ 1 triệu đến 500 triệu)
        df_filtered = df_filtered[
            (df_filtered["price_numeric"] >= 1_000_000) & 
            (df_filtered["price_numeric"] <= 500_000_000)
        ]
        
        # Lọc ra các năm đăng ký hợp lý (từ 1980 đến năm hiện tại)
        current_year = datetime.now().year
        df_filtered = df_filtered[
            (df_filtered["reg_year_numeric"] >= 1980) & 
            (df_filtered["reg_year_numeric"] <= current_year)
        ]
        
        # Lọc ra các số km hợp lý (từ 0 đến 1,000,000 km)
        df_filtered = df_filtered[
            (df_filtered["mileage_numeric"] >= 0) & 
            (df_filtered["mileage_numeric"] <= 1_000_000)
        ]
        
        logger.info(f"Đã lọc xong dữ liệu, còn {len(df_filtered)} bản ghi hợp lệ trên tổng số {len(df_original)} bản ghi")
        
        # Tạo DataFrame kết quả
        result_columns = [
            "title", "price", "price_numeric", "description", 
            "model", "model_normalized", "brand",
            "reg_year", "reg_year_numeric", 
            "mileage", "mileage_numeric",
            "origin", "origin_normalized",
            "location", "province",
            "condition", "vehicle_type", "engine_capacity",
            "post_time", "days_since_posted", "post_date",
            "url", "url_full"
        ]
        
        # Chỉ thêm các cột tồn tại
        existing_columns = [col for col in result_columns if col in df_filtered.columns]
        
        # Thêm các cột đã chuẩn hóa
        for col in df_filtered.columns:
            if col.endswith("_normalized") and col not in existing_columns:
                existing_columns.append(col)
            if col.endswith("_numeric") and col not in existing_columns:
                existing_columns.append(col)
            if col == "days_since_posted" and col not in existing_columns:
                existing_columns.append(col)
        
        result_df = df_filtered[existing_columns]
        
        # Thêm cột price_millions
        result_df["price_millions"] = (result_df["price_numeric"] / 1_000_000).round(2)
        
        # Tạo mô tả ngắn tập hợp các thông tin quan trọng
        result_df["short_desc"] = result_df.apply(
            lambda row: f"{row['model_normalized']} ({row['reg_year_numeric']}) - {int(row['mileage_numeric']):,} km - {row['origin_normalized']}", 
            axis=1
        )
        
        # Lưu dữ liệu đã lọc nếu có đường dẫn đầu ra
        if output_file_path:
            output_dir = os.path.dirname(output_file_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            result_df.to_csv(output_file_path, index=False, encoding="utf-8")
            logger.info(f"Đã lưu dữ liệu đã lọc vào {output_file_path}")
        
        return result_df
    
    except Exception as e:
        logger.error(f"Lỗi khi xử lý dữ liệu: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return pd.DataFrame()

def create_sqlite_database(df, db_path='data/processed/motorbike_db.sqlite'):
    """
    Tạo cơ sở dữ liệu SQLite từ DataFrame
    
    Args:
        df: DataFrame cần lưu
        db_path: Đường dẫn đến file cơ sở dữ liệu
    """
    try:
        import sqlite3
        
        # Tạo thư mục nếu chưa tồn tại
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Kết nối đến cơ sở dữ liệu
        conn = sqlite3.connect(db_path)
        
        # Lưu DataFrame vào bảng
        df.to_sql('motorbikes', conn, if_exists='replace', index=False)
        
        # Tạo chỉ mục để tăng tốc truy vấn
        cursor = conn.cursor()
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price ON motorbikes(price_numeric)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_model ON motorbikes(model_normalized)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON motorbikes(reg_year_numeric)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_brand ON motorbikes(brand)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_post_date ON motorbikes(post_date)')

        # Đóng kết nối
        conn.close()
        
        logger.info(f"Đã lưu {len(df)} bản ghi vào cơ sở dữ liệu SQLite tại {db_path}")
        
    except Exception as e:
        logger.error(f"Lỗi khi tạo cơ sở dữ liệu SQLite: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # Đường dẫn đến file dữ liệu raw
    raw_data_path = "data/processed/input_xe_cu.csv"
    
    # Đường dẫn để lưu dữ liệu đã lọc
    filtered_data_path = "data/processed/motorbike_data_filtered.csv"
    
    # Đường dẫn đến file cơ sở dữ liệu SQLite
    db_path = "data/motorbike_database.db"
    
    # Lọc dữ liệu
    filtered_df = filter_raw_data(raw_data_path, filtered_data_path)

    # Tạo cơ sở dữ liệu SQLite
    if not filtered_df.empty:
        create_sqlite_database(filtered_df, db_path)
    # In thông tin
    if not filtered_df.empty:
        print(f"Tổng số bản ghi hợp lệ: {len(filtered_df)}")
        print("Thống kê số lượng bản ghi theo model:")
        print(filtered_df["model_normalized"].value_counts().head(10))
        print("\nThống kê số lượng bản ghi theo xuất xứ:")
        print(filtered_df["origin_normalized"].value_counts())
        print("\nThống kê số lượng bản ghi theo tỉnh/thành phố:")
        print(filtered_df["province"].value_counts().head(10))
        print("\nThống kê giá trung bình theo model phổ biến:")
        top_models = filtered_df["model_normalized"].value_counts().head(10).index
        price_stats = filtered_df[filtered_df["model_normalized"].isin(top_models)].groupby("model_normalized")["price_millions"].agg(['mean', 'min', 'max', 'count'])
        print(price_stats.sort_values('count', ascending=False))