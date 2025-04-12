# webpages/price_prediction.py
import streamlit as st
import io
import base64
import pandas as pd
import os
from PIL import Image
from utils.price_prediction import MotorbikePricePredictor
from utils.data_service import *
from config import check_model
import logging

# Thiết lập logging
logger = logging.getLogger(__name__)
def show_price_prediction():
    """Hiển thị trang dự đoán giá xe"""
    st.title("Dự đoán giá xe máy cũ")
    st.markdown("Nhập thông tin xe để dự đoán giá.")
    
    # Tạo tabs cho các phương thức nhập
    tab1, tab2, tab3 = st.tabs(["Nhập thông số", "Tải lên ảnh", "Nhập mô tả"])
    
    with tab1:
        show_input_specs_tab()
    
    with tab2:
        show_upload_image_tab()
    
    with tab3:
        show_input_description_tab()

def show_input_specs_tab():
    """Hiển thị tab nhập thông số"""
    st.subheader("Nhập thông số xe")
    
    # Kiểm tra model tồn tại
    model_available = check_model()
    
    # Lấy danh sách thương hiệu
    brands = get_brands()
    
    col1, col2 = st.columns(2)
    with col1:
        brand = st.selectbox(
            "Thương hiệu",
            brands,
            key="brand_tab1",
        )
        
        # Lấy danh sách mẫu xe dựa trên thương hiệu đã chọn
        models = get_models(brand)
            
        model = st.selectbox(
            "Mẫu xe",
            models,
            key="model_tab1"
        )
        
        # # Lấy danh sách phiên bản dựa trên thương hiệu và mẫu xe đã chọn
        # if model and model != "Không có dữ liệu":
        #     try:
        #         # Lấy danh sách phiên bản
        #         variants = get_variants(brand, model)
                
        #         # Thêm tùy chọn "Tất cả phiên bản" vào đầu danh sách
        #         variant_options = ["Tất cả phiên bản"] + variants if variants else ["Tất cả phiên bản"]
                
        #         variant = st.selectbox(
        #             "Phiên bản",
        #             variant_options,
        #             key="variant_tab1",
        #             help="Chọn 'Tất cả phiên bản' nếu không nhớ chính xác phiên bản"
        #         )
                
        #         # Nếu chọn "Tất cả phiên bản", variant sẽ là None
        #         if variant == "Tất cả phiên bản":
        #             variant = None
                    
        #     except Exception as e:
        #         logger.error(f"Lỗi khi lấy thông tin phiên bản: {str(e)}")
        #         st.warning(f"Không thể lấy thông tin phiên bản: {str(e)}")
        #         variant = None
        # else:
        #     variant = None
        
        # year = st.slider(
        #     "Năm sản xuất", 
        #     min_value=2000, 
        #     max_value=2025, 
        #     value=2020,
        #     key="year_tab1"
        # )
    
    with col2:
        # Đổi số km đã đi thành các khoảng lựa chọn
        km_ranges = [
            "Dưới 5,000 km", 
            "5,000 - 10,000 km", 
            "10,000 - 20,000 km", 
            "20,000 - 30,000 km",
            "30,000 - 50,000 km",
            "Trên 50,000 km"
        ]
        
        km_range = st.selectbox(
            "Số km đã đi",
            km_ranges,
            index=2,  # Mặc định chọn "10,000 - 20,000 km"
            key="km_range_tab1"
        )
        
        # Chuyển đổi khoảng km thành giá trị số
        km_driven = convert_km_range_to_value(km_range)
        
        condition = "Tốt"
        year = 2022
        origin = st.selectbox(
            "Xuất xứ",
            ["Việt Nam", "Nhật Bản", "Đài Loan", "Ý", "Thái Lan", "Trung Quốc", "Khác"],
            key="origin_tab1"
        )
    
    if st.button("Dự đoán giá", key="predict_specs"):
        variant = ""
        process_prediction(brand, model, variant, year, km_driven, condition, origin)

