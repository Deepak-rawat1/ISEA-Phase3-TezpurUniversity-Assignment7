import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from datetime import datetime


class ChatClientGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Secure Multi-Client Chat")
        self.geometry("980x680")
        self.minsize(900, 620)
        self.configure(bg="#1e1e1e")

        self.client_socket = None
        self.receiver_thread = None
        self.stop_event = threading.Event()

        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.server_ip = tk.StringVar(value="10.0.0.1")
        self.server_port = tk.StringVar(value="5000")
        self.status_text = tk.StringVar(value="Disconnected")
        self.recipient_var = tk.StringVar(value="ALL")

        self._build_styles()
        self._build_login_frame()
        self._build_chat_frame()

        self.show_login()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background="#1e1e1e")
        style.configure("Card.TFrame", background="#252526")
        style.configure("TLabel", background="#1e1e1e", foreground="#ffffff", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#1e1e1e", foreground="#ffffff", font=("Segoe UI", 18, "bold"))
        style.configure("SubTitle.TLabel", background="#1e1e1e", foreground="#cfcfcf", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#252526", foreground="#ffffff", font=("Segoe UI", 11, "bold"))
        style.configure("Status.TLabel", background="#1e1e1e", foreground="#7ee787", font=("Segoe UI", 10, "bold"))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8)

    def _build_login_frame(self):
        self.login_frame = ttk.Frame(self, padding=24)
        self.login_frame.pack(fill="both", expand=True)

        header = ttk.Frame(self.login_frame)
        header.pack(fill="x", pady=(10, 15))

        ttk.Label(header, text="Secure Multi-Client Chat", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Connect securely with SHA-256 authenticated verification.", style="SubTitle.TLabel").pack(anchor="w", pady=(4, 0))

        card = ttk.Frame(self.login_frame, style="Card.TFrame", padding=20)
        card.pack(fill="x", pady=10)

        ttk.Label(card, text="Username", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(card, textvariable=self.username, font=("Segoe UI", 11), width=36).grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(card, text="Password", style="CardTitle.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(card, textvariable=self.password, font=("Segoe UI", 11), width=36, show="*").grid(row=3, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(card, text="Server IP", style="CardTitle.TLabel").grid(row=4, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(card, textvariable=self.server_ip, font=("Segoe UI", 11), width=36).grid(row=5, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(card, text="Port", style="CardTitle.TLabel").grid(row=6, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(card, textvariable=self.server_port, font=("Segoe UI", 11), width=36).grid(row=7, column=0, sticky="ew", pady=(0, 15))

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.grid(row=8, column=0, sticky="e")
        ttk.Button(btns, text="Connect & Login", command=self.connect_to_server).pack(side="right")

        card.columnconfigure(0, weight=1)

    def _build_chat_frame(self):
        self.chat_frame = ttk.Frame(self, padding=14)

        topbar = ttk.Frame(self.chat_frame)
        topbar.pack(fill="x", pady=(0, 12))

        left_top = ttk.Frame(topbar)
        left_top.pack(side="left", fill="x", expand=True)

        ttk.Label(left_top, text="Secure Multi-Client Chat", style="Title.TLabel").pack(anchor="w")
        ttk.Label(left_top, textvariable=self.status_text, style="Status.TLabel").pack(anchor="w", pady=(4, 0))

        ttk.Button(topbar, text="Disconnect / Logout", command=self.disconnect).pack(side="right")

        body = ttk.Frame(self.chat_frame)
        body.pack(fill="both", expand=True)

        users_card = ttk.Frame(body, style="Card.TFrame", padding=12)
        users_card.pack(side="left", fill="y", padx=(0, 12))
        users_card.configure(width=220)

        ttk.Label(users_card, text="Online Users", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))
        self.users_listbox = tk.Listbox(
            users_card, bg="#1f1f1f", fg="#ffffff", highlightthickness=0, bd=0,
            selectbackground="#2d7dd2", font=("Segoe UI", 10), activestyle="none", height=24
        )
        self.users_listbox.pack(fill="both", expand=True)
        self.users_listbox.bind("<ButtonRelease-1>", self._on_user_select)

        chat_card = ttk.Frame(body, style="Card.TFrame", padding=12)
        chat_card.pack(side="left", fill="both", expand=True)

        ttk.Label(chat_card, text="Secure Chat Stream", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))
        self.chat_area = ScrolledText(
            chat_card, wrap="word", bg="#1f1f1f", fg="#ffffff", insertbackground="#ffffff",
            relief="flat", font=("Segoe UI", 10), height=20
        )
        self.chat_area.pack(fill="both", expand=True)
        self.chat_area.config(state="disabled")

        controls = ttk.Frame(chat_card, style="Card.TFrame")
        controls.pack(fill="x", pady=(12, 0))

        ttk.Label(controls, text="Recipient", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.recipient_combo = ttk.Combobox(controls, textvariable=self.recipient_var, values=["ALL"], state="readonly", width=18)
        self.recipient_combo.grid(row=1, column=0, sticky="w", pady=(6, 10))

        ttk.Label(controls, text="Message", style="CardTitle.TLabel").grid(row=2, column=0, sticky="w")
        self.message_entry = ttk.Entry(controls, font=("Segoe UI", 11))
        self.message_entry.grid(row=3, column=0, sticky="ew", pady=(6, 10))
        self.message_entry.bind("<Return>", lambda event: self.send_message())

        send_btns = ttk.Frame(controls, style="Card.TFrame")
        send_btns.grid(row=4, column=0, sticky="e")
        ttk.Button(send_btns, text="Send", command=self.send_message).pack(side="right")
        ttk.Button(send_btns, text="Request /list", command=self.request_online_users).pack(side="right", padx=(0, 8))

        controls.columnconfigure(0, weight=1)

    def show_login(self):
        self.chat_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)
        self.status_text.set("Disconnected")

    def show_chat(self):
        self.login_frame.pack_forget()
        self.chat_frame.pack(fill="both", expand=True)
        self.message_entry.focus_set()

    def append_chat(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {text}\n"
        self.chat_area.config(state="normal")
        self.chat_area.insert("end", line)
        self.chat_area.see("end")
        self.chat_area.config(state="disabled")

    def update_users(self, users):
        # Dynamically exclude self from dropdown & side menu arrays
        my_name = self.username.get().strip()
        filtered_users = sorted(set(u for u in users if u and u != my_name), key=str.lower)
        
        self.users_listbox.delete(0, "end")
        self.users_listbox.insert("end", "ALL")
        for user in filtered_users:
            self.users_listbox.insert("end", user)

        current_recipient = self.recipient_var.get()
        options = ["ALL"] + filtered_users
        self.recipient_combo["values"] = options
        if current_recipient not in options:
            self.recipient_var.set("ALL")

    def connect_to_server(self):
        username = self.username.get().strip()
        password = self.password.get()
        server_ip = self.server_ip.get().strip()
        port_text = self.server_port.get().strip()

        if not username or not password:
            messagebox.showerror("Validation Error", "Both username and password are required.")
            return

        try:
            port = int(port_text)
        except ValueError:
            messagebox.showerror("Invalid Port", "Port must be an integer.")
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((server_ip, port))
            
            auth_payload = f"{username}:{password}"
            sock.sendall((auth_payload + "\n").encode())

            response = sock.recv(1024).decode().strip()
            if response.startswith("ERROR:"):
                messagebox.showerror("Authentication Failed", response)
                sock.close()
                return
            
        except Exception as exc:
            messagebox.showerror("Connection Failed", f"Could not reach server:\n{exc}")
            return

        self.client_socket = sock
        self.stop_event.clear()
        self.status_text.set(f"Connected as {username}")
        self.show_chat()
        self.append_chat("Successfully authenticated.")

        self.receiver_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receiver_thread.start()
        self.after(300, self.request_online_users)

    def request_online_users(self):
        if self.client_socket:
            try:
                self.client_socket.sendall(b"/list\n")
            except Exception:
                pass

    def _on_user_select(self, _event=None):
        sel = self.users_listbox.curselection()
        if not sel:
            return
        value = self.users_listbox.get(sel[0])
        self.recipient_var.set(value)
        self.message_entry.focus_set()

    def send_message(self):
        if not self.client_socket:
            return

        message = self.message_entry.get().strip()
        if not message:
            return

        recipient = self.recipient_var.get().strip()
        try:
            if recipient == "ALL":
                payload = message
            else:
                payload = f"/msg {recipient} {message}"

            self.client_socket.sendall((payload + "\n").encode())
            self.message_entry.delete(0, "end")
        except Exception as exc:
            messagebox.showerror("Send Failed", f"Connection terminated:\n{exc}")
            self.disconnect()

    def receive_messages(self):
        buffer = ""
        while not self.stop_event.is_set():
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                buffer += data.decode(errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        self.after(0, self.process_incoming_message, line)
            except Exception:
                break
        self.after(0, self.on_disconnected_remote)

    def process_incoming_message(self, message):
        if message.startswith("ERROR:"):
            messagebox.showerror("Server Alert", message)
            if "Session timed out" in message or "blocked" in message:
                self.disconnect()
            return

        # Intercept and process user list synchronizations
        if message.startswith("SYSTEM_USER_LIST:"):
            raw_users = message.replace("SYSTEM_USER_LIST:", "").strip()
            users = [u.strip() for u in raw_users.split(",") if u.strip()]
            self.update_users(users)
            return

        # Render chat messages
        self.append_chat(message)

    def on_disconnected_remote(self):
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception:
                pass
        self.client_socket = None
        self.stop_event.set()
        self.status_text.set("Disconnected")
        self.append_chat("Disconnected from server.")
        self.show_login()

    def disconnect(self):
        self.stop_event.set()
        if self.client_socket:
            try:
                self.client_socket.sendall(b"exit\n")
            except Exception:
                pass
            try:
                self.client_socket.close()
            except Exception:
                pass
        self.client_socket = None
        self.status_text.set("Disconnected")
        self.password.set("")
        self.show_login()

    def on_close(self):
        self.disconnect()
        self.destroy()


if __name__ == "__main__":
    app = ChatClientGUI()
    app.mainloop()
