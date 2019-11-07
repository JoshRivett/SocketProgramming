import socket
s=socket.socket(type=socket.SOCK_STREAM)
s.bind(('127.0.0.1', 80))
s.listen(5)
while True:
    # accept connections from outside
    (clientsocket, address) = s.accept()
    # now do something with the clientsocket
    # in this case, we'll pretend this is a threaded server
    #ct = client_thread(clientsocket)
    #ct.run()
    with clientsocket:
        print('Connected by', address)
        while True:
            data = clientsocket.recv(1024)
            #print(data)
            name=address[0]
            datastr= data.decode("utf-8") 
            print(name+ " : "+datastr)
            if not data:
                break
            clientsocket.sendall(data)