def show_upload_image_tab():
    """Hiển thị tab tải lên ảnh"""
    st.subheader("Tải lên ảnh xe")
    
    # Kiểm tra model tồn tại
    model_available = check_model()
        
    uploaded_file = st.file_uploader("Chọn ảnh xe máy", type=["jpg", "jpeg", "png"], key="file_uploader_tab2")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Ảnh đã tải lên", use_column_width=True)
        
        if st.button("Phân tích ảnh", key="analyze_image_btn"):
            with st.spinner("Đang phân tích ảnh..."):
                try:
                    # Chuyển ảnh thành base64 để gửi đến API
                    buffered = io.BytesIO()
                    image.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    
                    # Gọi API để phân tích ảnh
                    analysis_result = analyze_image(img_str)
                    
                    # Hiển thị kết quả phân tích
                    st.success("Kết quả phân tích:")
                    
                    # Hiển thị thông số gợi ý từ API
                    st.subheader("Thông số xe nhận diện được:")
                    for key, value in analysis_result.items():
                        st.write(f"**{key}:** {value}")
                    
                    # Lấy giá trị thương hiệu và mẫu xe từ kết quả phân tích
                    brand_detected = analysis_result.get("brand", "Honda")
                    model_detected = analysis_result.get("model", "")
                    year_detected = analysis_result.get("year", 2020)
                    condition_detected = analysis_result.get("condition", "Tốt")
                    
                    # Display form for adjustment
                    show_adjustment_form_from_analysis(brand_detected, model_detected, year_detected, condition_detected, "tab2")
                except Exception as e:
                    logger.error(f"Lỗi khi phân tích ảnh: {str(e)}")
                    st.error(f"Không thể phân tích ảnh: {str(e)}")

def show_input_description_tab():
    """Hiển thị tab nhập mô tả"""
    st.subheader("Nhập mô tả xe")
    
    # Kiểm tra model tồn tại
    model_available = check_model()
        
    description = st.text_area(
        "Mô tả chi tiết về xe máy của bạn",
        height=150,
        placeholder="Ví dụ: Honda Wave RSX 110cc màu đỏ đen đời 2019, đã đi được khoảng 20.000 km. Xe còn mới, máy êm, ít hao xăng, phanh đĩa trước, đã thay nhớt định kỳ...",
        key="description_tab3"
    )
    
    if st.button("Phân tích mô tả", key="analyze_description_btn"):
        if description:
            with st.spinner("Đang phân tích mô tả..."):
                try:
                    # Gọi API để phân tích mô tả
                    analysis_result = analyze_description(description)
                    
                    # Hiển thị kết quả phân tích
                    st.success("Kết quả phân tích:")
                    
                    # Hiển thị thông số gợi ý từ API
                    st.subheader("Thông số xe nhận diện được:")
                    for key, value in analysis_result.items():
                        st.write(f"**{key}:** {value}")
                    
                    # Lấy giá trị từ kết quả phân tích
                    brand_detected = analysis_result.get("brand", "Honda")
                    model_detected = analysis_result.get("model", "")
                    year_detected = analysis_result.get("year", 2020)
                    km_detected = analysis_result.get("km_driven", 15000)
                    condition_detected = analysis_result.get("condition", "Tốt")
                    
                    # Show form for adjustment
                    show_adjustment_form_from_analysis(brand_detected, model_detected, year_detected, condition_detected, "tab3", km_detected)
                except Exception as e:
                    logger.error(f"Lỗi khi phân tích mô tả: {str(e)}")
                    st.error(f"Không thể phân tích mô tả: {str(e)}")
        else:
            st.error("Vui lòng nhập mô tả về xe máy của bạn")

