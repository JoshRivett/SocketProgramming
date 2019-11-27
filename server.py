import socket
import select

IP = "127.0.0.1"
PORT = 2000
BUFFER_SIZE = 50

srvr_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

srvr_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

srvr_soc.bind((IP, PORT))

srvr_soc.listen()

socs_list = [srvr_soc]

clients = {}

print(f'Listening for connections on {IP}:{PORT}...')

def recv_msg(client_soc):

    try:
        msg_hdr = client_soc.recv(BUFFER_SIZE)

        if not len(msg_hdr):
            return False

        msg_len = int(msg_hdr.decode('utf-8').strip())

        return {'header': msg_hdr, 'data': client_soc.recv(msg_len)}

    except:
        return False

while True:
    read_socs, _, exception_socs = select.select(socs_list, [], socs_list)

    for notified_soc in read_socs:
        if notified_soc == srvr_soc:
            client_soc, client_addr = srvr_soc.accept()

            user = recv_msg(client_soc)

            if user is False:
                continue

            socs_list.append(client_soc)

            clients[client_soc] = user

            print('Accepted new connection from {}:{}, username: {}'.format(*client_addr, user['data'].decode('utf-8')))

        else:
            msg = recv_msg(notified_soc)

            if msg_hdr is False:
                print('Closed connection from: {}'.format(clients[notified_soc]['data'].decode('utf-8')))

                socs_list.remove(notified_soc)

                del clients[notified_soc]

                continue

            user = clients[notified_soc]

            print(f'Received message from {user["data"].decode("utf-8")}: {msg["data"].decode("utf-8")}')

            for client_soc in clients:
                if client_soc != notified_soc:
                    client_soc.send(user['header'] + user['data'] + msg['header'] + msg['data'])

    for notified_soc in exception_socs:
        socs_list.remove(notified_soc)
        del clients[notified_soc]
