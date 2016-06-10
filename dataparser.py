import json
import socket
import time

import gamestate
import socketeer


class CCTGParser(object):
    def __init__(self, game):
        self.parser_state = ""
        self.network_host = ""
        self.start_time = time.time()
        self.total_received_messages = []

        try:
            self.game_state = gamestate.GameState(json.load(open("games\\{}\\initialstate.cgs".format(game)), "utf-8"))

        except IOError:
            self.game_state = gamestate.GameState()

    def parse_cctg_data(self, client_list, client, data=""):
        print "Received \'{}\'!".format(data.strip("\n"))
        self.total_received_messages.append(data)

        if data == "":
            return client_list

        if data.upper().startswith("IPS "):
            for ip in data.split(" ")[1:]:
                new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                new_sock.connect((ip.split(":")[0], ip.split(":")[1]))
                client_list.append({"client": new_sock, "ip": ip.split(":")[0], "port": ip.split(":")[1]})
                socketeer.send_to_socket(client, "CONNECTEDTO " + ip + "\n")
            socketeer.send_to_socket(client, "CONNECTIONSDONE\n")

        if data.upper() == "IAMHOST":
            if self.network_host == "":
                socketeer.send_to_socket(client, "HOST ACCEPTED\n")

            else:
                socketeer.send_to_socket(client, "HOST REJECTED\n")

            self.network_host = client.getsockname()[0]

        if data.upper() == "GAMESTATE START":
            self.parser_state = "READING_GAME_STATE"
            socketeer.send_to_socket(client, self.parser_state + "\n")

        if data.upper() == "GETPARSERSTATE":
            socketeer.send_to_socket(client, self.parser_state + "\n")

        if self.parser_state == "READING_GAME_STATE":
            if data.upper().startswith("STATE "):
                data_splits = data.split(" ")
                self.game_state.set_game_data("state", data_splits[1], data_splits[2], data_splits[3])
                socketeer.send_to_socket(client, "GOTSDATA {} {} :{}".format(data_splits[1], data_splits[2],
                                                                             data_splits[3]) + "\n")
                return client_list

            elif data.upper().startswith("SUPERSTATE "):
                if client.getsockname()[0] != self.network_host:
                    socketeer.send_to_socket(client, "ERR PERMISSION_DENIED\n")

                data_splits = data.split(" ")
                self.game_state.set_game_data("superstate", data_splits[1], data_splits[2], data_splits[3])
                socketeer.send_to_socket(client, "GOTSSDATA {} {} :{}".format(data_splits[1], data_splits[2],
                                                                              data_splits[3]) + "\n")
                return client_list

            elif data.upper().startswith("USER "):
                data_splits = data.split(" ")
                self.game_state.set_game_data("user", data_splits[2], data_splits[3], data_splits[4], data_splits[1])
                socketeer.send_to_socket(client,
                                         "GOTUDATA {} {} {} :{}".format(data_splits[1], data_splits[2], data_splits[3],
                                                                        data_splits[4]) + "\n")
                return client_list

            elif data.upper() == "GAMESTATE END":
                self.parser_state = ""
                socketeer.send_to_socket(client, "GAMESTATECLIENT END\n")
                return client_list

            else:
                socketeer.send_to_socket(client, "ERR INVALID_GAMESTATE_CMD\n")

        if data.upper().startswith("GETSTATEDATA "):
            try:
                data_name = data.split(" ")[1]

            except IndexError:
                socketeer.send_to_socket(client, "ERR NOT_ENOUGH_ARGUMENTS\n")
                return client_list

            if data_name not in self.game_state.game_data:
                socketeer.send_to_socket(client, "ERR STATE_DATA_NOT_FOUND\n")

            game_data = self.game_state.get_game_data(data_name)

            socketeer.send_to_socket(client, "STATEDATA {} {} {} {}".format(
                game_data["scope"] + (" " + game_data["client_ip"] if game_data["client_ip"] == "user" else ""),
                game_data["name"],
                game_data["type"],
                game_data["content"]
            ) + "\n")

        if data.startswith("STATEDATA "):
            data_splits = data.split(" ")[1:]

            if data_splits[0].lower() == "state":
                self.game_state.set_game_data("state", data_splits[1], data_splits[2], data_splits[3])
                socketeer.send_to_socket(client, "GOTSDATA {} {} :{}".format(data_splits[1], data_splits[2],
                                                                             data_splits[3]) + "\n")

            elif data_splits[0].lower() == "":
                self.game_state.set_game_data("user", data_splits[1], data_splits[2], data_splits[3], data_splits[4])
                socketeer.send_to_socket(client, "GOTUDATA {} {} :{}".format(data_splits[1], data_splits[2],
                                                                             data_splits[3] + "\n"),
                                         data_splits[4])

            else:
                socketeer.send_to_socket(client, "ERR INVALID_GAMESTATE_CMD\n")

        if data.startswith("TERMINATINGCLIENT "):
            ip, port = data.split(" ")[1:]

            for index, client in enumerate(client_list):
                if (client["ip"], client["port"]) == (ip, port):
                    client_list.pop(index)

        return client_list
