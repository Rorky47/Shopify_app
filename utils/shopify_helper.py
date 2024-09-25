import requests
from bs4 import BeautifulSoup
import logging
import os
import random
import time
import urllib.parse
import base64
from config import SHOPIFY_STORE, SHOPIFY_ACCESS_TOKEN, IGNORE_LIST_FILE

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
]

def scrape_images(product_title):
    """
    Scrapes images related to the product title from Google Images. Introduces delay and user-agent rotation to avoid
    detection and rate limits.
    
    Args:
        product_title (str): The title of the product for which to scrape images.
    
    Returns:
        list: A list of image URLs related to the product title.
    """
    search_query = f"https://www.google.com/search?q={product_title}&tbm=isch"
    headers = {
        'User-Agent': random.choice(USER_AGENTS)  # Rotate User-Agent
    }

    try:
        # Introduce a random delay to avoid quick successive requests
        time.sleep(random.uniform(1.5, 4.0))

        # Make the request to Google Images
        response = requests.get(search_query, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse the response content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find image tags and extract the image URLs
        image_elements = soup.find_all('img')
        image_urls = [img['src'] for img in image_elements if 'src' in img.attrs]

        # Log the number of images found
        logging.info(f"Successfully fetched {len(image_urls)} images for {product_title}")

        # Return the list of image URLs
        return image_urls

    except requests.exceptions.Timeout:
        logging.error(f"Timeout occurred while trying to scrape images for {product_title}")
        return []  # Return an empty list if the request times out

    except requests.exceptions.RequestException as e:
        logging.error(f"Error scraping images for {product_title}: {e}")
        return []  # Return an empty list in case of any other error

def download_image(image_url):
    """
    Downloads an image from the specified URL and returns it as binary data.
    
    Args:
        image_url (str): The URL of the image to download.
    
    Returns:
        bytes: The binary image data.
    """
    response = requests.get(image_url)
    
    if response.status_code == 200:
        return response.content  # Return the image data as binary
    else:
        print(f"Failed to download image from {image_url}. Status code: {response.status_code}")
        return None

def upload_images_to_shopify(product_id, image_data, filename):
    """
    Uploads an image to Shopify for the specified product using base64 encoding.
    
    Args:
        product_id (str): The Shopify product ID.
        image_data (bytes): The binary data of the image.
        filename (str): The filename to use when uploading the image.
    
    Returns:
        None
    """
    # Convert the binary image data to a base64-encoded string
    base64_image = base64.b64encode(image_data).decode('utf-8')

    # Create the payload for the Shopify API
    payload = {
        "image": {
            "attachment": base64_image,
            "filename": filename  # Optionally, specify a filename for the image
        }
    }

    # Shopify API endpoint for uploading images to a product
    url = f"https://{SHOPIFY_STORE}/admin/api/2023-07/products/{product_id}/images.json"
    
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
    }

    # Send the HTTP POST request to Shopify
    response = requests.post(url, json=payload, headers=headers)

    # Log the result with more detail
    if response.status_code == 201:
        logging.info(f"Successfully uploaded image to product {product_id}")
    else:
        logging.error(f"Failed to upload image to product {product_id}. Status code: {response.status_code}, response: {response.text}")

def process_image_upload(product_id, image_url):
    """
    Downloads an image from the provided URL and uploads it to Shopify as a base64-encoded image.
    
    Args:
        product_id (str): The Shopify product ID.
        image_url (str): The URL of the image to download and upload.
    
    Returns:
        None
    """
    # Step 1: Download the image from the external source
    image_data = download_image(image_url)

    if image_data:
        # Step 2: Upload the image to Shopify
        upload_image_to_shopify(product_id, image_data, filename="product_image.jpg")
    else:
        print(f"Failed to process image for product {product_id}")


