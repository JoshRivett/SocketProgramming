# Sources:
# https://www.techbeamers.com/create-python-irc-bot/
# https://www.w3resource.com/python-exercises/python-basic-exercise-3.php
# https://www.guru99.com/reading-and-writing-files-in-python.html
# https://stackoverflow.com/questions/8380389/how-to-get-day-name-in-datetime-in-python
# https://machinelearningmastery.com/how-to-generate-random-numbers-in-python/

from irc_class import *
from os import path
from random import seed
from random import randint
import datetime

# Global variables
config = "config.ini"           # The location of the configuration file
messageList = "messages.txt"    # The location of the messages file

# If the config file exists, read in the stored values
if path.exists(config):
    file = open(config, "r")
    lines = file.readlines()
    server = lines[0].split(': ')[1].rstrip()
    port = int(lines[1].split(': ')[1])
    username = lines[2].split(': ')[1].rstrip()
    botnick = lines[3].split(': ')[1].rstrip()
    mode = int(lines[4].split(': ')[1])
    realname = lines[5].split(': ')[1].rstrip()
    channel = lines[6].split(': ')[1].rstrip()


# Otherwise, create the file and request the values from the user
else:
    print("Config file missing!")
    file = open(config, "w+")

    server = input("Enter server IP address: ")
    file.write("Server IP: " + server + "\n")

    # Gets a valid port
    port = -1
    while port < 0:
        try:
            port = int(input("Enter port: "))
            if port < 0:
                print("Invalid port! Must be a positive value.")
        except ValueError:
            print("Invalid port! Must be an integer value.")
    file.write("Port: " + str(port) + "\n")

    username = input("Enter bot username: ")
    file.write("Username: " + username + "\n")

    botnick = input("Enter bot nickname: ")
    file.write("Botnick: " + botnick + "\n")

    # Gets a valid mode
    try:
        mode = int(input("Enter mode: "))
    except ValueError:
        print("Invalid mode! Must be an integer value.")
    file.write("Mode: " + str(port) + "\n")

    realname = input("Enter bot realname: ")
    file.write("Realname: " + realname + "\n")

    channel = input("Enter channel: ")
    file.write("Channel: " + channel + "\n")

# File reading/writing is done
file.close()

# Connect to the server using the provided parameters
irc = IRC()
irc.connect(server, port, username, botnick, mode, realname, channel)

# Main loop of the bot
while True:
    text = irc.get_response()
    print(text)

    # Checks for commands sent in the chat (should start with a '!')
    if "PRIVMSG " + channel in text and "!" in text:
        if "!hello" in text:
            print("hello")
            irc.send(channel, "Hello!")
        if "!time" in text:
            now = datetime.datetime.now()
            irc.send(channel, "It is currently " + now.strftime("%H:%M:%S"))
        if "!date" in text:
            now = datetime.datetime.now()
            irc.send(channel, "Today's date is " + now.strftime("%d/%m/%Y"))
        if "!day" in text:
            now = datetime.datetime.now()
            irc.send(channel, "Today is " + now.strftime("%A"))
    # Checks for private messages sent directly to the bot
    elif "PRIVMSG " + botnick in text:
        # Gets the name of the user who messaged the bot
        user = text.split('!')[0].strip(':')
        # Sets a default message in case of no/empty file
        message = "Hello!"

        # If the messages file exists, read in its values
        if path.exists(messageList):
            file = open(messageList, "r")
            lines = file.readlines()
            file.close()

            # If the file isn't empty, select a random response
            if len(lines) != 0:
                seed()
                lineNum = randint(0, len(lines)-1)
                message = lines[lineNum]
            else:
                print("BOT: Messages file is empty!")

        # Otherwise, generate a file and use a default response
        else:
            print("Messages file is missing!")
            print("Creating file with default response...")
            file = open(messageList, "w+")
            file.write(message + "\n")
            file.close()

        # Sends the message to the user
        irc.send(user, message)
