import socket
import threading
s=socket.socket(type=socket.SOCK_STREAM)
s.bind(('127.0.0.1', 81))
s.listen(5)
connections=[]

def conncheck():
    (clientsocket, address) = s.accept()


def main(a, b, callback = None):
    print("adding {} + {}".format(a, b))
    if callback:
        callback(a+b)

main(1, 2, callback)


#while True:
    # accept connections from outside
    #address[:1]
    (clientsocket, address) = s.accept()
    '''thread=threading.Thread()
    thread.daemon = True
    
    
    thread.start()'''
    connections.append(s)
    print(connections)
    
    
    
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
