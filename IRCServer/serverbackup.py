import socket
import select
import errno
from class_client import *

HEADER_LENGTH = 20
IP = "127.0.0.1"
PORT = 1234

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))
server_socket.listen()

sockets_list = [server_socket]

clients = {}

commands = {
    "USER",
    "NICK",
}


def receive_message(client_socket):
    try:
        rawMessage = client_socket.recv(256)

        if len(rawMessage) == 0:
            return False

        messages = rawMessage.decode("utf-8").strip().split("\n")

        buffer = len(messages)
        print("Received " + str(len(messages)) + " messages.")

        i = 0
        while i < buffer:
            print(messages[i])
            msg = messages[i].split(" ")
            command = msg[0]

            if command not in commands:
                print("Unknown command: " + command)
                return False
            elif command == "NICK":
                print("Do command nick")
            elif command == "USER":
                print("Do command user")

            i += 1

        return {"command": command, "data": msg}

    except Exception as e:
        print("Exception: " + str(e))
        return False


while True:
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            client_socket, client_address = server_socket.accept()
            print("Receiving new connection from " + str(client_address[0]) + ":" + str(client_address[1]) + "...")

            user = receive_message(client_socket)

            if user is False:
                print("Connection failed.")
                continue

            sockets_list.append(client_socket)

            clients[client_socket] = Client("")

            print(f"Accepted new connection from {client_address[0]}:{client_address[1]} "
                  f"username:{user['data']}")

        else:
            message = receive_message(notified_socket)

            if message is False:
                print(f"Closed connection from {clients[notified_socket]['data']}")
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue

            user = clients[notified_socket]
            print(f"Received message from {user['data']}: {message['data']}")

            for client_socket in clients:
                if client_socket != notified_socket:
                    client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]
