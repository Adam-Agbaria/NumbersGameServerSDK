from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Allow CORS for frontend and other origins
CORS(app, resources={r"/*": {"origins": "*"}})  # Allows all origins

# Manually force CORS headers in every response
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Game routes
from routes.game_routes import game_blueprint
from routes.round_routes import round_blueprint

app.register_blueprint(game_blueprint, url_prefix='/game')
app.register_blueprint(round_blueprint, url_prefix='/round')

if __name__ == '__main__':
    app.run(debug=True)
