from flask import Blueprint, request, jsonify
from database import update_game_data, get_game_data

round_blueprint = Blueprint('round', __name__)

# Submit a number for a round
@round_blueprint.route('/submit', methods=['POST'])
def submit_number():
    data = request.json
    game_id = data.get("game_id")
    player_id = data.get("player_id")
    chosen_number = data.get("number")

    game = get_game_data(game_id)
    if not game or player_id not in game["players"]:
        return jsonify({"error": "Invalid game or player"}), 404

    game["players"][player_id]["number"] = chosen_number
    update_game_data(game_id, "players", game["players"])

    return jsonify({"message": "Number submitted"}), 200

# Calculate the winner of a round
@round_blueprint.route('/calculate_winner', methods=['POST'])
def calculate_winner():
    data = request.json
    game_id = data.get("game_id")

    game = get_game_data(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    numbers = [p["number"] for p in game["players"].values() if p["number"] is not None]
    if len(numbers) < 2:
        return jsonify({"error": "Not enough players"}), 400

    avg_number = sum(numbers) / len(numbers) * 0.8
    winner = min(game["players"], key=lambda pid: abs(game["players"][pid]["number"] - avg_number))

    game["round_results"][f"Round {game['current_round']}"] = {"winner": winner, "average": avg_number}
    game["current_round"] += 1

    if game["current_round"] > game["total_rounds"]:
        game["status"] = "finished"

    update_game_data(game_id, "round_results", game["round_results"])
    update_game_data(game_id, "current_round", game["current_round"])
    update_game_data(game_id, "status", game["status"])

    return jsonify({"average": avg_number, "winner": winner, "current_round": game["current_round"]}), 200
