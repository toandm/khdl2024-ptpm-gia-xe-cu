import json
import logging
import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
import re
import os
import statsmodels.api as sm
# Cấu hình logging
logger = logging.getLogger(__name__)


CURRENT_YEAR = 2025

# Bổ sung mapping xuất xứ
ORIGIN_MAPPING = {
    "Thái Lan": ["thái", "thai lan", "xe thái"],
    "Nhật Bản": ["nhật", "nhat ban", "xe nhật"],
    "Indonesia": ["indonesia", "xe indo"],
    "Ý": ["ý", "italia"],
    "Mỹ": ["mỹ", "america", "xe mỹ"],
    "Trung Quốc": ["trung", "xe tq", "xe trung quốc", "trung quốc"],
    "Ấn Độ": ["ấn", "xe ấn", "an do"],
    "Hàn Quốc": ["hàn", "xe hàn", "han quoc"],
    "Đức": ["đức", "xe đức", "duc"],
    "Đài Loan": ["đài", "xe đài", "dai loan"],
}

def read_json_stat(file_path: str) -> pd.DataFrame:
    """
    Đọc file JSON-stat và trả về DataFrame đã phân tích
    """
    with open(file_path, encoding="utf-8") as input_file:
        data = json.load(input_file)

    # Trích xuất các chiều và giá trị
    dimensions = data["dataset"]["dimension"]
    values = data["dataset"]["value"]

    # Tạo danh sách tiêu đề cho DataFrame
    headers = [dimensions[dim]["label"] for dim in dimensions["id"]] + ["Value"]

    # Tạo danh sách các hàng cho DataFrame
    rows = []
    for i, value in enumerate(values):
        row = []
        for dim in dimensions["id"]:
            for key, index in dimensions[dim]["category"]["index"].items():
                if index == i % dimensions["size"][dimensions["id"].index(dim)]:
                    row.append(dimensions[dim]["category"]["label"][key])
        row.append(value)
        rows.append(row)

    # Tạo DataFrame
    df = pd.DataFrame(rows, columns=headers)

    return df


def transform_mileage(df_col: pd.Series) -> pd.Series:
    """
    Chuyển đổi đặc trưng số km đã đi bằng cách áp dụng logarithm
    """
    df = df_col.to_frame()
    df["mileage"] = df.iloc[:, 0]
    df["mileage_log"] = np.log(df["mileage"])
    return df["mileage_log"]


def transform_model(df_col: pd.Series) -> pd.Series:
    """
    Chuyển đổi đặc trưng model bằng cách ánh xạ đến giá tham khảo
    """
    # Lấy giá trị tham khảo
    MODEL_REF_PRICE_PATH = "data/raw/model_ref_price_full.csv"
    MODEL_REF_EXTRA_PRICE_PATH = "data/raw/model_ref_price_extra.csv"
    df_variants = pd.read_csv(MODEL_REF_PRICE_PATH)
    df_model_extra = pd.read_csv(MODEL_REF_EXTRA_PRICE_PATH)

    # Lọc bỏ giá null
    df_variants.dropna(subset="price_min", inplace=True)

    # Tính giá trung bình
    df_variants["price_avg"] = (df_variants["price_min"] + df_variants["price_max"]) / 2

    # Lấy model. Xử lý các trường hợp đặc biệt như 'Air Blade'
    df_variants["model_original"] = (
        df_variants["model_name"].str.split().apply(lambda x: x[0])
    )
    df_variants["model"] = df_variants["model_original"].case_when(
        caselist=[
            (df_variants["model_name"].str.contains("Air Blade"), "Air Blade"),
            (df_variants["model_name"].str.contains("SH Mode"), "SH Mode"),
            (df_variants["model_name"].str.contains("Super Cub"), "Cub"),
            (df_variants["model_name"].str.contains("Winner X"), "Winner X"),
            (df_variants["brand_name"].eq("Vespa"), "Vespa"),
        ]
    )

    # Tính giá trung bình theo model
    df_model_ref_price_original = df_variants.groupby(by="model", as_index=False).agg(
        {"price_avg": "mean"}
    )
    df_model_ref_price = pd.concat([df_model_ref_price_original, df_model_extra])
    df_model_ref_price["price_avg_log"] = np.log(
        df_model_ref_price["price_avg"] * 1_000
    )

    # Join với dataframe
    df = df_col.to_frame()
    df["model"] = df.iloc[:, 0]

    output_df = df.merge(
        right=df_model_ref_price, left_on="model", right_on="model", how="left"
    )

    return output_df["price_avg_log"]


