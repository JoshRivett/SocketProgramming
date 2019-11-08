import socket
s=socket.socket(type=socket.SOCK_STREAM)
s.bind(('127.0.0.1', 80))
s.listen(5)
while True:
    # accept connections from outside
    #address[:1]
    (clientsocket, address) = s.accept()
    
    # now do something with the clientsocket
    # in this case, we'll pretend this is a threaded server
    #ct = client_thread(clientsocket)
    #ct.run()
    with clientsocket:
        print('Connected by', address)
        count=0
        while True:
            data = clientsocket.recv(1024)
            datastr= data.decode("utf-8")
            if count==0:
                namelen=int(datastr[0])
                username=datastr[1:namelen+1]
                message=datastr[namelen+1:]
                count=count+1
                print(username+ " connected!")
            
            else:
                message=datastr
                print(username+ " : "+message)
            name=address[0]
            
            
            if not data:
                break
            clientsocket.sendall(data)
