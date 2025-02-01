class Player:
    def __init__(self, player_id):
        self.player_id = player_id
        self.number = None  # Player's chosen number

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "number": self.number
        }
