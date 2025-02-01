class Game:
    def __init__(self, game_id, total_rounds):
        self.game_id = game_id
        self.players = {}
        self.status = "waiting"
        self.total_rounds = total_rounds
        self.current_round = 1
        self.round_results = {}

    def to_dict(self):
        return {
            "game_id": self.game_id,
            "players": self.players,
            "status": self.status,
            "total_rounds": self.total_rounds,
            "current_round": self.current_round,
            "round_results": self.round_results
        }
