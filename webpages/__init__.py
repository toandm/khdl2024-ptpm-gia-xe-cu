# pages/__init__.py
import os
import sys

# Thêm thư mục gốc vào sys.path để có thể import các module khác
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from .market_overview import show_market_overview
from .price_prediction import show_price_prediction
from .bike_comparison import show_bike_comparison
from .bike_suggestion import show_bike_suggestion