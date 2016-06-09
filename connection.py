import socket
import sys
import time
from threading import Thread

import dataparser


class CCT(object):
    def __init__(self, ips, host, game_name=""):
        self.client_list = []
        self.ip_bans = []
        self.num_connections = 0
        self.parser = dataparser.CCTGParser(game_name)
        self.start_time = time.time()
        self.host = host

        ip_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip_socket.connect(('google.com', 0))

        self.our_ip, self.our_port = ip_socket.getsockname()[0], ip_socket.getsockname()[1]

        print "Starting connections: " + " ".join(ips)

        for x in ips:
            self.num_connections += 1

            try:
                ip = x.split(":")[0]
                port = int(x.split(":")[1])

            except IndexError:
                continue

            self.add_connection(ip, port)

        print "Doing listening loop!"

        self.listening_loop()

    def add_connection(self, ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        client_index = len(self.client_list)
        self.client_list.append({"client": sock, "ip": ip, "port": port})
        Thread(name="Connection {}".format(client_index + 1), target=self.connection_loop, args=(client_index,))

    def listening_loop(self):
        listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listening_socket.bind((self.our_ip, self.our_port))
        listening_socket.listen(2)

        while True:
            (client, (ip, port)) = listening_socket.accept()

            if ip in self.ip_bans:
                client.sendall("ERR BANNED_CLIENT\n")
                continue

            self.client_list.append({"client": client, "ip": ip, "port": port})

            client.sendall("IPS " + " ".join([":".join((x["ip"], x["port"])) for x in self.client_list]) + "\n")

            if self.host:
                client.sendall("IAMHOST")

            client.sendall("GAMESTATE START\n")
            client.sendall("\n".join(["{} {} {} {}".format(
                game_data["scope"] + (" " + game_data["client_ip"] if game_data["client_ip"] == "user" else ""),
                game_data["name"],
                game_data["type"],
                game_data["content"]
            ) for game_data in self.parser.game_state.game_data.values()]))

    def connection_loop(self, client_index):
        try:
            while True:
                try:
                    client_dict = self.client_list[client_index]

                except KeyError:
                    return

                raw = ""

                while True:
                    try:
                        raw += client_dict["client"].recv(4096)

                    except socket.error:
                        continue

                    if not raw.endswith("\n"):
                        continue

                for data in raw.split("\n"):
                    self.client_list = self.parser.parse_cctg_data(self.client_list, client_dict["client"], data)

        finally:
            return

    def __del__(self):
        for client in self.client_list:
            client["client"].sendall("TERMINATINGCLIENT {} {}".format(self.our_ip, self.our_port))


if __name__ == "__main__":
    print "Starting connections!"
    if sys.argv[1].upper() == "HOST":
        CCT(sys.argv[3:], False, sys.argv[2])

    else:
        CCT(sys.argv[1:], False)
