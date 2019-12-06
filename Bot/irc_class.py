# Sources: https://www.techbeamers.com/create-python-irc-bot/

import socket
import time

errors = {
    "ERR_NICKNAMEINUSE": "433"
}


# Define the IRC class
class IRC:
    irc = socket.socket()

    # Define the socket
    def _init_(self):
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Send message data to the server
    def send(self, channel, msg):
        self.irc.send(bytes("PRIVMSG " + channel + " :" + msg + "\n", "UTF-8"))

    # Connect to a server
    def connect(self, server, port, username, botnick, mode, realname, channel):
        # Connect to the server
        print("Connecting to " + server + ", on port " + str(port) + "...")
        self.irc.connect((server, port))

        # User authentication
        print("Authenticating as '" + username + "'...")
        self.irc.send(bytes("NICK " + botnick + "\n", "UTF-8"))
        self.irc.send(bytes("USER " + username + " " + str(mode) + " * " + ":" + realname + "\n", "UTF-8"))
        resp = self.get_response()
        print(resp)

        if errors["ERR_NICKNAMEINUSE"] in resp:
            self.irc.send(bytes("NICK " + botnick + str(2) + "\n", "UTF-8"))

        # Joins the specified channel
        print("Joining channel: " + channel + "...")
        self.irc.send(bytes("JOIN " + channel + "\n", "UTF-8"))

    # Get response from server
    def get_response(self):
        time.sleep(1)
        resp = self.irc.recv(4096).decode("UTF-8")

        # Responds if the server pings the bot
        if resp.find('PING') != -1:
            self.irc.send(bytes('PONG ' + resp.split()[1] + '\r\n', "UTF-8"))

        return resp
