import socket
import threading


HOST = '0.0.0.0'  
PORT = 12345      

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []   
usernames = {} 



def broadcast(message, sender_socket=None):
    print(message.decode('utf-8'))
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message)
            except:
                remove_client(client, broadcast_departure=False)



def broadcast_user_count():
    user_count_message = f"USER_COUNT:{len(clients)}\n".encode('utf-8')
    for client in clients:
        try:
            client.send(user_count_message)
        except:
            remove_client(client, broadcast_departure=False)



def handle_client(client):
    while True:
        try:
            message = client.recv(1024)
            if not message:
                break
            broadcast(message, sender_socket=client)
        except:
            break
    remove_client(client)



def remove_client(client, broadcast_departure=True):
    try:
        if client in clients:
            username = usernames.get(client, "Unknown")
            print(f"[DISCONNECT] {username} left the chat.")
            if broadcast_departure:
                broadcast(f"{username} has left the chat.\n".encode('utf-8'))
            clients.remove(client)
            usernames.pop(client, None)

            broadcast_user_count()
        

        try:
            client.close()
        except:
            pass  
    except Exception as e:

        print(f"[ERROR] Error removing client: {e}")

        try:
            client.close()
        except:
            pass



def start():
    print(f"[STARTING] Server running on {HOST}:{PORT}")
    while True:
        client, address = server.accept()
        print(f"[NEW CONNECTION] {address} connected.")


        client.send("USERNAME".encode('utf-8'))
        username = client.recv(1024).decode('utf-8')
        usernames[client] = username
        clients.append(client)

        print(f"[USERNAME SET] {username} joined the chat.")
        broadcast(f"{username} has joined the chat!\n".encode('utf-8'),sender_socket=client)
        

        broadcast_user_count()

        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()


start()
