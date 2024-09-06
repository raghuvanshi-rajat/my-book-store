from flask import Flask, jsonify
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_mysqldb import MySQL
from config import Config
from routes.user_routes import user_blueprint
from routes.book_routes import book_blueprint
from flask_swagger_ui import get_swaggerui_blueprint
import json

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)

jwt = JWTManager(app)

app.register_blueprint(user_blueprint, url_prefix='/api')
app.register_blueprint(book_blueprint, url_prefix='/api')

# Configure Swagger UI
SWAGGER_URL = '/swagger'
API_URL = 'http://127.0.0.1:3000/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Book Store API"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


@app.route('/swagger.json')
def swagger():
    with open('swagger.json', 'r') as f:
        return jsonify(json.load(f))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int("3000"))
