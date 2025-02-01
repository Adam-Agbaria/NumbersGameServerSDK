from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS for all routes
CORS(app, supports_credentials=True)

# ✅ Manually add CORS headers in every response
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"  # Allow all domains
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"  # Allowed methods
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"  # Allow these headers
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Register routes
from routes.game_routes import game_blueprint
from routes.round_routes import round_blueprint

app.register_blueprint(game_blueprint, url_prefix='/game')
app.register_blueprint(round_blueprint, url_prefix='/round')

if __name__ == '__main__':
    app.run(debug=True)
