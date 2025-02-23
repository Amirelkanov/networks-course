import uuid
from flask import Flask, request, jsonify, abort, send_file
import os
import mimetypes

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'images')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class Product:
    def __init__(self, name, description, icon=""):
        self.id = uuid.uuid4().int
        self.name = name
        self.description = description
        self.icon = icon

products: list[Product] = []

@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e)), 400

@app.route('/')
def home():
    return jsonify(message="Welcome to AmEl shop REST service. Checkout the docs for more info.")

@app.route('/product', methods=['POST'])
def add_product():
    data = request.get_json()
    if not data or 'name' not in data or 'description' not in data:
        abort(400, description="Missing required fields: name and description")
    product = Product(data['name'], data['description'])
    products.append(product)
    return jsonify(product.__dict__), 201

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id: int):
    for product in products:
        if product.id == product_id:
            return jsonify(product.__dict__)
    abort(404, description="Product not found")

@app.route('/product/<int:product_id>', methods=['PUT'])
def update_product(product_id: int):
    data = request.get_json()
    if not data:
        abort(400, description="Invalid or missing JSON data")
    for product in products:
        if product.id == product_id:
            if 'name' in data:
                product.name = data['name']
            if 'description' in data:
                product.description = data['description']
            if 'icon' in data:
                product.icon = data['icon']
            return jsonify(product.__dict__)
    abort(404, description="Product not found")

@app.route('/product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id: int):
    for product in products:
        if product.id == product_id:
            products.remove(product)
            return jsonify(product.__dict__)
    abort(404, description="Product not found")

@app.route('/products', methods=['GET'])
def get_products():
    return jsonify([product.__dict__ for product in products])

@app.route('/product/<int:product_id>/image', methods=['POST'])
def upload_image(product_id: int):
    for product in products:
        if product.id == product_id:
            if 'icon' not in request.files:
                abort(400, description="No icon part in the request")
            icon = request.files['icon']
            if icon.filename == '':
                abort(400, description="No selected file")

            icon_path = os.path.join(app.config['UPLOAD_FOLDER'], icon.filename)
            icon.save(icon_path)
            product.icon = icon_path
            return jsonify(product.__dict__)
    abort(404, description="Product not found")

@app.route('/product/<int:product_id>/image', methods=['GET'])
def get_image(product_id: int):
    for product in products:
        if product.id == product_id:
            if product.icon and os.path.exists(product.icon):
                mime_type, _ = mimetypes.guess_type(product.icon)
                return send_file(product.icon, mimetype=mime_type)
            abort(404, description="Image not found")
    abort(404, description="Product not found")

if __name__ == '__main__':
    app.run(debug=True)
