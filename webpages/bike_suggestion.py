# pages/bike_suggestion.py
import streamlit as st
import pandas as pd
from services.data_service import get_brands
from config import get_db_connection

def show_bike_suggestion():
    """Hiển thị trang gợi ý mua xe"""
    st.markdown('<div class="main-header">Gợi ý mua xe phù hợp</div>', unsafe_allow_html=True)
    
    # Các tiêu chí lựa chọn xe
    st.subheader("Các tiêu chí của bạn")
    
    col1, col2 = st.columns(2)
    
    with col1:
        budget = st.slider(
            "Ngân sách (triệu VND)", 
            min_value=10, 
            max_value=100, 
            value=30,
            step=5,
            key="budget_slider"
        )
        
        segment = st.selectbox(
            "Phân khúc xe",
            ["Tất cả", "Xe số", "Xe tay ga", "Xe côn tay"],
            key="segment_select"
        )
        
        engine_size = st.selectbox(
            "Dung tích động cơ",
            ["Tất cả", "Dưới 125cc", "125-150cc", "Trên 150cc"],
            key="engine_size_select"
        )
    
    with col2:
        purpose = st.selectbox(
            "Mục đích sử dụng",
            ["Đi lại hàng ngày", "Đi phố", "Đi xa", "Thể thao"],
            key="purpose_select"
        )
        
        brand_preference = st.multiselect(
            "Thương hiệu ưa thích",
            get_brands(),
            key="brand_preference_multi"
        )
        
        feature_preference = st.multiselect(
            "Tính năng quan trọng",
            ["ABS", "Phanh đĩa", "Vận hành tiết kiệm", "Cốp rộng", "Mạnh mẽ"],
            key="feature_preference_multi"
        )
    
    # Nút tìm kiếm
    if st.button("Tìm xe phù hợp", key="find_bike_btn"):
        process_bike_suggestion(budget, segment, engine_size, purpose, brand_preference, feature_preference)

def process_bike_suggestion(budget, segment, engine_size, purpose, brand_preference, feature_preference):
    """Xử lý gợi ý xe"""
    with st.spinner("Đang tìm kiếm xe phù hợp..."):
        # Xây dựng truy vấn dựa trên các tiêu chí
        query_conditions = []
        query_params = []
        
        # Điều kiện về ngân sách
        query_conditions.append("avg_price_used <= ?")
        query_params.append(budget)
        
        # Điều kiện về phân khúc
        if segment != "Tất cả":
            query_conditions.append("segment = ?")
            query_params.append(segment)
        
        # Điều kiện về dung tích động cơ
        if engine_size != "Tất cả":
            if engine_size == "Dưới 125cc":
                query_conditions.append("engine_cc < 125")
            elif engine_size == "125-150cc":
                query_conditions.append("engine_cc >= 125 AND engine_cc <= 150")
            elif engine_size == "Trên 150cc":
                query_conditions.append("engine_cc > 150")
        
        # Điều kiện về thương hiệu
        if brand_preference:
            placeholders = ", ".join(["?" for _ in brand_preference])
            query_conditions.append(f"brand IN ({placeholders})")
            query_params.extend(brand_preference)
        
        # Điều kiện về tính năng
        for feature in feature_preference:
            if feature == "ABS":
                query_conditions.append("abs = 1")
            elif feature == "Phanh đĩa":
                query_conditions.append("brake_front = 'Đĩa'")
            elif feature == "Vận hành tiết kiệm":
                query_conditions.append("fuel_consumption < 2.2")
            elif feature == "Cốp rộng":
                # Đây chỉ là giả định, trong thực tế cần có dữ liệu về kích thước cốp
                if "Xe tay ga" in segment or segment == "Tất cả":
                    query_conditions.append("segment = 'Xe tay ga'")
            elif feature == "Mạnh mẽ":
                query_conditions.append("horsepower > 10")
        
        # Xây dựng câu truy vấn hoàn chỉnh
        query = """
            SELECT 
                brand, model, variant, engine_cc, 
                price_new, avg_price_used, 
                segment, abs, transmission,
                fuel_consumption
            FROM motorbikes
        """
        
        if query_conditions:
            query += " WHERE " + " AND ".join(query_conditions)
        
        # Thêm sắp xếp
        if purpose == "Đi lại hàng ngày":
            query += " ORDER BY fuel_consumption, avg_price_used"
        elif purpose == "Đi phố":
            query += " ORDER BY weight, avg_price_used"
        elif purpose == "Đi xa":
            query += " ORDER BY fuel_capacity DESC, avg_price_used"
        elif purpose == "Thể thao":
            query += " ORDER BY horsepower DESC, torque DESC"
        
        # Giới hạn kết quả
        query += " LIMIT 10"
        
        # Thực hiện truy vấn
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(query, query_params)
            results = cursor.fetchall()
            conn.close()
            
            if results and len(results) > 0:
                display_bike_suggestions(results, budget, purpose)
            else:
                st.warning("Không tìm thấy xe phù hợp với tiêu chí của bạn. Hãy thử điều chỉnh lại các tiêu chí.")
        except Exception as e:
            st.error(f"Lỗi khi tìm kiếm xe phù hợp: {str(e)}")
            st.info("Vui lòng thử lại với các tiêu chí khác hoặc liên hệ với quản trị viên.")

