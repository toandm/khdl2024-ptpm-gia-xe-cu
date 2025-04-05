# utils/visualization.py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def create_market_overview(data):
    """
    Tạo biểu đồ tổng quan thị trường
    
    Args:
        data (DataFrame): DataFrame chứa dữ liệu thị trường
        
    Returns:
        Figure: Đối tượng Figure của matplotlib
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    brands = data['Thương hiệu']
    x = np.arange(len(brands))
    width = 0.35
    
    ax.bar(x - width/2, data['Số lượng giao dịch'], width, label='Số lượng giao dịch')
    ax.set_xlabel('Thương hiệu')
    ax.set_ylabel('Số lượng giao dịch')
    ax.set_title('Số lượng giao dịch theo thương hiệu')
    ax.set_xticks(x)
    ax.set_xticklabels(brands)
    ax.legend()
    
    ax2 = ax.twinx()
    ax2.plot(x, data['Giá trung bình (triệu VND)'], 'ro-', label='Giá trung bình')
    ax2.set_ylabel('Giá trung bình (triệu VND)')
    ax2.legend(loc='lower right')
    
    fig.tight_layout()
    return fig

def create_price_trend():
    """
    Tạo biểu đồ xu hướng giá
    
    Returns:
        Figure: Đối tượng Figure của matplotlib
    """
    # Dữ liệu mẫu cho xu hướng giá
    months = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12']
    
    # Giá trung bình các loại xe theo tháng (triệu VND)
    honda_prices = [25, 24.5, 24.8, 25.2, 25.5, 26, 26.5, 27, 27.2, 27.5, 28, 28.2]
    yamaha_prices = [30, 29.5, 29.8, 30.2, 30.5, 31, 31.5, 32, 32.2, 32.5, 33, 33.2]
    suzuki_prices = [22, 21.5, 21.8, 22.2, 22.5, 23, 23.5, 24, 24.2, 24.5, 25, 25.2]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(months, honda_prices, 'b-', label='Honda')
    ax.plot(months, yamaha_prices, 'r-', label='Yamaha')
    ax.plot(months, suzuki_prices, 'g-', label='Suzuki')
    
    ax.set_xlabel('Tháng')
    ax.set_ylabel('Giá trung bình (triệu VND)')
    ax.set_title('Xu hướng giá xe máy cũ theo tháng')
    ax.legend()
    ax.grid(True)
    
    fig.tight_layout()
    return fig

def create_price_distribution(brand=None):
    """
    Tạo biểu đồ phân phối giá theo thương hiệu
    
    Args:
        brand (str, optional): Thương hiệu để lọc. Mặc định là None.
        
    Returns:
        Figure: Đối tượng Figure của matplotlib
    """
    # Dữ liệu mẫu cho phân phối giá
    brands = ['Honda', 'Yamaha', 'Suzuki', 'Piaggio', 'SYM']
    
    # Tạo dữ liệu phân phối giá giả lập
    np.random.seed(42)  # Để kết quả nhất quán
    data = []
    
    for b in brands:
        if brand is None or b == brand:
            if b == 'Honda':
                mean_price = 25
                std_price = 5
            elif b == 'Yamaha':
                mean_price = 30
                std_price = 7
            elif b == 'Suzuki':
                mean_price = 22
                std_price = 4
            elif b == 'Piaggio':
                mean_price = 40
                std_price = 10
            else:  # SYM
                mean_price = 18
                std_price = 3
            
            # Tạo dữ liệu phân phối giá
            prices = np.random.normal(mean_price, std_price, 100)
            prices = np.clip(prices, 0, None)  # Đảm bảo giá không âm
            
            for price in prices:
                data.append({'Thương hiệu': b, 'Giá (triệu VND)': price})
    
    df = pd.DataFrame(data)
    
    # Tạo biểu đồ histogram
    fig, ax = plt.subplots(figsize=(10, 6))
    
    if brand is None:
        for b in brands:
            subset = df[df['Thương hiệu'] == b]
            ax.hist(subset['Giá (triệu VND)'], alpha=0.5, label=b, bins=20)
        title = 'Phân phối giá theo thương hiệu'
    else:
        subset = df[df['Thương hiệu'] == brand]
        ax.hist(subset['Giá (triệu VND)'], alpha=0.7, label=brand, bins=20)
        title = f'Phân phối giá xe {brand}'
    
    ax.set_xlabel('Giá (triệu VND)')
    ax.set_ylabel('Tần suất')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    fig.tight_layout()
    return fig

def create_comparison_chart(features1, features2, prediction1, prediction2):
    """
    Tạo biểu đồ so sánh giữa hai xe
    
    Args:
        features1 (dict): Thông số xe thứ nhất
        features2 (dict): Thông số xe thứ hai
        prediction1 (dict): Kết quả dự đoán xe thứ nhất
        prediction2 (dict): Kết quả dự đoán xe thứ hai
        
    Returns:
        Figure: Đối tượng Figure của matplotlib
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Biểu đồ so sánh giá
    labels = ['Xe 1', 'Xe 2']
    prices = [prediction1['price'], prediction2['price']]
    min_prices = [prediction1['price_range'][0], prediction2['price_range'][0]]
    max_prices = [prediction1['price_range'][1], prediction2['price_range'][1]]
    
    x = np.arange(len(labels))
    width = 0.35
    
    ax1.bar(x, prices, width, label='Giá dự đoán')
    ax1.errorbar(x, prices, yerr=[np.array(prices)-np.array(min_prices), np.array(max_prices)-np.array(prices)], 
                fmt='o', color='r', capsize=5)
    
    ax1.set_ylabel('Giá (triệu VND)')
    ax1.set_title('So sánh giá dự đoán')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"{features1.get('brand', 'N/A')} {features1.get('model', 'N/A')}", 
                          f"{features2.get('brand', 'N/A')} {features2.get('model', 'N/A')}"])
    ax1.legend()
    
    # Biểu đồ radar cho so sánh thông số
    # Chuẩn hóa thông số để so sánh
    categories = ['Năm', 'CC', 'Km đã đi', 'Tình trạng', 'Giá']
    
    # Chuẩn hóa dữ liệu thông số
    year_norm = lambda y: (y - 2000) / 25  # Từ 2000-2025 -> 0-1
    cc_norm = lambda c: c / 1000  # Từ 0-1000cc -> 0-1
    km_norm = lambda k: 1 - k / 100000  # Từ 0-100000km -> 1-0 (càng ít càng tốt)
    condition_map = {"Rất kém": 0.2, "Kém": 0.4, "Trung bình": 0.6, "Tốt": 0.8, "Rất tốt": 1.0}
    condition_norm = lambda c: condition_map.get(c, 0.6)
    price_norm = lambda p: p / 50  # Từ 0-50 triệu -> 0-1
    
    # Áp dụng chuẩn hóa
    values1 = [
        year_norm(features1.get('year', 2020)),
        cc_norm(features1.get('cc', 125)),
        km_norm(features1.get('km_driven', 15000)),
        condition_norm(features1.get('condition', 'Trung bình')),
        price_norm(prediction1['price'])
    ]
    
    values2 = [
        year_norm(features2.get('year', 2020)),
        cc_norm(features2.get('cc', 125)),
        km_norm(features2.get('km_driven', 15000)),
        condition_norm(features2.get('condition', 'Trung bình')),
        price_norm(prediction2['price'])
    ]
    
    # Số lượng thông số
    N = len(categories)
    
    # Góc của mỗi trục
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Khép biểu đồ
    
    # Thêm giá trị đầu để khép biểu đồ
    values1 += values1[:1]
    values2 += values2[:1]
    
    # Vẽ biểu đồ radar
    ax2.plot(angles, values1, 'b-', linewidth=1, label=f"{features1.get('brand', 'N/A')} {features1.get('model', 'N/A')}")
    ax2.fill(angles, values1, 'b', alpha=0.1)
    ax2.plot(angles, values2, 'r-', linewidth=1, label=f"{features2.get('brand', 'N/A')} {features2.get('model', 'N/A')}")
    ax2.fill(angles, values2, 'r', alpha=0.1)
    
    # Thêm nhãn
    ax2.set_xticks(angles[:-1])
    ax2.set_xticklabels(categories)
    ax2.set_title('So sánh thông số')
    ax2.legend(loc='upper right')
    
    fig.tight_layout()
    return fig