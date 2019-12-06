# Sources:
# 1. https://tools.ietf.org/html/rfc2812#section-3.1.5
# 2. https://github.com/jrosdahl/miniircd/blob/master/miniircd
# 3. https://www.youtube.com/watch?v=CV7_stUWvBQ

# Imports required libraries
import socket
import select
import time
import datetime
from class_client import *
from class_channel import *

# Set required constants
IP = "10.0.42.17"
PORT = 6667
SERVER_NAME = "netServer"
VERSION = "1.0"
DATE = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# Initialise server sockets
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))
server_socket.listen()

sockets_list = [server_socket]

# List of clients and channels
clients = {}
channels = {}

# List of available commands
commands = {
    "USER",
    "NICK",
    "JOIN",
    "CAP",
    "MODE",
    "WHO",
    "PRIVMSG",
    "QUIT",
    "PART"
}

# Dictionary of command responses
responses = {
    "RPL_WELCOME": "001",
    "RPL_YOURHOST": "002",
    "RPL_CREATED": "003",
    "RPL_MYINFO": "004",
    "RPL_ENDOFWHO": "315",
    "RPL_NOTOPIC": "331",
    "RPL_WHOREPLY": "352",
    "RPL_NAMREPLY": "353",
    "RPL_ENDOFNAMES": "366"
}


# Send a command response to a client
def send_response(client_socket, response, message):
    client_socket.send(bytes(":" + SERVER_NAME + " " + response + " " + clients[client_socket].username + " :" +
                             message + "\n", "UTF-8"))


# Send message to HexChat (specific format)
def msg_chan(client_socket, chan, command, msg, include_self=False):
    line = ":" + clients[client_socket].nick + "!" + clients[client_socket].username + "@" + IP + " " + command + " " \
           + msg + "\n"

    # Sends the message to all clients except self (unless otherwise specified)
    for client in clients:
        if client != clients[client_socket] or include_self:
            client_socket.send(bytes(line, "UTF-8"))


# Send message to HexChat (specific format)
def reply(client_socket, msg):
    print(msg)
    client_socket.send(bytes(":" + clients[client_socket].nick + " " + msg + "\n", "UTF-8"))


# Handle a USER message
def user_message(client_socket, data):
    if client_socket not in clients:
        clients[client_socket] = Client()
        clients[client_socket].address = str(client_address[0]) + ":" + str(client_address[1])

    # Pull the information from the raw data
    username = data[1]
    mode = data[2]
    realname = data[4].strip(":")

    # Store it within the client class
    clients[client_socket].username = username
    clients[client_socket].mode = mode
    clients[client_socket].realname = realname

    # Sends the welcome message as the user is registered
    send_welcome(client_socket)
    print("Accepted new connection from " + clients[client_socket].address + ", nickname: " +
          clients[client_socket].nick)


# Handle a NICK message
def nick_message(client_socket, data):
    nick = data[1].strip(":").strip("\r")

    # Adds the client socket to the list of clients if it hasn't already been
    if client_socket not in clients:
        clients[client_socket] = Client()
        clients[client_socket].address = str(client_address[0]) + ":" + str(client_address[1])

    # Loops through all users to make sure the nickname isn't already in use
    for users in clients:
        if clients[users].nick == nick:
            send_response(client_socket, responses["ERR_NICKNAMEINUSE"], nick + " :Nickname is already in use")
            return False

    clients[client_socket].nick = nick


# Handle a JOIN message
def join_message(client_socket, data):
    channel = data[1]
    user = clients[client_socket]

    # Checks if the channel already exists and if not, creates it
    if channel not in channels:
        channels[channel] = Channel()

    channels[channel].clients[client_socket] = ""

    # Sends the client the join message for the channel
    client_socket.send(bytes(":" + user.nick + "!" + user.username + "@" + IP + " JOIN " + channel +
                             "\n", "UTF-8"))
    print("Joined channel " + channel)


# Handle a MODE message
def mode_message(client_socket, data):
    channel = data[1]
    send_response(client_socket, responses["RPL_NOTOPIC"], channel + " :No topic is set")


# Handle a WHO message
def who_message(client_socket, data):
    channel = data[1]

    # Checks which clients are connected to the server and informs the client
    for users in channels[channel].clients:
        send_response(client_socket, responses["RPL_NAMREPLY"], "= " + channel + " :" + clients[users].nick)

    send_response(client_socket, responses["RPL_ENDOFNAMES"], "End of NAMES list")

    for users in channels[channel].clients:
        send_response(client_socket, responses["RPL_WHOREPLY"], channel + " " + clients[client_socket].username + " "
                      + IP + " " + SERVER_NAME + " " + clients[users].nick + " H :0 " + clients[users].realname)

    send_response(client_socket, responses["RPL_ENDOFWHO"], channel + " :End of WHO list")


