from gamestate import GameState

import socket


class CCTGParser(object):
    def __init__(self):
        self.parser_state = ""
        self.game_state = GameState()

    def parse_cctg_data(self, client_list, client, data=""):
        if data.upper().startswith("IPS "):
            for ip in data.split(" ")[1:]:
                new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                new_sock.connect((ip.split(":")[0], ip.split(":")[1]))
                client_list.append({"client": new_sock, "ip": ip.split(":")[0], "port": ip.split(":")[1]})
                client.sendall("CONNECTEDTO " + ip)
            client.sendall("CONNECTIONSDONE")

        if data.upper() == "GAMESTATE START":
            self.parser_state = "READING_GAME_STATE"
            client.sendall(self.parser_state)

        if data.upper() == "GETPARSERSTATE":
            client.sendall(self.parser_state)

        if self.parser_state == "READING_GAME_STATE":
            if data.upper().startswith("STATE "):
                data_splits = data.split(" ")
                self.game_state.set_game_data("state", data_splits[1], data_splits[2], data_splits[3])
                client.sendall("GOTSDATA {} {} :{}".format(data_splits[1], data_splits[2], data_splits[3]))
                return client_list

            elif data.upper().startswith("USER "):
                data_splits = data.split(" ")
                self.game_state.set_game_data("user", data_splits[2], data_splits[3], data_splits[4], data_splits[1])
                client.sendall(
                    "GOTUDATA {} {} {} :{}".format(data_splits[1], data_splits[2], data_splits[3], data_splits[4]))
                return client_list

            elif data.upper() == "GAMESTATE END":
                self.parser_state = ""
                client.sendall("GAMESTATECLIENT END")
                return client_list

            else:
                client.sendall("ERR INVALID_GAMESTATE_CMD")

        if data.upper().startswith("GETSTATEDATA "):
            try:
                data_name = data.split(" ")[1]

            except IndexError:
                client.sendall("ERR NOT_ENOUGH_ARGUMENTS")
                return client_list

            if data_name not in self.game_state.game_data:
                client.sendall("ERR STATE_DATA_NOT_FOUND")

            game_data = self.game_state.get_game_data(data_name)

            client.sendall("STATEDATA {} {} {} {}".format(
                game_data["scope"] + (" " + game_data["client_ip"] if game_data["client_ip"] == "user" else ""),
                game_data["name"],
                game_data["type"],
                game_data["content"]
            ))

        if data.startswith("STATEDATA "):
            data_splits = data.split(" ")[1:]

            if data_splits[0].lower() == "state":
                self.game_state.set_game_data("state", data_splits[1], data_splits[2], data_splits[3])
                client.sendall("GOTSDATA {} {} :{}".format(data_splits[1], data_splits[2], data_splits[3]))

            elif data_splits[0].lower() == "":
                self.game_state.set_game_data("user", data_splits[1], data_splits[2], data_splits[3], data_splits[4])
                client.sendall("GOTUDATA {} {} :{}".format(data_splits[1], data_splits[2], data_splits[3]),
                               data_splits[4])

            else:
                client.sendall("ERR INVALID_GAMESTATE_CMD")

        if data.startswith("TERMINATINGCLIENT "):
            ip, port = data.split(" ")[1:]

            for index, client in enumerate(client_list):
                if (client["ip"], client["port"]) == (ip, port):
                    client_list.pop(index)

        return client_list
