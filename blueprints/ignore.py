from flask import Blueprint, request, redirect, url_for, render_template
from utils.shopify_helper import load_ignored_products, save_ignored_products

ignore_bp = Blueprint('ignore', __name__)

ignored_products = load_ignored_products()

# Route to manage ignored items
@ignore_bp.route('/ignore', methods=['GET', 'POST'])
def manage_ignored_items():
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        if product_name and product_name not in ignored_products:
            ignored_products.append(product_name)
            save_ignored_products(ignored_products)
        return redirect(url_for('ignore.manage_ignored_items'))
    return render_template('ignore.html', ignored_products=ignored_products)

# Route to remove ignored items
@ignore_bp.route('/ignore/remove/<product_name>', methods=['POST'])
def remove_ignored_item(product_name):
    if product_name in ignored_products:
        ignored_products.remove(product_name)
        save_ignored_products(ignored_products)
    return redirect(url_for('ignore.manage_ignored_items'))
