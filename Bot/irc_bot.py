# Sources:  https://www.techbeamers.com/create-python-irc-bot/
#           https://www.w3resource.com/python-exercises/python-basic-exercise-3.php
#           https://www.guru99.com/reading-and-writing-files-in-python.html

from irc_class import *
from os import path
import datetime

# Global variables
config = "config.ini"   # The location of the configuration file

# If the config file exists, read in the stored values
if path.exists(config):
    file = open(config, "r")
    lines = file.readlines()
    server = lines[0].split(': ')[1].rstrip()
    port = int(lines[1].split(': ')[1])
    channel = lines[2].split(': ')[1].rstrip()
    botnick = lines[3].split(': ')[1].rstrip()
    botnickpass = lines[4].split(': ')[1].rstrip()
    botpass = lines[5].split(': ')[1].rstrip()

# Otherwise, create the file and request the values from the user
else:
    print("Config file missing!")
    file = open(config, "w+")

    server = input("Enter server IP address: ")
    file.write("Server IP: " + server + "\n")

    port = int(input("Enter port: "))
    file.write("Port: " + str(port) + "\n")

    channel = input("Enter channel: ")
    file.write("Channel: " + channel + "\n")

    botnick = input("Enter bot nickname: ")
    file.write("Botnick: " + botnick + "\n")

    botnickpass = "netBot"
    file.write("Botnickpass: " + botnickpass + "\n")

    botpass = "<%= @bot123 %>"
    file.write("Botpass: " + botpass + "\n")

# Connect to the server using the provided parameters
irc = IRC()
irc.connect(server, port, channel, botnick, botpass, botnickpass)

# Main loop of the bot
while True:
    text = irc.get_response()
    print(text)

    # Checks for commands sent in the chat (should start with a '!')
    if "PRIVMSG" in text and channel in text and "!" in text:
        if "!hello" in text:
            irc.send(channel, "Hello!")
        if "!time" in text:
            now = datetime.datetime.now()
            irc.send(channel, "It is currently " + now.strftime("%H:%M:%S"))
        if "!date" in text:
            now = datetime.datetime.now()
            irc.send(channel, "Today's date is " + now.strftime("%d/%m/%Y"))
