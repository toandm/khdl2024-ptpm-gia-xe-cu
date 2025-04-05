# pages/bike_comparison.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from config import get_db_connection
from utils.data_service import get_brands, get_models, get_variants

def show_bar_comparison(bike1_data, bike2_data):
    """Hiển thị biểu đồ cột so sánh chi tiết thông số"""
    try:
        # Thông số cần so sánh
        attributes = ['adjusted_price', 'engine_cc', 'horsepower', 'torque', 'fuel_consumption']
        attribute_names = ['Giá (triệu VND)', 'Dung tích (cc)', 'Công suất (hp)', 'Mô-men xoắn (Nm)', 'Tiêu thụ nhiên liệu (L/100km)']
        
        # Tạo DataFrame cho biểu đồ
        df = pd.DataFrame({
            'Thuộc tính': attribute_names,
            bike1_data['brand'] + ' ' + bike1_data['model']: [float(bike1_data[attr]) for attr in attributes],
            bike2_data['brand'] + ' ' + bike2_data['model']: [float(bike2_data[attr]) for attr in attributes]
        })
        
        # Tạo 5 biểu đồ riêng biệt trong một hàng
        cols = st.columns(5)
        
        for i, (attr, attr_name) in enumerate(zip(attributes, attribute_names)):
            with cols[i]:
                fig, ax = plt.subplots(figsize=(3, 5))
                
                # Lấy tên xe rút gọn
                bike1_name = bike1_data['model']
                bike2_name = bike2_data['model']
                
                # Vẽ biểu đồ cột
                x = np.arange(2)
                width = 0.5
                
                ax.bar(x, [float(bike1_data[attr]), float(bike2_data[attr])], width)
                
                # Thêm giá trị lên biểu đồ
                for j, v in enumerate([float(bike1_data[attr]), float(bike2_data[attr])]):
                    ax.text(x[j], v + 0.01 * v, f"{v:.1f}", ha='center', va='bottom', fontsize=8)
                
                # Thêm nhãn
                ax.set_xticks(x)
                ax.set_xticklabels([bike1_name, bike2_name], rotation=45, fontsize=8)
                
                # Tiêu đề
                ax.set_title(attr_name, fontsize=10)
                
                # Điều chỉnh layout
                plt.tight_layout()
                
                # Hiển thị trong streamlit
                st.pyplot(fig)
    except Exception as e:
        st.error(f"Lỗi khi tạo biểu đồ cột: {str(e)}")

def cost_analysis(bike1_data, bike2_data):
    """Phân tích so sánh chi phí giữa hai xe"""
    bike1_name = f"{bike1_data['brand']} {bike1_data['model']}"
    bike2_name = f"{bike2_data['brand']} {bike2_data['model']}"
    
    # So sánh giá mua
    price_diff = abs(bike1_data['adjusted_price'] - bike2_data['adjusted_price'])
    price_percentage = (price_diff / min(bike1_data['adjusted_price'], bike2_data['adjusted_price'])) * 100
    
    if price_diff < 0.5:
        price_analysis = f"Giá của hai xe gần như tương đương nhau."
    else:
        if bike1_data['adjusted_price'] > bike2_data['adjusted_price']:
            price_analysis = f"{bike1_name} đắt hơn {bike2_name} khoảng {price_diff:.1f} triệu VND (tương đương {price_percentage:.1f}%)."
        else:
            price_analysis = f"{bike2_name} đắt hơn {bike1_name} khoảng {price_diff:.1f} triệu VND (tương đương {price_percentage:.1f}%)."
    
    # Tính chi phí sử dụng
    # Giả định đi khoảng 10,000 km/năm, giá xăng 25,000 VND/lít
    fuel_cost_bike1 = (bike1_data['fuel_consumption'] / 100) * 10000 * 25000 / 1000000  # Triệu VND/năm
    fuel_cost_bike2 = (bike2_data['fuel_consumption'] / 100) * 10000 * 25000 / 1000000  # Triệu VND/năm
    
    fuel_diff = abs(fuel_cost_bike1 - fuel_cost_bike2)
    if fuel_diff < 0.2:
        fuel_analysis = f"Chi phí nhiên liệu hàng năm của hai xe gần như tương đương nhau."
    else:
        if fuel_cost_bike1 > fuel_cost_bike2:
            fuel_analysis = f"{bike2_name} tiết kiệm hơn khoảng {fuel_diff:.2f} triệu VND/năm về chi phí nhiên liệu."
        else:
            fuel_analysis = f"{bike1_name} tiết kiệm hơn khoảng {fuel_diff:.2f} triệu VND/năm về chi phí nhiên liệu."
    
    # Giả định chi phí bảo dưỡng bằng 5% giá xe mỗi năm
    maintenance_bike1 = bike1_data['adjusted_price'] * 0.05
    maintenance_bike2 = bike2_data['adjusted_price'] * 0.05
    
    maintenance_diff = abs(maintenance_bike1 - maintenance_bike2)
    if maintenance_diff < 0.2:
        maintenance_analysis = f"Chi phí bảo dưỡng ước tính của hai xe tương đối giống nhau."
    else:
        if maintenance_bike1 > maintenance_bike2:
            maintenance_analysis = f"Chi phí bảo dưỡng của {bike1_name} có thể cao hơn khoảng {maintenance_diff:.2f} triệu VND/năm."
        else:
            maintenance_analysis = f"Chi phí bảo dưỡng của {bike2_name} có thể cao hơn khoảng {maintenance_diff:.2f} triệu VND/năm."
    
    # Tổng chi phí sở hữu trong 3 năm
    total_cost_3yr_bike1 = bike1_data['adjusted_price'] + (fuel_cost_bike1 + maintenance_bike1) * 3
    total_cost_3yr_bike2 = bike2_data['adjusted_price'] + (fuel_cost_bike2 + maintenance_bike2) * 3
    
    total_diff = abs(total_cost_3yr_bike1 - total_cost_3yr_bike2)
    if total_cost_3yr_bike1 > total_cost_3yr_bike2:
        total_analysis = f"Tổng chi phí sở hữu trong 3 năm của {bike1_name} cao hơn khoảng {total_diff:.2f} triệu VND."
    else:
        total_analysis = f"Tổng chi phí sở hữu trong 3 năm của {bike2_name} cao hơn khoảng {total_diff:.2f} triệu VND."
    
    # Hiển thị phân tích chi phí
    st.subheader("Chi phí sở hữu")
    st.markdown(f"- {price_analysis}")
    st.markdown(f"- {fuel_analysis}")
    st.markdown(f"- {maintenance_analysis}")
    st.markdown(f"- {total_analysis}")
    
    # Tạo bảng chi phí
    cost_data = {
        "Chi phí": ["Giá mua (triệu VND)", "Chi phí nhiên liệu hàng năm (triệu VND)", 
                    "Chi phí bảo dưỡng hàng năm (triệu VND)", "Tổng chi phí 3 năm (triệu VND)"],
        bike1_name: [bike1_data['adjusted_price'], round(fuel_cost_bike1, 2), 
                     round(maintenance_bike1, 2), round(total_cost_3yr_bike1, 2)],
        bike2_name: [bike2_data['adjusted_price'], round(fuel_cost_bike2, 2), 
                     round(maintenance_bike2, 2), round(total_cost_3yr_bike2, 2)]
    }
    
    cost_df = pd.DataFrame(cost_data)
    st.dataframe(cost_df, use_container_width=True)