def transform_origin(df_col: pd.Series) -> pd.Series:
    """
    Chuyển đổi đặc trưng xuất xứ bằng cách ánh xạ đến hệ số quốc gia
    """
    # Lấy giá trị tham khảo
    COUNTRY_MULTIPLIER_PATH = "data/raw/origin_country_multiplier.csv"
    df_countries = pd.read_csv(COUNTRY_MULTIPLIER_PATH)

    # Join với dataframe
    df = df_col.to_frame()
    df["origin"] = df.iloc[:, 0]
    output_df = df.merge(
        right=df_countries, left_on="origin", right_on="country_name", how="left"
    )

    # Kiểm tra giá trị nan
    count_nan_value = int(output_df["country_multiplier"].isnull().sum())
    if count_nan_value > 0:
        logging.error(
            f"Có giá trị nan: {output_df[output_df['country_multiplier'].isnull()]}"
        )
        raise ValueError(f"Tìm thấy {count_nan_value} giá trị nan")

    return output_df["country_multiplier"]


def transform_province(df_col: pd.Series) -> pd.Series:
    """
    Chuyển đổi đặc trưng tỉnh thành bằng cách ánh xạ đến giá trị SCOLI
    """
    # Lấy giá trị tham khảo
    SCOLI_PATH = "data/raw/input_scoli_2023.json"
    df_scoli = read_json_stat(file_path=SCOLI_PATH)
    df_scoli.columns = ["province", "year", "province_scoli"]

    # Join với dataframe
    df = df_col.to_frame()
    df["province"] = df.iloc[:, 0]
    output_df = df.merge(
        right=df_scoli, left_on="province", right_on="province", how="left"
    )

    # Kiểm tra giá trị nan
    count_nan_value = int(output_df["province_scoli"].isnull().sum())
    if count_nan_value > 0:
        logging.error(
            f"Có giá trị nan: {output_df[output_df['province_scoli'].isnull()]}"
        )
        raise ValueError(f"Tìm thấy {count_nan_value} giá trị nan")

    return output_df["province_scoli"]


def transform_reg_year(df_col: pd.Series) -> pd.Series:
    """
    Chuyển đổi đặc trưng năm đăng ký bằng cách tính tuổi xe logarit
    """
    # Đọc cột
    df = df_col.to_frame()
    df["reg_year"] = df.iloc[:, 0]
    df["age"] = CURRENT_YEAR - df["reg_year"]

    # Chuyển age = 0 thành age = 0.5 vì xe phải có một độ tuổi nào đó
    df["age_updated"] = df["age"].case_when(caselist=[(df["age"].eq(0), 0.5)])

    df["age_log"] = np.log(df["age_updated"])

    return df["age_log"]


def update_origin_from_text(row):
    """
    Cập nhật xuất xứ dựa trên mô tả và tiêu đề
    """
    if pd.isna(row["origin"]) or row["origin"].lower() in ["đang cập nhật", "nước khác"]:
        text = ""
        if "description" in row and not pd.isna(row["description"]):
            text += str(row["description"])
        if "title" in row and not pd.isna(row["title"]):
            text += " " + str(row["title"])
        text = text.lower().strip()
        
        for country, keywords in ORIGIN_MAPPING.items():
            if any(re.search(rf"\b{keyword}\b", text) for keyword in keywords):
                return country
        return "Việt Nam"
    else:
        return row["origin"]


