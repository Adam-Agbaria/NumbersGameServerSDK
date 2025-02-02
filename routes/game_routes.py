from flask import Blueprint, request, jsonify
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

def handle_rounds(game_id):
    """Handles round timing and checks if all players have submitted before ending the round"""
    while True:
        game = get_game_data(game_id)

        if not game or game["status"] == "finished":
            break  # Stop if game is over

        current_round = game["current_round"]
        total_rounds = game["total_rounds"]

        print(f"🔹 Round {current_round} started for game {game_id}")

        # ✅ Start the round (Give players X seconds to submit)
        time.sleep(20)

        # ✅ Check if all players have submitted their numbers
        for wait_time in [5, 10, 10]:  # Total max wait time: 25 seconds
            game = get_game_data(game_id)
            if all(p["number"] is not None for p in game["players"].values()):
                break  # All players have submitted, proceed
            print(f"⏳ Waiting {wait_time} seconds for remaining players...")
            time.sleep(wait_time)

        # ✅ Mark round as finished
        game["status"] = "round_finished"
        update_game_data(game_id, "status", "round_finished")
        print(f"✔️ Round {current_round} finished! Showing results...")

        # ✅ Display round results for 15 seconds
        time.sleep(15)

        # ✅ Move to next round or finish the game
        if current_round >= total_rounds:
            game["status"] = "finished"
            update_game_data(game_id, "status", "finished")
            print(f"🏁 Game {game_id} has ended!")
            break
        else:
            game["current_round"] += 1
            game["status"] = "started"
            update_game_data(game_id, "current_round", game["current_round"])
            update_game_data(game_id, "status", "started")
            print(f"🚀 Starting round {game['current_round']} for game {game_id}")