class GameState(object):
    def __init__(self):
        self.game_data = {}

    def set_game_data(self, scope, name, data_type="int", content="0", client_ip=""):
        self.game_data[name] = {"scope": scope, "type": data_type, "content": content, "client_ip": client_ip}

    def get_game_data(self, name):
        return self.game_data[name]

    def remove_game_data(self, name):
        return self.game_data.pop(name)
