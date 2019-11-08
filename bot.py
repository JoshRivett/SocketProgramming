import socket

ircSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server = "192.168.0.53"         # Server ip address
port = 6667                     # The server's port
channel = "#1"                  # Channel to join
botNick = "IamaPythonBot"       # The nickname of the bot
adminName = "Josh"              # My IRC nickname
exitcode = "bye " + botNick     # Code used to end the bot script

# Connects to the server and port specified and sets the bot's username/name
ircSock.connect((server, port))
ircSock.send(bytes("USER " + botNick + " " + botNick + " " + botNick + " " + botNick + "n", "UTF-8"))
ircSock.send(bytes("NICK " + botNick + "n", "UTF-8"))


# Respond to pings from the server
def ping():
    ircSock.send(bytes("PONG :pingisn", "UTF-8"))


# Function to join channels
def joinchannel(chan):
    ircSock.send(bytes("JOIN " + chan + "n", "UTF-8"))
    ircmsg = ""
    while ircmsg.find("End of /NAMES list.") == -1:
        ircmsg = ircSock.recv(2048).decode("UTF-8")
        ircmsg = ircmsg.strip('nr')
        print(ircmsg)


# Sends a message to the target
def sendmsg(msg, target=channel):
    ircSock.send(bytes("PRIVMSG " + target + " :" + msg + "n", "UTF-8"))


# Main method of the program
def main():
    joinchannel(channel)
    while 1:
        ircmsg = ircSock.recv(2048).decode("UTF-8")
        ircmsg = ircmsg.strip('nr')
        print(ircmsg)

        if ircmsg.find("PRIVMSG") != -1:
            name = ircmsg.split('!', 1)[0][1:]
            message = ircmsg.split('PRIVMSG', 1)[1].split(':', 1)[1]

            if len(name) < 17:
                if message.find('Hi ' + botNick) != -1:
                    sendmsg("Hello " + name + "!")
                if message[:5].find('.tell') != -1:
                    target = message.split(' ', 1)[1]
                    if target.find(' ') != -1:
                        message = target.split(' ', 1)[1]
                        target = target.split(' ')[0]
                    else:
                        target = name
                        message = "Could not parse." \
                                  "The message should be in the format of '.tell [target] [message]' to work properly."
                    sendmsg(message, target)

            if name.lower() == adminName.lower() and message.rstrip() == exitcode:
                sendmsg("See ya!")
                ircSock.send(bytes("QUIT n", "UTF-8"))
                return
        else:
            if ircmsg.find("PING :") != -1:
                ping()


main()
