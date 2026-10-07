"""
Advanced Web Scraper con APIs de tiendas (más confiable que web scraping)
Usa APIs públicas y endpoints cuando es posible
"""

import requests
import json
from datetime import datetime
import logging
from typing import Dict, List
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedPriceScraper:
    """Scraper mejorado usando APIs y endpoints reales de las tiendas"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_walmart_api(self, products: List[str]) -> Dict:
        """Usar Walmart Search API"""
        logger.info("Scraping Walmart via API...")
        walmart_prices = {}
        
        for product in products:
            try:
                # Walmart Search endpoint
                url = "https://www.walmart.com/api/v3/search"
                params = {
                    'query': product,
                    'limit': 1,
                    'offset': 0,
                    'sort': 'best_match'
                }
                
                response = requests.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('items'):
                        item = data['items'][0]
                        price = item.get('price')
                        
                        if price:
                            walmart_prices[product] = float(price)
                            logger.info(f"✓ Walmart {product}: ${price}")
                        else:
                            walmart_prices[product] = None
                    else:
                        walmart_prices[product] = None
                else:
                    walmart_prices[product] = None
                    
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error Walmart {product}: {e}")
                walmart_prices[product] = None
        
        return walmart_prices
    
    def scrape_target_api(self, products: List[str]) -> Dict:
        """Usar Target Product API"""
        logger.info("Scraping Target via API...")
        target_prices = {}
        
        for product in products:
            try:
                # Target Product Search
                url = "https://redsky.target.com/redsky_aggregations/v1/web/search_api/search"
                params = {
                    'category': '0',
                    'offset': '0',
                    'pageSize': '24',
                    'keyword': product,
                    'response_groups': 'Product,Offers'
                }
                
                response = requests.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('data', {}).get('search', {}).get('products'):
                        products_list = data['data']['search']['products']
                        
                        if products_list:
                            item = products_list[0]
                            price = item.get('price', {}).get('current_retail')
                            
                            if price:
                                target_prices[product] = float(price)
                                logger.info(f"✓ Target {product}: ${price}")
                            else:
                                target_prices[product] = None
                        else:
                            target_prices[product] = None
                    else:
                        target_prices[product] = None
                else:
                    target_prices[product] = None
                    
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error Target {product}: {e}")
                target_prices[product] = None
        
        return target_prices
    
    def scrape_costco_api(self, products: List[str]) -> Dict:
        """Usar Costco Search API"""
        logger.info("Scraping Costco via API...")
        costco_prices = {}
        
        for product in products:
            try:
                # Costco Search endpoint
                url = "https://www.costco.com/DoSearch"
                params = {
                    'keyword': product,
                    'SearchButton': 'Search',
                    'languageId': '-1',
                    'catalogId': '10701'
                }
                
                response = requests.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    # Parse HTML response
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Buscar precio en estructura de Costco
                    price_elem = soup.find('span', {'class': 'price'})
                    
                    if price_elem:
                        price_text = price_elem.text.strip().replace('$', '')
                        try:
                            price = float(price_text.split('-')[0].strip())
                            costco_prices[product] = price
                            logger.info(f"✓ Costco {product}: ${price}")
                        except:
                            costco_prices[product] = None
                    else:
                        costco_prices[product] = None
                else:
                    costco_prices[product] = None
                    
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error Costco {product}: {e}")
                costco_prices[product] = None
        
        return costco_prices
    
    def scrape_sams_api(self, products: List[str]) -> Dict:
        """Usar Sam's Club Search API"""
        logger.info("Scraping Sam's Club via API...")
        sams_prices = {}
        
        for product in products:
            try:
                # Sam's Club Search endpoint
                url = "https://www.samsclub.com/api/v1/products/search"
                params = {
                    'keyword': product,
                    'pageNumber': 1,
                    'pageSize': 20
                }
                
                response = requests.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('items'):
                        item = data['items'][0]
                        # Sam's Club devuelve 'price' o 'msrp'
                        price = item.get('price') or item.get('msrp')
                        
                        if price:
                            sams_prices[product] = float(price)
                            logger.info(f"✓ Sam's Club {product}: ${price}")
                        else:
                            sams_prices[product] = None
                    else:
                        sams_prices[product] = None
                else:
                    sams_prices[product] = None
                    
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error Sam's Club {product}: {e}")
                sams_prices[product] = None
        
        return sams_prices
    
    def scrape_safeway_api(self, products: List[str]) -> Dict:
        """Usar Safeway API (requiere header especial)"""
        logger.info("Scraping Safeway via API...")
        safeway_prices = {}
        
        # Safeway usa una API con autenticación
        # Para el MVP, usaremos web scraping
        
        for product in products:
            try:
                from bs4 import BeautifulSoup
                
                url = f"https://www.safeway.com/shop/search-results.html?q={product.replace(' ', '+')}"
                
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Buscar precio en estructura de Safeway
                    price_elem = soup.find('span', {'class': 'price'})
                    
                    if price_elem:
                        price_text = price_elem.text.strip().replace('$', '')
                        try:
                            price = float(price_text.split('-')[0].strip())
                            safeway_prices[product] = price
                            logger.info(f"✓ Safeway {product}: ${price}")
                        except:
                            safeway_prices[product] = None
                    else:
                        safeway_prices[product] = None
                else:
                    safeway_prices[product] = None
                    
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Error Safeway {product}: {e}")
                safeway_prices[product] = None
        
        return safeway_prices
    
    def scrape_all(self, products: List[str]) -> Dict:
        """Scrape todos los supermercados"""
        logger.info(f"Starting advanced scraping for {len(products)} products...")
        
        results = {
            'walmart': self.scrape_walmart_api(products),
            'target': self.scrape_target_api(products),
            'costco': self.scrape_costco_api(products),
            'sams': self.scrape_sams_api(products),
            'safeway': self.scrape_safeway_api(products),
            'timestamp': datetime.now().isoformat(),
            'success_rate': '0%'
        }
        
        # Calcular tasa de éxito
        total_attempts = len(products) * 5  # 5 tiendas
        successful = sum(1 for store in results if isinstance(results[store], dict) 
                        for product in results[store] if results[store][product] is not None)
        
        success_rate = (successful / total_attempts) * 100 if total_attempts > 0 else 0
        results['success_rate'] = f"{success_rate:.1f}%"
        
        logger.info(f"Scraping complete - Success rate: {success_rate:.1f}%")
        return results


if __name__ == "__main__":
    # Productos de tu lista
    products = [
        'Tomates',
        'Cebollas Blancas',
        'Cebolla Morada',
        'Pepino',
        'Limones Verdes',
        'Chiles Jalapeños',
        'Chiles Serranos',
        'Salsa Tomate',
        'Tostadas',
        'Huevos',
        'Leche',
        'Leche de Coco',
        'Sweet Potato'
    ]
    
    scraper = AdvancedPriceScraper()
    prices = scraper.scrape_all(products)
    
    # Pretty print
    import json
    print(json.dumps(prices, indent=2))
