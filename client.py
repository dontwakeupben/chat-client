import socket
import threading
import sys
import os


HOST = "192.168.88.22" 
PORT = 12345

username = input("Enter your username: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))


input_active = False


# Receive messages from server
def receive():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message == "USERNAME":
                client.send(username.encode('utf-8'))
            else:
                # Clear current line and print message
                if input_active:
                    # Move cursor to beginning of line and clear it
                    print('\r' + ' ' * 50 + '\r', end='', flush=True)
                
                print(message, flush=True)
                
                # Restore input prompt if input was active
                if input_active:
                    print(f"[{username}]: ", end='', flush=True)
        except:
            print("\nDisconnected from server.")
            client.close()
            break


# Send messages to server
def write():
    global input_active
    while True:
        try:
            input_active = True
            print(f"[{username}]: ", end='', flush=True)
            message = input("")
            input_active = False
            
            if message.lower() == '/quit':
                client.close()
                break
            

            client.send(f"[{username}]: {message}".encode('utf-8'))
        except KeyboardInterrupt:
            print("\nExiting...")
            client.close()
            break
        except:
            print("Error sending message.")
            client.close()
            break


# Start threads
print("Connected to chat server. Type '/quit' to exit.")
print("=" * 50)

receive_thread = threading.Thread(target=receive)
receive_thread.daemon = True  # Dies when main thread dies
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.daemon = True
write_thread.start()

try:
    write_thread.join()
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    client.close()
