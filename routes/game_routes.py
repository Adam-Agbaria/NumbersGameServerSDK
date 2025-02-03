from flask import Blueprint, request, jsonify, current_app
import uuid, time, threading
from database import create_game_in_db, update_game_data, get_game_data
from utils.qr_generator import generate_qr_code
import logging
import asyncio

game_blueprint = Blueprint('game', __name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



game_blueprint = Blueprint('game', __name__)

@game_blueprint.route('/create', methods=['POST'])
def create_game():
    """Create a new game session."""
    data = request.get_json()
    if "total_rounds" not in data:
        return jsonify({"error": "Missing 'total_rounds' field"}), 400

    total_rounds = data.get("total_rounds", 3)
    game_id = str(uuid.uuid4())[:8]

    create_game_in_db(game_id, total_rounds)
    qr_code_base64, session_url = generate_qr_code(game_id)

    return jsonify({
        "game_id": game_id,
        "session_url": session_url,
        "qr_code_base64": qr_code_base64,
        "message": "Game created successfully."
    }), 201


@game_blueprint.route('/join', methods=['POST'])
def join_game():
    """Allow a player to join an existing game."""
    data = request.get_json()
    game_id = data.get("game_id")
    player_name = data.get("player_name").strip()

    game = get_game_data(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    player_id = str(uuid.uuid4())[:6]
    game["players"][player_id] = {"name": player_name, "number": None}

    update_game_data(game_id, "players", game["players"])
    return jsonify({"player_id": player_id, "message": "Player joined successfully."}), 200


@game_blueprint.route('/start', methods=['POST'])
def start_game():
    """Start the game (first round)."""
    data = request.get_json()
    game_id = data.get("game_id")

    game = get_game_data(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    if game["status"] != "waiting":
        return jsonify({"error": "Game already started or finished"}), 400

    game["status"] = "started"
    game["current_round"] = 1
    update_game_data(game_id, "status", "started")
    update_game_data(game_id, "current_round", 1)

    return jsonify({"message": "Game started", "current_round": 1}), 200


@game_blueprint.route('/next_round', methods=['POST'])
def next_round():
    """Moves the game to the next round or marks it as finished."""
    data = request.get_json()
    game_id = data.get("game_id")

    game = get_game_data(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    current_round = game["current_round"]
    total_rounds = game["total_rounds"]

    if current_round >= total_rounds:
        # ✅ Game is finished
        game["status"] = "finished"
        update_game_data(game_id, "status", "finished")
        return jsonify({"message": "Game finished"}), 200
    else:
        # ✅ Move to next round
        game["current_round"] += 1
        game["status"] = "started"
        update_game_data(game_id, "current_round", game["current_round"])
        update_game_data(game_id, "status", "started")
        return jsonify({
            "message": f"Round {game['current_round']} started",
            "current_round": game["current_round"]
        }), 200


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


@game_blueprint.route('/status/<game_id>', methods=['OPTIONS'])
def options_handler(game_id):
    """Handle preflight CORS requests"""
    return jsonify({"message": "OK"}), 200

async def async_get_game_status(game_id, timeout=9, poll_interval=2):
    """Asynchronous function to check game status within Vercel's timeout"""
    elapsed_time = 0

    while elapsed_time < timeout:
        game = get_game_data(game_id)  # Fetch game data

        if not game:
            return {"error": "Game not found"}, 404

        if game["status"] in ["started", "round_finished", "finished"]:
            return {"status": game["status"]}, 200

        await asyncio.sleep(poll_interval)  # Non-blocking wait
        elapsed_time += poll_interval

    return {"status": "waiting"}, 200

@game_blueprint.route('/status/<game_id>', methods=['GET'])
async def get_game_status(game_id):
    """Optimized non-blocking endpoint for Vercel"""
    try:
        response, status_code = await async_get_game_status(game_id)
        return jsonify(response), status_code

    except Exception as e:
        print(f"❌ Server Error: {str(e)}")  # Log errors for debugging
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    

@game_blueprint.route('/end_round', methods=['POST'])
def end_round():
    """Manually end the current round and calculate the winner."""
    data = request.get_json()
    game_id = data.get("game_id")

    game = get_game_data(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    if game["status"] != "started":
        return jsonify({"error": "Game is not in progress"}), 400

    current_round = game["current_round"]

    # Assign default numbers (10) for players who didn't submit
    for player_id, player in game["players"].items():
        if player["number"] is None:
            game["players"][player_id]["number"] = 10

    update_game_data(game_id, "players", game["players"])

    # ✅ FIX: Convert all numbers to integers before calculations
    numbers = [int(p["number"]) for p in game["players"].values()]

    # Calculate the average and winner
    avg_number = sum(numbers) / len(numbers) * 0.8
    winner = min(game["players"], key=lambda pid: abs(int(game["players"][pid]["number"]) - avg_number))

    game["round_results"][f"Round {current_round}"] = {
        "winner": winner,
        "winning_number": avg_number,
        "chosen_number": game["players"][winner]["number"]
    }

    update_game_data(game_id, "round_results", game["round_results"])

    # Move to next round or finish the game
    if current_round >= game["total_rounds"]:
        game["status"] = "finished"
        update_game_data(game_id, "status", "finished")
        return jsonify({"message": "Game finished!", "winner": winner}), 200
    else:
        game["current_round"] += 1
        update_game_data(game_id, "current_round", game["current_round"])
        update_game_data(game_id, "status", "round_ended")
        return jsonify({
            "message": f"Round {game['current_round']} started",
            "previous_winner": winner
        }), 200
