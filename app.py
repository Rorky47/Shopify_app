from flask import Flask, render_template, redirect, url_for
from blueprints.webhook import webhook_bp
from blueprints.products import products_bp
from blueprints.logs import logs_bp
from blueprints.ignore import ignore_bp
from utils.logging_helper import setup_logging

app = Flask(__name__)

# Setup custom logging
setup_logging()

# Register blueprints
app.register_blueprint(webhook_bp)
app.register_blueprint(products_bp)
app.register_blueprint(logs_bp)
app.register_blueprint(ignore_bp)

# Home route
@app.route('/')
def home():
    return render_template('home.html')  # Renders the 'home.html' template

if __name__ == "__main__":
    app.run(port=5000, debug=True)