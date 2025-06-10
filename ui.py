import streamlit as st
import requests

# Configure page
st.set_page_config(page_title="SmartCart", layout="wide")

# API base URL
API_BASE = "http://localhost:5000/api"

def check_api():
    try:
        urls_to_try = [
            "http://localhost:5000/api/products",
            "http://127.0.0.1:5000/api/products"
        ]
        
        for url in urls_to_try:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    global API_BASE
                    API_BASE = url.replace('/products', '')
                    return True
            except:
                continue
        return False
    except:
        return False

def get_products(search="", category_id=None, sort_by="name"):
    params = {}
    if search:
        params['search'] = search
    if category_id:
        params['category_id'] = category_id
    if sort_by:
        params['sort_by'] = sort_by
    
    try:
        response = requests.get(f"{API_BASE}/products", params=params)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_categories():
    try:
        response = requests.get(f"{API_BASE}/categories")
        return response.json() if response.status_code == 200 else []
    except:
        return []

def create_cart():
    try:
        response = requests.post(f"{API_BASE}/cart")
        return response.json() if response.status_code == 200 else None
    except:
        return None

def add_to_cart(cart_id, product_id, quantity=1):
    try:
        data = {"product_id": product_id, "quantity": quantity}
        response = requests.post(f"{API_BASE}/cart/{cart_id}/add", json=data)
        return response.status_code == 200
    except:
        return False

def get_cart(cart_id):
    try:
        response = requests.get(f"{API_BASE}/cart/{cart_id}")
        return response.json() if response.status_code == 200 else None
    except:
        return None

def purchase_cart(cart_id):
    try:
        response = requests.post(f"{API_BASE}/cart/{cart_id}/purchase")
        return response.status_code == 200
    except:
        return False

def get_stats():
    try:
        response = requests.get(f"{API_BASE}/stats")
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

def get_purchases():
    try:
        response = requests.get(f"{API_BASE}/purchases")
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_recommended_cart():
    try:
        response = requests.get(f"{API_BASE}/recommend-cart")
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

def get_frequently_bought_together(product_id):
    try:
        response = requests.get(f"{API_BASE}/frequently-bought-together/{product_id}")
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

def compare_prices(product_id):
    try:
        response = requests.get(f"{API_BASE}/compare-price/{product_id}")
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

def get_recipe_suggestion(products):
    try:
        data = {"products": products}
        response = requests.post(f"{API_BASE}/recipe-suggestion", json=data)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

def analyze_nutrition(cart_id):
    try:
        data = {"cart_id": cart_id}
        response = requests.post(f"{API_BASE}/nutrition-analysis", json=data)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

# Main application
def main():
    st.title("SmartCart - Smart Shopping Cart")
    
    # Check API connection
    if not check_api():
        st.error("Cannot connect to Flask API!")
        st.info("Make sure the Flask app is running on http://localhost:5000")
        return
    
    st.success("Successfully connected to API!")
    
    # Initialize session state
    if 'current_cart_id' not in st.session_state:
        st.session_state.current_cart_id = None
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Select page:",
        [
            "Products and Shopping", 
            "Cart Management", 
            "Data Analysis", 
            "Web Scraping", 
            "AI Features"
        ]
    )
    
    if page == "Products and Shopping":
        show_products_page()
    elif page == "Cart Management":
        show_cart_page()
    elif page == "Data Analysis":
        show_analytics_page()
    elif page == "Web Scraping":
        show_scraping_page()
    elif page == "AI Features":
        show_ai_page()

def show_products_page():
    st.header("Product Catalog")
    
    # Cart management
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("New Cart"):
            cart = create_cart()
            if cart:
                st.session_state.current_cart_id = cart['id']
                st.success(f"Created cart #{cart['id']}")
    
    with col2:
        if st.session_state.current_cart_id:
            st.info(f"Current cart: #{st.session_state.current_cart_id}")
    
    # Search and filter
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("Search products:")
    
    with col2:
        categories = get_categories()
        category_options = ["All categories"] + [cat['name'] for cat in categories]
        selected_category = st.selectbox("Category:", category_options)
    
    with col3:
        sort_options = ["name", "price"]
        sort_by = st.selectbox("Sort by:", sort_options)
    
    # Get category ID
    category_id = None
    if selected_category != "All categories":
        for cat in categories:
            if cat['name'] == selected_category:
                category_id = cat['id']
                break
    
    # Get products
    products = get_products(search_term, category_id, sort_by)
    
    if not products:
        st.warning("No products found")
        return
    
    st.subheader(f"Found {len(products)} products")
    
    # Display products
    for product in products:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.write(f"**{product['name']}**")
            st.write(f"{product['description']}")
            st.write(f"Category: {product['category']}")
        
        with col2:
            st.write(f"€{product['price']:.2f}")
        
        with col3:
            qty = st.number_input("Qty", min_value=1, value=1, key=f"qty_{product['id']}")
        
        with col4:
            if st.button("Add", key=f"add_{product['id']}"):
                if st.session_state.current_cart_id:
                    if add_to_cart(st.session_state.current_cart_id, product['id'], qty):
                        st.success("Added!")
                    else:
                        st.error("Error")
                else:
                    st.warning("Create cart first!")
        
        st.markdown("---")

