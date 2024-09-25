from flask import Blueprint, render_template, request, redirect, url_for
import logging
from utils.openai_helper import generate_product_content, parse_generated_content
from utils.shopify_helper import get_vendor_products, update_product_with_content, scrape_images, upload_images_to_shopify, download_image

products_bp = Blueprint('products', __name__)

@products_bp.route('/generate_for_vendor', methods=['POST'])
def generate_for_vendor():
    vendor = request.form.get('vendor')
    min_inventory_level = int(request.form.get('min_inventory_level', 0))  # Default to 0 if not specified
    
    if not vendor:
        return "Vendor not specified", 400

    # Fetch products that are below the minimum inventory level
    products = get_vendor_products(vendor, min_inventory_level)
    
    if not products:
        return f"No products found for vendor {vendor} below the minimum inventory level", 404

    product_responses = []

    for product in products:
        product_title = product['title']
        product_id = product['id']

        # Generate content only for products below the minimum inventory level
        generated_content = generate_product_content(product_title)
        if not generated_content:
            continue

        description, tags, category = parse_generated_content(generated_content)
        images = scrape_images(product_title)

        product_responses.append({
            "product_id": product_id,
            "title": product_title,
            "description": description,
            "tags": tags,
            "category": category,
            "images": images
        })

    return render_template('review_content.html', products=product_responses)

@products_bp.route('/upload_content', methods=['POST'])
def upload_content():
    product_ids = request.form.getlist('product_ids')
    
    for product_id in product_ids:
        description = request.form.get(f'description_{product_id}')
        tags = request.form.get(f'tags_{product_id}')
        category = request.form.get(f'category_{product_id}')
        selected_images = request.form.getlist(f'selected_images_{product_id}')

        # Log the collected data for each product
        logging.info(f"Processing product {product_id} with description: {description}, tags: {tags}, category: {category}")
        logging.info(f"Selected images: {selected_images}")

        # Process the content and upload images
        update_product_with_content(product_id, description, tags, category)
        
        for image_url in selected_images:
            image_data = download_image(image_url)
            if image_data:
                upload_images_to_shopify(product_id, image_data, filename="product_image.jpg")

    return redirect(url_for('products.success_page'))

@products_bp.route('/upload_success')
def success_page():
    return render_template('success.html')
