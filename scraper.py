"""
Web Scraper para Walmart, Safeway, Target, Costco y Sam's Club
Extrae precios de productos en Colorado basado en estructura HTML real
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.timeout = 15
        
    def scrape_walmart(self, products: List[str]) -> Dict:
        """Scrape Walmart.com para precios"""
        logger.info("Scraping Walmart...")
        walmart_prices = {}
        
        for product in products:
            try:
                url = f"https://www.walmart.com/search?q={product.replace(' ', '+')}"
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar en h3 tags: "Price $ 0.49 Was $ 0.89"
                h3_tags = soup.find_all('h3')
                price = None
                
                for h3 in h3_tags:
                    text = h3.get_text()
                    match = re.search(r'Price\s*\$\s*([\d.]+)', text)
                    if match:
                        price = float(match.group(1))
                        break
                
                if price:
                    walmart_prices[product] = round(price, 2)
                    logger.info(f"Walmart {product}: ${price}")
                else:
                    walmart_prices[product] = None
                    logger.warning(f"No se encontró precio en Walmart para {product}")
                    
            except Exception as e:
                logger.warning(f"Error en Walmart {product}: {e}")
                walmart_prices[product] = None
        
        return walmart_prices
    
    def scrape_safeway(self, products: List[str]) -> Dict:
        """Scrape Safeway.com para precios"""
        logger.info("Scraping Safeway...")
        safeway_prices = {}
        
        for product in products:
            try:
                url = f"https://www.safeway.com/shop/search-results.html?q={product.replace(' ', '+')}"
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar en aria-label: "price approximatly $X.XX each"
                links = soup.find_all('a')
                price = None
                
                for link in links:
                    aria_label = link.get('aria-label', '')
                    match = re.search(r'price\s+approximatly?\s*\$\s*([\d.]+)', aria_label, re.IGNORECASE)
                    if match:
                        price = float(match.group(1))
                        break
                
                if price:
                    safeway_prices[product] = round(price, 2)
                    logger.info(f"Safeway {product}: ${price}")
                else:
                    safeway_prices[product] = None
                    logger.warning(f"No se encontró precio en Safeway para {product}")
                    
            except Exception as e:
                logger.warning(f"Error en Safeway {product}: {e}")
                safeway_prices[product] = None
        
        return safeway_prices
    
    def scrape_target(self, products: List[str]) -> Dict:
        """Scrape Target.com para precios"""
        logger.info("Scraping Target...")
        target_prices = {}
        
        for product in products:
            try:
                url = f"https://www.target.com/s?searchTerm={product.replace(' ', '+')}"
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Target tiene estructura compleja, buscar en spans con precio
                spans = soup.find_all('span')
                price = None
                
                for span in spans:
                    text = span.get_text().strip()
                    match = re.search(r'^\$\s*([\d.]+)', text)
                    if match:
                        price = float(match.group(1))
                        break
                
                if price:
                    target_prices[product] = round(price, 2)
                    logger.info(f"Target {product}: ${price}")
                else:
                    target_prices[product] = None
                    logger.warning(f"No se encontró precio en Target para {product}")
                    
            except Exception as e:
                logger.warning(f"Error en Target {product}: {e}")
                target_prices[product] = None
        
        return target_prices
    
    def scrape_costco(self, products: List[str]) -> Dict:
        """Scrape Costco.com para precios"""
        logger.info("Scraping Costco...")
        costco_prices = {}
        
        for product in products:
            try:
                url = f"https://www.costco.com/CatalogSearch?dept=All&keyword={product.replace(' ', '+')}"
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Costco: buscar en spans con "$X.XX"
                spans = soup.find_all('span')
                price = None
                
                for span in spans:
                    text = span.get_text().strip()
                    # Patrón: "$4.49"
                    match = re.search(r'^\$\s*([\d.]+)', text)
                    if match:
                        price = float(match.group(1))
                        # Validar que sea un precio razonable (entre $0.50 y $50)
                        if 0.50 < price < 50:
                            break
                
                if price:
                    costco_prices[product] = round(price, 2)
                    logger.info(f"Costco {product}: ${price}")
                else:
                    costco_prices[product] = None
                    logger.warning(f"No se encontró precio en Costco para {product}")
                    
            except Exception as e:
                logger.warning(f"Error en Costco {product}: {e}")
                costco_prices[product] = None
        
        return costco_prices
    
    def scrape_sams(self, products: List[str]) -> Dict:
        """Scrape SamsClub.com para precios"""
        logger.info("Scraping Sam's Club...")
        sams_prices = {}
        
        for product in products:
            try:
                url = f"https://www.samsclub.com/search/{product.replace(' ', '+')}"
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Sam's: buscar en h3 tags: "Envy Apples, 4 lbs. $6.17"
                h3_tags = soup.find_all('h3')
                price = None
                
                for h3 in h3_tags:
                    text = h3.get_text()
                    match = re.search(r'\$\s*([\d.]+)', text)
                    if match:
                        price = float(match.group(1))
                        break
                
                if price:
                    sams_prices[product] = round(price, 2)
                    logger.info(f"Sam's Club {product}: ${price}")
                else:
                    sams_prices[product] = None
                    logger.warning(f"No se encontró precio en Sam's Club para {product}")
                    
            except Exception as e:
                logger.warning(f"Error en Sam's Club {product}: {e}")
                sams_prices[product] = None
        
        return sams_prices
    
    def scrape_all(self, products: List[str]) -> Dict:
        """Scrape todos los supermercados"""
        logger.info(f"Iniciando scraping para {len(products)} productos...")
        
        results = {
            'walmart': self.scrape_walmart(products),
            'safeway': self.scrape_safeway(products),
            'target': self.scrape_target(products),
            'costco': self.scrape_costco(products),
            'sams': self.scrape_sams(products),
            'timestamp': datetime.now().isoformat()
        }
        
        return results


if __name__ == "__main__":
    # Productos de ejemplo
    products = [
        'Manzanas',
        'Leche',
        'Pan',
        'Arroz',
        'Naranjas'
    ]
    
    scraper = PriceScraper()
    prices = scraper.scrape_all(products)
    
    # Mostrar resultados
    import json
    print(json.dumps(prices, indent=2))
