from flask import Blueprint, request, jsonify
from database import update_game_data, get_game_data

round_blueprint = Blueprint('round', __name__)

@round_blueprint.route('/submit', methods=['POST'])
def submit_number():
    """Submit a number for the current round."""
    data = request.get_json()
    game_id = data.get("game_id")
    player_id = data.get("player_id")
    chosen_number = data.get("number")

    game = get_game_data(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    if player_id not in game["players"]:
        return jsonify({"error": "Player not in game"}), 404

    game["players"][player_id]["number"] = chosen_number
    update_game_data(game_id, "players", game["players"])

    return jsonify({"message": "Number submitted successfully"}), 200


@round_blueprint.route('/calculate_winner', methods=['POST'])
def calculate_winner():
    """Determine the winner for the current round."""
    data = request.get_json()
    game_id = data.get("game_id")

    game = get_game_data(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    numbers = [p["number"] for p in game["players"].values()]
    avg_number = sum(numbers) / len(numbers) * 0.8

    winner = min(game["players"], key=lambda pid: abs(game["players"][pid]["number"] - avg_number))

    game["round_results"][f"Round {game['current_round']}"] = {
        "winner": winner,
        "winning_number": avg_number,
        "chosen_number": game["players"][winner]["number"]
    }

    update_game_data(game_id, "round_results", game["round_results"])

    return jsonify({"winner": winner, "winning_number": avg_number}), 200