def update_product_with_content(product_id, description, tags, category):
    payload = {
        "product": {
            "id": product_id,
            "body_html": description,
            "tags": tags,
            "product_type": category
        }
    }
    url = f"https://{SHOPIFY_STORE}/admin/api/2023-07/products/{product_id}.json"
    headers = {"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
    response = requests.put(url, json=payload, headers=headers)

    if response.status_code == 200:
        logging.info(f"Successfully updated product {product_id}.")
    else:
        logging.error(f"Failed to update product {product_id}. Status code: {response.status_code}")

def get_parent_product_info(inventory_item_id):
    """
    Fetches product information including the title, variants, and total inventory
    for the given inventory item ID from Shopify using GraphQL.
    """
    url = f"https://{SHOPIFY_STORE}/admin/api/2023-07/graphql.json"
    
    query = """
    {
      inventoryItem(id: "gid://shopify/InventoryItem/{inventory_item_id}") {
        id
        variant {
          product {
            title
            id
            variants(first: 100) {
              edges {
                node {
                  inventoryQuantity
                }
              }
            }
          }
          title
        }
      }
    }
    """.replace("{inventory_item_id}", str(inventory_item_id))

    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
    }

    response = requests.post(url, json={'query': query}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        inventory_item = data['data'].get('inventoryItem')
        if inventory_item:
            product_name = inventory_item['variant']['product']['title']
            variant_name = inventory_item['variant']['title']
            product_id = inventory_item['variant']['product']['id']

            total_inventory = sum(
                edge['node']['inventoryQuantity'] for edge in inventory_item['variant']['product']['variants']['edges']
            )

            return f"{product_name} ({variant_name})", total_inventory, product_id
        else:
            logging.error(f"No product found for inventory item ID: {inventory_item_id}")
    else:
        logging.error(f"Failed to fetch inventory item. Status code: {response.status_code}")

    return 'Unknown Product', 0, None

def update_product_status(product_id, status):
    """
    Updates the status (e.g., 'draft', 'active') of a product on Shopify.
    
    Args:
        product_id (str): The product ID in Shopify.
        status (str): The status to set for the product (e.g., 'draft', 'active').
    
    Returns:
        None
    """
    # Extract the numeric part of the product ID (Shopify uses GID format)
    numeric_product_id = product_id.split('/')[-1]
    
    # Shopify API URL to update product status
    url = f"https://{SHOPIFY_STORE}/admin/api/2023-07/products/{numeric_product_id}.json"
    
    # Payload to update product status
    payload = {
        "product": {
            "id": numeric_product_id,
            "status": status
        }
    }
    
    # Headers for the request
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
    }

    # Send the PUT request to Shopify to update the product status
    response = requests.put(url, json=payload, headers=headers)
    
    # Log the result
    if response.status_code == 200:
        logging.info(f"Successfully updated product {numeric_product_id} to {status}.")
    else:
        logging.error(f"Failed to update product {numeric_product_id} to {status}. Status code: {response.status_code}")

def get_vendor_products(vendor, min_inventory_level):
    """
    Fetch all products from a vendor with pagination and filter out products whose total inventory 
    is above the minimum inventory level.
    
    Args:
        vendor (str): The vendor to filter products by.
        min_inventory_level (int): The minimum total inventory level for a product to be included.
    
    Returns:
        list: A list of products that meet the inventory requirement.
    """
    products = []
    limit = 50  # Number of products to fetch per page
    page_info = None  # For pagination tracking

    # URL-encode the vendor name to handle spaces or special characters
    vendor = urllib.parse.quote(vendor)

    while True:
        # Construct the URL for the request
        if page_info:
            # Use page_info for pagination, omit the vendor parameter in subsequent requests
            url = f"https://{SHOPIFY_STORE}/admin/api/2023-07/products.json?limit={limit}&page_info={page_info}"
        else:
            # Initial request includes the vendor parameter
            url = f"https://{SHOPIFY_STORE}/admin/api/2023-07/products.json?limit={limit}&vendor={vendor}"

        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN
        }

        logging.info(f"Requesting URL: {url}")  # Log the request URL

        # Fetch the data from Shopify
        response = requests.get(url, headers=headers)

        if response.status_code == 400:
            logging.error(f"Failed to fetch products for vendor {vendor}. Status code: {response.status_code}. Response: {response.text}")
            break

        if response.status_code != 200:
            logging.error(f"Failed to fetch products. Status code: {response.status_code}")
            break

        # Parse the response
        data = response.json()
        fetched_products = data.get('products', [])

        logging.info(f"Fetched {len(fetched_products)} products from the Shopify API.")

        # Filter products by the total inventory of all variants
        for product in fetched_products:
            # Sum the inventory of all variants
            total_inventory = sum(variant['inventory_quantity'] for variant in product['variants'])

            # Log the total inventory and the threshold for debugging
            logging.info(f"Product '{product['title']}' has total inventory: {total_inventory}, threshold: {min_inventory_level}")

            # Only include products where the total inventory is below the threshold
            if total_inventory >= min_inventory_level:
                logging.info(f"Skipping product '{product['title']}' with total inventory: {total_inventory} (above threshold).")
            else:
                logging.info(f"Including product '{product['title']}' with total inventory: {total_inventory} (below threshold).")
                products.append(product)

        # Check for pagination (if there's a next page)
        link_header = response.headers.get('Link', '')
        if 'rel="next"' in link_header:
            # Extract the page_info parameter from the 'Link' header
            next_link = [link for link in link_header.split(',') if 'rel="next"' in link]
            if next_link:
                page_info = next_link[0].split('page_info=')[-1].split('>')[0]
                logging.info(f"Fetching next page with page_info: {page_info}")
        else:
            # No more pages, exit the loop
            break

    logging.info(f"Total products after filtering: {len(products)}")
    return products

def load_ignored_products():
    """
    Loads the list of ignored products from a text file.
    
    Returns:
        list: A list of ignored product names.
    """
    if os.path.exists(IGNORE_LIST_FILE):
        with open(IGNORE_LIST_FILE, 'r') as file:
            data = file.read().strip()
            # Split the file content by commas to create a list of ignored products
            return data.split(",") if data else []
    else:
        return []

def save_ignored_products(ignored_products):
    """
    Saves the list of ignored products to a text file.
    
    Args:
        ignored_products (list): The list of ignored product names.
    """
    with open(IGNORE_LIST_FILE, 'w') as file:
        file.write(",".join(ignored_products))