def display_bike_suggestions(results, budget, purpose):
    """Hiển thị kết quả gợi ý xe"""
    # Hiển thị kết quả
    st.markdown('<div class="sub-header">Các xe phù hợp với tiêu chí của bạn</div>', unsafe_allow_html=True)
    
    # Chuyển đổi kết quả thành DataFrame
    results_df = pd.DataFrame([dict(row) for row in results])
    
    # Đổi tên cột để hiển thị đẹp hơn
    results_df = results_df.rename(columns={
        'brand': 'Thương hiệu',
        'model': 'Mẫu xe',
        'variant': 'Phiên bản',
        'engine_cc': 'Dung tích (cc)',
        'price_new': 'Giá mới (triệu)',
        'avg_price_used': 'Giá cũ TB (triệu)',
        'segment': 'Phân khúc',
        'abs': 'ABS',
        'transmission': 'Hộp số',
        'fuel_consumption': 'Tiêu thụ nhiên liệu (L/100km)'
    })
    
    # Hiển thị DataFrame
    st.dataframe(results_df)
    
    # Hiển thị top 3 gợi ý (hoặc ít hơn nếu không đủ kết quả)
    num_results = min(3, len(results))
    st.markdown(f"### Top {num_results} gợi ý")
    
    for i, row in enumerate(results[:num_results]):
        row_dict = dict(row)
        
        expander = st.expander(f"{i+1}. {row_dict['brand']} {row_dict['model']} {row_dict['variant']}")
        with expander:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Đây sẽ là nơi hiển thị hình ảnh trong trường hợp thực tế
                st.image("https://via.placeholder.com/150", caption=f"{row_dict['brand']} {row_dict['model']}")
            
            with col2:
                st.markdown(f"**Giá mới:** {row_dict['price_new']} triệu VND")
                st.markdown(f"**Giá cũ trung bình:** {row_dict['avg_price_used']} triệu VND")
                st.markdown(f"**Phân khúc:** {row_dict['segment']}")
                st.markdown(f"**Dung tích động cơ:** {row_dict['engine_cc']}cc")
                st.markdown(f"**Hộp số:** {row_dict['transmission']}")
                st.markdown(f"**Tiêu thụ nhiên liệu:** {row_dict['fuel_consumption']} L/100km")
                st.markdown(f"**ABS:** {'Có' if row_dict['abs'] else 'Không'}")
            
            # Đánh giá phù hợp
            st.markdown("#### Đánh giá phù hợp")
            
            # Đánh giá dựa trên ngân sách
            budget_fit = min(100, max(0, 100 - (row_dict['avg_price_used'] / budget * 100 - 80)))
            
            # Đánh giá dựa trên mục đích sử dụng
            purpose_fit = 50  # Giá trị mặc định
            if purpose == "Đi lại hàng ngày" and row_dict['fuel_consumption'] < 2.0:
                purpose_fit = 90
            elif purpose == "Đi phố" and row_dict['segment'] == "Xe tay ga":
                purpose_fit = 90
            elif purpose == "Đi xa" and row_dict['engine_cc'] >= 150:
                purpose_fit = 90
            elif purpose == "Thể thao" and "côn tay" in row_dict['segment'].lower():
                purpose_fit = 90
            
            # Tổng hợp đánh giá
            overall_fit = (budget_fit + purpose_fit) / 2
            
            # Hiển thị đánh giá
            st.markdown(f"**Phù hợp với ngân sách:** {budget_fit:.0f}%")
            st.markdown(f"**Phù hợp với mục đích sử dụng:** {purpose_fit:.0f}%")
            st.markdown(f"**Đánh giá tổng thể:** {overall_fit:.0f}%")
    
    # Hiển thị lời khuyên với kiểm tra số lượng kết quả
    if len(results) >= 2:
        # Nếu có ít nhất 2 kết quả, hiển thị lời khuyên đầy đủ
        st.info(f"""
            **Lời khuyên:** Dựa trên tiêu chí của bạn, chúng tôi đề xuất bạn nên tập trung vào các xe có giá trong khoảng {budget-5} đến {budget} triệu VND. 
            Nếu bạn cần xe chủ yếu cho mục đích {purpose.lower()}, hãy chú ý đến các mẫu xe {results[0]['brand']} {results[0]['model']} hoặc {results[1]['brand']} {results[1]['model']}.
            Các mẫu xe này đều có mức giá phù hợp và các tính năng đáp ứng nhu cầu của bạn.
        """)
    elif len(results) == 1:
        # Nếu chỉ có 1 kết quả
        st.info(f"""
            **Lời khuyên:** Dựa trên tiêu chí của bạn, chúng tôi đề xuất bạn nên tập trung vào các xe có giá trong khoảng {budget-5} đến {budget} triệu VND.
            Mẫu xe {results[0]['brand']} {results[0]['model']} có mức giá phù hợp và các tính năng đáp ứng nhu cầu của bạn cho mục đích {purpose.lower()}.
        """)
    else:
        # Trường hợp này không nên xảy ra vì chúng ta đã kiểm tra results trước đó
        st.info(f"""
            **Lời khuyên:** Dựa trên tiêu chí của bạn, chúng tôi đề xuất bạn nên tập trung vào các xe có giá trong khoảng {budget-5} đến {budget} triệu VND cho mục đích {purpose.lower()}.
        """)