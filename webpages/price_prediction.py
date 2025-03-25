# pages/price_prediction.py
import streamlit as st
import io
import base64
import pandas as pd
from PIL import Image
from services.data_service import get_brands, get_models, get_variants, get_prediction
from services.api_service import analyze_image, analyze_description
from config import get_db_connection

def show_price_prediction():
    """Hiển thị trang dự đoán giá xe"""
    st.markdown('<div class="main-header">Dự đoán giá xe máy cũ</div>', unsafe_allow_html=True)
    
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
    
    # Lấy danh sách thương hiệu
    brands = get_brands()
    
    col1, col2 = st.columns(2)
    with col1:
        brand = st.selectbox(
            "Thương hiệu",
            brands,
            key="brand_tab1"
        )
        
        # Lấy danh sách mẫu xe dựa trên thương hiệu đã chọn
        models = get_models(brand)
        model = st.selectbox(
            "Mẫu xe",
            models if models else [""],
            key="model_tab1"
        )
        
        # Lấy danh sách phiên bản dựa trên thương hiệu và mẫu xe đã chọn
        if model:
            try:
                # Lấy danh sách phiên bản
                variants = get_variants(brand, model)
                
                # Thêm tùy chọn "Tất cả phiên bản" vào đầu danh sách
                variant_options = ["Tất cả phiên bản"] + variants
                
                variant = st.selectbox(
                    "Phiên bản",
                    variant_options,
                    key="variant_tab1",
                    help="Chọn 'Tất cả phiên bản' nếu không nhớ chính xác phiên bản"
                )
                
                # Nếu chọn "Tất cả phiên bản", variant sẽ là None
                if variant == "Tất cả phiên bản":
                    variant = None
                    
            except Exception as e:
                st.warning(f"Không thể lấy thông tin phiên bản: {str(e)}")
                variant = None
        else:
            variant = None
        
        year = st.number_input(
            "Năm sản xuất", 
            min_value=1990, 
            max_value=2025, 
            value=2020,
            key="year_tab1"
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
        
        km_range = st.selectbox(
            "Số km đã đi",
            km_ranges,
            index=2,  # Mặc định chọn "10,000 - 20,000 km"
            key="km_range_tab1"
        )
        
        # Chuyển đổi khoảng km thành giá trị số
        km_driven = convert_km_range_to_value(km_range)
        
        condition = st.select_slider(
            "Tình trạng xe",
            options=["Rất kém", "Kém", "Trung bình", "Tốt", "Rất tốt"],
            value="Tốt",
            key="condition_tab1"
        )
        
        location = st.selectbox(
            "Khu vực",
            ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Khác"],
            key="location_tab1"
        )
    
    if st.button("Dự đoán giá", key="predict_specs"):
        process_prediction(brand, model, variant, year, km_driven, condition, location)

def show_upload_image_tab():
    """Hiển thị tab tải lên ảnh"""
    st.subheader("Tải lên ảnh xe")
    uploaded_file = st.file_uploader("Chọn ảnh xe máy", type=["jpg", "jpeg", "png"], key="file_uploader_tab2")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Ảnh đã tải lên", use_column_width=True)
        
        if st.button("Phân tích ảnh", key="analyze_image_btn"):
            with st.spinner("Đang phân tích ảnh..."):
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
                brand_detected = analysis_result.get("Thương hiệu", "Honda")
                model_detected = analysis_result.get("Mẫu xe", "").split()[0] if analysis_result.get("Mẫu xe", "") else ""
                
                # Display form for adjustment
                show_adjustment_form_from_analysis(brand_detected, model_detected, analysis_result.get("Năm sản xuất", "2019"), "tab2")

def show_input_description_tab():
    """Hiển thị tab nhập mô tả"""
    st.subheader("Nhập mô tả xe")
    description = st.text_area(
        "Mô tả chi tiết về xe máy của bạn",
        height=150,
        placeholder="Ví dụ: Honda Wave RSX 110cc màu đỏ đen đời 2019, đã đi được khoảng 20.000 km. Xe còn mới, máy êm, ít hao xăng, phanh đĩa trước, đã thay nhớt định kỳ...",
        key="description_tab3"
    )
    
    if st.button("Phân tích mô tả", key="analyze_description_btn"):
        if description:
            with st.spinner("Đang phân tích mô tả..."):
                # Gọi API để phân tích mô tả
                analysis_result = analyze_description(description)
                
                # Hiển thị kết quả phân tích
                st.success("Kết quả phân tích:")
                
                # Hiển thị thông số gợi ý từ API
                st.subheader("Thông số xe nhận diện được:")
                for key, value in analysis_result.items():
                    st.write(f"**{key}:** {value}")
                
                # Lấy giá trị thương hiệu và mẫu xe từ kết quả phân tích
                brand_detected = analysis_result.get("Thương hiệu", "Honda")
                model_detected = analysis_result.get("Mẫu xe", "").split()[0] if analysis_result.get("Mẫu xe", "") else ""
                
                # Show form for adjustment
                show_adjustment_form_from_analysis(brand_detected, model_detected, analysis_result.get("Năm sản xuất", "2019"), "tab3", analysis_result.get("Số km đã đi", "20,000 km"))
        else:
            st.error("Vui lòng nhập mô tả về xe máy của bạn")

def show_adjustment_form_from_analysis(brand_detected, model_detected, year_string, tab_key, km_string=None):
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
            models = get_models(brand)
        
        model = st.selectbox(
            "Mẫu xe",
            models if models else [""],
            index=models.index(model_detected) if model_detected in models and models else 0,
            key=f"model_{tab_key}"
        )
        
        # Lấy danh sách phiên bản
        if model:
            variants = get_variants(brand, model)
            variant_options = ["Tất cả phiên bản"] + variants
            
            variant = st.selectbox(
                "Phiên bản",
                variant_options,
                key=f"variant_{tab_key}",
                help="Chọn 'Tất cả phiên bản' nếu không nhớ chính xác phiên bản"
            )
            
            # Nếu chọn "Tất cả phiên bản", variant sẽ là None
            if variant == "Tất cả phiên bản":
                variant = None
        else:
            variant = None
        
        # Xử lý năm sản xuất từ chuỗi thành số
        try:
            if '-' in year_string:
                # Nếu là khoảng năm như "2018-2020"
                years = [int(y) for y in year_string.replace('Khoảng', '').strip().split('-')]
                year_value = sum(years) // len(years)  # Lấy giá trị trung bình
            else:
                # Nếu là một năm cụ thể
                year_value = int(''.join(filter(str.isdigit, year_string)))
        except:
            year_value = 2019
        
        year = st.number_input(
            "Năm sản xuất", 
            min_value=1990, 
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
        if km_string:
            try:
                km_value = int(''.join(filter(str.isdigit, km_string)))
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
        
        condition = st.select_slider(
            "Tình trạng xe",
            options=["Rất kém", "Kém", "Trung bình", "Tốt", "Rất tốt"],
            value="Tốt",
            key=f"condition_{tab_key}"
        )
        
        location = st.selectbox(
            "Khu vực",
            ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Khác"],
            key=f"location_{tab_key}"
        )
    
    if st.button("Dự đoán giá", key=f"predict_from_{tab_key}_btn"):
        process_prediction(brand, model, variant, year, km_driven, condition, location)

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

def process_prediction(brand, model, variant, year, km_driven, condition, location):
    """Xử lý dự đoán giá"""
    # Tạo payload từ thông số
    payload = {
        "brand": brand,
        "model": model,
        "variant": variant,
        "year": year,
        "km_driven": km_driven,
        "condition": condition,
        "location": location
    }
    
    # Dự đoán giá
    try:
        with st.spinner("Đang dự đoán giá..."):
            prediction = get_prediction(payload)
            
            if "error" in prediction and prediction["error"]:
                st.error(prediction["error"])
                return
            
            # Hiển thị kết quả dự đoán
            st.markdown('<div class="success-box">Kết quả dự đoán:</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Giá dự đoán", f"{prediction['price']} triệu VND")
                st.metric("Dải giá thị trường", f"{prediction['price_range'][0]} - {prediction['price_range'][1]} triệu VND")
            with col2:
                st.metric("Độ tin cậy", f"{int(prediction['confidence']*100)}%")
                st.write("Thời gian bán ước tính: 2-3 tuần")
            
            # Hiển thị các xe tương tự
            st.markdown('<div class="sub-header">Các xe tương tự trên thị trường</div>', unsafe_allow_html=True)
            
            # Lấy các xe tương tự từ database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if variant:
                cursor.execute("""
                    SELECT brand, model, variant, 
                           year_start as 'Năm', 
                           engine_cc as 'Dung tích (cc)', 
                           avg_price_used as 'Giá (triệu VND)'
                    FROM motorbikes
                    WHERE brand = ? AND model = ? AND variant = ?
                    ORDER BY avg_price_used
                    LIMIT 3
                """, (brand, model, variant))
            else:
                cursor.execute("""
                    SELECT brand, model, variant, 
                           year_start as 'Năm', 
                           engine_cc as 'Dung tích (cc)', 
                           avg_price_used as 'Giá (triệu VND)'
                    FROM motorbikes
                    WHERE brand = ? AND model = ?
                    ORDER BY avg_price_used
                    LIMIT 3
                """, (brand, model))
            
            similar_bikes = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            if similar_bikes:
                similar_df = pd.DataFrame(similar_bikes)
            else:
                # Nếu không tìm thấy xe tương tự, tạo dữ liệu mẫu
                similar_df = pd.DataFrame({
                    'brand': [brand, brand, brand],
                    'model': [model, model, model],
                    'variant': [variant if variant else f"{model}", variant if variant else f"{model}", variant if variant else f"{model}"],
                    'Năm': [year-1, year, year+1],
                    'Dung tích (cc)': [125, 125, 125],
                    'Giá (triệu VND)': [prediction['price_range'][0], prediction['price'], prediction['price_range'][1]]
                })
            
            # Hiển thị dữ liệu xe tương tự
            st.dataframe(similar_df)
    except Exception as e:
        st.error(f"Lỗi khi dự đoán giá: {str(e)}")