def clean_training_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Làm sạch dữ liệu huấn luyện
    
    Args:
        df: DataFrame chứa dữ liệu thô
        
    Returns:
        DataFrame đã làm sạch
    """
    # Làm sạch cột giá
    df["price_clean"] = pd.to_numeric(df["price"].str.replace("đ", "").str.replace(".", ""))
    
    # Làm sạch cột tỉnh/thành phố
    df["province"] = df["location"].str.split(", ").apply(lambda x: x[-1])
    df["province_clean"] = df["province"].case_when(
        caselist=[
            (df["province"].eq("Tp Hồ Chí Minh"), "TP. Hồ Chí Minh"),
            (df["province"].eq("Bà Rịa - Vũng Tàu"), "Bà Rịa-Vũng Tàu"),
            (df["province"].eq("Thừa Thiên Huế"), "Thừa Thiên - Huế"),
            (df["province"].eq("Thanh Hóa"), "Thanh Hoá"),
            (df["province"].eq("Khánh Hòa"), "Khánh Hoà"),
            (df["province"].eq("Hòa Bình"), "Hoà Bình"),
        ]
    )
    
    # Làm sạch cột năm đăng ký
    df["reg_year_clean"] = pd.to_numeric(
        df["reg_year"].case_when(caselist=[(df["reg_year"].eq("trước năm 1980"), 1980)])
    )
    
    # Cập nhật xuất xứ từ mô tả và tiêu đề
    df["origin_updated"] = df.apply(update_origin_from_text, axis=1)
    
    # Giảm quy mô giá và chuyển đổi sang log
    df["price_clean"] = df["price_clean"] / 1_000
    df["price_log"] = np.log(df["price_clean"])
    
    return df


def clean_prediction_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Làm sạch dữ liệu dự đoán
    
    Args:
        df: DataFrame chứa dữ liệu dự đoán
        
    Returns:
        DataFrame đã làm sạch
    """
    # Đảm bảo location có giá trị
    if "location" not in df.columns or df["location"].isnull().any():
        df["location"] = "Hà Nội"  # Giá trị mặc định
    
    # Trích xuất tỉnh thành từ location
    df["province"] = df["location"].str.split(", ").apply(lambda x: x[-1])
    df["province_clean"] = df["province"].case_when(
        caselist=[
            (df["province"].eq("Tp Hồ Chí Minh"), "TP. Hồ Chí Minh"),
            (df["province"].eq("Bà Rịa - Vũng Tàu"), "Bà Rịa-Vũng Tàu"),
            (df["province"].eq("Thừa Thiên Huế"), "Thừa Thiên - Huế"),
            (df["province"].eq("Thanh Hóa"), "Thanh Hoá"),
            (df["province"].eq("Khánh Hòa"), "Khánh Hoà"),
            (df["province"].eq("Hòa Bình"), "Hoà Bình"),
        ]
    )
    
    # Cập nhật xuất xứ từ mô tả và tiêu đề nếu có
    df["origin_updated"] = df.apply(update_origin_from_text, axis=1)
    
    return df


