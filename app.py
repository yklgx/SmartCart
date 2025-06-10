# SmartCart - Simple Complete Flask Application
# University of Piraeus - Python Project 2024-2025

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartcart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

db = SQLAlchemy(app)

# DATABASE MODELS
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref='products')

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_purchased = db.Column(db.Boolean, default=False)
    purchased_at = db.Column(db.DateTime)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product = db.relationship('Product')

# API ENDPOINTS
@app.route('/api/products')
def get_products():
    search = request.args.get('search', '')
    category_id = request.args.get('category_id', type=int)
    sort_by = request.args.get('sort_by', 'name')
    
    query = Product.query
    
    if search:
        query = query.filter(Product.name.contains(search))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if sort_by == 'price':
        query = query.order_by(Product.price)
    else:
        query = query.order_by(Product.name)
    
    products = query.all()
    result = []
    for product in products:
        result.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'category': product.category.name
        })
    return jsonify(result)

@app.route('/api/categories')
def get_categories():
    categories = Category.query.all()
    result = []
    for category in categories:
        result.append({'id': category.id, 'name': category.name})
    return jsonify(result)

@app.route('/api/cart', methods=['POST'])
def create_cart():
    cart = Cart()
    db.session.add(cart)
    db.session.commit()
    return jsonify({'id': cart.id, 'message': 'Cart created'})

@app.route('/api/cart/<int:cart_id>')
def get_cart(cart_id):
    cart = Cart.query.get_or_404(cart_id)
    items = CartItem.query.filter_by(cart_id=cart_id).all()
    
    cart_items = []
    total = 0
    for item in items:
        item_total = item.product.price * item.quantity
        total += item_total
        cart_items.append({
            'id': item.id,
            'product_name': item.product.name,
            'price': item.product.price,
            'quantity': item.quantity,
            'total': item_total
        })
    
    return jsonify({
        'id': cart.id,
        'items': cart_items,
        'total': total,
        'is_purchased': cart.is_purchased
    })

@app.route('/api/cart/<int:cart_id>/add', methods=['POST'])
def add_to_cart(cart_id):
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    cart = Cart.query.get_or_404(cart_id)
    if cart.is_purchased:
        return jsonify({'error': 'Cannot modify purchased cart'}), 400
    
    existing_item = CartItem.query.filter_by(cart_id=cart_id, product_id=product_id).first()
    
    if existing_item:
        existing_item.quantity += quantity
    else:
        cart_item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    return jsonify({'message': 'Item added'})

@app.route('/api/cart/<int:cart_id>/remove/<int:item_id>', methods=['DELETE'])
def remove_from_cart(cart_id, item_id):
    cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart_id).first_or_404()
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'message': 'Item removed'})

@app.route('/api/cart/<int:cart_id>/purchase', methods=['POST'])
def purchase_cart(cart_id):
    cart = Cart.query.get_or_404(cart_id)
    cart.is_purchased = True
    cart.purchased_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Cart purchased'})

@app.route('/api/purchases')
def get_purchases():
    purchased_carts = Cart.query.filter_by(is_purchased=True).order_by(Cart.purchased_at.desc()).all()
    result = []
    for cart in purchased_carts:
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        items = []
        total = 0
        for item in cart_items:
            item_total = item.product.price * item.quantity
            total += item_total
            items.append({
                'product_name': item.product.name,
                'quantity': item.quantity,
                'price': item.product.price,
                'total': item_total
            })
        
        result.append({
            'id': cart.id,
            'purchased_at': cart.purchased_at.strftime('%Y-%m-%d %H:%M:%S'),
            'items': items,
            'total': total
        })
    
    return jsonify(result)

# DATA ANALYSIS SUBSYSTEM
@app.route('/api/stats')
def get_stats():
    total_purchases = Cart.query.filter_by(is_purchased=True).count()
    
    if total_purchases == 0:
        return jsonify({
            'total_purchases': 0,
            'total_spent': 0,
            'average_per_purchase': 0,
            'most_popular_products': []
        })
    
    total_spent = 0
    product_counts = {}
    
    purchased_carts = Cart.query.filter_by(is_purchased=True).all()
    
    for cart in purchased_carts:
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        for item in cart_items:
            total_spent += item.product.price * item.quantity
            product_name = item.product.name
            product_counts[product_name] = product_counts.get(product_name, 0) + item.quantity
    
    most_popular = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return jsonify({
        'total_purchases': total_purchases,
        'total_spent': round(total_spent, 2),
        'average_per_purchase': round(total_spent / total_purchases, 2),
        'most_popular_products': [{'name': name, 'count': count} for name, count in most_popular]
    })

