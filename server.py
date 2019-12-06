import socket
import select
import time
import re

class Channel(object):
    def __init__(self, server, name):
        self.name = name
        self.server = server
        self.members = {}
        self.topic = ""

    def add_member(self, client):
        self.members[client] = client

    def remove_client(self, client):
        del self.members[client]

        if not self.members:
            self.server.remove_channel(self)

    def get_topic(self):
        return self.topic

class Client(object):
    def __init__(self, client_socket, server):
        self.channels = {}
        self.nick = None
        self.realname = None
        self.server = server
        self.socket = client_socket
        self.host, self.port = client_socket.getpeername()
        self.hostname = socket.getfqdn(self.host)
        self.recv_buffer = ""
        self.write_buffer = ""
        self.user = None
        self.time = time.time()
        self.command = self.reg_handler
        self.ping_sent = False
        self.lines_regexp = re.compile(r"\r?\n")

    def read_socket(self):
        read_data = self.socket.recv(1024)
        self.recv_buffer += read_data.decode("UTF-8")
        self.parse_recv_buffer()

    def write_socket(self):
        try:
            sent = self.socket.send(self.write_buffer.encode())
            self.write_buffer = self.write_buffer[sent:]
        except socket.error:
            self.disconnect("socket write error")

    def check_ping_pong(self):
        now = time.time()

        if self.time + 180 < now:
            self.disconnect("ping timeout")
            return

        if not self.ping_sent and self.time + 90 < now:
            if self.command == self.command_handler:
                self.msg("PING :%s" % self.server.name)
                self.ping_sent = True
            else:
                self.disconnect("ping timeout")

    def parse_recv_buffer(self):
        lines = self.lines_regexp.split(self.recv_buffer)
        self.recv_buffer = lines[-1]
        lines = lines[0:-1]

        for line in lines:
            if not line:
                continue

            print(line)

            l = line.split(" ", 1)
            command = l[0].upper()

            if len(l) == 1:
                args = []
            else:
                if len(l[1]) > 0 and l[1][0] == ":":
                    args = [l[1][1:]]
                else:
                    k = l[1].split(" :", 1)
                    args = k[0].split()
                    if len(k) == 2:
                        args.append(k[1])

            self.command(command, args)


    def reg_handler(self, command, args):
        server = self.server

        if command == "NICK":
            if len(args) < 1:
                self.reply("431 :No nickname given")
                return

            nick = args[0]

            if server.get_client(nick):
                self.reply("433 %s :Nickname is already in use" % nick)
            else:
                self.nick = nick
                server.client_changed_nickname(self, None)
        elif command == "USER":
            if len(args) < 4:
                self.reply461("USER")
                return

            self.user = args[0]
            self.realname = args[3]
        elif command == "QUIT":
            self.disconnect("Client quit")
            return

        if self.nick and self.user:
            self.reply("001 %s :Hi, welcome to IRC" % self.nick)
            self.reply("002 %s :Your host is %s, running version miniircd-1.3"% (self.nick, self.server.name))
            self.reply("003 %s :This server was created sometime" % self.nick)
            self.reply("004 %s %s miniircd-1.3 o o" % (self.nick, self.server.name))

            self.command = self.command_handler

    def send(self, args, for_join=False):
        server = self.server

        if len(args) > 0:
            chan_names = args[0].split(",")
        else:
            chan_names = sorted(self.channels.keys())
        if len(args) > 1:
            keys = args[1].split(",")
        else:
            keys = []

        keys.extend((len(chan_names) - len(keys)) * [None])

        for (i, chan_name) in enumerate(chan_names):
            if for_join and chan_name in self.channels:
                continue

            chan = server.get_chan(chan_name)

            if for_join:
                chan.add_member(self)
                self.channels[chan_name] = chan
                self.msg_chan(chan, "JOIN", chan_name, True)

                if chan.topic:
                    self.reply("332 %s %s :%s" % (self.nick, chan.name, chan.topic))
                else:
                    self.reply("331 %s %s :No topic is set" % (self.nick, chan.name))

            names_prefix = "353 %s = %s :" % (self.nick, chan_name)
            names = ""
            max_len = 512 - (len(server.name) + 2 + 2)

            for name in sorted(x.nick for x in chan.members):
                if not names:
                    names = names_prefix + name
                elif len(names) + len(name) >= max_len:
                    self.reply(names)
                    names = names_prefix + name
                else:
                    names += " " + name

            if names:
                self.reply(names)

            self.reply("366 %s %s :End of NAMES list"% (self.nick, chan_name))

    def command_handler(self, command, args):
        def join_handler():
            if len(args) < 1:
                self.reply461("JOIN")
                return

            if args[0] == "0":
                for (chan_name, chan) in self.channels.items():
                    self.msg_chan(chan, "PART", chan_name, True)
                    server.remove_from_chan(self, chan_name)
                self.channels = {}
                return

            self.send(args, for_join=True)

        def nick_handler():
            if len(args) < 1:
                self.reply("431 :No nickname given")
                return

            new_nick = args[0]
            client = server.get_client(new_nick)

            if new_nick == self.nick:
                pass
            elif client and client is not self:
                self.reply("433 %s %s :Nickname is already in use" % (self.nick, new_nick))
            else:
                old_nick = self.nick
                self.nick = new_nick
                server.client_changed_nickname(self, old_nick)

        def privmsg_handler():
            if len(args) == 0:
                self.reply("411 %s :No recipient given (%s)" % (self.nick, command))
                return

            if len(args) == 1:
                self.reply("412 %s :No text to send" % self.nick)
                return

            target_name = args[0]
            msg = args[1]

            client = server.get_client(target_name)

            if client:
                client.msg(":%s %s %s :%s" % (self.nick, command, target_name, msg))
            elif server.has_chan(target_name):
                chan = server.get_chan(target_name)
                self.msg_chan(chan, command, "%s :%s" % (chan.name, msg))
            else:
                self.reply("401 %s %s :No such nick/channel" % (self.nick, target_name))

        def part_handler():
            if len(args) < 1:
                self.reply461("PART")
                return

            if len(args) > 1:
                msg = args[1]
            else:
                msg = self.nick

            for chan_name in args[0].split(","):
                chan_name.strip("#")

                if not chan_name in self.channels:
                    self.reply("422 %s %s :You're not on that channel" % (self.nick, chan_name))
                else:
                    chan = self.channels[chan_name]
                    self.msg_chan(chan, "PART", "%s :%s" % (chan_name, msg), True)
                    del self.channels[chan_name]
                    server.remove_from_chan(self, chan_name)

        def ping_handler():
            if len(args) < 1:
                self.reply("409 %s :No origin specified" % self.nick)
                return

            self.reply("PONG %s :%s" % (server.name, args[0]))

        def pong_handler():
            pass

        def quit_handler():
            if len(args) < 1:
                msg = self.nick
            else:
                msg = args[0]

            self.disconnect(msg)

        def topic_handler():
            if len(args) < 1:
                self.reply461("TOPIC")
                return

            chan_name = args[0]
            chan = self.channels.get(chan_name)

            if chan:
                if len(args) > 1:
                    new_topic = args[1]
                    channel.topic = new_topic
                    self.msg_chan(chan, "TOPIC", "%s :%s" % (chan_name, new_topic), True)
                else:
                    if channel.topic:
                        self.reply("322 %s %s :%s" % (self.nick, chan_name, channel.topic))
                    else:
                        self.reply("311 %s %s :No topic is set" % (self.nick, channel.topic))
            else:
                self.reply("422 %s :You're not on that channel" % chan_name)

        handlers = {
            "JOIN": join_handler,
            "NICK": nick_handler,
            "PRIVMSG": privmsg_handler,
            "PART": part_handler,
            "PING": ping_handler,
            "PONG": pong_handler,
            "QUIT": quit_handler,
            "TOPIC": topic_handler,
        }
        server = self.server
        try:
            handlers[command]()
        except KeyError:
            self.reply("421 %s %s :Unknown command" % (self.nick, command))

    def disconnect(self, msg):
        self.msg("ERROR :%s" % msg)
        self.reply("QUIT :Disconnected connection from %s:%s (%s)." % (self.host, self.port, msg))
        self.socket.close()
        self.server.remove_client(self, msg)

    def msg(self, mes):
        self.write_buffer += mes + "\r\n"
        print(">>>" + mes)

    def reply(self, msg):
        self.msg(":%s %s" % (self.nick, msg))

    def reply461(self, command):
        nick = self.nick or "*"
        self.reply("461 %s %s :Not enough parameters" % (nick, command))

    def msg_chan(self, chan, command, msg, include_self=False):
        line = ":%s!%s@%s %s %s" % (self.nick, self.user, self.hostname, command, msg)

        for client in chan.members.values():
            if client != self or include_self:
                client.msg(line)

