import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chotot_crawler.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ChototCrawler")

class ChototCrawler:
    """Crawler để thu thập dữ liệu từ website Chợ Tốt"""
    
    def __init__(self):
        """Khởi tạo crawler với các cấu hình cơ bản"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.base_url = "https://xe.chotot.com/mua-ban-xe-may"
        
    def get_page_content(self, url):
        """Lấy nội dung từ một trang web
        
        Args:
            url (str): URL của trang web cần lấy nội dung
            
        Returns:
            str: Nội dung HTML của trang web hoặc None nếu có lỗi
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Lỗi khi tải trang: {e}")
            return None
            
    def parse_single_listing(self, listing):
        """Phân tích một phần tử sản phẩm để lấy URL
        
        Args:
            listing (BeautifulSoup): Đối tượng BeautifulSoup của phần tử sản phẩm
            
        Returns:
            str: URL của sản phẩm hoặc None nếu có lỗi
        """
        try:
            href = listing.find('a', class_='cebeqpz')['href']
            logger.info(f"Đã tìm thấy URL: {href}")
            return href
        except Exception as e:
            logger.error(f"Lỗi khi phân tích phần tử: {e}")
            return None
            
    def parse_page_listings(self, content):
        """Phân tích nội dung trang để lấy danh sách các URL sản phẩm
        
        Args:
            content (str): Nội dung HTML của trang
            
        Returns:
            list: Danh sách các URL sản phẩm
        """
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        listings = soup.find_all('li', {'itemtype': 'http://schema.org/ListItem'})
        
        all_listings = []
        for listing in listings:
            data = self.parse_single_listing(listing)
            if data:
                all_listings.append(data)
        
        return all_listings
            
    def scrape_multiple_pages(self, num_pages=5):
        """Thu thập URL sản phẩm từ nhiều trang
        
        Args:
            num_pages (int): Số trang cần thu thập
            
        Returns:
            list: Danh sách các URL sản phẩm
        """
        all_listings = []
        
        for page in range(1, num_pages + 1):
            logger.info(f"\nĐang thu thập trang {page}...")
            page_url = f"{self.base_url}?f=p&page={page}"
            
            content = self.get_page_content(page_url)
            page_listings = self.parse_page_listings(content)
            
            if page_listings:
                all_listings.extend(page_listings)
                logger.info(f"Đã tìm thấy {len(page_listings)} sản phẩm trên trang {page}")
            
            # Chờ giữa các request để không gây quá tải cho server
            time.sleep(1)
        
        # Lưu danh sách URLs vào file CSV
        df = pd.DataFrame(all_listings)
        filename = 'data/raw/chotot_listings.csv'
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"Đã lưu danh sách URLs vào file {filename}")
        
        return all_listings
        
    def extract_data(self, url):
        """Trích xuất thông tin chi tiết từ trang sản phẩm
        
        Args:
            url (str): URL của trang sản phẩm
            
        Returns:
            dict: Thông tin chi tiết của sản phẩm hoặc None nếu có lỗi
        """
        try:
            logger.info(f"\nĐang phân tích URL: {url}")
            full_url = self.base_url + url if not url.startswith('http') else url
            response = requests.get(full_url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trích xuất các thông tin cần thiết
            title = soup.find("div", {"class": "cpmughi"}).find("h1").text
            price = soup.find("b", {"class": "p26z2wb"}).text
            description = soup.find("p", {"class": "cvatvjo"}).text
            details = soup.find_all("span", {"class": "bwq0cbs"})
            
            # Trích xuất các chi tiết cụ thể
            origin = details[7].text
            location = details[8].text
            post_time = details[9].text
            brand = details[11].text
            model = details[13].text
            reg_year = details[15].text
            mileage = details[17].text
            condition = details[19].text
            vehicle_type = details[21].text
            engine_capacity = details[23].text
            warranty = details[27].text
            weight = details[29].text
            
            # In thông tin để kiểm tra
            logger.info(f"Tiêu đề: {title}")
            logger.info(f"Giá: {price}")
            
            # Trả về dưới dạng từ điển
            return {
                "title": title,
                "price": price,
                "description": description,
                "origin": origin,
                "location": location,
                "post_time": post_time,
                "brand": brand,
                "model": model,
                "reg_year": reg_year,
                "mileage": mileage,
                "condition": condition,
                "vehicle_type": vehicle_type,
                "engine_capacity": engine_capacity,
                "warranty": warranty,
                "weight": weight,
                "url": url
            }
            
        except Exception as e:
            logger.error(f"Lỗi khi phân tích trang sản phẩm {url}: {e}")
            return None
            
    def scrape_listings_with_details(self, urls):
        """Thu thập thông tin chi tiết từ danh sách URLs
        
        Args:
            urls (list): Danh sách URLs sản phẩm cần thu thập
            
        Returns:
            list: Danh sách thông tin chi tiết của các sản phẩm
        """
        all_data = []
        total = len(urls)
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Đang xử lý {i}/{total}: {url}")
            
            # Thêm độ trễ nhỏ để tránh bị chặn
            time.sleep(1)
            
            # Trích xuất dữ liệu
            data = self.extract_data(url)
            if data:
                all_data.append(data)
                
            # Ghi log tiến độ
            if i % 10 == 0:
                logger.info(f"Đã xử lý {i}/{total} URLs")
        
        # Lưu kết quả vào file CSV
        df = pd.DataFrame(all_data)
        filename = 'data/processed/chotot_motorbikes.csv'
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"Đã lưu dữ liệu chi tiết vào file {filename}")
        
        return all_data