import logging
import time
from .chotot_crawler import ChototCrawler
from .vnexpress_crawler import VnExpressBikeCrawler

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CrawlerManager")

class CrawlerManager:
    """Lớp quản lý các crawler khác nhau trong hệ thống"""
    
    def __init__(self):
        """Khởi tạo manager với các crawler cụ thể"""
        self.crawlers = {
            'chotot': ChototCrawler(),
            'vnexpress': VnExpressBikeCrawler()
        }
        
    def run_crawler(self, crawler_name, **kwargs):
        """Chạy một crawler cụ thể với các tham số tùy chọn
        
        Args:
            crawler_name (str): Tên của crawler cần chạy
            **kwargs: Các tham số bổ sung cho crawler cụ thể
            
        Returns:
            list: Dữ liệu thu thập được
        """
        if crawler_name not in self.crawlers:
            logger.error(f"Crawler không tồn tại: {crawler_name}")
            return None
            
        logger.info(f"Đang chạy crawler: {crawler_name}")
        start_time = time.time()
        
        try:
            if crawler_name == 'chotot':
                # Chạy crawler cho Chợ Tốt
                listings = self.crawlers[crawler_name].scrape_multiple_pages(
                    num_pages=kwargs.get('num_pages', 5)
                )
                if kwargs.get('get_details', False):
                    return self.crawlers[crawler_name].scrape_listings_with_details(listings)
                return listings
            
            elif crawler_name == 'vnexpress':
                # Chạy crawler cho VnExpress
                brands_list = kwargs.get('brands_list', [])
                return self.crawlers[crawler_name].crawl_all_brands(brands_list)
            
        except Exception as e:
            logger.error(f"Lỗi khi chạy {crawler_name}: {e}")
            return None
        finally:
            logger.info(f"Hoàn thành {crawler_name} trong {time.time() - start_time:.2f} giây")
            
    def run_all_crawlers(self, **kwargs):
        """Chạy tất cả các crawler
        
        Args:
            **kwargs: Các tham số cho từng crawler
            
        Returns:
            dict: Kết quả từ tất cả các crawler
        """
        results = {}
        
        for crawler_name in self.crawlers:
            logger.info(f"Đang chạy crawler: {crawler_name}")
            results[crawler_name] = self.run_crawler(crawler_name, **kwargs.get(crawler_name, {}))
            
        return results