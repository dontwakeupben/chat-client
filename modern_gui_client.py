import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import socket
import threading


# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class ModernChatClient:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Modern Chat Client")
        self.root.geometry("700x600")
        
        # Chat variables
        self.client = None
        self.username = ""
        self.connected = False
        
        self.setup_ui()
        self.setup_connection()
        
    def setup_ui(self):
        # Configure grid weight
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(self.root, text="Chat Room", 
                                  font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # Chat display area with frame
        chat_frame = ctk.CTkFrame(self.root)
        chat_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        chat_frame.grid_columnconfigure(0, weight=1)
        chat_frame.grid_rowconfigure(0, weight=1)
        
        # Scrollable text area for messages
        self.chat_text = ctk.CTkTextbox(chat_frame, font=ctk.CTkFont(size=13))
        self.chat_text.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        # Make chat box read-only
        self.chat_text.configure(state="disabled")
        
        # Message input frame
        input_frame = ctk.CTkFrame(self.root)
        input_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Message entry and send button
        self.message_entry = ctk.CTkEntry(input_frame, placeholder_text="Type your message here...",
                                         font=ctk.CTkFont(size=14), height=40)
        self.message_entry.grid(row=0, column=0, padx=(15, 10), pady=15, sticky="ew")
        self.message_entry.bind('<Return>', self.send_message)
        
        self.send_button = ctk.CTkButton(input_frame, text="Send", command=self.send_message,
                                        font=ctk.CTkFont(size=14, weight="bold"), 
                                        height=40, width=100)
        self.send_button.grid(row=0, column=1, padx=(0, 15), pady=15)
        
        # Reconnect button (initially hidden)
        self.reconnect_button = ctk.CTkButton(input_frame, text="🔄 Reconnect", command=self.manual_reconnect,
                                             font=ctk.CTkFont(size=14, weight="bold"), 
                                             height=40, width=120, fg_color="#27ae60", hover_color="#229954")
        # Don't grid it initially - it will be shown when disconnected
        
        # Status frame
        status_frame = ctk.CTkFrame(self.root)
        status_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.status_label = ctk.CTkLabel(status_frame, text="🔴 Not connected", 
                                        font=ctk.CTkFont(size=12))
        self.status_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        # Online users label (placeholder for future feature)
        self.users_label = ctk.CTkLabel(status_frame, text="👥 Users: 0", 
                                       font=ctk.CTkFont(size=12))
        self.users_label.grid(row=0, column=1, padx=15, pady=10, sticky="e")
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Disable input initially
        self.message_entry.configure(state="disabled")
        self.send_button.configure(state="disabled")
        
    def manual_reconnect(self):
        """Manually trigger reconnection"""
        # Hide reconnect button and cancel auto-reconnect
        self.reconnect_button.grid_remove()
        self.send_button.grid(row=0, column=1, padx=(0, 15), pady=15)
        
        # Clear any pending auto-reconnect
        # (We can't easily cancel the after() call, but return_to_connection will handle being called multiple times)
        
        # Immediately return to connection
        self.return_to_connection()
        
    def setup_connection(self):
        while True:  # Keep trying until successful connection or user cancels
            # Get connection details
            dialog = ModernConnectionDialog(self.root)
            self.root.wait_window(dialog.dialog)
            
            if dialog.result:
                host, port, username = dialog.result
                self.username = username
                if self.connect_to_server(host, port):
                    break  # Connection successful, exit loop
                # If connection failed, loop will restart and show dialog again
            else:
                self.root.quit()
                break
            
    def connect_to_server(self, host, port):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((host, int(port)))
            
            # Handle initial USERNAME request immediately
            initial_message = self.client.recv(1024).decode('utf-8')
            if initial_message == "USERNAME":
                self.client.send(self.username.encode('utf-8'))
                print(f"[GUI CLIENT] Sent username: {self.username}")
            
            self.connected = True
            
            # Start receiving thread after handling initial exchange
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            
            self.status_label.configure(text=f"🟢 Connected as {self.username}")
            self.message_entry.configure(state="normal")
            self.send_button.configure(state="normal")
            self.message_entry.focus()
            
            self.add_message("🎉 Welcome to the chat room!", "system")
            return True  # Connection successful
            
        except Exception as e:
            # Show error message but don't quit the application
            messagebox.showerror("Connection Error", 
                               f"Failed to connect to {host}:{port}\n\nError: {str(e)}\n\nPlease check the server details and try again.")
            print(f"[GUI CLIENT] Connection failed: {e}")
            return False  # Connection failed
            
    def receive_messages(self):
        while self.connected:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message == "USERNAME":
                    # This shouldn't happen after initial connection, but handle it just in case
                    self.client.send(self.username.encode('utf-8'))
                    print(f"[GUI CLIENT] Re-sent username: {self.username}")
                elif message.startswith("USER_COUNT:"):
                    # Handle user count update
                    user_count = message.split(":")[1].strip()
                    self.users_label.configure(text=f"👥 Users: {user_count}")
                    print(f"[GUI CLIENT] User count updated: {user_count}")
                elif message:
                    print(f"[GUI CLIENT] Received: {message}")
                    # Don't display your own messages again (avoid duplicates)
                    if not message.startswith(f"[{self.username}]:"):
                        self.add_message(message, "received")
                else:
                    print("[GUI CLIENT] Empty message received, connection closed")
                    break
            except Exception as e:
                print(f"[GUI CLIENT] Receive error: {e}")
                break
                
        self.connected = False
        self.add_message("❌ Disconnected from server", "system")
        self.add_message("🔄 Returning to connection screen in 2 seconds...", "system")
        self.add_message("💡 Or click the Reconnect button to reconnect immediately", "system")
        self.status_label.configure(text="🔴 Disconnected")
        self.message_entry.configure(state="disabled")
        self.send_button.grid_remove()  # Hide send button
        self.reconnect_button.grid(row=0, column=1, padx=(0, 15), pady=15)  # Show reconnect button
        self.users_label.configure(text="👥 Users: 0")
        print("[GUI CLIENT] Disconnected from chat server")
        
        # Return to connection screen after a brief delay
        self.root.after(2000, self.return_to_connection)  # 2 second delay
        
    def return_to_connection(self):
        """Return to the connection dialog after disconnect"""
        # Only proceed if still disconnected (avoid double-execution)
        if self.connected:
            return
            
        # Clear the chat
        self.chat_text.configure(state="normal")
        self.chat_text.delete("1.0", "end")
        self.chat_text.configure(state="disabled")
        
        # Reset UI to initial state
        self.reconnect_button.grid_remove()  # Hide reconnect button
        self.send_button.grid(row=0, column=1, padx=(0, 15), pady=15)  # Show send button
        self.send_button.configure(state="disabled")  # But keep it disabled
        
        # Reset connection state
        self.connected = False
        self.client = None
        self.username = ""
        
        # Show connection dialog again
        self.setup_connection()
        
    def send_message(self, event=None):
        message = self.message_entry.get().strip()
        if message and self.connected:
            try:
                if message.lower() == '/quit':
                    self.on_closing()
                    return
                
                # Display your own message immediately
                self.add_message(f"[{self.username}]: {message}", "sent")
                
                full_message = f"[{self.username}]: {message}"
                self.client.send(full_message.encode('utf-8'))
                self.message_entry.delete(0, tk.END)
            except:
                messagebox.showerror("Error", "Failed to send message")
                
    def add_message(self, message, msg_type):
        # Temporarily enable editing to add message
        self.chat_text.configure(state="normal")
        
        current_text = self.chat_text.get("1.0", tk.END)
        
        if msg_type == "system":
            formatted_message = f"--- {message} ---\n"
        elif msg_type == "sent":
            # Style your own messages differently
            formatted_message = f"You: {message.replace(f'[{self.username}]: ', '')}\n"
        else:
            formatted_message = f"{message}\n"
            
        self.chat_text.insert(tk.END, formatted_message)
        self.chat_text.see(tk.END)
        
        # Disable editing again to make it read-only
        self.chat_text.configure(state="disabled")
        
    def on_closing(self):
        if self.connected:
            try:
                self.client.close()
            except:
                pass
        self.root.destroy()
        
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()


class ModernConnectionDialog:
    def __init__(self, parent):
        self.result = None
        
        # Create dialog window
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Connect to Chat Server")
        self.dialog.geometry("450x400")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Configure grid
        self.dialog.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(self.dialog, text="🚀 Join Chat Server", 
                                  font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=30, pady=(30, 40))
        
        # Input frame
        input_frame = ctk.CTkFrame(self.dialog)
        input_frame.grid(row=1, column=0, padx=30, pady=20, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Host input
        ctk.CTkLabel(input_frame, text="Server Host:", 
                    font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        self.host_entry = ctk.CTkEntry(input_frame, placeholder_text="Enter server IP or ngrok URL (e.g., 0.tcp.ngrok.io)",
                                      font=ctk.CTkFont(size=13), height=35)
        self.host_entry.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.host_entry.insert(0, "localhost")  # Default to localhost
        
        # Port input
        ctk.CTkLabel(input_frame, text="Port:", 
                    font=ctk.CTkFont(size=14, weight="bold")).grid(row=2, column=0, padx=20, pady=(0, 5), sticky="w")
        self.port_entry = ctk.CTkEntry(input_frame, placeholder_text="Enter port number (e.g., 12345 or ngrok port)",
                                      font=ctk.CTkFont(size=13), height=35)
        self.port_entry.grid(row=3, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.port_entry.insert(0, "12345")
        
        # Username input
        ctk.CTkLabel(input_frame, text="Username:", 
                    font=ctk.CTkFont(size=14, weight="bold")).grid(row=4, column=0, padx=20, pady=(0, 5), sticky="w")
        self.username_entry = ctk.CTkEntry(input_frame, placeholder_text="Choose your username",
                                          font=ctk.CTkFont(size=13), height=35)
        self.username_entry.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Button frame
        button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=30, pady=20, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Buttons
        self.cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self.on_cancel,
                                          font=ctk.CTkFont(size=14, weight="bold"), height=40,
                                          fg_color="#e74c3c", hover_color="#c0392b")
        self.cancel_button.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        self.connect_button = ctk.CTkButton(button_frame, text="🚀 Connect", command=self.on_connect,
                                           font=ctk.CTkFont(size=14, weight="bold"), height=40)
        self.connect_button.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        
        # Bind Enter key to connect
        self.dialog.bind('<Return>', lambda e: self.on_connect())
        
        # Focus on username field
        self.username_entry.focus()
        
    def on_connect(self):
        host = self.host_entry.get().strip()
        port = self.port_entry.get().strip()
        username = self.username_entry.get().strip()
        
        if not all([host, port, username]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
            
        try:
            int(port)  # Validate port is a number
        except ValueError:
            messagebox.showerror("Error", "Port must be a number")
            return
            
        if len(username) > 20:
            messagebox.showerror("Error", "Username must be 20 characters or less")
            return
            
        self.result = (host, port, username)
        self.dialog.destroy()
        
    def on_cancel(self):
        self.dialog.destroy()


if __name__ == "__main__":
    app = ModernChatClient()
    app.run()
