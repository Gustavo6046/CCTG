import socket

def send_to_socket(sock, string, encoding="utf-8"):
    bytes_sent = 0

    print "Sending {} to some indeterminable socket!".format(string)

    while True:
        try:
            bytes_sent += sock.send(string[bytes_sent:].encode(encoding))

        except socket.error:
            return 1

        if bytes_sent > 0:
            continue

        if bytes_sent == -1:
            continue

        return 0