class Server(object):
    def __init__(self, name):
        self.channels = {}
        self.clients = {}
        self.name = name
        self.host = socket.getfqdn(socket.gethostname())
        self.nicks = {}
        self.recv_buffer = ""
        self.lines_regexp = re.compile(r"\r?\n")

    def get_client (self, nick):
        return self.nicks.get(nick)

    def has_chan(self, name):
        return name in self.channels

    def get_chan(self, chan_name):
        if chan_name in self.channels.values():
            chan = self.channels[chan_name]
        else:
            chan = Channel(self, chan_name)
            self.channels[chan_name] = chan

        return chan

    def client_changed_nickname(self, client, old_nick):
        if old_nick:
            del self.nicks[old_nick]

        self.nicks[client.nick] = client

    def remove_from_chan(self, client, chan_name):
        if chan_name in self.channels:
            channel = self.channels[chan_name]
            channel.remove_client(client)

    def remove_client(self, client, msg):
        for c in client.channels.values():
            c.remove_client(client)

        if client.nick in self.nicks:
            del self.nicks[client.nick]

        del self.clients[client.socket]

    def remove_channel(self, chan):
        chan = chan.name.strip("#")
        del self.channels[chan]

    def start(self):
        soc_list = []
        PORT = 6667
        IP = "127.0.0.1"

        srvr_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srvr_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            srvr_soc.bind((IP, PORT))
        except socket.errror as e:
            print("Couldn't bind port %s:%s" % (PORT, e))
            sys.exit(1)

        srvr_soc.listen()
        soc_list.append(srvr_soc)

        self.run(soc_list)

        del srvr_soc

        print("Listening on port %d." % PORT)

    def run(self, soc_list):
        last_alive = time.time()

        while True:
            read_socs, write_socs, exception_socs = select.select(soc_list, soc_list, soc_list, 2)
            
            for s in read_socs:
                if s not in self.clients:
                    client_soc, client_addr = s.accept()

                    try:
                        self.clients[client_soc] = Client(client_soc, self)
                        soc_list.append(client_soc)
                        print("Accepted new connection from %s:%s." % (client_addr[0], client_addr[1]))
                    except socket.error:
                        try:
                            client_soc.close()
                        except Exception:
                            pass
                else:
                    self.clients[s].read_socket()

            for s in write_socs:
                if s in self.clients:
                    self.clients[s].write_socket()

            for s in exception_socs:
                del s

            now = time.time()
            
            if last_alive + 10 < now:
                for client in list(self.clients.values()):
                    client.check_ping_pong()

                last_alive = now

def main():
    myServer = Server(socket.gethostname())
    myServer.start()

if __name__ == "__main__":
    main()