import time
import os
import re
import datetime
import json
import pandas as pd
import logging
import traceback
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from urllib.parse import urljoin

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/raw/vnexpress_crawler.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("VnExpressBikeCrawler")

# URL cơ sở cho phần xe máy của VnExpress
BASE_URL = "https://vnexpress.net"

class VnExpressBikeCrawler:
    def __init__(self):
        """Khởi tạo crawler"""
        self.driver = None
        self.all_models = []
        self.create_folders()
        
    def create_folders(self):
        """Tạo các thư mục cần thiết cho output"""
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        os.makedirs("screenshots", exist_ok=True)
        
    def setup_driver(self):
        """Thiết lập và trả về trình duyệt Chrome WebDriver"""
        logger.info("Đang thiết lập Chrome WebDriver...")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-notifications")
        
        # Thêm user agent để tránh bị phát hiện
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        try:
            # Thử tạo driver (không có Service cho phiên bản mới)
            logger.info("Đang thử tạo Chrome driver...")
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome driver đã được tạo thành công")
        except Exception as e:
            logger.warning(f"Khởi tạo trực tiếp thất bại: {e}")
            try:
                # Thử với Service cho phiên bản cũ hơn
                logger.info("Đang thử tạo Chrome driver với Service...")
                service = Service('chromedriver')
                driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("Chrome driver đã được tạo với Service")
            except Exception as e:
                logger.error(f"Không thể khởi tạo Chrome WebDriver: {e}")
                logger.error("Hãy đảm bảo chromedriver đã được cài đặt và nằm trong PATH")
                raise
        
        # Thiết lập thời gian chờ
        driver.set_page_load_timeout(60)  # Tăng từ 30 lên 60 giây
        driver.implicitly_wait(20)  # Tăng từ 10 lên 20 giây
        
        return driver
    
    def take_screenshot(self, filename):
        """Chụp ảnh màn hình để gỡ lỗi"""
        if not self.driver:
            return
            
        try:
            path = f"screenshots/{filename}.png"
            self.driver.save_screenshot(path)
            logger.info(f"Đã lưu ảnh chụp màn hình vào {path}")
        except Exception as e:
            logger.warning(f"Không thể chụp ảnh màn hình: {e}")
    
    def get_bike_models(self, brand_url, brand_name, brand_id):
        """
        Lấy tất cả mẫu xe máy cho một hãng cụ thể
        """
        models = []
        full_url = urljoin(BASE_URL, brand_url)
        current_page = 1
        
        logger.info(f"Đang xử lý hãng: {brand_name}, URL: {full_url}")
        
        try:
            # Tải trang đầu tiên
            logger.info(f"Đang tải trang 1...")
            self.driver.get(full_url)
            
            # Xử lý các trang cho đến khi không còn nữa
            while True:
                logger.info(f"Đang xử lý trang {current_page}...")
                
                # Chờ nội dung tải xong
                self.wait_for_content()
                
                # Trích xuất nội dung trang
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Xử lý xe máy trên trang hiện tại
                page_models = self.extract_bikes_from_page(soup, brand_name, brand_id)
                
                if not page_models:
                    logger.warning(f"Không tìm thấy mẫu xe nào trên trang {current_page}")
                    break
                    
                models.extend(page_models)
                logger.info(f"Đã trích xuất {len(page_models)} xe từ trang {current_page}")
                
                # Cố gắng chuyển đến trang tiếp theo
                if not self.go_to_next_page(current_page, brand_name):
                    logger.info(f"Không còn trang nào cho {brand_name}")
                    break
                    
                current_page += 1
                
        except Exception as e:
            logger.error(f"Lỗi khi xử lý hãng {brand_name}: {e}")
            logger.error(traceback.format_exc())
            self.take_screenshot(f"{brand_name}_error")
        
        logger.info(f"Hoàn thành xử lý {brand_name}. Tìm thấy {len(models)} mẫu xe.")
        return models
    
    def wait_for_content(self):
        """Chờ nội dung trang tải xong"""
        try:
            # Chờ các mục xe máy xuất hiện - TĂNG THỜI GIAN CHỜ Ở ĐÂY
            WebDriverWait(self.driver, 100).until(  # Tăng từ 10 lên 30 giây
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.article-item.full"))
            )
            logger.info("Nội dung đã tải thành công")
        except TimeoutException:
            logger.warning("Hết thời gian chờ nội dung tải")
            # Kiểm tra xem nội dung có hiện diện dù hết thời gian chờ
            if len(self.driver.find_elements(By.CSS_SELECTOR, "div.article-item.full")) > 0:
                logger.info("Nội dung có vẻ đã tải dù hết thời gian chờ")
            else:
                logger.error("Không tìm thấy nội dung sau khi hết thời gian chờ")
    
    def go_to_next_page(self, current_page, brand_name):
        """Cố gắng điều hướng đến trang tiếp theo, trả về True nếu thành công"""
        # Tìm phần tử phân trang
        pagination = self.driver.find_elements(By.CSS_SELECTOR, "div#pagination")
        if not pagination:
            logger.info("Không tìm thấy phân trang")
            return False
            
        # Tìm nút trang tiếp theo
        next_buttons = self.driver.find_elements(By.CSS_SELECTOR, "div#pagination a.pa_next")
        if not next_buttons:
            logger.info("Không tìm thấy nút trang tiếp theo")
            return False
            
        next_button = next_buttons[0]
        next_page_num = next_button.get_attribute("data-page-number")
        
        if not next_page_num or next_page_num != str(current_page + 1):
            logger.info(f"Nút trang tiếp không trỏ đến trang {current_page + 1}")
            return False
            
        # Chụp ảnh màn hình trước khi nhấp
        self.take_screenshot(f"{brand_name}_page{current_page}_before_click")
        
        # Lấy URL hiện tại để so sánh
        current_url = self.driver.current_url
        
        try:
            # Nhấp vào nút trang tiếp theo
            logger.info(f"Đang nhấp vào nút trang tiếp đến trang {next_page_num}...")
            next_button.click()
            
            # Chờ việc điều hướng hoàn tất (nhiều chiến lược khác nhau)
            success = self.wait_for_page_change(current_url, current_page, brand_name)
            
            # Thêm độ trễ để lịch sự với máy chủ
            time.sleep(2)
            
            return success
            
        except Exception as e:
            logger.error(f"Lỗi khi điều hướng đến trang tiếp theo: {e}")
            self.take_screenshot(f"{brand_name}_page{current_page}_click_error")
            return False
    
    def wait_for_page_change(self, old_url, current_page, brand_name):
        """Chờ trang thay đổi sau khi nhấp vào nút trang tiếp theo"""
        try:
            # Chờ URL thay đổi hoặc các phần tử mới tải - TĂNG THỜI GIAN CHỜ
            try:
                # Cố gắng chờ URL thay đổi
                WebDriverWait(self.driver, 15).until(lambda d: d.current_url != old_url)  # Tăng từ 5 lên 15 giây
                logger.info("URL đã thay đổi - điều hướng trang thành công")
                self.take_screenshot(f"{brand_name}_page{current_page+1}_loaded")
                return True
            except TimeoutException:
                logger.warning("Hết thời gian chờ URL thay đổi, đang kiểm tra nội dung...")
                
                # Nếu URL không thay đổi, kiểm tra xem nội dung có thay đổi không - thêm độ trễ ở đây
                time.sleep(5)  # Thêm độ trễ để đảm bảo nội dung có thời gian tải
                
                new_items = self.driver.find_elements(By.CSS_SELECTOR, "div.article-item.full h3.title-name")
                
                if new_items:
                    logger.info(f"Tìm thấy {len(new_items)} tiêu đề xe máy, trang có thể đã thay đổi")
                    self.take_screenshot(f"{brand_name}_page{current_page+1}_content_check")
                    return True
                else:
                    logger.warning("Không phát hiện bằng chứng trang đã thay đổi")
                    return False
                    
        except Exception as e:
            logger.error(f"Lỗi khi chờ trang thay đổi: {e}")
            return False
    
    def extract_bikes_from_page(self, soup, brand_name, brand_id):
        """Trích xuất các mẫu xe máy từ trang hiện tại"""
        models = []
        bike_items = soup.select('div.article-item.full')
        
        if not bike_items:
            logger.warning("Không tìm thấy mục xe máy nào trên trang")
            return models
            
        logger.info(f"Tìm thấy {len(bike_items)} mục xe máy")
        
        # Trích xuất danh mục đang hoạt động nếu có
        category = self.extract_category(soup)
        logger.info(f"Danh mục đang hoạt động: {category}")
        
        for index, item in enumerate(bike_items, 1):
            try:
                model = self.extract_bike_data(item, brand_name, brand_id, category, index)
                if model:
                    models.append(model)
            except Exception as e:
                logger.error(f"Lỗi trích xuất dữ liệu xe máy: {e}")
                continue
                
        return models
    
    def extract_category(self, soup):
        """Trích xuất danh mục đang hoạt động từ trang"""
        try:
            category_tabs = soup.select('div.tab-default a')
            for tab in category_tabs:
                if tab.has_attr('class') and 'active' in tab['class']:
                    if tab.get('title'):
                        return tab.get('title')
                    else:
                        tab_text = tab.get_text(strip=True)
                        if tab_text and tab_text != "Tất cả":
                            return tab_text
        except Exception as e:
            logger.error(f"Lỗi trích xuất danh mục: {e}")
        
        return None
    
    def extract_bike_data(self, item, brand_name, brand_id, category, index):
        """Trích xuất dữ liệu cho một mục xe máy"""
        # Trích xuất thông tin cơ bản
        link_elem = item.select_one('h3.title-name a')
        if not link_elem:
            logger.warning(f"Mục {index}: Thiếu liên kết tiêu đề")
            return None
            
        model_name = link_elem.get('title')
        model_url = link_elem.get('href')
        
        # Trích xuất ID model
        model_id_match = re.search(r'(\d+)$', model_url)
        model_id = model_id_match.group(1) if model_id_match else None
        
        # Trích xuất hình ảnh
        img_elem = item.select_one('picture img')
        model_image = img_elem.get('src') if img_elem else None
        
        # Trích xuất giá và ngày ra mắt
        price_text = None
        release_date = None
        
        des_elems = item.select('div.des p')
        for des in des_elems:
            text = des.text.strip()
            if 'Khoảng giá:' in text:
                price_text = text
            elif 'Ra mắt:' in text:
                release_date = text
        
        # Xử lý giá để lấy giá trị tối thiểu và tối đa
        price_min, price_max = self.process_price(price_text)
        
        # Trích xuất năm ra mắt
        release_year = self.extract_release_year(release_date)
        
        model_data = {
            'brand_name': brand_name,
            'brand_id': brand_id,
            'model_name': model_name,
            'model_url': model_url,
            'model_id': model_id,
            'model_image': model_image,
            'model_category': category,
            'price_text': price_text.replace('Khoảng giá:', '').strip() if price_text else None,
            'price_min': price_min,
            'price_max': price_max,
            'release_date': release_date.replace('Ra mắt:', '').strip() if release_date else None,
            'release_year': release_year
        }
        
        logger.info(f"Đã trích xuất model: {model_name} (ID: {model_id})")
        return model_data
    
    def process_price(self, price_text):
        """Xử lý văn bản giá để trích xuất giá trị tối thiểu và tối đa"""
        if not price_text:
            return None, None
        
        # Loại bỏ tiền tố
        price_text = price_text.replace('Khoảng giá:', '').strip()
        
        # Xử lý các định dạng giá khác nhau
        if ' - ' in price_text:
            # Định dạng phạm vi: "XX - YY triệu"
            parts = price_text.split(' - ')
            min_price_text = parts[0].strip()
            max_price_text = parts[1].strip()
            
            min_price = self.extract_numeric_price(min_price_text)
            max_price = self.extract_numeric_price(max_price_text)
        elif ' triệu' in price_text:
            # Định dạng giá đơn: "XX triệu"
            min_price = max_price = self.extract_numeric_price(price_text)
        else:
            # Định dạng không xác định
            min_price = max_price = None
        
        return min_price, max_price
    
    def extract_numeric_price(self, price_text):
        """Trích xuất giá trị số từ văn bản"""
        # Loại bỏ ký tự không phải số trừ dấu thập phân
        price_text = re.sub(r'[^\d.,]', '', price_text)
        
        # Thay thế dấu phẩy bằng dấu chấm cho số thập phân
        price_text = price_text.replace(',', '.')
        
        try:
            return float(price_text)
        except (ValueError, TypeError):
            return None
    
    def extract_release_year(self, release_date):
        """Trích xuất năm ra mắt từ văn bản ngày"""
        if not release_date:
            return None
        
        # Loại bỏ tiền tố
        release_date = release_date.replace('Ra mắt:', '').strip()
        
        # Cố gắng trích xuất năm trực tiếp
        year_match = re.search(r'20\d{2}', release_date)
        if year_match:
            return int(year_match.group(0))
        
        # Cố gắng định dạng tháng/năm
        date_match = re.search(r'(\d{1,2})/(\d{4})', release_date)
        if date_match:
            return int(date_match.group(2))
        
        # Nếu chỉ có tên tháng, sử dụng năm hiện tại
        current_year = datetime.datetime.now().year
        month_names = [
            'tháng 1', 'tháng 2', 'tháng 3', 'tháng 4', 'tháng 5', 'tháng 6',
            'tháng 7', 'tháng 8', 'tháng 9', 'tháng 10', 'tháng 11', 'tháng 12',
            'jan', 'feb', 'mar', 'apr', 'may', 'jun', 
            'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
        ]
        
        for month in month_names:
            if month.lower() in release_date.lower():
                return current_year
        
        return None
    
    def crawl_all_brands(self, brands_list):
        """Thu thập dữ liệu từ tất cả các hãng trong danh sách được cung cấp"""
        logger.info(f"Bắt đầu crawler cho {len(brands_list)} hãng")
        
        # Khởi tạo driver nếu chưa tạo
        if not self.driver:
            self.driver = self.setup_driver()
        
        start_time = time.time()
        
        try:
            # Xử lý từng hãng
            for idx, brand in enumerate(brands_list, 1):
                logger.info(f"===== Đang xử lý hãng {idx}/{len(brands_list)}: {brand['brand_name']} =====")
                
                brand_start_time = time.time()
                
                # Lấy các model cho hãng này
                models = self.get_bike_models(
                    brand['brand_url'],
                    brand['brand_name'],
                    brand['brand_id']
                )
                
                # Thêm logo hãng vào từng model
                for model in models:
                    model['brand_logo'] = brand['brand_logo']
                
                # Thêm vào bộ sưu tập toàn cục
                self.all_models.extend(models)
                
                # Lưu kết quả trung gian
                self.save_intermediate_results(idx, len(brands_list))
                
                # Ghi log thời gian
                brand_duration = time.time() - brand_start_time
                logger.info(f"Hoàn thành hãng {brand['brand_name']} trong {brand_duration:.2f} giây")
                logger.info(f"Tìm thấy {len(models)} model cho {brand['brand_name']}")
                
                # Hiển thị mẫu model
                self.display_sample(models, brand['brand_name'])
                
                # Tạm dừng giữa các hãng
                if idx < len(brands_list):
                    logger.info("Đang chờ trước khi xử lý hãng tiếp theo...")
                    time.sleep(3)
        
        except Exception as e:
            logger.error(f"Lỗi trong quá trình crawl chính: {e}")
            logger.error(traceback.format_exc())
        
        finally:
            # Lưu kết quả cuối cùng
            self.save_results()
            
            # Đóng driver
            if self.driver:
                logger.info("Đóng WebDriver...")
                self.driver.quit()
                self.driver = None
        
        # Ghi log thống kê
        total_duration = time.time() - start_time
        logger.info(f"Hoàn thành crawl trong {total_duration:.2f} giây")
        logger.info(f"Tổng model đã thu thập: {len(self.all_models)}")
        self.log_statistics()
        
        return self.all_models
    
    def save_intermediate_results(self, current_idx, total_brands):
        """Lưu kết quả trung gian vào CSV"""
        if not self.all_models:
            logger.warning("Không có model nào để lưu kết quả trung gian")
            return
            
        try:
            df = pd.DataFrame(self.all_models)
            path = f"data/raw/models_progress_{current_idx}_{total_brands}.csv"
            df.to_csv(path, index=False, encoding='utf-8-sig')
            logger.info(f"Đã lưu kết quả trung gian vào {path}")
        except Exception as e:
            logger.error(f"Lỗi lưu kết quả trung gian: {e}")
    
    def save_results(self):
        """Lưu kết quả cuối cùng vào CSV"""
        if not self.all_models:
            logger.warning("Không có model nào để lưu kết quả cuối cùng")
            return
            
        try:
            # Lưu vào CSV
            df = pd.DataFrame(self.all_models)
            csv_path = "data/processed/all_motorcycle_models.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            logger.info(f"Đã lưu kết quả cuối cùng vào {csv_path}")
            
            # Đồng thời lưu như JSON để sao lưu
            json_path = "data/raw/all_motorcycle_models.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.all_models, f, ensure_ascii=False, indent=2)
            logger.info(f"Đã lưu bản sao lưu vào {json_path}")
        
        except Exception as e:
            logger.error(f"Lỗi lưu kết quả cuối cùng: {e}")
    
    def display_sample(self, models, brand_name, sample_size=5):
        """Hiển thị mẫu các model cho một hãng"""
        if not models:
            return
            
        sample = models[:min(sample_size, len(models))]
        logger.info(f"\nMẫu các model từ {brand_name}:")
        
        for i, model in enumerate(sample, 1):
            price_info = "N/A"
            if model.get('price_min') and model.get('price_max'):
                if model['price_min'] == model['price_max']:
                    price_info = f"{model['price_min']} triệu"
                else:
                    price_info = f"{model['price_min']} - {model['price_max']} triệu"
                    
            logger.info(f"  {i}. {model['model_name']} - {price_info}")
        
        if len(models) > sample_size:
            logger.info(f"  ... và {len(models) - sample_size} model khác")
    
    def log_statistics(self):
        """Ghi log thống kê về dữ liệu đã thu thập"""
        if not self.all_models:
            return
            
        # Đếm model theo hãng
        brand_counts = {}
        for model in self.all_models:
            brand = model['brand_name']
            brand_counts[brand] = brand_counts.get(brand, 0) + 1
        
        logger.info("\nModel theo hãng:")
        for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {brand}: {count} model")
        
        # Đếm model theo danh mục nếu có
        category_counts = {}
        for model in self.all_models:
            if model.get('model_category'):
                cat = model['model_category']
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        if category_counts:
            logger.info("\nModel theo danh mục:")
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {cat}: {count} model")