def show_adjustment_form_from_analysis(brand_detected, model_detected, year_detected, condition_detected, tab_key, km_detected=None):
    """Hiển thị form điều chỉnh thông số dựa trên kết quả phân tích"""
    # Lấy danh sách thương hiệu và mẫu xe
    brands = get_brands()
    
    models = get_models(brand_detected) if brand_detected in brands else []
  
    
    # Tạo form để người dùng điều chỉnh thông số
    st.subheader("Điều chỉnh thông số (nếu cần):")
    
    col1, col2 = st.columns(2)
    with col1:
        brand = st.selectbox(
            "Thương hiệu",
            brands,
            index=brands.index(brand_detected) if brand_detected in brands else 0,
            key=f"brand_{tab_key}"
        )
        
        # Lấy lại danh sách mẫu xe nếu thương hiệu thay đổi
        if brand != brand_detected:
            try:
                models = get_models(brand)
            except Exception as e:
                models = []
        
        model = st.selectbox(
            "Mẫu xe",
            models if models else [""],
            index=models.index(model_detected) if model_detected in models and models else 0,
            key=f"model_{tab_key}"
        )
        
        # Chuyển year về số nguyên nếu là chuỗi
        if isinstance(year_detected, str):
            try:
                year_value = int(year_detected)
            except:
                try:
                    # Nếu có "năm" hoặc chứa nhiều số, lấy số đầu tiên
                    import re
                    year_matches = re.findall(r'\d{4}', year_detected)
                    if year_matches:
                        year_value = int(year_matches[0])
                    else:
                        year_value = 2020
                except:
                    year_value = 2020
        else:
            year_value = int(year_detected) if isinstance(year_detected, (int, float)) else 2020
        
        year = st.slider(
            "Năm sản xuất", 
            min_value=2000, 
            max_value=2025, 
            value=year_value,
            key=f"year_{tab_key}"
        )
    
    with col2:
        # Đổi số km đã đi thành các khoảng lựa chọn
        km_ranges = [
            "Dưới 5,000 km", 
            "5,000 - 10,000 km", 
            "10,000 - 20,000 km", 
            "20,000 - 30,000 km",
            "30,000 - 50,000 km",
            "Trên 50,000 km"
        ]
        
        # Xử lý số km từ kết quả phân tích
        if km_detected:
            try:
                km_value = int(km_detected) if isinstance(km_detected, (int, float)) else 15000
                # Chọn khoảng km phù hợp với giá trị phát hiện
                if km_value < 5000:
                    default_index = 0
                elif km_value < 10000:
                    default_index = 1
                elif km_value < 20000:
                    default_index = 2
                elif km_value < 30000:
                    default_index = 3
                elif km_value < 50000:
                    default_index = 4
                else:
                    default_index = 5
            except:
                default_index = 2  # Mặc định "10,000 - 20,000 km"
        else:
            default_index = 2  # Mặc định "10,000 - 20,000 km"
        
        km_range = st.selectbox(
            "Số km đã đi",
            km_ranges,
            index=default_index,
            key=f"km_range_{tab_key}"
        )
        
        # Chuyển đổi khoảng km thành giá trị số
        km_driven = convert_km_range_to_value(km_range)
        
        condition = "Tốt"
        
        origin = st.selectbox(
            "Xuất xứ",
            ["Việt Nam", "Nhật Bản", "Đài Loan", "Ý", "Thái Lan", "Trung Quốc", "Khác"],
            key=f"origin_{tab_key}"
        )
    
    if st.button("Dự đoán giá", key=f"predict_from_{tab_key}_btn"):
        variant = ""
        process_prediction(brand, model, variant, year, km_driven, condition, origin)