def overall_evaluation(bike1_data, bike2_data):
    """Đánh giá tổng thể và đưa ra khuyến nghị"""
    bike1_name = f"{bike1_data['brand']} {bike1_data['model']}"
    bike2_name = f"{bike2_data['brand']} {bike2_data['model']}"
    
    # Tính điểm cho từng xe (thang điểm 100)
    # Hiệu suất (40 điểm), chi phí (30 điểm), tiện nghi (30 điểm)
    
    # Điểm hiệu suất (dựa trên công suất, mô-men xoắn và trọng lượng)
    # Chuẩn hóa về thang điểm từ 0-40
    max_hp = max(bike1_data['horsepower'], bike2_data['horsepower'])
    max_torque = max(bike1_data['torque'], bike2_data['torque'])
    min_weight = min(bike1_data['weight'], bike2_data['weight'])
    
    # Điểm công suất (tối đa 15)
    hp_score1 = (bike1_data['horsepower'] / max_hp) * 15
    hp_score2 = (bike2_data['horsepower'] / max_hp) * 15
    
    # Điểm mô-men xoắn (tối đa 15)
    torque_score1 = (bike1_data['torque'] / max_torque) * 15
    torque_score2 = (bike2_data['torque'] / max_torque) * 15
    
    # Điểm trọng lượng (tối đa 10, nhẹ hơn điểm cao hơn)
    if bike1_data['weight'] == 0 or bike2_data['weight'] == 0:
        weight_score1 = weight_score2 = 5
    else:
        weight_score1 = (min_weight / bike1_data['weight']) * 10
        weight_score2 = (min_weight / bike2_data['weight']) * 10
    
    # Tổng điểm hiệu suất
    performance_score1 = hp_score1 + torque_score1 + weight_score1
    performance_score2 = hp_score2 + torque_score2 + weight_score2
    
    # Điểm chi phí (tối đa 30 điểm)
    # Giá mua (tối đa 15 điểm)
    min_price = min(bike1_data['adjusted_price'], bike2_data['adjusted_price'])
    if min_price > 0:
        price_score1 = (min_price / bike1_data['adjusted_price']) * 15
        price_score2 = (min_price / bike2_data['adjusted_price']) * 15
    else:
        price_score1 = price_score2 = 7.5
    
    # Tiêu thụ nhiên liệu (tối đa 15 điểm)
    min_consumption = min(bike1_data['fuel_consumption'], bike2_data['fuel_consumption'])
    if min_consumption > 0:
        fuel_score1 = (min_consumption / bike1_data['fuel_consumption']) * 15
        fuel_score2 = (min_consumption / bike2_data['fuel_consumption']) * 15
    else:
        fuel_score1 = fuel_score2 = 7.5
    
    # Tổng điểm chi phí
    cost_score1 = price_score1 + fuel_score1
    cost_score2 = price_score2 + fuel_score2
    
    # Điểm tiện nghi (tối đa 30 điểm)
    # Đánh giá dựa trên phân khúc
    if bike1_data['segment'] == 'Xe tay ga':
        convenience_score1 = 25
    elif bike1_data['segment'] == 'Xe côn tay':
        convenience_score1 = 20
    else:  # Xe số
        convenience_score1 = 15
    
    if bike2_data['segment'] == 'Xe tay ga':
        convenience_score2 = 25
    elif bike2_data['segment'] == 'Xe côn tay':
        convenience_score2 = 20
    else:  # Xe số
        convenience_score2 = 15
    
    # Thêm điểm cho dung tích bình xăng (tối đa 5 điểm)
    max_fuel_capacity = max(bike1_data['fuel_capacity'], bike2_data['fuel_capacity'])
    if max_fuel_capacity > 0:
        fuel_cap_score1 = (bike1_data['fuel_capacity'] / max_fuel_capacity) * 5
        fuel_cap_score2 = (bike2_data['fuel_capacity'] / max_fuel_capacity) * 5
    else:
        fuel_cap_score1 = fuel_cap_score2 = 2.5
    
    # Tổng điểm tiện nghi
    convenience_score1 += fuel_cap_score1
    convenience_score2 += fuel_cap_score2
    
    # Tổng điểm
    total_score1 = performance_score1 + cost_score1 + convenience_score1
    total_score2 = performance_score2 + cost_score2 + convenience_score2
    
    # Hiển thị điểm số
    st.subheader("Đánh giá tổng thể")
    
    # Tạo bảng điểm
    score_data = {
        "Tiêu chí": ["Hiệu suất (40 điểm)", "Chi phí (30 điểm)", "Tiện nghi (30 điểm)", "Tổng điểm (100 điểm)"],
        bike1_name: [round(performance_score1, 1), round(cost_score1, 1), 
                     round(convenience_score1, 1), round(total_score1, 1)],
        bike2_name: [round(performance_score2, 1), round(cost_score2, 1), 
                     round(convenience_score2, 1), round(total_score2, 1)]
    }
    
    score_df = pd.DataFrame(score_data)
    st.dataframe(score_df, use_container_width=True)
    
    # Hiển thị đánh giá và gợi ý
    st.markdown("### Kết luận")
    
    score_diff = abs(total_score1 - total_score2)
    if score_diff < 5:
        conclusion = f"""
        **Cả hai xe có điểm số khá tương đồng** (chênh lệch < 5 điểm), việc lựa chọn giữa hai xe phụ thuộc nhiều vào sở thích cá nhân và mục đích sử dụng cụ thể của bạn.
        """
    else:
        if total_score1 > total_score2:
            conclusion = f"""
            **{bike1_name} đạt điểm cao hơn** với {round(total_score1, 1)} điểm so với {round(total_score2, 1)} điểm của {bike2_name}. 
            Xe này nổi bật hơn ở {'hiệu suất' if performance_score1 > performance_score2 else 'chi phí' if cost_score1 > cost_score2 else 'tiện nghi'}.
            """
        else:
            conclusion = f"""
            **{bike2_name} đạt điểm cao hơn** với {round(total_score2, 1)} điểm so với {round(total_score1, 1)} điểm của {bike1_name}. 
            Xe này nổi bật hơn ở {'hiệu suất' if performance_score2 > performance_score1 else 'chi phí' if cost_score2 > cost_score1 else 'tiện nghi'}.
            """
    
    st.markdown(conclusion)
    
    # Gợi ý dựa trên mục đích sử dụng
    st.markdown("### Gợi ý theo mục đích sử dụng")
    
    # Xe phù hợp cho đi lại hàng ngày (tiêu chí: tiết kiệm nhiên liệu, giá thành)
    daily_score1 = fuel_score1 * 1.5 + price_score1 * 1.2
    daily_score2 = fuel_score2 * 1.5 + price_score2 * 1.2
    
    # Xe phù hợp cho đi xa (tiêu chí: công suất, bình xăng, tiện nghi)
    travel_score1 = hp_score1 + fuel_cap_score1 * 2 + convenience_score1
    travel_score2 = hp_score2 + fuel_cap_score2 * 2 + convenience_score2
    
    # Xe phù hợp cho thể thao (tiêu chí: công suất, mô-men xoắn, trọng lượng)
    sport_score1 = hp_score1 * 1.5 + torque_score1 * 1.5 + weight_score1
    sport_score2 = hp_score2 * 1.5 + torque_score2 * 1.5 + weight_score2
    
    suggestions = [
        f"**Đi lại hàng ngày**: {'Cả hai xe đều phù hợp' if abs(daily_score1 - daily_score2) < 5 else bike1_name if daily_score1 > daily_score2 else bike2_name} {'vì tiết kiệm nhiên liệu và chi phí sở hữu hợp lý' if abs(daily_score1 - daily_score2) < 5 else f'phù hợp hơn vì tiết kiệm nhiên liệu hơn và chi phí sở hữu thấp hơn' if (daily_score1 > daily_score2 and bike1_data['fuel_consumption'] < bike2_data['fuel_consumption']) or (daily_score2 > daily_score1 and bike2_data['fuel_consumption'] < bike1_data['fuel_consumption']) else f'phù hợp hơn về tổng chi phí sở hữu'}.",
        
        f"**Đi xa**: {'Cả hai xe đều phù hợp' if abs(travel_score1 - travel_score2) < 5 else bike1_name if travel_score1 > travel_score2 else bike2_name} {'vì có đủ công suất và bình xăng dung tích lớn' if abs(travel_score1 - travel_score2) < 5 else f'phù hợp hơn vì có bình xăng dung tích lớn hơn và công suất tốt' if (travel_score1 > travel_score2 and bike1_data['fuel_capacity'] > bike2_data['fuel_capacity']) or (travel_score2 > travel_score1 and bike2_data['fuel_capacity'] > bike1_data['fuel_capacity']) else f'phù hợp hơn vì có công suất và khả năng vận hành tốt hơn'}.",
        
        f"**Thể thao**: {'Cả hai xe đều phù hợp' if abs(sport_score1 - sport_score2) < 5 else bike1_name if sport_score1 > sport_score2 else bike2_name} {'vì có công suất và mô-men xoắn tốt' if abs(sport_score1 - sport_score2) < 5 else f'phù hợp hơn vì có công suất mạnh hơn và mô-men xoắn tốt hơn' if (sport_score1 > sport_score2 and bike1_data['horsepower'] > bike2_data['horsepower']) or (sport_score2 > sport_score1 and bike2_data['horsepower'] > bike1_data['horsepower']) else f'phù hợp hơn về tổng thể về mặt hiệu suất'}"
    ]
    
    for suggestion in suggestions:
        st.markdown(f"- {suggestion}")
    
    # Lời kết
    st.markdown("""
    ### Lời khuyên cuối cùng
    Tham khảo ý kiến của các chuyên gia và trải nghiệm trực tiếp cả hai xe trước khi đưa ra quyết định cuối cùng. 
    Mỗi xe đều có ưu điểm riêng và phù hợp với các nhu cầu cụ thể.
    """)

