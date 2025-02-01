import firebase_admin
from firebase_admin import credentials, firestore
from config import FIREBASE_CREDENTIALS_PATH

# Initialize Firebase
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred)
db = firestore.client()

def create_game_in_db(game_id, total_rounds):
    """Creates a new game session in Firestore"""
    db.collection("games").document(game_id).set({
        "game_id": game_id,
        "players": {},
        "status": "waiting",
        "total_rounds": total_rounds,
        "current_round": 1,
        "round_results": {}
    })

def update_game_data(game_id, field, value):
    """Update a specific field in the game document"""
    db.collection("games").document(game_id).update({field: value})

def get_game_data(game_id):
    """Retrieve game data from Firestore"""
    game_ref = db.collection("games").document(game_id)
    game = game_ref.get()
    return game.to_dict() if game.exists else None
