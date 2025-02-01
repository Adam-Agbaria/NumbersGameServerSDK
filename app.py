from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enables CORS for all routes

from routes.game_routes import game_blueprint
from routes.round_routes import round_blueprint

app.register_blueprint(game_blueprint, url_prefix='/game')
app.register_blueprint(round_blueprint, url_prefix='/round')

if __name__ == '__main__':
    app.run(debug=True)