# Handle a PRIVMSG
def private_message(client_socket, data):
    target = data[1]
    print(target)

    # Isolates the actual "message" part of the message (no command/channel)
    msg = " ".join(data).split(":", 1)[1]

    # If the target is a channel
    if "#" in target:
        for users in channels[target].clients:
            if users != client_socket:
                print(clients[users].nick + ":" + clients[users].username)
                users.send(bytes(":" + clients[client_socket].nick + "!" + clients[client_socket].username + "@" + IP +
                                 " PRIVMSG " + target + " :" + msg + "\n", "UTF-8"))
                print(msg)
    # If the target is a user
    else:
        for users in clients:
            if clients[users].nick == target:
                users.send(bytes(":" + clients[client_socket].nick + "!" + clients[client_socket].username + "@" + IP +
                                 " PRIVMSG " + target + " :" + msg + "\n", "UTF-8"))


# Handle a PART message
def part_handler(client_socket, data):
    chan_name = data[1]

    # Checks where or not the client is a member of said channel before removing them
    if not chan_name in channels:
        reply(client_socket, "422" + clients[client_socket].nick + chan_name + ":You're not on that channel")
    else:
        # client_socket, chan, command, msg, include_self=False
        msg_chan(client_socket, chan_name, "PART", chan_name + " :", True)
        remove_from_chan(chan_name, client_socket)
        del channels[chan_name]


# Handle a QUIT message
def quit_message(client_socket):
    disconnect(clients[client_socket].nick)


# Disconnect the client from the server
def disconnect(msg):
    reply(client_socket, "QUIT :Disconnected connection from " + IP + ":" + str(PORT) + "(" + msg + ").")


# Disconnect the client from a channel
def remove_from_chan(chan_name, client_socket):
    if chan_name in channels:
        remove_client(clients[client_socket])


# Remove a client's socket
def remove_client(client_socket):
    if client_socket in clients:
        clients.remove(client_socket)


# The welcome message for after successful user registration
def send_welcome(client_socket):
    send_response(client_socket, responses["RPL_WELCOME"], "Welcome to the Internet Relay Network " +
                 clients[client_socket].nick + "!" + clients[client_socket].username + "@" + IP)
    send_response(client_socket, responses["RPL_YOURHOST"], "Your host is " + SERVER_NAME + ", running "
                                                           "version " + VERSION)
    send_response(client_socket, responses["RPL_CREATED"], "This server was created " + DATE)
    send_response(client_socket, responses["RPL_MYINFO"], SERVER_NAME + " " + VERSION + " o o")


# Receives message(s) from a client
def receive_message(client_socket):
    try:
        # Waits and gets the raw message(s) from the client
        time.sleep(1)
        rawMessage = client_socket.recv(512)

        # Checks if the message is empty
        if len(rawMessage) == 0:
            return False

        # If multiple messages were sent, split them up
        messages = rawMessage.decode("utf-8").strip().split("\n")

        # Checks how many messages were sent
        buffer = len(messages)
        print("Received " + str(len(messages)) + " message(s)")

        # Deals with each message procedurally
        i = 0
        while i < buffer:
            # Finds out what command has been sent
            print(messages[i])
            msg = messages[i].split(" ")
            command = msg[0]

            # Calls the appropriate function (if there is one)
            if command not in commands:
                print("Unknown command: " + command)
            elif command == "NICK":
                nick_message(client_socket, msg)
            elif command == "USER":
                user_message(client_socket, msg)
            elif command == "JOIN":
                join_message(client_socket, msg)
            elif command == "CAP":
                print("Do command cap")
            elif command == "MODE":
                mode_message(client_socket, msg)
            elif command == "WHO":
                who_message(client_socket, msg)
            elif command == "PRIVMSG":
                private_message(client_socket, msg)
            elif command == "QUIT":
                quit_message(client_socket)
            elif command == "PART":
                part_handler(client_socket, msg)

            i += 1

        return

    # Catches any possible exceptions
    except Exception as e:
        print("Exception: " + str(e))
        return False


# Main loop of the program
while True:
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    # Checks for new connections to the server
    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            client_socket, client_address = server_socket.accept()
            print("Receiving new connection from " + str(client_address[0]) + ":" + str(client_address[1]) + "...")
            sockets_list.append(client_socket)

            user = receive_message(client_socket)

            if user is False:
                continue

        else:
            message = receive_message(notified_socket)

            # Failed to receive a message so close the connection
            if message is False:
                print(f"Closed connection from {clients[notified_socket].address}")
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue

            user = clients[notified_socket]

    # Removes and exception sockets
    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]