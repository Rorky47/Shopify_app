from flask import Blueprint, request, jsonify
from utils.shopify_helper import get_parent_product_info, update_product_status
import logging
from threading import Timer

webhook_bp = Blueprint('webhook', __name__)

# In-memory store for webhook events
webhook_store = {}

# Webhook route to handle Shopify product updates
@webhook_bp.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.json
    logging.info('Received webhook payload:')
    logging.info(payload)

    inventory_item_id = payload.get('inventory_item_id')
    product_name, total_inventory, parent_product_id = get_parent_product_info(inventory_item_id)

    webhook_store[parent_product_id] = {
        'product_name': product_name,
        'total_inventory': total_inventory,
        'product_id': parent_product_id,
    }

    timer = Timer(2.0, process_webhook, args=[parent_product_id])
    timer.start()

    return jsonify({"status": "success"}), 200

def process_webhook(parent_product_id):
    webhook_data = webhook_store.pop(parent_product_id, None)

    if webhook_data:
        product_name = webhook_data.get('product_name')
        total_inventory = webhook_data.get('total_inventory')
        product_id = webhook_data.get('product_id')

        if total_inventory <= 0:
            update_product_status(product_id, 'draft')
        else:
            update_product_status(product_id, 'active')
