from flask import Blueprint, request, jsonify
import uuid
from database import create_game_in_db, update_game_data, get_game_data
from utils.qr_generator import generate_qr_code

game_blueprint = Blueprint('game', __name__)

@game_blueprint.route('/create', methods=['POST'])
def create_game():
    try:
        # Ensure request contains JSON
        if not request.is_json:
            return jsonify({"error": "Invalid request format. Expected JSON."}), 400

        data = request.get_json()

        # Validate required field (total_rounds)
        if "total_rounds" not in data:
            return jsonify({"error": "Missing 'total_rounds' field in request."}), 400

        total_rounds = data.get("total_rounds", 3)

        # Validate total_rounds is a positive integer
        if not isinstance(total_rounds, int) or total_rounds <= 0:
            return jsonify({"error": "'total_rounds' must be a positive integer."}), 400

        # Generate game ID and save to Firebase
        game_id = str(uuid.uuid4())[:8]
        create_game_in_db(game_id, total_rounds)

        # Generate QR code and session URL
        qr_code_base64, session_url = generate_qr_code(game_id)

        return jsonify({
            "game_id": game_id,
            "session_url": session_url,
            "qr_code_base64": qr_code_base64,
            "message": "Game session successfully created."
        }), 201

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500


# Player joins a game
@game_blueprint.route('/join', methods=['POST'])
def join_game():
    data = request.json
    game_id = data.get("game_id")
    player_id = str(uuid.uuid4())[:6]

    game = get_game_data(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    game["players"][player_id] = {"number": None}
    update_game_data(game_id, "players", game["players"])

    return jsonify({"player_id": player_id}), 200
