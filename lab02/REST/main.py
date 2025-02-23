from flask import Flask, request, jsonify, abort
import uuid
        
app = Flask(__name__)

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
    try:
        data = request.get_json()
        product = Product(data['name'], data['description'])
        products.append(product)
        return jsonify(product.__dict__)
    except Exception:
        abort(400)
    
@app.route('/product/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id: int):
    for product in products:
        if product.id == product_id:
            return jsonify(product.__dict__)
    abort(404)


@app.route('/product/<int:product_id>', methods=['PUT'])
def update_product(product_id: int):
    try:
        data = request.get_json()
        for product in products:
            if product.id == product_id:
                product.name = data['name']
                product.description = data['description']
                return jsonify(product.__dict__)
        abort(404)
    except Exception:
        abort(400)

@app.route('/product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id: int):
    for product in products:
        if product.id == product_id:
            products.remove(product)
            return jsonify(product.__dict__)
    abort(404)

@app.route('/products', methods=['GET'])
def get_products():
    return jsonify([product.__dict__ for product in products])

if __name__ == '__main__': 
    app.run(debug=True)
