def send_to_socket(sock, string, encoding="utf-8"):
    bytes_sent = 0

    while True:
        bytes_sent += sock.send(string[bytes_sent:].encode(encoding))

        if bytes_sent > 0:
            continue

        if bytes_sent == -1:
            continue

        return
