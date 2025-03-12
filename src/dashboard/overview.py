import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# Thiết lập trang
st.set_page_config(
    page_title="AQI Forecast",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh
st.markdown("""
<style>
    .main {
        background-color: #f5f7fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 5px 5px 0px 0px;
        gap: 1px;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4361ee;
        color: white;
    }
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .aqi-value {
        font-size: 40px;
        font-weight: bold;
    }
    .aqi-label {
        font-size: 14px;
        color: #555;
    }
    .aqi-good {
        color: #00e400;
    }
    .aqi-moderate {
        color: #ffff00;
    }
    .aqi-unhealthy-sensitive {
        color: #ff7e00;
    }
    .aqi-unhealthy {
        color: #ff0000;
    }
    .aqi-very-unhealthy {
        color: #99004c;
    }
    .aqi-hazardous {
        color: #7d0023;
    }
</style>
""", unsafe_allow_html=True)

# Tạo dữ liệu mẫu cho demo
@st.cache_data
def generate_sample_data():
    # Dữ liệu AQI trong 7 ngày qua
    dates = [(datetime.now() - timedelta(days=i)).strftime("%d/%m/%Y") for i in range(7, 0, -1)]
    
    # AQI cơ bản với xu hướng tăng nhẹ
    base_aqi = [45, 52, 75, 85, 67, 58, 63]
    
    # Dữ liệu AQI theo giờ trong ngày
    hours = [f"{i:02d}:00" for i in range(24)]
    hourly_aqi = []
    
    # Tạo dữ liệu theo mẫu ngày đêm, với AQI cao hơn vào giờ cao điểm
    for i in range(24):
        if 6 <= i <= 9:  # Giờ cao điểm buổi sáng
            hourly_aqi.append(base_aqi[-1] + random.randint(10, 25))
        elif 16 <= i <= 19:  # Giờ cao điểm buổi chiều
            hourly_aqi.append(base_aqi[-1] + random.randint(15, 30))
        elif 22 <= i or i <= 5:  # Ban đêm
            hourly_aqi.append(base_aqi[-1] - random.randint(5, 15))
        else:  # Các giờ khác
            hourly_aqi.append(base_aqi[-1] + random.randint(-10, 10))
    
    # Đảm bảo AQI không âm
    hourly_aqi = [max(0, aqi) for aqi in hourly_aqi]
    
    # Dữ liệu dự báo 7 ngày tiếp theo
    forecast_dates = [(datetime.now() + timedelta(days=i)).strftime("%d/%m/%Y") for i in range(1, 8)]
    # Dự báo dựa trên AQI hiện tại với một xu hướng
    forecast_aqi = []
    current = base_aqi[-1]
    
    # Tạo xu hướng: tăng nhẹ, sau đó giảm, rồi tăng nhẹ trở lại
    trends = [5, 8, -3, -7, -10, 3, 7]
    for trend in trends:
        current += trend + random.randint(-5, 5)
        current = max(20, min(200, current))  # Giới hạn giá trị AQI
        forecast_aqi.append(current)
    
    # Dữ liệu các thành phần ô nhiễm
    pollutants = {
        "PM2.5": [round(aqi * 0.6 + random.uniform(-5, 5), 1) for aqi in base_aqi],
        "PM10": [round(aqi * 0.8 + random.uniform(-10, 10), 1) for aqi in base_aqi],
        "O3": [round(aqi * 0.3 + random.uniform(-3, 3), 1) for aqi in base_aqi],
        "NO2": [round(aqi * 0.15 + random.uniform(-2, 2), 1) for aqi in base_aqi],
        "SO2": [round(aqi * 0.1 + random.uniform(-1, 1), 1) for aqi in base_aqi],
        "CO": [round(aqi * 0.05 + random.uniform(-0.5, 0.5), 1) for aqi in base_aqi]
    }
    
    # Điều kiện môi trường
    env_conditions = {
        "temperature": [random.randint(20, 32) for _ in range(7)],  # °C
        "humidity": [random.randint(55, 85) for _ in range(7)],  # %
        "wind_speed": [round(random.uniform(1, 15), 1) for _ in range(7)],  # km/h
        "precipitation": [round(random.uniform(0, 15), 1) for _ in range(7)]  # mm
    }
    
    # Đóng gói dữ liệu
    daily_data = pd.DataFrame({
        "date": dates,
        "aqi": base_aqi,
        "PM2.5": pollutants["PM2.5"],
        "PM10": pollutants["PM10"],
        "O3": pollutants["O3"],
        "NO2": pollutants["NO2"],
        "SO2": pollutants["SO2"],
        "CO": pollutants["CO"],
        "temperature": env_conditions["temperature"],
        "humidity": env_conditions["humidity"],
        "wind_speed": env_conditions["wind_speed"],
        "precipitation": env_conditions["precipitation"]
    })
    
    hourly_data = pd.DataFrame({
        "hour": hours,
        "aqi": hourly_aqi
    })
    
    forecast_data = pd.DataFrame({
        "date": forecast_dates,
        "aqi": forecast_aqi
    })
    
    return daily_data, hourly_data, forecast_data

# Hàm lấy thông tin AQI
def get_aqi_info(aqi):
    if aqi <= 50:
        return {
            "category": "Tốt",
            "color": "#00e400",
            "description": "Chất lượng không khí tốt, không có rủi ro sức khỏe.",
            "recommendation": "Bạn có thể tham gia các hoạt động ngoài trời bình thường."
        }
    elif aqi <= 100:
        return {
            "category": "Trung bình",
            "color": "#ffff00",
            "description": "Chất lượng không khí ở mức trung bình, có thể ảnh hưởng đến một số người nhạy cảm.",
            "recommendation": "Những người nhạy cảm (người có bệnh hô hấp) nên hạn chế các hoạt động ngoài trời kéo dài."
        }
    elif aqi <= 150:
        return {
            "category": "Kém",
            "color": "#ff7e00",
            "description": "Chất lượng không khí kém, có thể ảnh hưởng đến những người nhạy cảm.",
            "recommendation": "Những người nhạy cảm nên giảm hoạt động ngoài trời. Mọi người nên hạn chế các hoạt động ngoài trời kéo dài."
        }
    elif aqi <= 200:
        return {
            "category": "Xấu",
            "color": "#ff0000",
            "description": "Chất lượng không khí xấu, có thể gây ảnh hưởng sức khỏe cho mọi người.",
            "recommendation": "Mọi người nên giảm hoạt động ngoài trời. Những người nhạy cảm nên ở trong nhà."
        }
    elif aqi <= 300:
        return {
            "category": "Rất xấu",
            "color": "#99004c",
            "description": "Chất lượng không khí rất xấu, cảnh báo nguy cơ sức khỏe.",
            "recommendation": "Tránh hoạt động ngoài trời. Những người nhạy cảm nên ở trong nhà và giảm hoạt động."
        }
    else:
        return {
            "category": "Nguy hiểm",
            "color": "#7d0023",
            "description": "Chất lượng không khí ở mức nguy hiểm, cảnh báo khẩn cấp về sức khỏe.",
            "recommendation": "Mọi người nên ở trong nhà, đóng cửa sổ và sử dụng máy lọc không khí nếu có thể."
        }

# Tải dữ liệu mẫu
daily_data, hourly_data, forecast_data = generate_sample_data()

# Sidebar
st.sidebar.title("AQI Forecast")

# Chọn thành phố
city = st.sidebar.selectbox(
    "Chọn thành phố",
    ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ"]
)

# Thời gian cập nhật
st.sidebar.markdown(f"**Cập nhật lần cuối:** {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")

# Các cài đặt của người dùng
st.sidebar.markdown("### Cài đặt cá nhân")

# Nhận thông báo
notification = st.sidebar.toggle("Nhận thông báo khi AQI vượt ngưỡng", value=True)
if notification:
    notification_threshold = st.sidebar.slider("Ngưỡng cảnh báo AQI", min_value=50, max_value=200, value=100, step=10)

# Chọn chế độ hiển thị
display_mode = st.sidebar.radio("Chế độ hiển thị", ["Tất cả chỉ số", "Chỉ PM2.5", "Chỉ PM10", "Tùy chỉnh"])

if display_mode == "Tùy chỉnh":
    pollutants_to_show = st.sidebar.multiselect(
        "Chọn các chỉ số hiển thị",
        ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"],
        default=["PM2.5", "PM10"]
    )

# Hiển thị thông tin về AQI
st.sidebar.markdown("### Thông tin về AQI")
st.sidebar.markdown("""
- **0-50**: Tốt (Xanh lá)
- **51-100**: Trung bình (Vàng)
- **101-150**: Kém (Cam)
- **151-200**: Xấu (Đỏ)
- **201-300**: Rất xấu (Tím)
- **>300**: Nguy hiểm (Nâu đỏ)
""")

# Thông tin liên hệ hoặc nguồn dữ liệu
st.sidebar.markdown("---")
st.sidebar.info("Dữ liệu từ: *Trung tâm Quan trắc Môi trường*")

# Nội dung chính
st.title(f"Chất lượng không khí tại {city}")

# Tabs chính
tab1, tab2, tab3 = st.tabs(["📊 Tổng quan", "🔍 Phân tích", "🧪 Trải nghiệm người dùng"])

with tab1:
    # Hàng đầu với AQI hiện tại
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Lấy AQI gần nhất (hôm nay)
        current_aqi = daily_data.iloc[-1]["aqi"]
        aqi_info = get_aqi_info(current_aqi)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="aqi-value" style="color:{aqi_info['color']}">{int(current_aqi)}</div>
            <div class="aqi-label" style="font-size:24px; color:{aqi_info['color']}; font-weight:bold">{aqi_info['category']}</div>
            <div class="aqi-label">Chỉ số AQI hiện tại</div>
            <hr style="margin: 15px 0">
            <div style="font-size:15px">{aqi_info['description']}</div>
            <div style="font-size:14px; margin-top:10px; color:#555">
                <strong>Khuyến nghị:</strong> {aqi_info['recommendation']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Biểu đồ diễn biến 24 giờ
        st.markdown("<h3>Diễn biến AQI 24 giờ qua</h3>", unsafe_allow_html=True)
        
        fig = px.line(
            hourly_data, 
            x="hour", 
            y="aqi",
            markers=True,
            line_shape="spline",
            color_discrete_sequence=["#4361ee"]
        )
        
        # Tùy chỉnh giao diện
        fig.update_layout(
            xaxis_title="Giờ",
            yaxis_title="AQI",
            margin=dict(l=10, r=10, t=10, b=10),
            height=300,
            xaxis=dict(tickmode='linear', dtick=3),
            plot_bgcolor="white",
            hovermode="x unified"
        )
        
        # Thêm vùng biểu thị mức độ AQI
        fig.add_hrect(y0=0, y1=50, line_width=0, fillcolor="green", opacity=0.1)
        fig.add_hrect(y0=50, y1=100, line_width=0, fillcolor="yellow", opacity=0.1)
        fig.add_hrect(y0=100, y1=150, line_width=0, fillcolor="orange", opacity=0.1)
        fig.add_hrect(y0=150, y1=200, line_width=0, fillcolor="red", opacity=0.1)
        fig.add_hrect(y0=200, y1=300, line_width=0, fillcolor="purple", opacity=0.1)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Dự báo 7 ngày
    st.markdown("<h3>Dự báo 7 ngày tới</h3>", unsafe_allow_html=True)
    
    # Thêm cột màu dựa vào AQI
    forecast_data["color"] = forecast_data["aqi"].apply(lambda x: get_aqi_info(x)["color"])
    forecast_data["category"] = forecast_data["aqi"].apply(lambda x: get_aqi_info(x)["category"])
    
    fig = px.bar(
        forecast_data, 
        x="date", 
        y="aqi",
        color="category",
        text="aqi",
        color_discrete_map={
            "Tốt": "#00e400",
            "Trung bình": "#ffff00",
            "Kém": "#ff7e00",
            "Xấu": "#ff0000",
            "Rất xấu": "#99004c",
            "Nguy hiểm": "#7d0023"
        },
        category_orders={"category": ["Tốt", "Trung bình", "Kém", "Xấu", "Rất xấu", "Nguy hiểm"]}
    )
    
    # Tùy chỉnh giao diện
    fig.update_layout(
        xaxis_title="Ngày",
        yaxis_title="AQI",
        legend_title="Mức độ",
        margin=dict(l=10, r=10, t=10, b=10),
        height=400,
        plot_bgcolor="white",
        hovermode="x unified"
    )
    
    # Thêm vùng biểu thị mức độ AQI
    fig.add_hrect(y0=0, y1=50, line_width=0, fillcolor="green", opacity=0.1)
    fig.add_hrect(y0=50, y1=100, line_width=0, fillcolor="yellow", opacity=0.1)
    fig.add_hrect(y0=100, y1=150, line_width=0, fillcolor="orange", opacity=0.1)
    fig.add_hrect(y0=150, y1=200, line_width=0, fillcolor="red", opacity=0.1)
    fig.add_hrect(y0=200, y1=300, line_width=0, fillcolor="purple", opacity=0.1)
    
    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Hiển thị thông tin thành phần ô nhiễm
    st.markdown("<h3>Thành phần ô nhiễm</h3>", unsafe_allow_html=True)
    
    # Lọc các cột dựa vào lựa chọn người dùng
    if display_mode == "Chỉ PM2.5":
        pollutant_cols = ["PM2.5"]
    elif display_mode == "Chỉ PM10":
        pollutant_cols = ["PM10"]
    elif display_mode == "Tùy chỉnh":
        pollutant_cols = pollutants_to_show
    else:
        pollutant_cols = ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"]
    
    # Tạo DataFrame để vẽ biểu đồ
    pollutant_df = daily_data[["date"] + pollutant_cols]
    pollutant_df_long = pd.melt(pollutant_df, id_vars=["date"], value_vars=pollutant_cols, 
                              var_name="Chất ô nhiễm", value_name="Nồng độ (µg/m³)")
    
    fig = px.line(
        pollutant_df_long, 
        x="date", 
        y="Nồng độ (µg/m³)", 
        color="Chất ô nhiễm",
        markers=True,
        line_shape="spline"
    )
    
    # Tùy chỉnh giao diện
    fig.update_layout(
        xaxis_title="Ngày",
        yaxis_title="Nồng độ (µg/m³)",
        legend_title="Chất ô nhiễm",
        margin=dict(l=10, r=10, t=10, b=10),
        height=400,
        plot_bgcolor="white",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Hiển thị điều kiện môi trường
    st.markdown("<h3>Điều kiện môi trường</h3>", unsafe_allow_html=True)
    
    env_cols = st.columns(4)
    
    with env_cols[0]:
        st.metric(
            label="Nhiệt độ", 
            value=f"{daily_data.iloc[-1]['temperature']}°C",
            delta=f"{daily_data.iloc[-1]['temperature'] - daily_data.iloc[-2]['temperature']}°C"
        )
    
    with env_cols[1]:
        st.metric(
            label="Độ ẩm", 
            value=f"{daily_data.iloc[-1]['humidity']}%",
            delta=f"{daily_data.iloc[-1]['humidity'] - daily_data.iloc[-2]['humidity']}%"
        )
    
    with env_cols[2]:
        st.metric(
            label="Tốc độ gió", 
            value=f"{daily_data.iloc[-1]['wind_speed']} km/h",
            delta=f"{daily_data.iloc[-1]['wind_speed'] - daily_data.iloc[-2]['wind_speed']} km/h"
        )
    
    with env_cols[3]:
        st.metric(
            label="Lượng mưa", 
            value=f"{daily_data.iloc[-1]['precipitation']} mm",
            delta=f"{daily_data.iloc[-1]['precipitation'] - daily_data.iloc[-2]['precipitation']} mm"
        )

with tab2:
    st.markdown("<h2>Phân tích chi tiết</h2>", unsafe_allow_html=True)
    
    # Tương quan giữa các thành phần ô nhiễm
    st.markdown("<h3>Tương quan giữa các thành phần ô nhiễm</h3>", unsafe_allow_html=True)
    
    correlation = daily_data[["aqi", "PM2.5", "PM10", "O3", "NO2", "SO2", "CO"]].corr()
    
    fig = px.imshow(
        correlation,
        text_auto=True,
        color_continuous_scale='RdBu_r',
        zmin=-1, zmax=1
    )
    
    fig.update_layout(
        height=500,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tương quan với điều kiện môi trường
    st.markdown("<h3>Ảnh hưởng của điều kiện môi trường đến AQI</h3>", unsafe_allow_html=True)
    
    env_factor = st.selectbox(
        "Chọn yếu tố môi trường:",
        ["temperature", "humidity", "wind_speed", "precipitation"],
        format_func=lambda x: {
            "temperature": "Nhiệt độ",
            "humidity": "Độ ẩm",
            "wind_speed": "Tốc độ gió",
            "precipitation": "Lượng mưa"
        }[x]
    )
    
    fig = px.scatter(
        daily_data,
        x=env_factor,
        y="aqi",
        trendline="ols",
        color_discrete_sequence=["#4361ee"],
        labels={
            "temperature": "Nhiệt độ (°C)",
            "humidity": "Độ ẩm (%)",
            "wind_speed": "Tốc độ gió (km/h)",
            "precipitation": "Lượng mưa (mm)",
            "aqi": "Chỉ số AQI"
        }
    )
    
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Phân tích theo thời gian
    st.markdown("<h3>Phân tích xu hướng theo thời gian</h3>", unsafe_allow_html=True)
    
    st.markdown("""
    Phân tích xu hướng chỉ số AQI cho thấy:
    
    - Chỉ số AQI thường cao hơn vào giờ cao điểm giao thông (6-9h sáng và 16-19h chiều)
    - Cuối tuần thường có chỉ số AQI thấp hơn ngày trong tuần
    - Chỉ số PM2.5 và PM10 có mối tương quan cao với AQI tổng thể
    - Tốc độ gió cao thường đi kèm với chỉ số AQI thấp hơn
    """)
    
    # Tạo nút để tải về dữ liệu phân tích
    st.download_button(
        label="Tải về báo cáo phân tích (.csv)",
        data=daily_data.to_csv(index=False).encode('utf-8'),
        file_name=f'aqi_analysis_{city}_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv',
    )

with tab3:
    st.markdown("<h2>Trải nghiệm người dùng</h2>", unsafe_allow_html=True)
    
    # Tạo tab con trong tab trải nghiệm
    whatif_tab, health_tab, sensor_tab = st.tabs(["🔮 Dự đoán What-If", "❤️ Nhật ký sức khỏe", "📱 Cảm biến cá nhân"])
    
    with whatif_tab:
        st.markdown("<h3>Dự đoán What-If</h3>", unsafe_allow_html=True)
        st.write("Điều chỉnh các thông số để xem tác động đến chỉ số AQI")
        
        col1, col2 = st.columns(2)
        
        with col1:
            location = st.selectbox(
                "Vị trí:",
                ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ"],
                index=0
            )
            
            temperature = st.slider("Nhiệt độ (°C):", 0, 40, 28)
            humidity = st.slider("Độ ẩm (%):", 0, 100, 70)
            wind_speed = st.slider("Tốc độ gió (km/h):", 0, 30, 10)
        
        with col2:
            traffic_level = st.slider("Mức độ giao thông (%):", 0, 100, 60)
            industrial_activity = st.slider("Hoạt động công nghiệp (%):", 0, 100, 40)
            season = st.selectbox(
                "Mùa:",
                ["Xuân", "Hè", "Thu", "Đông"],
                index=1
            )
        
        # Hàm tính toán AQI dựa trên các thông số
        def calculate_aqi_whatif(params):
            base_aqi = 50
            
            # Tăng AQI khi gió thấp
            base_aqi += max(0, (15 - params["wind_speed"]) * 1.5)
            
            # Tăng AQI khi nhiệt độ cao
            base_aqi += max(0, (params["temperature"] - 25) * 2)
            
            # Tăng AQI theo mức độ giao thông
            base_aqi += params["traffic_level"] * 0.4
            
            # Tăng AQI theo hoạt động công nghiệp
            base_aqi += params["industrial_activity"] * 0.5
            
            # Điều chỉnh theo độ ẩm (độ ẩm trung bình làm giảm AQI)
            if params["humidity"] < 40 or params["humidity"] > 80:
                base_aqi += 10
            else:
                base_aqi -= 5
            
            # Điều chỉnh theo mùa
            if params["season"] == "Đông":
                base_aqi += 15
            elif params["season"] == "Thu":
                base_aqi += 5
            elif params["season"] == "Hè":
                base_aqi -= 5
            
            # Giới hạn kết quả
            return min(300, max(20, round(base_aqi)))
        
        # Tính toán AQI dựa trên các thông số đã chọn
        params = {
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "traffic_level": traffic_level,
            "industrial_activity": industrial_activity,
            "season": season
        }
        
        predicted_aqi = calculate_aqi_whatif(params)
        aqi_info = get_aqi_info(predicted_aqi)
        
        # Hiển thị kết quả
        st.markdown("### Kết quả dự đoán")
        
        st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
                <div>
                    <div style="font-size: 18px; font-weight: bold;">{location} - Kịch bản của bạn</div>
                    <div style="font-size: 14px; color: #555;">Dự đoán dựa trên thông số đã nhập</div>
                </div>
                <div style="background-color: {aqi_info['color']}; color: white; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold;">
                    {predicted_aqi}
                </div>
            </div>
            <hr style="margin: 10px 0;">
            <div style="font-size: 16px; font-weight: bold; color: {aqi_info['color']}; margin-bottom: 10px;">{aqi_info['category']}</div>
            <div style="font-size: 14px; margin-bottom: 10px;">{aqi_info['description']}</div>
            <div style="font-size: 14px;"><strong>Khuyến nghị:</strong> {aqi_info['recommendation']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Hiển thị so sánh
        st.markdown("### So sánh với kịch bản cơ sở")
        
        # Tạo biểu đồ so sánh
        comparison_data = pd.DataFrame({
            'Kịch bản': ['Hiện tại', 'Dự đoán của bạn'],
            'AQI': [daily_data.iloc[-1]["aqi"], predicted_aqi]
        })
        
        fig = px.bar(
            comparison_data,
            x='Kịch bản',
            y='AQI',
            color='AQI',
            color_continuous_scale=[(0, "#00e400"), (0.2, "#ffff00"), (0.4, "#ff7e00"), 
                                    (0.6, "#ff0000"), (0.8, "#99004c"), (1, "#7d0023")],
            text='AQI'
        )
        
        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="white"
        )
        
        fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Thêm giải thích
        st.markdown("### Phân tích tác động")
        
        impact_factors = []
        
        if params["wind_speed"] < 8:
            impact_factors.append("Tốc độ gió thấp làm tăng nồng độ ô nhiễm")
        
        if params["temperature"] > 30:
            impact_factors.append("Nhiệt độ cao thúc đẩy phản ứng quang hóa, tạo O3")
        
        if params["traffic_level"] > 70:
            impact_factors.append("Mức độ giao thông cao làm tăng PM2.5 và NOx")
        
        if params["industrial_activity"] > 70:
            impact_factors.append("Hoạt động công nghiệp cao làm tăng SO2 và bụi")
        
        if params["humidity"] > 80:
            impact_factors.append("Độ ẩm cao có thể làm tăng nồng độ bụi mịn")
        
        if params["season"] == "Đông":
            impact_factors.append("Mùa đông thường có hiện tượng nghịch nhiệt, giữ ô nhiễm gần mặt đất")
        
        if not impact_factors:
            impact_factors.append("Các thông số đều ở mức trung bình, không có yếu tố nổi bật")
        
        for factor in impact_factors:
            st.markdown(f"- {factor}")
        
        # Tải xuống kịch bản
        scenario_data = pd.DataFrame({
            'Thông số': ['Vị trí', 'Nhiệt độ (°C)', 'Độ ẩm (%)', 'Tốc độ gió (km/h)', 
                        'Mức độ giao thông (%)', 'Hoạt động công nghiệp (%)', 'Mùa', 'AQI dự đoán', 'Mức độ'],
            'Giá trị': [location, temperature, humidity, wind_speed, 
                       traffic_level, industrial_activity, season, predicted_aqi, aqi_info['category']]
        })
        
        st.download_button(
            label="Tải xuống kịch bản",
            data=scenario_data.to_csv(index=False).encode('utf-8'),
            file_name=f'aqi_scenario_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mime='text/csv',
        )
        
    with health_tab:
        st.markdown("<h3>Nhật ký sức khỏe</h3>", unsafe_allow_html=True)
        st.write("Ghi lại các triệu chứng để theo dõi mối tương quan với chất lượng không khí")
        
        # Ngày ghi nhật ký
        log_date = st.date_input("Ngày:", datetime.now())
        
        # Hiển thị AQI vào ngày đó (giả lập)
        simulated_aqi = int(daily_data.iloc[-1]["aqi"] + random.randint(-15, 15))
        aqi_info = get_aqi_info(simulated_aqi)
        
        st.markdown(f"""
        <div style="background-color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center;">
                <div style="background-color: {aqi_info['color']}; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: bold; margin-right: 15px;">
                    {simulated_aqi}
                </div>
                <div>
                    <div style="font-weight: bold;">AQI hôm nay: {aqi_info['category']}</div>
                    <div style="font-size: 14px; color: #555;">Dữ liệu từ trạm gần nhất</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Triệu chứng
        st.markdown("#### Triệu chứng")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cough = st.checkbox("Ho")
            eye_irritation = st.checkbox("Kích ứng mắt/mũi")
            breathing_difficulty = st.checkbox("Khó thở")
        
        with col2:
            headache = st.checkbox("Đau đầu")
            fatigue = st.checkbox("Mệt mỏi")
            other_symptoms = st.checkbox("Triệu chứng khác")
        
        # Thêm mô tả nếu có triệu chứng khác
        if other_symptoms:
            other_symptoms_desc = st.text_area("Mô tả triệu chứng khác:")
        
        # Ghi chú
        st.markdown("#### Ghi chú thêm")
        notes = st.text_area("Thêm ghi chú về sức khỏe và hoạt động trong ngày:")
        
        # Thời gian ở ngoài trời
        st.markdown("#### Thời gian hoạt động")
        outdoor_time = st.slider("Thời gian ở ngoài trời (giờ):", 0, 24, 2)
        
        # Các biện pháp bảo vệ
        st.markdown("#### Biện pháp bảo vệ đã sử dụng")
        
        col1, col2 = st.columns(2)
        
        with col1:
            mask = st.checkbox("Đeo khẩu trang")
            air_purifier = st.checkbox("Sử dụng máy lọc không khí")
        
        with col2:
            reduced_outdoor = st.checkbox("Hạn chế hoạt động ngoài trời")
            medications = st.checkbox("Sử dụng thuốc")
        
        # Nút lưu nhật ký
        if st.button("Lưu nhật ký sức khỏe"):
            st.success("Đã lưu thành công nhật ký sức khỏe ngày " + log_date.strftime("%d/%m/%Y"))
            
            # Đây chỉ là demo, trong ứng dụng thực tế sẽ lưu dữ liệu vào cơ sở dữ liệu
        
        # Hiển thị phân tích xu hướng (giả lập)
        st.markdown("### Phân tích xu hướng sức khỏe")
        
        # Tạo dữ liệu giả lập cho biểu đồ xu hướng
        days = 30
        dates = [(datetime.now() - timedelta(days=i)).strftime("%d/%m") for i in range(days, 0, -1)]
        
        # Tạo dữ liệu AQI
        aqi_trend = [50 + random.randint(-20, 60) for _ in range(days)]
        
        # Tạo dữ liệu triệu chứng (giả lập tương quan với AQI)
        symptom_trend = []
        for aqi in aqi_trend:
            if aqi < 50:
                symptom_trend.append(random.randint(0, 1))
            elif aqi < 100:
                symptom_trend.append(random.randint(0, 2))
            elif aqi < 150:
                symptom_trend.append(random.randint(1, 3))
            else:
                symptom_trend.append(random.randint(2, 5))
        
        # Tạo DataFrame
        trend_data = pd.DataFrame({
            "Ngày": dates,
            "AQI": aqi_trend,
            "Số triệu chứng": symptom_trend
        })
        
        # Vẽ biểu đồ
        fig = go.Figure()
        
        # Thêm đường AQI
        fig.add_trace(go.Scatter(
            x=trend_data["Ngày"],
            y=trend_data["AQI"],
            name="AQI",
            line=dict(color="#4361ee", width=2),
            yaxis="y"
        ))
        
        # Thêm cột số triệu chứng
        fig.add_trace(go.Bar(
            x=trend_data["Ngày"],
            y=trend_data["Số triệu chứng"],
            name="Số triệu chứng",
            marker_color="#ff6b6b",
            yaxis="y2"
        ))
        
        # Cấu hình layout với hai trục y
        fig.update_layout(
            title="Mối tương quan giữa AQI và triệu chứng sức khỏe",
            xaxis=dict(title="Ngày"),
            yaxis=dict(
                title="AQI",
                title_font=dict(color="#4361ee"),
                tickfont=dict(color="#4361ee")
            ),
            yaxis2=dict(
                title="Số triệu chứng",
                title_font=dict(color="#ff6b6b"),
                tickfont=dict(color="#ff6b6b"),
                anchor="x",
                overlaying="y",
                side="right"
            ),
            legend=dict(x=0.01, y=0.99),
            margin=dict(l=10, r=10, t=50, b=10),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Phân tích tương quan
        correlation = np.corrcoef(trend_data["AQI"], trend_data["Số triệu chứng"])[0, 1]
        
        st.markdown(f"""
        #### Phân tích cá nhân hóa
        
        Hệ số tương quan giữa AQI và triệu chứng của bạn: **{correlation:.2f}**
        
        Dựa trên dữ liệu nhật ký của bạn:
        
        - Bạn thường gặp triệu chứng về đường hô hấp khi AQI vượt quá 100
        - Việc đeo khẩu trang khi ra ngoài đã giúp giảm 60% triệu chứng
        - Thời gian ở ngoài trời trên 3 giờ vào những ngày có AQI cao làm tăng nguy cơ có triệu chứng
        
        **Khuyến nghị cá nhân:**
        - Đeo khẩu trang N95 khi AQI vượt quá 80
        - Sử dụng máy lọc không khí trong nhà
        - Nên theo dõi chỉ số AQI trước khi ra ngoài
        """)
    
    with sensor_tab:
        st.markdown("<h3>Cảm biến cá nhân</h3>", unsafe_allow_html=True)
        st.write("Kết nối cảm biến cá nhân hoặc nhập dữ liệu thủ công để cải thiện độ chính xác dự báo")
        
        # Chọn phương thức nhập dữ liệu
        input_method = st.radio(
            "Chọn phương thức nhập dữ liệu:",
            ["Nhập thủ công", "Tải lên từ file", "Kết nối với cảm biến IoT"]
        )
        
        if input_method == "Nhập thủ công":
            st.markdown("#### Nhập dữ liệu đo được từ cảm biến của bạn")
            
            col1, col2 = st.columns(2)
            
            with col1:
                pm25 = st.number_input("PM2.5 (µg/m³):", min_value=0.0, max_value=1000.0, value=25.0, step=0.1)
                pm10 = st.number_input("PM10 (µg/m³):", min_value=0.0, max_value=1000.0, value=45.0, step=0.1)
                o3 = st.number_input("O3 (ppb):", min_value=0.0, max_value=500.0, value=30.0, step=0.1)
            
            with col2:
                no2 = st.number_input("NO2 (ppb):", min_value=0.0, max_value=500.0, value=15.0, step=0.1)
                so2 = st.number_input("SO2 (ppb):", min_value=0.0, max_value=500.0, value=5.0, step=0.1)
                co = st.number_input("CO (ppm):", min_value=0.0, max_value=50.0, value=0.8, step=0.1)
            
            location_details = st.text_input("Vị trí chi tiết:", "Quận Đống Đa, Hà Nội")
            measurement_time = st.time_input("Thời điểm đo:", datetime.now().time())
            
            if st.button("Gửi dữ liệu"):
                st.success("Đã gửi dữ liệu thành công!")
                
                # Tính AQI từ dữ liệu cảm biến (đơn giản hóa)
                sensor_aqi = int(pm25 * 3) # Giả lập tính toán
                aqi_info = get_aqi_info(sensor_aqi)
                
                st.markdown(f"""
                <div style="background-color: white; padding: 20px; border-radius: 10px; margin-top: 20px;">
                    <h4>AQI được tính từ cảm biến của bạn</h4>
                    <div style="display: flex; align-items: center;">
                        <div style="background-color: {aqi_info['color']}; color: white; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; margin-right: 20px;">
                            {sensor_aqi}
                        </div>
                        <div>
                            <div style="font-weight: bold; font-size: 18px;">{aqi_info['category']}</div>
                            <div style="font-size: 14px;">{location_details} - {measurement_time.strftime('%H:%M')}</div>
                        </div>
                    </div>
                    <p style="margin-top: 15px;">{aqi_info['description']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # So sánh với trạm quan trắc gần nhất
                station_aqi = daily_data.iloc[-1]["aqi"]
                difference = sensor_aqi - station_aqi
                
                st.markdown(f"""
                #### So sánh với trạm quan trắc gần nhất
                
                - AQI từ cảm biến của bạn: **{sensor_aqi}** ({aqi_info['category']})
                - AQI từ trạm quan trắc gần nhất: **{station_aqi}** ({get_aqi_info(station_aqi)['category']})
                - Chênh lệch: **{difference}** điểm
                
                {'Chỉ số AQI từ cảm biến của bạn cao hơn đáng kể so với trạm quan trắc chính thức. Điều này có thể do vị trí của bạn gần nguồn ô nhiễm cục bộ.' if difference > 10 else 'Chỉ số AQI từ cảm biến của bạn tương đối phù hợp với dữ liệu từ trạm quan trắc chính thức.'}
                """)
        
        elif input_method == "Tải lên từ file":
            st.markdown("#### Tải lên dữ liệu từ cảm biến")
            
            uploaded_file = st.file_uploader("Chọn file CSV hoặc Excel", type=["csv", "xlsx"])
            
            if uploaded_file is not None:
                st.success("Đã tải lên file thành công!")
                st.markdown("""
                #### Hướng dẫn định dạng file
                
                File CSV nên có các cột sau:
                - timestamp: Thời gian đo (định dạng YYYY-MM-DD HH:MM:SS)
                - pm25: Nồng độ PM2.5 (µg/m³)
                - pm10: Nồng độ PM10 (µg/m³)
                - o3: Nồng độ O3 (ppb) - tùy chọn
                - no2: Nồng độ NO2 (ppb) - tùy chọn
                - so2: Nồng độ SO2 (ppb) - tùy chọn
                - co: Nồng độ CO (ppm) - tùy chọn
                - location: Vị trí đo - tùy chọn
                """)
                
                # Trường hợp thực tế sẽ đọc file và xử lý dữ liệu
                # Demo: hiển thị bản xem trước
                st.markdown("#### Bản xem trước dữ liệu")
                
                # Tạo dữ liệu mẫu
                preview_data = pd.DataFrame({
                    "timestamp": [(datetime.now() - timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(5)],
                    "pm25": [24.5, 26.3, 25.7, 23.8, 22.9],
                    "pm10": [45.2, 48.7, 46.5, 44.1, 42.8],
                    "o3": [30.5, 32.1, 31.8, 29.7, 28.9],
                    "location": ["Quận Đống Đa, Hà Nội"] * 5
                })
                
                st.dataframe(preview_data)
                
                if st.button("Xử lý dữ liệu"):
                    st.success("Đã xử lý dữ liệu thành công!")
                    
                    # Hiển thị biểu đồ dữ liệu
                    st.markdown("#### Phân tích dữ liệu cảm biến")
                    
                    fig = px.line(
                        preview_data,
                        x="timestamp",
                        y=["pm25", "pm10"],
                        labels={"value": "Nồng độ (µg/m³)", "timestamp": "Thời gian", "variable": "Chất ô nhiễm"},
                        markers=True
                    )
                    
                    fig.update_layout(
                        height=400,
                        margin=dict(l=10, r=10, t=10, b=10),
                        legend_title="Chất ô nhiễm"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tích hợp dữ liệu
                    st.markdown("""
                    #### Dữ liệu của bạn đã được tích hợp!
                    
                    Dự báo AQI cá nhân hóa sẽ tính đến dữ liệu từ cảm biến của bạn, giúp tăng độ chính xác cho khu vực cụ thể của bạn.
                    
                    Cảm ơn bạn đã đóng góp dữ liệu để cải thiện hệ thống dự báo của chúng tôi.
                    """)
        
        else:  # Kết nối với cảm biến IoT
            st.markdown("#### Kết nối với cảm biến IoT")
            
            # Hiển thị các tùy chọn kết nối
            sensor_type = st.selectbox(
                "Loại cảm biến:",
                ["PurpleAir", "AirVisual", "Sensirion", "Atmotube", "Khác"]
            )
            
            connection_method = st.radio(
                "Phương thức kết nối:",
                ["API", "MQTT", "Bluetooth", "Wi-Fi trực tiếp"]
            )
            
            if connection_method == "API":
                api_key = st.text_input("API Key:", type="password")
                sensor_id = st.text_input("Sensor ID:")
            elif connection_method == "MQTT":
                mqtt_broker = st.text_input("MQTT Broker:")
                mqtt_topic = st.text_input("MQTT Topic:")
                mqtt_username = st.text_input("Username:")
                mqtt_password = st.text_input("Password:", type="password")
            elif connection_method == "Bluetooth":
                st.markdown("Quét các thiết bị Bluetooth gần đây:")
                
                # Giả lập danh sách thiết bị
                devices = [
                    {"name": "AirSensor-1A2B", "id": "00:11:22:33:44:55", "rssi": -67},
                    {"name": "PM25-Monitor", "id": "AA:BB:CC:DD:EE:FF", "rssi": -72},
                    {"name": "AQI-NodeMCU", "id": "A1:B2:C3:D4:E5:F6", "rssi": -85}
                ]
                
                for device in devices:
                    st.markdown(f"""
                    <div style="background-color: white; padding: 10px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: bold;">{device['name']}</div>
                            <div style="font-size: 12px; color: #555;">{device['id']} | Tín hiệu: {device['rssi']} dBm</div>
                        </div>
                        <button style="background-color: #4361ee; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;">Kết nối</button>
                    </div>
                    """, unsafe_allow_html=True)
            else:  # Wi-Fi
                st.markdown("Cấu hình kết nối Wi-Fi trực tiếp:")
                sensor_ip = st.text_input("Địa chỉ IP cảm biến:")
                sensor_port = st.text_input("Cổng:", "80")
                auth_required = st.checkbox("Yêu cầu xác thực")
                
                if auth_required:
                    sensor_username = st.text_input("Username:")
                    sensor_password = st.text_input("Password:", type="password")
            
            if st.button("Kết nối"):
                st.success("Đang kết nối với cảm biến... Vui lòng đợi trong giây lát")
                
                # Giả lập kết nối thành công
                st.markdown("""
                ✅ **Kết nối thành công!**
                
                Cảm biến đã được kết nối thành công và bắt đầu đồng bộ dữ liệu. Dữ liệu sẽ được cập nhật mỗi 5 phút.
                """)
                
                # Hiển thị dữ liệu mẫu từ cảm biến
                st.markdown("#### Dữ liệu từ cảm biến")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(label="PM2.5", value="24.3 µg/m³", delta="1.2 µg/m³")
                
                with col2:
                    st.metric(label="PM10", value="42.7 µg/m³", delta="-0.8 µg/m³")
                
                with col3:
                    st.metric(label="AQI tính toán", value="73", delta="2")
                
                # Hiển thị trạng thái cảm biến
                st.markdown("""
                #### Trạng thái cảm biến
                
                - **Tên cảm biến:** {sensor_type}-{random.randint(1000, 9999)}
                - **Phiên bản firmware:** 1.2.5
                - **Pin:** 78%
                - **Thời gian hoạt động:** 3 ngày 7 giờ
                - **Cường độ tín hiệu:** Tốt (-67 dBm)
                
                #### Cài đặt cảm biến
                """)
                
                update_interval = st.slider("Tần suất cập nhật dữ liệu (phút):", 1, 60, 5)
                
                sync_settings = st.checkbox("Đồng bộ dữ liệu lên đám mây", value=True)
                local_storage = st.checkbox("Lưu trữ dữ liệu cục bộ khi mất kết nối", value=True)
                
                if st.button("Lưu cài đặt"):
                    st.success("Đã lưu cài đặt cảm biến thành công!")

# Chạy ứng dụng
if __name__ == "__main__":
    # Ứng dụng đã được thiết lập ở trên
    pass