def show_bike_comparison():
    """Hiển thị trang so sánh xe"""
    st.markdown('<div class="main-header">So sánh xe máy</div>', unsafe_allow_html=True)
    
    # Tạo layout với 2 cột để chọn xe so sánh
    st.subheader("Chọn xe để so sánh")
    
    col1, col2 = st.columns(2)
    
    # Các thông tin xe để so sánh
    bike1 = {}
    bike2 = {}
    
    # Xe thứ nhất
    with col1:
        st.markdown("### Xe thứ nhất")
        brands = get_brands()
        bike1['brand'] = st.selectbox(
            "Thương hiệu",
            brands,
            key="brand_bike1"
        )
        
        models = get_models(bike1['brand'])
        bike1['model'] = st.selectbox(
            "Mẫu xe", 
            models if models else [""],
            key="model_bike1"
        )
        
        if bike1['model']:
            variants = get_variants(bike1['brand'], bike1['model'])
            variant_options = ["Tất cả phiên bản"] + variants
            selected_variant = st.selectbox(
                "Phiên bản",
                variant_options,
                key="variant_bike1"
            )
            
            bike1['variant'] = None if selected_variant == "Tất cả phiên bản" else selected_variant
            
            # Thêm năm sản xuất (tùy chọn)
            bike1['year'] = st.number_input(
                "Năm sản xuất",
                min_value=1990,
                max_value=2025,
                value=2020,
                key="year_bike1"
            )
    
    # Xe thứ hai
    with col2:
        st.markdown("### Xe thứ hai")
        bike2['brand'] = st.selectbox(
            "Thương hiệu",
            brands,
            key="brand_bike2"
        )
        
        models = get_models(bike2['brand'])
        bike2['model'] = st.selectbox(
            "Mẫu xe",
            models if models else [""],
            key="model_bike2"
        )
        
        if bike2['model']:
            variants = get_variants(bike2['brand'], bike2['model'])
            variant_options = ["Tất cả phiên bản"] + variants
            selected_variant = st.selectbox(
                "Phiên bản",
                variant_options,
                key="variant_bike2"
            )
            
            bike2['variant'] = None if selected_variant == "Tất cả phiên bản" else selected_variant
            
            # Thêm năm sản xuất (tùy chọn)
            bike2['year'] = st.number_input(
                "Năm sản xuất",
                min_value=1990,
                max_value=2025,
                value=2020,
                key="year_bike2"
            )
    
    # Nút so sánh
    if st.button("So sánh xe", key="compare_bikes_btn"):
        if bike1['model'] and bike2['model']:
            compare_bikes(bike1, bike2)
        else:
            st.warning("Vui lòng chọn đầy đủ thông tin cả hai xe để so sánh.")

