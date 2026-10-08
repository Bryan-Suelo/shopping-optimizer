"""
Shopping Optimizer API
Flask app para comparar precios entre supermercados
Deployable en Render.com
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timedelta
import os
import time
import logging
from dotenv import load_dotenv
import schedule
import threading
from scraper import PriceScraper

load_dotenv()

# Configuración logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Inicializar Flask app
app = Flask(__name__)
CORS(app)

# Configuración base de datos
database_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/shopping_db')
# Fix para SQLAlchemy 2.0+
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app, model_class=Base)

# ==================== MODELOS ====================

class ShoppingItem(db.Model):
    """Modelo para items en la lista de compras"""
    __tablename__ = 'shopping_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    quantity = db.Column(db.Float, default=1)
    unit = db.Column(db.String(50), default='unidad')  # kg, lb, litro, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con precios
    prices = db.relationship('ProductPrice', backref='item', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'quantity': self.quantity,
            'unit': self.unit,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ProductPrice(db.Model):
    """Modelo para precios por supermercado"""
    __tablename__ = 'product_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('shopping_items.id'), nullable=False)
    store = db.Column(db.String(50), nullable=False)  # walmart, safeway, target, costco, sams
    price = db.Column(db.Float)  # Precio por unidad
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índice compuesto para búsquedas rápidas
    __table_args__ = (db.UniqueConstraint('item_id', 'store', name='unique_item_store'),)
    
    def to_dict(self):
        return {
            'store': self.store,
            'price': self.price,
            'last_updated': self.last_updated.isoformat()
        }


# ==================== RUTAS API ====================

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})


@app.route('/api/items', methods=['GET'])
def get_items():
    """Obtener lista de compras completa con precios"""
    try:
        items = ShoppingItem.query.all()
        result = []
        
        for item in items:
            item_data = item.to_dict()
            item_data['prices'] = {
                price.store: price.to_dict() for price in item.prices
            }
            result.append(item_data)
        
        return jsonify({
            'success': True,
            'items': result,
            'count': len(result)
        })
    except Exception as e:
        logger.error(f"Error getting items: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/items', methods=['POST'])
def add_item():
    """Agregar nuevo item a la lista"""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        
        # Verificar si el item ya existe
        existing = ShoppingItem.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'Item already exists',
                'item': existing.to_dict()
            }), 409
        
        # Crear nuevo item
        item = ShoppingItem(
            name=data['name'],
            quantity=data.get('quantity', 1),
            unit=data.get('unit', 'unidad')
        )
        
        db.session.add(item)
        db.session.commit()
        
        logger.info(f"Item added: {item.name}")
        return jsonify({
            'success': True,
            'message': f'Item "{item.name}" added successfully',
            'item': item.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding item: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Eliminar item de la lista"""
    try:
        item = ShoppingItem.query.get(item_id)
        
        if not item:
            return jsonify({'success': False, 'error': 'Item not found'}), 404
        
        db.session.delete(item)
        db.session.commit()
        
        logger.info(f"Item deleted: {item.name}")
        return jsonify({
            'success': True,
            'message': f'Item "{item.name}" deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting item: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/prices/<item_name>', methods=['GET'])
def get_prices(item_name):
    """Obtener precios para un producto específico"""
    try:
        item = ShoppingItem.query.filter_by(name=item_name).first()
        
        if not item:
            return jsonify({'success': False, 'error': 'Item not found'}), 404
        
        prices = {
            price.store: price.to_dict() for price in item.prices
        }
        
        # Calcular mejor opción
        best_store = None
        best_price = float('inf')
        
        for store, price_data in prices.items():
            if price_data['price'] and price_data['price'] < best_price:
                best_price = price_data['price']
                best_store = store
        
        return jsonify({
            'success': True,
            'item': item.to_dict(),
            'prices': prices,
            'best_option': {
                'store': best_store,
                'price': best_price if best_store else None,
                'total': best_price * item.quantity if best_store else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting prices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/prices', methods=['POST'])
def update_prices():
    """Actualizar precios desde scraping"""
    try:
        data = request.get_json()
        
        if not data or 'prices' not in data:
            return jsonify({'success': False, 'error': 'Prices data required'}), 400
        
        prices_data = data['prices']  # Dict format: {store: {item_name: price}}
        updated_count = 0
        
        for store, items in prices_data.items():
            for item_name, price in items.items():
                if price is None:
                    continue
                
                # Obtener o crear item
                item = ShoppingItem.query.filter_by(name=item_name).first()
                if not item:
                    item = ShoppingItem(name=item_name)
                    db.session.add(item)
                    db.session.flush()
                
                # Obtener o crear precio
                prod_price = ProductPrice.query.filter_by(
                    item_id=item.id,
                    store=store
                ).first()
                
                if not prod_price:
                    prod_price = ProductPrice(item_id=item.id, store=store)
                    db.session.add(prod_price)
                
                prod_price.price = float(price)
                prod_price.last_updated = datetime.utcnow()
                updated_count += 1
        
        db.session.commit()
        logger.info(f"Updated {updated_count} prices")
        
        return jsonify({
            'success': True,
            'message': f'{updated_count} prices updated',
            'updated_count': updated_count
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating prices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/comparison', methods=['GET'])
def get_comparison():
    """Obtener comparación de precios totales por supermercado"""
    try:
        items = ShoppingItem.query.all()
        
        stores = ['walmart', 'safeway', 'target', 'costco', 'sams']
        totals = {store: 0.0 for store in stores}
        item_count = {store: 0 for store in stores}
        
        for item in items:
            for price in item.prices:
                if price.price:
                    total_price = price.price * item.quantity
                    totals[price.store] += total_price
                    item_count[price.store] += 1
        
        # Encontrar mejor opción
        best_store = min(totals, key=totals.get)
        max_total = max(totals.values())
        min_total = min([t for t in totals.values() if t > 0], default=0)
        
        return jsonify({
            'success': True,
            'totals': totals,
            'item_counts': item_count,
            'best_option': best_store,
            'best_price': min_total,
            'worst_price': max_total,
            'potential_savings': max_total - min_total if max_total > 0 else 0
        })
        
    except Exception as e:
        logger.error(f"Error getting comparison: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/comparison-by-product', methods=['GET'])
def get_comparison_by_product():
    """Obtener comparación de precios POR PRODUCTO (tabla)"""
    try:
        items = ShoppingItem.query.all()
        stores = ['walmart', 'safeway', 'target', 'costco', 'sams']
        
        result = []
        
        for item in items:
            row = {
                'product': item.name,
                'quantity': item.quantity,
                'unit': item.unit,
                'prices': {}
            }
            
            # Obtener precio de cada supermercado
            for store in stores:
                price_obj = ProductPrice.query.filter_by(
                    item_id=item.id,
                    store=store
                ).first()
                
                if price_obj and price_obj.price:
                    # Calcular precio total para esta cantidad
                    total = price_obj.price * item.quantity
                    row['prices'][store] = {
                        'unit_price': price_obj.price,
                        'total': round(total, 2),
                        'last_updated': price_obj.last_updated.isoformat() if price_obj.last_updated else None
                    }
                else:
                    row['prices'][store] = None
            
            # Encontrar mejor opción
            valid_prices = {store: data['total'] for store, data in row['prices'].items() if data}
            
            if valid_prices:
                best_store = min(valid_prices, key=valid_prices.get)
                row['best_option'] = {
                    'store': best_store,
                    'price': valid_prices[best_store]
                }
            else:
                row['best_option'] = None
            
            result.append(row)
        
        return jsonify({
            'success': True,
            'comparison_table': result,
            'stores': stores,
            'products_count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting comparison by product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/test-scraper', methods=['POST'])
def test_scraper():
    """Ejecutar scraper bajo demanda (para testing)"""
    try:
        logger.info("Manual scraper test triggered")
        
        # Obtener todos los items
        items = ShoppingItem.query.all()
        product_names = [item.name for item in items]
        
        if not product_names:
            return jsonify({
                'success': False,
                'error': 'No products to scrape',
                'products_count': 0
            }), 400
        
        # Ejecutar scraper
        scraper = PriceScraper()
        prices = scraper.scrape_all(product_names)
        
        # Guardar en BD
        updated_count = 0
        for store in ['walmart', 'safeway', 'target', 'costco', 'sams']:
            store_prices = prices.get(store, {})
            
            for product_name, price in store_prices.items():
                if price is None:
                    continue
                
                item = ShoppingItem.query.filter_by(name=product_name).first()
                if not item:
                    item = ShoppingItem(name=product_name)
                    db.session.add(item)
                    db.session.flush()
                
                prod_price = ProductPrice.query.filter_by(
                    item_id=item.id,
                    store=store
                ).first()
                
                if not prod_price:
                    prod_price = ProductPrice(item_id=item.id, store=store)
                    db.session.add(prod_price)
                
                prod_price.price = float(price)
                prod_price.last_updated = datetime.utcnow()
                updated_count += 1
        
        db.session.commit()
        logger.info(f"Test scraper completed: {updated_count} prices updated")
        
        return jsonify({
            'success': True,
            'message': f'Scraper test completed',
            'products_scraped': len(product_names),
            'prices_updated': updated_count,
            'timestamp': datetime.utcnow().isoformat(),
            'prices': prices
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in test scraper: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== SCRAPING AUTOMÁTICO ====================

def run_scraper():
    """Ejecutar scraper automático"""
    logger.info("Starting scheduled scraper...")
    try:
        # Obtener todos los items de la BD
        items = ShoppingItem.query.all()
        product_names = [item.name for item in items]
        
        if not product_names:
            logger.warning("No products to scrape")
            return
        
        # Ejecutar scraper
        scraper = PriceScraper()
        prices = scraper.scrape_all(product_names)
        
        # Guardar en BD
        for store in ['walmart', 'safeway', 'target', 'costco', 'sams']:
            store_prices = prices.get(store, {})
            
            for product_name, price in store_prices.items():
                if price is None:
                    continue
                
                item = ShoppingItem.query.filter_by(name=product_name).first()
                if not item:
                    item = ShoppingItem(name=product_name)
                    db.session.add(item)
                    db.session.flush()
                
                prod_price = ProductPrice.query.filter_by(
                    item_id=item.id,
                    store=store
                ).first()
                
                if not prod_price:
                    prod_price = ProductPrice(item_id=item.id, store=store)
                    db.session.add(prod_price)
                
                prod_price.price = float(price)
                prod_price.last_updated = datetime.utcnow()
        
        db.session.commit()
        logger.info("Scraper completed successfully")
        
    except Exception as e:
        logger.error(f"Error in scraper: {e}")
        db.session.rollback()


def schedule_scraper():
    """Configurar scraper automático en horario de Colorado."""

    timezone = "America/Denver"

    # 6:00 AM Colorado
    schedule.every().day.at("06:00", timezone).do(run_scraper)

    # 3:00 PM Colorado
    schedule.every().day.at("15:00", timezone).do(run_scraper)

    # 10:00 PM Colorado
    schedule.every().day.at("22:00", timezone).do(run_scraper)

    def scheduler_thread():
        while True:
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(daemon=True, target=scheduler_thread)
    thread.start()

    logger.info(
        "Scheduler started - Running daily at 6:00 AM, 3:00 PM, and 10:00 PM Colorado time"
    )


# ==================== INICIALIZACIÓN ====================

@app.before_request
def create_tables():
    """Crear tablas si no existen"""
    if not hasattr(app, 'db_created'):
        with app.app_context():
            db.create_all()
            app.db_created = True
            logger.info("Database tables created")


if __name__ == '__main__':    
    # Crear tablas
    with app.app_context():
        db.create_all()
    
    # Iniciar scheduler
    schedule_scraper()
    
    # Ejecutar app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)