def process_prediction(brand, model, variant, year, km_driven, condition, origin):
    """Xử lý dự đoán giá"""
    try:
        with st.spinner("Đang dự đoán giá..."):
            # Khởi tạo model từ đường dẫn trong config
            predictor = MotorbikePricePredictor()
            
            # Chuẩn bị dữ liệu đầu vào
            input_data = {
                "brand": brand,
                "model": model,
                "variant": variant if variant else "",
                "reg_year": year,
                "mileage": km_driven,
                "origin": origin,
                "condition": condition
            }
            # Dự đoán giá
            result = predictor.predict(input_data)
            
            # Định dạng giá trị tiền để dễ đọc
            formatted_price = f"{result['price'] / 1_000_000:.2f}".rstrip('0').rstrip('.') if result['price'] % 1_000_000 == 0 else f"{result['price'] / 1_000_000:.2f}"
            formatted_low = f"{result['price_range'][0] / 1_000_000:.2f}".rstrip('0').rstrip('.')
            formatted_high = f"{result['price_range'][1] / 1_000_000:.2f}".rstrip('0').rstrip('.')
            
            # Hiển thị kết quả
            st.success("Kết quả dự đoán:")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Giá dự đoán", f"{formatted_price} triệu VND")
                st.metric("Khoảng giá", f"{formatted_low} - {formatted_high} triệu VND")
            with col2:
                st.progress(result['confidence'])
                st.write(f"Độ tin cậy: {int(result['confidence']*100)}%")
            
            
            # Tìm và hiển thị các bài đăng tương tự
            with st.spinner("Đang tìm kiếm các bài đăng tương tự..."):
                similar_listings = fetch_similar_listings(
                    predicted_price=result['price'],
                    input_data=input_data,
                )
                
                if not similar_listings.empty:
                    st.markdown("---")
                    display_similar_listings(similar_listings)
                else:
                    st.info("Không tìm thấy bài đăng tương tự.")
            
    except Exception as e:
        logger.error(f"Lỗi khi dự đoán giá: {str(e)}")
        st.error(f"Lỗi khi dự đoán giá: {str(e)}")

def convert_km_range_to_value(km_range):
    """Chuyển đổi khoảng km thành giá trị số"""
    if km_range == "Dưới 5,000 km":
        return 2500
    elif km_range == "5,000 - 10,000 km":
        return 7500
    elif km_range == "10,000 - 20,000 km":
        return 15000
    elif km_range == "20,000 - 30,000 km":
        return 25000
    elif km_range == "30,000 - 50,000 km":
        return 40000
    else:  # Trên 50,000 km
        return 60000
    
def fetch_similar_listings(predicted_price, input_data):
    """
    Truy vấn các bài đăng có giá gần với giá dự đoán
    
    Args:
        predicted_price: Giá dự đoán (VND)
        input_data: Dictionary chứa thông tin xe người dùng nhập (brand, model, reg_year, mileage, condition, origin)
        limit: Số lượng bài đăng muốn hiển thị
        max_days_old: Số ngày tối đa kể từ ngày đăng
        
    Returns:
        DataFrame chứa thông tin các bài đăng tương tự
    """
    try:
        # Trích xuất các thông số từ input_data
        model = input_data.get("model", "")
        year = input_data.get("reg_year")
        mileage = input_data.get("mileage")
        condition = input_data.get("condition")
        origin = input_data.get("origin")
        brand = input_data.get("brand")
        
        logger.info(f"Tìm kiếm bài đăng tương tự: brand={brand}, model={model}, year={year}, mileage={mileage}, condition={condition}, origin={origin}")
        
        # Gọi hàm get_similar_listings từ data_service với đầy đủ thông số
        similar_listings = get_similar_listings(
            predicted_price=predicted_price,
            brand=brand,
            model=model,
            year=year,
            mileage=mileage,
            condition=condition,
            origin=origin,
        )
        valid_urls = []
        count = 0
        for url in similar_listings['url_full']:
            try:
                if count > 5:
                    break
                count +=1
                # Thử kết nối và kiểm tra status code
                response = requests.get(url)
                
                # Chỉ giữ lại URL có status code 200
                if response.status_code == 200:
                    valid_urls.append(url)
            
            except requests.RequestException:
                # Bỏ qua các URL gặp lỗi kết nối
                continue
        
        # Lọc DataFrame chỉ giữ lại các URL hợp lệ
        similar_listings =  similar_listings[similar_listings['url_full'].isin(valid_urls)]
        logger.info(f"Đã tìm thấy {len(similar_listings)} bài đăng tương tự")
        return similar_listings
    
    except Exception as e:
        logger.error(f"Lỗi khi tìm kiếm bài đăng tương tự: {str(e)}")
        return pd.DataFrame()

