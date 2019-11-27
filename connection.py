import socket
import threading

class MySocket:
    """demonstration class only
      - coded for clarity, not efficiency
    """

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(
                            socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host, port):
        self.sock.connect((host, port))

    def mysend(self, m):

        msg=bytes(m, 'utf-8')

        MSGLEN=len(msg)

        totalsent = 0
        while totalsent < MSGLEN:
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def myreceive(self):

        chunks = []
        bytes_recd = 0
        while bytes_recd < MSGLEN:
            chunk = sethread.start_new_thread(on_new_client,(c,addr))
            lf.sock.recv(min(MSGLEN - bytes_recd, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)

    def getusername(self):
        uname=input("Username: ")
        unameLen= len(uname)
        return (str(unameLen),uname)

    def messenger(self):
        mess=input("Enter message: ")
        return mess


call = MySocket()

call.connect('127.0.0.1',2000)
length,username=call.getusername()
call.mysend(length+username)
while True:
    mess=call.messenger()
    call.mysend(mess)
#call.mysend('cat')
