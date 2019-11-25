# Sources: https://www.techbeamers.com/create-python-irc-bot/

import socket
import time


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
    def connect(self, server, port, channel, botnick, botpass, botnickpass):
        # Connect to the server
        print("Connecting to: " + server)
        self.irc.connect((server, port))

        # User authentication
        self.irc.send(bytes("USER " + botnick + " " + botnick + " " + botnick + " :python\n", "UTF-8"))
        self.irc.send(bytes("NICK " + botnick + "\n", "UTF-8"))
        self.irc.send(bytes("NICKSERV IDENTIFY " + botnickpass + " " + botpass + "\n", "UTF-8"))
        time.sleep(5)

        # Joins the specified channel
        self.irc.send(bytes("JOIN " + channel + "\n", "UTF-8"))

    # Get response from server
    def get_response(self):
        time.sleep(1)
        resp = self.irc.recv(2040).decode("UTF-8")

        if resp.find('PING') != -1:
            self.irc.send(bytes('PONG ' + resp.split()[1] + '\r\n', "UTF-8"))

        return resp