def get_bike_data(bike_info):
    """Lấy thông tin chi tiết về xe từ cơ sở dữ liệu"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if bike_info.get('variant'):
            # Truy vấn cụ thể theo variant
            cursor.execute("""
                SELECT * FROM motorbikes
                WHERE brand = ? AND model = ? AND variant = ?
                LIMIT 1
            """, (bike_info['brand'], bike_info['model'], bike_info['variant']))
        else:
            # Truy vấn không chọn cụ thể variant
            cursor.execute("""
                SELECT 
                    brand, model, 'Trung bình các phiên bản' as variant,
                    AVG(engine_cc) as engine_cc, 
                    AVG(price_new) as price_new,
                    AVG(avg_price_used) as avg_price_used,
                    AVG(fuel_consumption) as fuel_consumption,
                    AVG(horsepower) as horsepower,
                    AVG(torque) as torque,
                    AVG(weight) as weight,
                    AVG(fuel_capacity) as fuel_capacity,
                    MIN(year_start) as year_start,
                    MAX(year_end) as year_end,
                    segment, transmission
                FROM motorbikes
                WHERE brand = ? AND model = ?
                GROUP BY brand, model, segment, transmission
                LIMIT 1
            """, (bike_info['brand'], bike_info['model']))
        
        bike_data = cursor.fetchone()
        conn.close()
        
        if bike_data:
            # Tính giá trị giảm theo năm
            bike_dict = dict(bike_data)
            
            # Điều chỉnh giá theo năm đã chọn
            if 'year' in bike_info and bike_info['year'] > 0:
                # Lấy năm được chọn
                year = bike_info['year']
                
                # Tính số năm chênh lệch (từ năm bắt đầu sản xuất)
                year_diff = year - bike_dict['year_start'] if year > bike_dict['year_start'] else 0
                
                # Điều chỉnh giá trị xe dựa trên năm (giảm 5% mỗi năm)
                price_used = float(bike_dict['avg_price_used'])
                price_used = price_used * (0.95 ** year_diff)
                
                # Cập nhật giá đã điều chỉnh
                bike_dict['adjusted_price'] = round(price_used, 1)
            else:
                bike_dict['adjusted_price'] = bike_dict['avg_price_used']
            
            return bike_dict
        
        return None
    except Exception as e:
        st.error(f"Lỗi khi lấy thông tin xe: {str(e)}")
        return None

def compare_bikes(bike1, bike2):
    """So sánh hai xe dựa trên thông tin đã chọn"""
    # Lấy dữ liệu chi tiết về hai xe
    bike1_data = get_bike_data(bike1)
    bike2_data = get_bike_data(bike2)
    
    if not bike1_data or not bike2_data:
        st.error("Không thể lấy đủ thông tin để so sánh. Vui lòng thử lại với các lựa chọn khác.")
        return
    
    # Hiển thị kết quả so sánh
    st.markdown("## Kết quả so sánh")
    
    # Tạo và hiển thị bảng so sánh chi tiết
    comparison_table = create_comparison_table(bike1_data, bike2_data)
    st.dataframe(comparison_table, use_container_width=True)
    
    # Hiển thị biểu đồ radar để so sánh tổng thể
    st.markdown("### Biểu đồ so sánh tổng thể")
    show_radar_chart(bike1_data, bike2_data)
    
    # Vẽ biểu đồ cột để so sánh chi tiết
    st.markdown("### Biểu đồ so sánh chi tiết")
    show_bar_comparison(bike1_data, bike2_data)
    
    # Phân tích chi phí
    st.markdown("### Phân tích chi phí sở hữu")
    cost_analysis(bike1_data, bike2_data)
    
    # Đánh giá tổng thể
    overall_evaluation(bike1_data, bike2_data)

def create_comparison_table(bike1_data, bike2_data):
    """Tạo bảng so sánh chi tiết giữa hai xe"""
    bike1_name = f"{bike1_data['brand']} {bike1_data['model']}"
    bike2_name = f"{bike2_data['brand']} {bike2_data['model']}"
    
    # Tạo DataFrame cho toàn bộ so sánh
    comparison_data = []
    
    # 1. THÔNG SỐ CƠ BẢN
    comparison_data.append({
        "Chỉ tiêu": "**THÔNG SỐ CƠ BẢN**",
        "Nhận xét": "",
        bike1_name: "",
        bike2_name: ""
    })
    
    # Thương hiệu
    comparison_data.append({
        "Chỉ tiêu": "Thương hiệu",
        "Nhận xét": f"{'Cùng thương hiệu' if bike1_data['brand'] == bike2_data['brand'] else 'Khác thương hiệu'}",
        bike1_name: bike1_data['brand'],
        bike2_name: bike2_data['brand']
    })
    
    # Phân khúc
    comparison_data.append({
        "Chỉ tiêu": "Phân khúc",
        "Nhận xét": f"{'Cùng phân khúc' if bike1_data['segment'] == bike2_data['segment'] else 'Khác phân khúc'}",
        bike1_name: bike1_data['segment'],
        bike2_name: bike2_data['segment']
    })
    
    # Hộp số
    comparison_data.append({
        "Chỉ tiêu": "Hộp số",
        "Nhận xét": f"{'Cùng loại' if bike1_data['transmission'] == bike2_data['transmission'] else 'Khác loại'}",
        bike1_name: bike1_data['transmission'],
        bike2_name: bike2_data['transmission']
    })
    
    # Năm sản xuất
    comparison_data.append({
        "Chỉ tiêu": "Năm sản xuất",
        "Nhận xét": f"Chênh lệch {abs(bike1_data['year_start'] - bike2_data['year_start'])} năm",
        bike1_name: str(bike1_data['year_start']),
        bike2_name: str(bike2_data['year_start'])
    })
    
    # 2. ĐỘNG CƠ VÀ HIỆU SUẤT
    comparison_data.append({
        "Chỉ tiêu": "**ĐỘNG CƠ VÀ HIỆU SUẤT**",
        "Nhận xét": "",
        bike1_name: "",
        bike2_name: ""
    })
    
    # Dung tích động cơ
    engine_diff = round(abs(bike1_data['engine_cc'] - bike2_data['engine_cc']), 1)
    engine_diff_percent = round((engine_diff / min(bike1_data['engine_cc'], bike2_data['engine_cc'])) * 100, 1) if min(bike1_data['engine_cc'], bike2_data['engine_cc']) > 0 else 0
    
    if engine_diff < 1:
        engine_comment = "Tương đương"
    else:
        engine_comment = f"{bike1_name if bike1_data['engine_cc'] > bike2_data['engine_cc'] else bike2_name} lớn hơn {engine_diff_percent}%"
    
    comparison_data.append({
        "Chỉ tiêu": "Dung tích động cơ (cc)",
        "Nhận xét": engine_comment,
        bike1_name: str(round(bike1_data['engine_cc'], 1)),
        bike2_name: str(round(bike2_data['engine_cc'], 1))
    })
    
    # Công suất
    hp_diff = round(abs(bike1_data['horsepower'] - bike2_data['horsepower']), 1)
    hp_diff_percent = round((hp_diff / min(bike1_data['horsepower'], bike2_data['horsepower'])) * 100, 1) if min(bike1_data['horsepower'], bike2_data['horsepower']) > 0 else 0
    
    if hp_diff < 0.5:
        hp_comment = "Tương đương"
    else:
        hp_comment = f"{bike1_name if bike1_data['horsepower'] > bike2_data['horsepower'] else bike2_name} mạnh hơn {hp_diff_percent}%"
    
    comparison_data.append({
        "Chỉ tiêu": "Công suất (hp)",
        "Nhận xét": hp_comment,
        bike1_name: str(round(bike1_data['horsepower'], 1)),
        bike2_name: str(round(bike2_data['horsepower'], 1))
    })
    
    # Mô-men xoắn
    torque_diff = round(abs(bike1_data['torque'] - bike2_data['torque']), 1)
    torque_diff_percent = round((torque_diff / min(bike1_data['torque'], bike2_data['torque'])) * 100, 1) if min(bike1_data['torque'], bike2_data['torque']) > 0 else 0
    
    if torque_diff < 0.5:
        torque_comment = "Tương đương"
    else:
        torque_comment = f"{bike1_name if bike1_data['torque'] > bike2_data['torque'] else bike2_name} cao hơn {torque_diff_percent}%"
    
    comparison_data.append({
        "Chỉ tiêu": "Mô-men xoắn (Nm)",
        "Nhận xét": torque_comment,
        bike1_name: str(round(bike1_data['torque'], 1)),
        bike2_name: str(round(bike2_data['torque'], 1))
    })
    
    # 3. KÍCH THƯỚC VÀ TRỌNG LƯỢNG
    comparison_data.append({
        "Chỉ tiêu": "**KÍCH THƯỚC VÀ TRỌNG LƯỢNG**",
        "Nhận xét": "",
        bike1_name: "",
        bike2_name: ""
    })
    
    # Trọng lượng
    weight_diff = round(abs(bike1_data['weight'] - bike2_data['weight']), 1)
    weight_diff_percent = round((weight_diff / min(bike1_data['weight'], bike2_data['weight'])) * 100, 1) if min(bike1_data['weight'], bike2_data['weight']) > 0 else 0
    
    if weight_diff < 3:
        weight_comment = "Tương đương"
    else:
        weight_comment = f"{bike1_name if bike1_data['weight'] < bike2_data['weight'] else bike2_name} nhẹ hơn {weight_diff_percent}%"
    
    comparison_data.append({
        "Chỉ tiêu": "Trọng lượng (kg)",
        "Nhận xét": weight_comment,
        bike1_name: str(round(bike1_data['weight'], 1)),
        bike2_name: str(round(bike2_data['weight'], 1))
    })
    
    # Dung tích bình xăng
    fuel_cap_diff = round(abs(bike1_data['fuel_capacity'] - bike2_data['fuel_capacity']), 1)
    fuel_cap_diff_percent = round((fuel_cap_diff / min(bike1_data['fuel_capacity'], bike2_data['fuel_capacity'])) * 100, 1) if min(bike1_data['fuel_capacity'], bike2_data['fuel_capacity']) > 0 else 0
    
    if fuel_cap_diff < 0.5:
        fuel_cap_comment = "Tương đương"
    else:
        fuel_cap_comment = f"{bike1_name if bike1_data['fuel_capacity'] > bike2_data['fuel_capacity'] else bike2_name} lớn hơn {fuel_cap_diff_percent}%"
    
    comparison_data.append({
        "Chỉ tiêu": "Dung tích bình xăng (L)",
        "Nhận xét": fuel_cap_comment,
        bike1_name: str(round(bike1_data['fuel_capacity'], 1)),
        bike2_name: str(round(bike2_data['fuel_capacity'], 1))
    })
    
    # 4. CHI PHÍ
    comparison_data.append({
        "Chỉ tiêu": "**CHI PHÍ**",
        "Nhận xét": "",
        bike1_name: "",
        bike2_name: ""
    })
    
    # Giá mới
    price_new_diff = round(abs(bike1_data['price_new'] - bike2_data['price_new']), 1)
    price_new_diff_percent = round((price_new_diff / min(bike1_data['price_new'], bike2_data['price_new'])) * 100, 1) if min(bike1_data['price_new'], bike2_data['price_new']) > 0 else 0
    
    if price_new_diff < 1:
        price_new_comment = "Tương đương"
    else:
        price_new_comment = f"{bike1_name if bike1_data['price_new'] < bike2_data['price_new'] else bike2_name} rẻ hơn {price_new_diff_percent}%"
    
    comparison_data.append({
        "Chỉ tiêu": "Giá mới (triệu VND)",
        "Nhận xét": price_new_comment,
        bike1_name: str(round(bike1_data['price_new'], 1)),
        bike2_name: str(round(bike2_data['price_new'], 1))
    })
    
    # Giá cũ ước tính
    price_used_diff = round(abs(bike1_data['adjusted_price'] - bike2_data['adjusted_price']), 1)
    price_used_diff_percent = round((price_used_diff / min(bike1_data['adjusted_price'], bike2_data['adjusted_price'])) * 100, 1) if min(bike1_data['adjusted_price'], bike2_data['adjusted_price']) > 0 else 0
    
    if price_used_diff < 1:
        price_used_comment = "Tương đương"
    else:
        price_used_comment = f"{bike1_name if bike1_data['adjusted_price'] < bike2_data['adjusted_price'] else bike2_name} rẻ hơn {price_used_diff_percent}%"
    
    comparison_data.append({
        "Chỉ tiêu": "Giá cũ ước tính (triệu VND)",
        "Nhận xét": price_used_comment,
        bike1_name: str(round(bike1_data['adjusted_price'], 1)),
        bike2_name: str(round(bike2_data['adjusted_price'], 1))
    })
    
    # Tiêu thụ nhiên liệu
    fuel_cons_diff = round(abs(bike1_data['fuel_consumption'] - bike2_data['fuel_consumption']), 1)
    fuel_cons_diff_percent = round((fuel_cons_diff / min(bike1_data['fuel_consumption'], bike2_data['fuel_consumption'])) * 100, 1) if min(bike1_data['fuel_consumption'], bike2_data['fuel_consumption']) > 0 else 0
    
    if fuel_cons_diff < 0.3:
        fuel_cons_comment = "Tương đương"
    else:
        fuel_cons_comment = f"{bike1_name if bike1_data['fuel_consumption'] < bike2_data['fuel_consumption'] else bike2_name} tiết kiệm hơn {fuel_cons_diff_percent}%"
    
    comparison_data.append({
        "Chỉ tiêu": "Tiêu thụ nhiên liệu (L/100km)",
        "Nhận xét": fuel_cons_comment,
        bike1_name: str(round(bike1_data['fuel_consumption'], 1)),
        bike2_name: str(round(bike2_data['fuel_consumption'], 1))
    })
    
    # Chi phí nhiên liệu hàng năm
    # Giả định đi khoảng 10,000 km/năm, giá xăng 25,000 VND/lít
    fuel_cost_bike1 = (bike1_data['fuel_consumption'] / 100) * 10000 * 25000 / 1000000  # Triệu VND/năm
    fuel_cost_bike2 = (bike2_data['fuel_consumption'] / 100) * 10000 * 25000 / 1000000  # Triệu VND/năm
    
    fuel_cost_diff = round(abs(fuel_cost_bike1 - fuel_cost_bike2), 1)
    fuel_cost_diff_percent = round((fuel_cost_diff / min(fuel_cost_bike1, fuel_cost_bike2)) * 100, 1) if min(fuel_cost_bike1, fuel_cost_bike2) > 0 else 0
    
    if fuel_cost_diff < 0.3:
        fuel_cost_comment = "Tương đương"
    else:
        fuel_cost_comment = f"{bike1_name if fuel_cost_bike1 < fuel_cost_bike2 else bike2_name} tiết kiệm hơn {fuel_cost_diff_percent}%"
    
    comparison_data.append({
        "Chỉ tiêu": "Chi phí nhiên liệu hàng năm (triệu VND)",
        "Nhận xét": fuel_cost_comment,
        bike1_name: str(round(fuel_cost_bike1, 1)),
        bike2_name: str(round(fuel_cost_bike2, 1))
    })
    
    # 5. ĐÁNH GIÁ TỔNG QUAN
    comparison_data.append({
        "Chỉ tiêu": "**ĐÁNH GIÁ TỔNG QUAN**",
        "Nhận xét": "",
        bike1_name: "",
        bike2_name: ""
    })
    
    # Ưu điểm
    comparison_data.append({
        "Chỉ tiêu": "Ưu điểm",
        "Nhận xét": "Điểm nổi bật của mỗi xe",
        bike1_name: determine_advantages(bike1_data, bike2_data),
        bike2_name: determine_advantages(bike2_data, bike1_data)
    })
    
    # Phù hợp với
    comparison_data.append({
        "Chỉ tiêu": "Phù hợp với",
        "Nhận xét": "Nhu cầu sử dụng phù hợp",
        bike1_name: determine_suitable_usage(bike1_data),
        bike2_name: determine_suitable_usage(bike2_data)
    })
    
    return pd.DataFrame(comparison_data)

def determine_advantages(bike_data, compare_bike_data):
    """Xác định ưu điểm của một xe so với xe khác"""
    advantages = []
    
    # Kiểm tra công suất
    if bike_data['horsepower'] > compare_bike_data['horsepower'] * 1.1:
        advantages.append("Công suất cao")
    
    # Kiểm tra tiêu thụ nhiên liệu
    if bike_data['fuel_consumption'] < compare_bike_data['fuel_consumption'] * 0.9:
        advantages.append("Tiết kiệm nhiên liệu")
    
    # Kiểm tra giá
    if bike_data['adjusted_price'] < compare_bike_data['adjusted_price'] * 0.9:
        advantages.append("Giá thành hợp lý")
    
    # Kiểm tra trọng lượng
    if bike_data['weight'] < compare_bike_data['weight'] * 0.9:
        advantages.append("Nhẹ hơn, dễ điều khiển")
    
    # Kiểm tra bình xăng
    if bike_data['fuel_capacity'] > compare_bike_data['fuel_capacity'] * 1.1:
        advantages.append("Bình xăng lớn, đi xa hơn")
    
    # Nếu không có ưu điểm rõ rệt
    if not advantages:
        # Thêm ưu điểm dựa vào phân khúc
        if bike_data['segment'] == 'Xe tay ga':
            advantages.append("Tiện nghi và thoải mái")
        elif bike_data['segment'] == 'Xe côn tay':
            advantages.append("Cảm giác lái thể thao")
        else:  # Xe số
            advantages.append("Bền bỉ, dễ sửa chữa")
    
    return ", ".join(advantages)

def determine_suitable_usage(bike_data):
    """Xác định nhu cầu sử dụng phù hợp cho xe"""
    suitability = []
    
    # Dựa vào phân khúc
    if bike_data['segment'] == 'Xe tay ga':
        suitability.append("Đi lại trong thành phố")
        suitability.append("Phù hợp với nữ giới")
    elif bike_data['segment'] == 'Xe côn tay':
        suitability.append("Đam mê tốc độ")
        suitability.append("Trải nghiệm cảm giác lái")
    else:  # Xe số
        suitability.append("Đi lại hàng ngày tiết kiệm")
        suitability.append("Địa hình đa dạng")
    
    # Dựa vào công suất
    if bike_data['horsepower'] > 15:
        suitability.append("Đi xa, đường trường")
    
    # Dựa vào tiêu thụ nhiên liệu
    if bike_data['fuel_consumption'] < 2.0:
        suitability.append("Tiết kiệm chi phí")
    
    # Dựa vào dung tích bình xăng
    if bike_data['fuel_capacity'] > 5:
        suitability.append("Quãng đường dài")
    
    return ", ".join(suitability[:3])  # Chỉ lấy 3 mục đầu tiên để gọn

def show_radar_chart(bike1_data, bike2_data):
    """Hiển thị biểu đồ radar so sánh hai xe"""
    try:
        # Chuẩn hóa các thông số cho biểu đồ radar
        attributes = ['engine_cc', 'horsepower', 'torque', 'weight', 'fuel_capacity', 'fuel_consumption']
        attribute_names = ['Dung tích', 'Công suất', 'Mô-men xoắn', 'Trọng lượng', 'Bình xăng', 'Tiêu thụ nhiên liệu']
        
        # Lấy các giá trị
        bike1_values = [float(bike1_data[attr]) for attr in attributes]
        bike2_values = [float(bike2_data[attr]) for attr in attributes]
        
        # Chuẩn hóa các giá trị từ 0 đến 1
        max_values = [max(bike1_values[i], bike2_values[i]) for i in range(len(attributes))]
        min_values = [min(bike1_values[i], bike2_values[i]) * 0.5 for i in range(len(attributes))]
        
        # Điều chỉnh cho giá trị đối với weight và fuel_consumption (thấp hơn tốt hơn)
        for i in [3, 5]:  # indices for weight and fuel_consumption
            bike1_values[i] = max_values[i] - bike1_values[i] + min_values[i]
            bike2_values[i] = max_values[i] - bike2_values[i] + min_values[i]
            max_values[i] = max(bike1_values[i], bike2_values[i])
            min_values[i] = min(bike1_values[i], bike2_values[i])
        
        # Chuẩn hóa
        bike1_normalized = [(bike1_values[i] - min_values[i]) / (max_values[i] - min_values[i]) if max_values[i] != min_values[i] else 0.5 for i in range(len(attributes))]
        bike2_normalized = [(bike2_values[i] - min_values[i]) / (max_values[i] - min_values[i]) if max_values[i] != min_values[i] else 0.5 for i in range(len(attributes))]
        
        # Tạo biểu đồ radar
        angles = np.linspace(0, 2*np.pi, len(attribute_names), endpoint=False).tolist()
        
        # Thêm giá trị đầu vào cuối để tạo đồ thị kín
        bike1_normalized.append(bike1_normalized[0])
        bike2_normalized.append(bike2_normalized[0])
        angles.append(angles[0])  # Thêm góc đầu tiên vào cuối để đóng biểu đồ
        
        fig, ax = plt.subplots(figsize=(10, 6), subplot_kw=dict(polar=True))
        
        # Vẽ biểu đồ cho từng xe
        ax.plot(angles, bike1_normalized, 'o-', linewidth=2, label=f"{bike1_data['brand']} {bike1_data['model']}")
        ax.fill(angles, bike1_normalized, alpha=0.1)
        
        ax.plot(angles, bike2_normalized, 'o-', linewidth=2, label=f"{bike2_data['brand']} {bike2_data['model']}")
        ax.fill(angles, bike2_normalized, alpha=0.1)
        
        # Thêm nhãn - chỉ sử dụng nhãn cho các điểm gốc (không bao gồm điểm được thêm vào để đóng biểu đồ)
        ax.set_thetagrids(np.degrees(angles[:-1]), attribute_names)
        
        # Thêm legend
        ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
        
        # Tiêu đề
        plt.title('So sánh tổng thể')
        
        # Hiển thị biểu đồ
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Lỗi khi tạo biểu đồ radar: {str(e)}")
        st.info("Vui lòng kiểm tra lại dữ liệu hai xe hoặc chọn xe khác để so sánh.")