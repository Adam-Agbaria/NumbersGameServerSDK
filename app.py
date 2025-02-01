from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://numbers-game-web-app.vercel.app",
            "http://localhost:5500",   # Allow local testing
            "http://127.0.0.1:5000",   # Allow Flask local server
            "*",  # If you want to allow all origins (less secure)
        ],
        "methods": ["GET", "POST", "OPTIONS"],  # Allowed methods
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
from routes.game_routes import game_blueprint
from routes.round_routes import round_blueprint

app.register_blueprint(game_blueprint, url_prefix='/game')
app.register_blueprint(round_blueprint, url_prefix='/round')

if __name__ == '__main__':
    app.run(debug=True)
