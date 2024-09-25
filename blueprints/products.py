from flask import Blueprint, render_template, request, redirect, url_for
import logging
from utils.openai_helper import generate_product_content, parse_generated_content
from utils.shopify_helper import get_vendor_products, update_product_with_content, scrape_images, upload_images_to_shopify, download_image

# Define the products blueprint
products_bp = Blueprint('products', __name__)

# Route for generating content for a vendor
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

        # Log the product being processed
        logging.info(f"Processing product '{product_title}' with ID {product_id}")

        # Generate content only for products below the minimum inventory level
        generated_content = generate_product_content(product_title)
        if not generated_content:
            logging.error(f"Failed to generate content for product '{product_title}'")
            continue

        description, tags, category = parse_generated_content(generated_content)
        images = scrape_images(product_title)

        # Add the product details and generated content to the response list
        product_responses.append({
            "product_id": product_id,
            "title": product_title,
            "description": description,
            "tags": tags,
            "category": category,
            "images": images
        })

    # Render the review content page for the user to review the generated content
    return render_template('review_content.html', products=product_responses)

# Route for uploading content
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

        # Update the product with the generated content and upload images
        update_product_with_content(product_id, description, tags, category)

        for image_url in selected_images:
            image_data = download_image(image_url)
            if image_data:
                upload_images_to_shopify(product_id, image_data, filename="product_image.jpg")

    # Redirect to the success page after all products are processed
    return redirect(url_for('products.success_page'))

# Route for the success page after content upload
@products_bp.route('/upload_success')
def success_page():
    return render_template('success.html')