"""
Web Scraper para Walmart, Safeway, Target, Costco y Sam's Club
Extrae precios de productos en Colorado (Lone Tree, Highland Ranch)
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, List, Tuple
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.prices = {}
        
    def scrape_walmart(self, products: List[str]) -> Dict:
        """Scrape Walmart.com para precios"""
        logger.info("Scraping Walmart...")
        walmart_prices = {}
        
        try:
            for product in products:
                # Walmart search
                url = f"https://www.walmart.com/search?q={product.replace(' ', '+')}"
                
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Buscar precio con selectores más robustos
                    price_elem = soup.find('span', {'data-testid': 'product-price'})
                    
                    if not price_elem:
                        # Intenta otro selector
                        price_span = soup.find('div', {'class': 'price-module'})
                        if price_span:
                            price_elem = price_span.find('span')
                    
                    if price_elem:
                        price_text = price_elem.text.strip().replace('$', '').replace(',', '')
                        try:
                            # Tomar solo el primer número
                            price = float(price_text.split('-')[0].split()[0].strip())
                            walmart_prices[product] = round(price, 2)
                            logger.info(f"Walmart {product}: ${price}")
                        except (ValueError, IndexError):
                            logger.warning(f"No se pudo parsear precio de Walmart para {product}")
                            walmart_prices[product] = None
                    else:
                        # Si no encuentra precio, poner None
                        walmart_prices[product] = None
                        logger.warning(f"No se encontró precio en Walmart para {product}")
                        
                except requests.Timeout:
                    logger.warning(f"Timeout en Walmart para {product}")
                    walmart_prices[product] = None
                
        except Exception as e:
            logger.error(f"Error scraping Walmart: {e}")
            
        return walmart_prices
    
    def scrape_safeway(self, products: List[str]) -> Dict:
        """Scrape Safeway.com para precios"""
        logger.info("Scraping Safeway...")
        safeway_prices = {}
        
        try:
            for product in products:
                # Safeway search
                url = f"https://www.safeway.com/shop/search-results.html?q={product.replace(' ', '+')}"
                
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Buscar precio
                    price_elem = soup.find('span', {'data-testid': 'product-price'})
                    
                    if not price_elem:
                        price_elem = soup.find('div', {'class': 'product-price'})
                    
                    if price_elem:
                        price_text = price_elem.text.strip().replace('$', '').replace(',', '')
                        try:
                            price = float(price_text.split('-')[0].split()[0].strip())
                            safeway_prices[product] = round(price, 2)
                            logger.info(f"Safeway {product}: ${price}")
                        except (ValueError, IndexError):
                            safeway_prices[product] = None
                    else:
                        safeway_prices[product] = None
                        logger.warning(f"No se encontró precio en Safeway para {product}")
                        
                except requests.Timeout:
                    logger.warning(f"Timeout en Safeway para {product}")
                    safeway_prices[product] = None
                
        except Exception as e:
            logger.error(f"Error scraping Safeway: {e}")
            
        return safeway_prices
    
    def scrape_target(self, products: List[str]) -> Dict:
        """Scrape Target.com para precios"""
        logger.info("Scraping Target...")
        target_prices = {}
        
        try:
            for product in products:
                # Target search
                url = f"https://www.target.com/s?searchTerm={product.replace(' ', '+')}"
                
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Buscar precio
                    price_elem = soup.find('span', {'data-testid': 'product-price'})
                    
                    if not price_elem:
                        price_elem = soup.find('span', {'class': 'Text-sc'})
                    
                    if price_elem:
                        price_text = price_elem.text.strip().replace('$', '').replace(',', '')
                        try:
                            price = float(price_text.split('-')[0].split()[0].strip())
                            target_prices[product] = round(price, 2)
                            logger.info(f"Target {product}: ${price}")
                        except (ValueError, IndexError):
                            target_prices[product] = None
                    else:
                        target_prices[product] = None
                        logger.warning(f"No se encontró precio en Target para {product}")
                        
                except requests.Timeout:
                    logger.warning(f"Timeout en Target para {product}")
                    target_prices[product] = None
                
        except Exception as e:
            logger.error(f"Error scraping Target: {e}")
            
        return target_prices
    
    def scrape_costco(self, products: List[str]) -> Dict:
        """Scrape Costco.com para precios"""
        logger.info("Scraping Costco...")
        costco_prices = {}
        
        try:
            for product in products:
                # Costco search
                url = f"https://www.costco.com/CatalogSearch?dept=All&keyword={product.replace(' ', '+')}"
                
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Buscar precio
                    price_elem = soup.find('span', {'data-testid': 'product-price'})
                    
                    if not price_elem:
                        price_elem = soup.find('div', {'class': 'price'})
                    
                    if price_elem:
                        price_text = price_elem.text.strip().replace('$', '').replace(',', '')
                        try:
                            price = float(price_text.split('-')[0].split()[0].strip())
                            costco_prices[product] = round(price, 2)
                            logger.info(f"Costco {product}: ${price}")
                        except (ValueError, IndexError):
                            costco_prices[product] = None
                    else:
                        costco_prices[product] = None
                        logger.warning(f"No se encontró precio en Costco para {product}")
                        
                except requests.Timeout:
                    logger.warning(f"Timeout en Costco para {product}")
                    costco_prices[product] = None
                
        except Exception as e:
            logger.error(f"Error scraping Costco: {e}")
            
        return costco_prices
    
    def scrape_sams(self, products: List[str]) -> Dict:
        """Scrape SamsClub.com para precios"""
        logger.info("Scraping Sam's Club...")
        sams_prices = {}
        
        try:
            for product in products:
                # Sam's Club search
                url = f"https://www.samsclub.com/search/{product.replace(' ', '+')}"
                
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Buscar precio
                    price_elem = soup.find('span', {'data-testid': 'product-price'})
                    
                    if not price_elem:
                        price_elem = soup.find('span', {'class': 'price'})
                    
                    if price_elem:
                        price_text = price_elem.text.strip().replace('$', '').replace(',', '')
                        try:
                            price = float(price_text.split('-')[0].split()[0].strip())
                            sams_prices[product] = round(price, 2)
                            logger.info(f"Sam's Club {product}: ${price}")
                        except (ValueError, IndexError):
                            sams_prices[product] = None
                    else:
                        sams_prices[product] = None
                        logger.warning(f"No se encontró precio en Sam's Club para {product}")
                        
                except requests.Timeout:
                    logger.warning(f"Timeout en Sam's Club para {product}")
                    sams_prices[product] = None
                
        except Exception as e:
            logger.error(f"Error scraping Sam's Club: {e}")
            
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
    
    scraper = PriceScraper()
    prices = scraper.scrape_all(products)
    
    # Convertir a pandas para visualizar
    df = pd.DataFrame(prices)
    print(df)