def display_similar_listings(similar_listings):
    """
    Hiển thị các bài đăng có giá gần với giá dự đoán
    
    Args:
        similar_listings: DataFrame chứa thông tin các bài đăng tương tự
    """
    if similar_listings.empty:
        st.info("Không tìm thấy bài đăng tương tự.")
        return
    
    st.subheader("Các bài đăng tương tự trên thị trường")
    
    # Hiển thị các bài đăng
    for i, row in similar_listings.iterrows():
        with st.container():
            # Tạo layout với 3 columns
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                # Thông tin chính về xe
                st.markdown(f"**{row['title']}**")
                
                # Thông tin chi tiết về xe với icon
                if 'brand' in row and row['brand'] and 'model' in row and row['model']:
                    st.text(f"🏭 Model: {row['brand']} {row['model']}")
                if 'reg_year' in row and row['reg_year']:
                    st.text(f"📅 Năm đăng ký: {row['reg_year']}")
                if 'condition' in row and row['condition']:
                    st.text(f"🔍 Tình trạng: {row['condition']}")
                
                # Thông tin về vị trí và thời gian đăng
                if 'location' in row and row['location']:
                    st.text(f"📍 {row['location']}")
                
                # Thông tin về thời gian đăng
                if 'post_date_display' in row and row['post_date_display']:
                    st.text(f"⏱️ Đăng ngày: {row['post_date_display']}")
                elif 'days_since_posted' in row and row['days_since_posted'] is not None:
                    st.text(f"⏱️ Đã đăng: {row['days_since_posted']} ngày trước")
                
            with col2:
                # Thông tin kỹ thuật
                tech_details = []
                if 'mileage' in row and row['mileage']:
                    tech_details.append(f"📏 Số km: {row['mileage']}")
                if 'engine_capacity' in row and row['engine_capacity']:
                    tech_details.append(f"🔧 Dung tích: {row['engine_capacity']}")
                if 'origin' in row and row['origin']:
                    tech_details.append(f"🌐 Nguồn gốc: {row['origin']}")
                
                for detail in tech_details:
                    st.text(detail)
                
                # Mô tả ngắn nếu có
                if 'description' in row and row['description']:
                    # Cắt mô tả nếu quá dài
                    description = row['description']
                    if len(description) > 150:
                        description = description[:147] + "..."
                    st.markdown(f"📝 **Mô tả:**\n{description}")
            
            with col3:
                # Hiển thị giá và nút xem chi tiết
                if 'price_millions' in row and row['price_millions'] is not None:
                    st.markdown(f"### {row['price_millions']} triệu")
                elif 'price' in row and row['price']:
                    st.markdown(f"### {row['price']}")
                                
                # Tạo khóa duy nhất cho mỗi nút
                button_key = f"btn_listing_{row.get('id', i)}"
                
                # Kiểm tra URL có đầy đủ không
                url = row.get('url_full', row.get('url', ''))
                if url and not url.startswith(('http://', 'https://')):
                    url = f"https://xe.chotot.com{url}"
                
                # Hiển thị liên kết trực tiếp
                st.markdown(f"<a href='{url}' target='_blank'><button style='background-color:#1E88E5; color:white; border:none; border-radius:4px; padding:8px 16px; cursor:pointer; width:100%;'>Xem chi tiết</button></a>", unsafe_allow_html=True)
            
            st.markdown("---")