def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Lọc dữ liệu để loại bỏ các giá trị không phù hợp và ngoại lai
    
    Args:
        df: DataFrame chứa dữ liệu đã làm sạch
        
    Returns:
        DataFrame đã lọc
    """
    # Loại bỏ các model không rõ ràng
    df_filter = df[~df["model"].isin(["Dòng khác", "dòng khác"])]
    
    # Giá phải ít nhất 1 triệu, tối đa 600 triệu (chỉ áp dụng cho dữ liệu huấn luyện)
    if "price_clean" in df.columns:
        df_filter = df_filter[
            df_filter["price_clean"].between(1_000, 600_000, inclusive="neither")
        ]
    
    # Chỉ giữ lại các model có giá tham khảo
    df_filter = df_filter[df_filter["model_ref_price_log"].notnull()]
    
    # Chỉ giữ lại các model có ít nhất 30 bài đăng (chỉ áp dụng cho dữ liệu huấn luyện)
    if "price_clean" in df.columns:
        df_model_count = df_filter.groupby("model").agg(counts=("model", "count")).reset_index()
        df_model_over_30 = df_model_count[df_model_count["counts"] >= 30]
        df_filter = df_filter[df_filter["model"].isin(df_model_over_30["model"])]
        
        # Loại bỏ các giá trị không hợp lý (chỉ áp dụng cho dữ liệu huấn luyện)
        df_filter = df_filter[
            ~((df_filter["model"] == "SH") & (df_filter["price_clean"] < 3_000))
        ]
        
        # Loại bỏ một số model cụ thể (chỉ áp dụng cho dữ liệu huấn luyện)
        df_filter = df_filter[~df_filter["model"].isin(["Vespa", "Cub", "R", "Dream"])]
    
    # Chỉ giữ lại các bản ghi có số km hợp lý
    df_filter = df_filter[df_filter["mileage"].between(500, 900_000)]
    
    return df_filter


def apply_feature_transformations(df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
    """
    Áp dụng các biến đổi đặc trưng cho dữ liệu
    
    Args:
        df: DataFrame chứa dữ liệu đã làm sạch
        is_training: Boolean xác định liệu đây có phải dữ liệu huấn luyện hay không
        
    Returns:
        DataFrame với các đặc trưng đã được biến đổi
    """
    # Chuyển đổi các cột cơ bản
    reg_year_col = "reg_year_clean" if is_training else "reg_year"
    origin_col = "origin_updated"
    province_col = "province_clean"
    
    df["age_log"] = transform_reg_year(df_col=df[reg_year_col])
    df["mileage_log"] = transform_mileage(df_col=df["mileage"])
    df["origin_multiplier"] = transform_origin(df_col=df[origin_col])
    df["model_ref_price_log"] = transform_model(df_col=df["model"])
    df["province_scoli"] = transform_province(df_col=df[province_col])
    
    return df


def prepare_feature_matrix(df: pd.DataFrame, include_province: bool = False) -> np.ndarray:
    """
    Chuẩn bị ma trận đặc trưng cho mô hình
    
    Args:
        df: DataFrame đã qua biến đổi đặc trưng
        include_province: Boolean xác định có đưa SCOLI vào ma trận đặc trưng hay không
        
    Returns:
        Ma trận đặc trưng X
    """
    # Danh sách các đặc trưng bậc 1 (không dùng đa thức cho age_log)
    df = df.reset_index(drop=True)
    features = ["age_log", "mileage_log", "origin_multiplier", "model_ref_price_log"]
    # Thêm constant và chuyển đổi thành numpy array
    X = sm.add_constant(df[features]).values
    return X


def process_training_data(df: pd.DataFrame, save_path: str = "data/processed") -> tuple:
    """
    Xử lý dữ liệu thô cho việc huấn luyện mô hình
    
    Args:
        df: DataFrame chứa dữ liệu thô với các cột cần thiết
        save_path: Đường dẫn thư mục để lưu dữ liệu đã làm giàu
        
    Returns:
        Tuple của (X, y) trong đó X là ma trận đặc trưng và y là vector mục tiêu
    """
    # Xác minh các cột cần thiết
    required_columns = ["price", "mileage", "model", "origin", "location", "reg_year"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Không tìm thấy cột bắt buộc {col} trong dữ liệu đầu vào")
    
    # Tạo thư mục lưu trữ nếu chưa tồn tại
    os.makedirs(save_path, exist_ok=True)
    
    # Làm sạch dữ liệu - hàm này sẽ tạo cột province từ location
    df_clean = clean_training_data(df)

    # Áp dụng các biến đổi đặc trưng
    df_transformed = apply_feature_transformations(df_clean, is_training=True)
    
    # Lọc dữ liệu
    df_filter = filter_data(df_transformed)
    
    # Chọn các cột cần thiết cho mô hình
    cols_for_model = [
        "price_log",
        "age_log",
        "mileage_log",
        "model",
        "model_ref_price_log",
        "origin",
        "origin_multiplier",
        "province_clean",
        "province_scoli",
    ]
    df_final = df_filter[cols_for_model]
    
    # Lưu thông tin về df_final để tiện debug và kiểm tra
    if save_path:
        df_final.to_csv(f"{save_path}/processed_training_data.csv", index=False)
    
    # Chuẩn bị ma trận đặc trưng và vector mục tiêu
    X = prepare_feature_matrix(df_final, include_province=False)
    y = df_final["price_log"].values
    
    # Lưu shape của X để kiểm tra khi dự đoán
    logger.info(f"Ma trận đặc trưng X có kích thước: {X.shape}")
    
    return X, y


def process_prediction_input(input_data: dict) -> tuple:
    """
    Xử lý dữ liệu đầu vào cho dự đoán
    
    Args:
        input_data: Dictionary hoặc DataFrame chứa các đặc trưng đầu vào
        
    Returns:
        Ma trận đặc trưng sẵn sàng cho dự đoán và DataFrame dữ liệu đã xử lý
    """
    # Chuyển thành DataFrame nếu là dict
    if isinstance(input_data, dict):
        df = pd.DataFrame([input_data])
    else:
        df = pd.DataFrame(input_data)
    
    # Xác minh các cột cần thiết
    required_columns = ["mileage", "model", "origin", "reg_year"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Không tìm thấy các cột bắt buộc: {', '.join(missing_columns)}")
    
    # Thêm cột location nếu không có
    if "location" not in df.columns:
        df["location"] = "Hà Nội"  # Giá trị mặc định
    
    # Làm sạch dữ liệu dự đoán
    df_clean = clean_prediction_data(df)
    # Áp dụng các biến đổi đặc trưng
    df_transformed = apply_feature_transformations(df_clean, is_training=False)

    # Kiểm tra và xử lý các giá trị NaN
    has_nan = df_transformed.isnull().any().any()
    if has_nan:
        logger.warning("Phát hiện giá trị NaN trong dữ liệu, đang thực hiện xử lý...")
        columns_with_nan = df_transformed.columns[df_transformed.isnull().any()].tolist()
        logger.warning(f"Các cột chứa NaN: {columns_with_nan}")
        
        # Điền giá trị cho các cột có NaN
        for col in columns_with_nan:
            if col == "model_ref_price_log":
                # Sử dụng giá trị trung bình cho model_ref_price_log
                df_transformed[col].fillna(df_transformed[col].median(), inplace=True)
            elif col == "origin_multiplier":
                # Giá trị mặc định cho origin_multiplier (ví dụ: 1.0 cho Việt Nam)
                df_transformed[col].fillna(1.0, inplace=True)
            elif col == "province_scoli":
                # Giá trị mặc định cho province_scoli (ví dụ: 100 cho Hà Nội)
                df_transformed[col].fillna(100.0, inplace=True)
            else:
                # Sử dụng giá trị trung bình cho các cột còn lại
                df_transformed[col].fillna(df_transformed[col].median(), inplace=True)

    # Chuẩn bị ma trận đặc trưng - sử dụng cùng hàm như khi huấn luyện
    X = prepare_feature_matrix(df_transformed, include_province=False)
    if X.shape[1] != 5:
        logger.error(f"Ma trận đặc trưng có {X.shape[1]} cột, nhưng cần 5 cột (bao gồm cột hằng số)")
        # Nếu thiếu cột hằng số, thêm vào
        if X.shape[1] == 4:
            logger.info("Đang thêm cột hằng số vào đầu ma trận đặc trưng")
            const_column = np.ones((X.shape[0], 1))
            X = np.hstack((const_column, X))
    # Log thông tin về kích thước của ma trận đặc trưng
    logger.info(f"Ma trận đặc trưng dự đoán có kích thước: {X.shape}")
    
    # Kiểm tra lần cuối xem ma trận đặc trưng có chứa NaN không
    if np.isnan(X).any():
        logger.warning("Ma trận đặc trưng X vẫn chứa giá trị NaN sau khi xử lý!")
        # Thay thế bất kỳ giá trị NaN còn lại bằng 0
        X = np.nan_to_num(X, nan=0.0)
        logger.info("Đã thay thế tất cả giá trị NaN còn lại bằng 0")
    
    return X, df_transformed