@app.route('/api/recommend-cart')
def recommend_cart():
    product_counts = {}
    purchased_carts = Cart.query.filter_by(is_purchased=True).all()
    
    for cart in purchased_carts:
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        for item in cart_items:
            product_id = item.product_id
            product_counts[product_id] = product_counts.get(product_id, 0) + item.quantity
    
    most_popular_ids = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    recommendations = []
    for product_id, count in most_popular_ids:
        product = Product.query.get(product_id)
        if product:
            recommendations.append({
                'product_id': product.id,
                'name': product.name,
                'price': product.price,
                'suggested_quantity': 1
            })
    
    return jsonify({
        'message': 'Recommended cart based on purchase history',
        'recommendations': recommendations
    })

@app.route('/api/frequently-bought-together/<int:product_id>')
def frequently_bought_together(product_id):
    target_product = Product.query.get_or_404(product_id)
    
    cart_items_with_product = CartItem.query.filter_by(product_id=product_id).all()
    cart_ids = [item.cart_id for item in cart_items_with_product]
    
    other_product_counts = {}
    for cart_id in cart_ids:
        other_items = CartItem.query.filter(
            CartItem.cart_id == cart_id,
            CartItem.product_id != product_id
        ).all()
        
        for item in other_items:
            other_product_counts[item.product_id] = other_product_counts.get(item.product_id, 0) + 1
    
    frequent_products = sorted(other_product_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    recommendations = []
    for prod_id, count in frequent_products:
        product = Product.query.get(prod_id)
        if product:
            recommendations.append({
                'product_id': product.id,
                'name': product.name,
                'price': product.price,
                'frequency': count
            })
    
    return jsonify({
        'product': target_product.name,
        'frequently_bought_together': recommendations
    })

# WEB SCRAPING SUBSYSTEM (Demo)
@app.route('/api/compare-price/<int:product_id>')
def compare_price(product_id):
    product = Product.query.get_or_404(product_id)
    
    our_price = product.price
    competitor1_price = round(our_price * random.uniform(0.8, 1.2), 2)
    competitor2_price = round(our_price * random.uniform(0.8, 1.2), 2)
    
    return jsonify({
        'product_name': product.name,
        'our_price': our_price,
        'competitors': [
            {'store': 'Store A', 'price': competitor1_price},
            {'store': 'Store B', 'price': competitor2_price}
        ],
        'best_price': min(our_price, competitor1_price, competitor2_price),
        'note': 'Demo price comparison data'
    })

# AI SUBSYSTEM (Demo)
@app.route('/api/recipe-suggestion', methods=['POST'])
def recipe_suggestion():
    data = request.get_json()
    products = data.get('products', [])
    
    recipes = {
        'chicken': 'Grilled Chicken: Season chicken and grill with herbs.',
        'fish': 'Pan-fried Fish: Cook fish with lemon and butter.',
        'tomatoes': 'Fresh Salad: Mix tomatoes with olive oil.',
        'milk': 'Smoothie: Blend milk with fruits.',
        'cheese': 'Cheese Sandwich: Make sandwich with fresh bread.'
    }
    
    suggested_recipe = 'Mixed Salad: Combine your ingredients for a healthy meal.'
    
    for product in products:
        for ingredient, recipe in recipes.items():
            if ingredient.lower() in product.lower():
                suggested_recipe = recipe
                break
    
    return jsonify({
        'products': products,
        'recipe_suggestion': suggested_recipe,
        'note': 'Simple recipe suggestions'
    })

@app.route('/api/nutrition-analysis', methods=['POST'])
def nutrition_analysis():
    data = request.get_json()
    cart_id = data.get('cart_id')
    
    cart = Cart.query.get_or_404(cart_id)
    cart_items = CartItem.query.filter_by(cart_id=cart_id).all()
    
    categories = {}
    for item in cart_items:
        category = item.product.category.name
        categories[category] = categories.get(category, 0) + item.quantity
    
    analysis = "Nutritional analysis: "
    
    if 'Fruits' in categories and 'Vegetables' in categories:
        analysis += "Good variety of fruits and vegetables. "
    
    if 'Dairy' in categories:
        analysis += "Good calcium intake. "
    
    if categories.get('Meat', 0) > 3:
        analysis += "Consider reducing meat consumption. "
    
    analysis += "Try to maintain a balanced diet."
    
    return jsonify({
        'cart_id': cart_id,
        'categories': categories,
        'nutrition_analysis': analysis,
        'note': 'Simple nutrition analysis'
    })

# INITIALIZE DATABASE
def init_database():
    with app.app_context():
        db.create_all()
        
        if Category.query.first():
            return
        
        # Add categories
        categories = [
            Category(name='Dairy'),
            Category(name='Fruits'),
            Category(name='Vegetables'),
            Category(name='Meat'),
            Category(name='Fish'),
            Category(name='Bakery'),
            Category(name='Beverages'),
            Category(name='Snacks')
        ]
        
        for category in categories:
            db.session.add(category)
        db.session.commit()
        
        # Add products
        products = [
            # Dairy
            Product(name='Fresh Milk 1L', description='Fresh cow milk', price=1.50, category_id=1),
            Product(name='Greek Yogurt', description='Traditional yogurt', price=2.80, category_id=1),
            Product(name='Feta Cheese', description='Greek feta cheese', price=4.50, category_id=1),
            Product(name='Butter', description='Fresh butter', price=3.20, category_id=1),
            
            # Fruits
            Product(name='Red Apples', description='Fresh red apples', price=2.90, category_id=2),
            Product(name='Bananas', description='Fresh bananas', price=1.80, category_id=2),
            Product(name='Oranges', description='Fresh oranges', price=1.60, category_id=2),
            Product(name='Strawberries', description='Sweet strawberries', price=4.20, category_id=2),
            
            # Vegetables
            Product(name='Tomatoes', description='Fresh tomatoes', price=2.40, category_id=3),
            Product(name='Cucumbers', description='Fresh cucumbers', price=1.90, category_id=3),
            Product(name='Onions', description='Yellow onions', price=1.20, category_id=3),
            Product(name='Potatoes', description='Fresh potatoes', price=1.80, category_id=3),
            
            # Meat
            Product(name='Chicken Breast', description='Fresh chicken breast', price=8.90, category_id=4),
            Product(name='Beef Steak', description='Premium beef steak', price=12.50, category_id=4),
            Product(name='Pork Chops', description='Fresh pork chops', price=9.80, category_id=4),
            
            # Fish
            Product(name='Fresh Salmon', description='Atlantic salmon', price=15.60, category_id=5),
            Product(name='Sea Bass', description='Fresh sea bass', price=11.90, category_id=5),
            Product(name='Cod Fish', description='Fresh cod', price=13.40, category_id=5),
            
            # Bakery
            Product(name='White Bread', description='Fresh white bread', price=1.20, category_id=6),
            Product(name='Croissants', description='Butter croissants', price=0.80, category_id=6),
            Product(name='Baguette', description='French baguette', price=1.50, category_id=6),
            
            # Beverages
            Product(name='Water 1.5L', description='Bottled water', price=0.60, category_id=7),
            Product(name='Orange Juice', description='Fresh orange juice', price=2.30, category_id=7),
            Product(name='Coffee', description='Ground coffee', price=4.50, category_id=7),
            
            # Snacks
            Product(name='Potato Chips', description='Crispy chips', price=1.80, category_id=8),
            Product(name='Chocolate Bar', description='Milk chocolate', price=2.50, category_id=8),
            Product(name='Cookies', description='Butter cookies', price=1.90, category_id=8)
        ]
        
        for product in products:
            db.session.add(product)
        db.session.commit()
        
        # Add sample purchase history (15-20 purchases)
        for i in range(18):
            cart = Cart(
                created_at=datetime.now() - timedelta(days=random.randint(1, 90)),
                is_purchased=True,
                purchased_at=datetime.now() - timedelta(days=random.randint(1, 90))
            )
            db.session.add(cart)
            db.session.commit()
            
            # Add 2-5 random items to each cart
            num_items = random.randint(2, 5)
            selected_products = random.sample(range(1, 26), num_items)
            
            for product_id in selected_products:
                cart_item = CartItem(
                    cart_id=cart.id,
                    product_id=product_id,
                    quantity=random.randint(1, 3)
                )
                db.session.add(cart_item)
        
        db.session.commit()
        print("Database initialized with sample data")

if __name__ == '__main__':
    init_database()
    print("SmartCart Backend Starting...")
    print("API running on: http://localhost:5000")
    app.run(debug=True)