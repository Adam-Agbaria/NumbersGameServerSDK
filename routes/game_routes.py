from flask import Blueprint, request, jsonify, current_app
import uuid, time, threading
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



game_blueprint = Blueprint('game', __name__)

@game_blueprint.route('/join', methods=['POST'])
def join_game():
    try:
        # Ensure request contains JSON
        if not request.is_json:
            return jsonify({"error": "Invalid request format. Expected JSON."}), 400

        data = request.get_json()

        # Validate required fields (game_id, player_name)
        if "game_id" not in data:
            return jsonify({"error": "Missing 'game_id' field in request."}), 400
        if "player_name" not in data:
            return jsonify({"error": "Missing 'player_name' field in request."}), 400

        game_id = data["game_id"]
        player_name = data["player_name"].strip()

        # Ensure name is not empty
        if not player_name:
            return jsonify({"error": "Player name cannot be empty."}), 400

        # Retrieve game session
        game = get_game_data(game_id)
        if not game:
            return jsonify({"error": "Game not found."}), 404

        # Generate a unique player ID
        player_id = str(uuid.uuid4())[:6]

        # Add player to the game
        game["players"][player_id] = {
            "name": player_name,
            "number": None  # Number will be submitted later
        }
        update_game_data(game_id, "players", game["players"])

        return jsonify({
            "player_id": player_id,
            "player_name": player_name,
            "message": f"Player '{player_name}' joined the game."
        }), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500

# Fetch game results
@game_blueprint.route('/results', methods=['GET'])
def get_game_results():
    game_id = request.args.get("game_id")
    
    if not game_id:
        return jsonify({"error": "Missing 'game_id' parameter"}), 400

    game = get_game_data(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    return jsonify({
        "game_id": game_id,
        "total_rounds": game["total_rounds"],
        "round_results": game["round_results"],
        "status": game["status"]
    }), 200

@game_blueprint.route('/status/<game_id>', methods=['GET'])
def get_game_status(game_id):
    """Check game status (long polling support)"""
    timeout = 200
    poll_interval = 4
    elapsed_time = 0

    while elapsed_time < timeout:
        game = get_game_data(game_id)

        if not game:
            return jsonify({"error": "Game not found"}), 404

        if game["status"] in ["started", "round_finished", "finished"]:
            return jsonify({"status": game["status"]}), 200

        time.sleep(poll_interval)
        elapsed_time += poll_interval

    return jsonify({"status": "waiting"}), 200


@game_blueprint.route('/start', methods=['POST'])
def start_game():
    """Start the game and handle round progression"""
    data = request.get_json()
    game_id = data.get("game_id")

    if not game_id:
        return jsonify({"error": "Missing game ID"}), 400

    game = get_game_data(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    if game["status"] != "waiting":
        return jsonify({"error": "Game has already started or finished"}), 400

    # Change game status to "started"
    game["status"] = "started"
    game["current_round"] = 1
    update_game_data(game_id, "status", "started")
    update_game_data(game_id, "current_round", 1)

    # Start round processing in a separate thread
    threading.Thread(target=handle_rounds, args=(game_id,)).start()

    return jsonify({"message": "Game started"}), 200

import time
from flask import current_app
from database import update_game_data, get_game_data

def handle_rounds(game_id):
    """Handles round timing and forces end after 30 seconds"""
    logger = current_app.logger  # ✅ Use Flask's logger

    while True:
        game = get_game_data(game_id)

        if not game or game["status"] == "finished":
            logger.info(f"🏁 Game {game_id} has already finished. Exiting round handler.")
            break  # Stop if game is over

        current_round = game["current_round"]
        total_rounds = game["total_rounds"]

        logger.info(f"🔹 Round {current_round} started for game {game_id}")

        # ✅ Step 1: Give 20 seconds for normal submissions
        time.sleep(20)

        # ✅ Step 2: Extra 10 seconds grace period
        time.sleep(10)

        # ✅ Step 3: Assign default number (10) if player didn’t pick
        game = get_game_data(game_id)  # Refresh game data
        for player_id, player_data in game["players"].items():
            if player_data.get("number") is None:  # If no number was picked
                logger.warning(f"⚠️ Player {player_id} didn't pick. Assigning default 10.")
                game["players"][player_id]["number"] = 10  # Default to 10

        update_game_data(game_id, "players", game["players"])  # ✅ Save default numbers

        # ✅ Step 4: **FORCE update to "round_finished"**
        logger.info(f"✔️ Forcing game status to 'round_finished' for game {game_id}")
        update_game_data(game_id, "status", "round_finished")

        # ✅ Step 5: Verify if the update was successful
        game_check = get_game_data(game_id)  # Check database again
        if game_check["status"] == "round_finished":
            logger.info(f"✅ Round {current_round} successfully marked as 'round_finished'")
        else:
            logger.error(f"❌ Failed to update status to 'round_finished'. Current status: {game_check['status']}")

        # ✅ Step 6: Display results for 15 seconds
        time.sleep(15)

        # ✅ Step 7: Move to next round or finish the game
        if current_round >= total_rounds:
            update_game_data(game_id, "status", "finished")
            logger.info(f"🏁 Game {game_id} has ended!")
            break
        else:
            game["current_round"] += 1
            update_game_data(game_id, "current_round", game["current_round"])
            update_game_data(game_id, "status", "started")
            logger.info(f"🚀 Starting round {game['current_round']} for game {game_id}")