def get_bike_brands():
    """Trả về danh sách các hãng xe máy từ VnExpress"""
    return [
        {'brand_name': 'Honda', 'brand_url': '/oto-xe-may/v-bike/hang-xe/honda-1', 'brand_id': '1', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/03/16/2552pxHondaLogosvgpng-1678932914.png?w=220&h=0&q=100&dpr=1&fit=crop&s=yR5_NaOU-YnIvgD8iF37sA&t=image'},
        {'brand_name': 'Yamaha', 'brand_url': '/oto-xe-may/v-bike/hang-xe/yamaha-2', 'brand_id': '2', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2024/06/14/imagepng-1718357049.png?w=220&h=0&q=100&dpr=1&fit=crop&s=tc4___X8qajoh6eI5lGh8Q&t=image'},
        {'brand_name': 'Vespa', 'brand_url': '/oto-xe-may/v-bike/hang-xe/vespa-4', 'brand_id': '4', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/03/Vespapng-1680494134.png?w=220&h=0&q=100&dpr=1&fit=crop&s=R7jmP3TA4ih_Bu9RbXBfaQ&t=image'},
        {'brand_name': 'Piaggio', 'brand_url': '/oto-xe-may/v-bike/hang-xe/piaggio-5', 'brand_id': '5', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/03/PiaggioLogoPNG1png-1680494127.png?w=220&h=0&q=100&dpr=1&fit=crop&s=Dwv_R7-5i9gdHs8vJiyZ0Q&t=image'},
        {'brand_name': 'SYM', 'brand_url': '/oto-xe-may/v-bike/hang-xe/sym-6', 'brand_id': '6', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/03/SYMpng-1680494114.png?w=220&h=0&q=100&dpr=1&fit=crop&s=2V8-Os0a5LqsxUJVjdn_rQ&t=image'},
        {'brand_name': 'Suzuki', 'brand_url': '/oto-xe-may/v-bike/hang-xe/suzuki-7', 'brand_id': '7', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/03/SuzukiMotorCorporationlogosvgpng-1680494893.png?w=220&h=0&q=100&dpr=1&fit=crop&s=BAZd22GoEqn3mx9Gc-YxdA&t=image'},
        {'brand_name': 'Ducati', 'brand_url': '/oto-xe-may/v-bike/hang-xe/ducati-8', 'brand_id': '8', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/03/DucatiPNG-1680494097.png?w=220&h=0&q=100&dpr=1&fit=crop&s=HLcZFbNpp713ibdY9uESdw&t=image'},
        {'brand_name': 'BMW Motorrad', 'brand_url': '/oto-xe-may/v-bike/hang-xe/bmw-motorrad-9', 'brand_id': '9', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/03/BMWMotorradpng-1680494087.png?w=220&h=0&q=100&dpr=1&fit=crop&s=9kw0sXPCFbCirYWOoSs10A&t=image'},
        {'brand_name': 'Harley-Davidson', 'brand_url': '/oto-xe-may/v-bike/hang-xe/harley-davidson-10', 'brand_id': '10', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/14/HDOKpng-1681441767.png?w=220&h=0&q=100&dpr=1&fit=crop&s=IrFaD9rfUlFrkSUwrHQ-RQ&t=image'},
        {'brand_name': 'Aprilia', 'brand_url': '/oto-xe-may/v-bike/hang-xe/aprilia-11', 'brand_id': '11', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/03/Apriliapng-1680494067.png?w=220&h=0&q=100&dpr=1&fit=crop&s=g0cBPbv89ImwvH25V7_Phg&t=image'},
        {'brand_name': 'Moto Guzzi', 'brand_url': '/oto-xe-may/v-bike/hang-xe/moto-guzzi-12', 'brand_id': '12', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/03/MotoGuzzipng-1680494059.png?w=220&h=0&q=100&dpr=1&fit=crop&s=8utZn0bYmC4MJVeKTdD5OA&t=image'},
        {'brand_name': 'Kawasaki', 'brand_url': '/oto-xe-may/v-bike/hang-xe/kawasaki-13', 'brand_id': '13', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/03/Kawasakilogosvgpng-1680494791.png?w=220&h=0&q=100&dpr=1&fit=crop&s=Z-x2xYqHiFczOU9c9JUYIg&t=image'},
        {'brand_name': 'Triumph', 'brand_url': '/oto-xe-may/v-bike/hang-xe/triumph-14', 'brand_id': '14', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/03/Triumphpng-1680494042.png?w=220&h=0&q=100&dpr=1&fit=crop&s=ilqcJarSIY47p__R1qFfyw&t=image'},
        {'brand_name': 'KTM', 'brand_url': '/oto-xe-may/v-bike/hang-xe/ktm-15', 'brand_id': '15', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/03/KTMLogosvgpng-1680494970.png?w=220&h=0&q=100&dpr=1&fit=crop&s=I730zkDDpHBV4oU51CaRgQ&t=image'},
        {'brand_name': 'Royal Enfield', 'brand_url': '/oto-xe-may/v-bike/hang-xe/royal-enfield-16', 'brand_id': '16', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/03/RoyalEnfieldLogopng-1680494023.png?w=220&h=0&q=100&dpr=1&fit=crop&s=5st5T93K5imApPOlELGiDg&t=image'},
        {'brand_name': 'Yadea', 'brand_url': '/oto-xe-may/v-bike/hang-xe/yadea-17', 'brand_id': '17', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/03/Yadeapngcrdownloadpng-1680494007.png?w=220&h=0&q=100&dpr=1&fit=crop&s=X25UqYpyuLJ5CZ6ApYjcvA&t=image'},
        {'brand_name': 'VinFast', 'brand_url': '/oto-xe-may/v-bike/hang-xe/vinfast-18', 'brand_id': '18', 'brand_logo': 'https://i1-vnexpress.vnecdn.net/2023/04/03/VinFastpng-1680493996.png?w=220&h=0&q=100&dpr=1&fit=crop&s=VJB2BHutYcntoKtSZpYqXw&t=image'}
    ]

def main():
   """Điểm nhập chính"""
   logger.info("=== Bắt đầu VnExpress Motorcycle Crawler ===")
   
   # Danh sách các hãng để crawl
   brands_list = get_bike_brands()
   
   # Tạo và chạy crawler
   crawler = VnExpressBikeCrawler()
   crawler.crawl_all_brands(brands_list)
   
   logger.info("=== Hoàn thành chạy crawler ===")

if __name__ == "__main__":
   main()