def show_cart_page():
    st.header("Cart Management")
    
    if not st.session_state.current_cart_id:
        st.warning("No active cart. Create one from Products page.")
        
        # Show cart recommendation
        if st.button("Get Recommended Cart"):
            rec_data = get_recommended_cart()
            if rec_data.get('recommendations'):
                st.subheader("Recommended Products:")
                for rec in rec_data['recommendations']:
                    st.write(f"- {rec['name']} - €{rec['price']:.2f}")
        return
    
    cart = get_cart(st.session_state.current_cart_id)
    if not cart:
        st.error("Cart not found")
        return
    
    if cart['is_purchased']:
        st.success("This cart has been purchased!")
        st.session_state.current_cart_id = None
        return
    
    if not cart['items']:
        st.info("Cart is empty")
        return
    
    # Display cart
    st.subheader(f"Cart #{cart['id']}")
    
    total = 0
    for item in cart['items']:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"**{item['product_name']}**")
        with col2:
            st.write(f"€{item['price']:.2f}")
        with col3:
            st.write(f"x{item['quantity']}")
        with col4:
            st.write(f"€{item['total']:.2f}")
        total += item['total']
    
    st.markdown("---")
    st.markdown(f"### Total: €{total:.2f}")
    
    # Purchase button
    if st.button("Complete Purchase", type="primary"):
        if purchase_cart(st.session_state.current_cart_id):
            st.success("Purchase completed!")
            st.balloons()
            st.session_state.current_cart_id = None
        else:
            st.error("Purchase error")

def show_analytics_page():
    st.header("Data Analysis")
    
    stats = get_stats()
    purchases = get_purchases()
    
    if not stats or stats.get('total_purchases', 0) == 0:
        st.warning("No purchase data available")
        return
    
    # Basic stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Purchases", stats['total_purchases'])
    with col2:
        st.metric("Total Spent", f"€{stats['total_spent']:.2f}")
    with col3:
        st.metric("Average per Purchase", f"€{stats['average_per_purchase']:.2f}")
    
    # Most popular products
    if stats.get('most_popular_products'):
        st.subheader("Most Popular Products")
        for product in stats['most_popular_products']:
            st.write(f"- {product['name']}: {product['count']} times")
    
    # Purchase history
    st.subheader("Purchase History")
    
    if purchases:
        for purchase in purchases[:10]:
            with st.expander(f"Purchase #{purchase['id']} - €{purchase['total']:.2f}"):
                st.write(f"Date: {purchase['purchased_at']}")
                st.write(f"Items: {len(purchase['items'])}")
                for item in purchase['items']:
                    st.write(f"  - {item['product_name']}: {item['quantity']}x €{item['price']:.2f}")

def show_scraping_page():
    st.header("Web Scraping - Price Comparison")
    st.info("This demonstrates web scraping with simulated data")
    
    products = get_products()
    if products:
        product_names = [p['name'] for p in products]
        selected_product = st.selectbox("Select product:", product_names)
        
        # Find product ID
        product_id = None
        for p in products:
            if p['name'] == selected_product:
                product_id = p['id']
                break
        
        if st.button("Compare Prices"):
            price_data = compare_prices(product_id)
            if price_data:
                st.subheader(f"Price comparison for: {price_data['product_name']}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Our Price", f"€{price_data['our_price']:.2f}")
                with col2:
                    st.metric("Store A", f"€{price_data['competitors'][0]['price']:.2f}")
                with col3:
                    st.metric("Store B", f"€{price_data['competitors'][1]['price']:.2f}")
                
                st.info(f"Best price: €{price_data['best_price']:.2f}")
                st.write(price_data['note'])
        
        # Frequently bought together
        st.subheader("Frequently Bought Together")
        if st.button("Find Related Products"):
            freq_data = get_frequently_bought_together(product_id)
            if freq_data.get('frequently_bought_together'):
                st.write(f"Products often bought with {freq_data['product']}:")
                for item in freq_data['frequently_bought_together']:
                    st.write(f"- {item['name']} (frequency: {item['frequency']})")
            else:
                st.info("No related products found")

def show_ai_page():
    st.header("AI Features")
    st.info("AI-powered suggestions and analysis")
    
    # Recipe suggestions
    st.subheader("Recipe Suggestions")
    
    products = get_products()
    if products:
        selected_products = st.multiselect(
            "Select products for recipe:",
            [p['name'] for p in products]
        )
        
        if st.button("Get Recipe Suggestion"):
            recipe_data = get_recipe_suggestion(selected_products)
            if recipe_data:
                st.success("Recipe Suggestion:")
                st.write(recipe_data['recipe_suggestion'])
                st.info(recipe_data['note'])
    
    # Nutrition analysis
    st.subheader("Nutrition Analysis")
    
    if st.session_state.current_cart_id:
        if st.button("Analyze Current Cart"):
            nutrition_data = analyze_nutrition(st.session_state.current_cart_id)
            if nutrition_data:
                st.success("Nutritional Analysis:")
                st.write(nutrition_data['nutrition_analysis'])
                
                if nutrition_data['categories']:
                    st.subheader("Product Categories in Cart:")
                    for category, count in nutrition_data['categories'].items():
                        st.write(f"- {category}: {count} items")
                
                st.info(nutrition_data['note'])
    else:
        st.warning("Create and fill a cart first to analyze nutrition")

if __name__ == "__main__":
    main()