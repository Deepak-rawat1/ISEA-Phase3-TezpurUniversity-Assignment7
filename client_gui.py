import socket
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
import json

class ChatClientGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Secure Multi-Client Network Engine")
        self.geometry("1100x740")
        self.minsize(980, 680)
        self.configure(bg="#0F0F12") # Muzli Dark Obsidian Base

        # Load operational parameter configurations
        self.config_ip = "10.0.0.1"
        self.config_port = "5000"
        try:
            with open("config.json", "r") as f:
                cfg = json.load(f)
                self.config_ip = cfg["server"]["default_ip"]
                self.config_port = str(cfg["server"]["port"])
        except:
            pass

        self.client_socket = None
        self.receiver_thread = None
        self.stop_event = threading.Event()
        self.is_connected = False
        
        # Automatic Reconnection Engine Parameters
        self.auto_reconnect_enabled = tk.BooleanVar(value=True)
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 4 

        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.server_ip = tk.StringVar(value=self.config_ip)
        self.server_port = tk.StringVar(value=self.config_port)
        self.status_text = tk.StringVar(value="● Engine Offline")
        self.recipient_var = tk.StringVar(value="ALL")

        self._build_styles()
        
        # Instantiate layout containers properly before layout injection
        self.login_frame = ttk.Frame(self, style="TFrame")
        self.chat_frame = ttk.Frame(self, style="TFrame")
        
        self._build_login_frame()
        self._build_chat_frame()
        self.show_login()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_styles(self):
        style = ttk.Style(self)
        try: style.theme_use("clam")
        except: pass
        
        # Dribbble Premium Dark Glass Visual Aesthetics
        style.configure("TFrame", background="#0F0F12")
        style.configure("Card.TFrame", background="#16161D")
        style.configure("ChatInput.TFrame", background="#16161D")
        
        style.configure("TLabel", background="#0F0F12", foreground="#9499A6", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#0F0F12", foreground="#FFFFFF", font=("Segoe UI", 22, "bold"))
        style.configure("SubTitle.TLabel", background="#0F0F12", foreground="#5C606B", font=("Segoe UI", 10))
        
        style.configure("CardTitle.TLabel", background="#16161D", foreground="#FFFFFF", font=("Segoe UI", 11, "bold"))
        style.configure("Status.TLabel", background="#16161D", foreground="#FF5A60", font=("Segoe UI", 11, "bold"))
        
        # Flat Smooth UI Buttons
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=9, background="#22222B", foreground="#FFFFFF", borderwidth=0)
        style.map("TButton", background=[("active", "#2E2E3A")])
        
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=9, background="#4F46E5", foreground="#FFFFFF", borderwidth=0)
        style.map("Action.TButton", background=[("active", "#6366F1")])

    def _build_login_frame(self):
        center_container = ttk.Frame(self.login_frame, style="Card.TFrame", padding=40)
        center_container.pack(expand=True)

        ttk.Label(center_container, text="Authorization Gate", style="Title.TLabel").pack(anchor="w", pady=(0, 2))
        ttk.Label(center_container, text="Provide parameters to establish transmission path.", style="SubTitle.TLabel").pack(anchor="w", pady=(0, 25))

        # Fields
        ttk.Label(center_container, text="IDENTIFIER (USERNAME)", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))
        self.user_ent = tk.Entry(center_container, textvariable=self.username, bg="#1E1E26", fg="#FFFFFF", insertbackground="#FFFFFF", font=("Segoe UI", 11), relief="flat", bd=8)
        self.user_ent.pack(fill="x", pady=(0, 16))

        ttk.Label(center_container, text="ACCESS PASSPHRASE", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))
        self.pass_ent = tk.Entry(center_container, textvariable=self.password, show="●", bg="#1E1E26", fg="#FFFFFF", insertbackground="#FFFFFF", font=("Segoe UI", 11), relief="flat", bd=8)
        self.pass_ent.pack(fill="x", pady=(0, 16))

        ttk.Label(center_container, text="SERVER IP ROUTE", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))
        self.ip_ent = tk.Entry(center_container, textvariable=self.server_ip, bg="#1E1E26", fg="#FFFFFF", insertbackground="#FFFFFF", font=("Segoe UI", 11), relief="flat", bd=8)
        self.ip_ent.pack(fill="x", pady=(0, 16))

        ttk.Label(center_container, text="PORT", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))
        self.port_ent = tk.Entry(center_container, textvariable=self.server_port, bg="#1E1E26", fg="#FFFFFF", insertbackground="#FFFFFF", font=("Segoe UI", 11), relief="flat", bd=8)
        self.port_ent.pack(fill="x", pady=(0, 25))

        # Bottom Bar Actions
        action_bar = ttk.Frame(center_container, style="Card.TFrame")
        action_bar.pack(fill="x")
        
        # Correctly style Tkinter checkbutton dark background pairing
        self.chk_btn = tk.Checkbutton(action_bar, text="Auto Reconnection", variable=self.auto_reconnect_enabled, bg="#16161D", fg="#9499A6", selectcolor="#1E1E26", activebackground="#16161D", activeforeground="#FFFFFF", font=("Segoe UI", 10))
        self.chk_btn.pack(side="left")
        
        ttk.Button(action_bar, text="Open Channel", style="Action.TButton", command=self.connect_to_server).pack(side="right")

    def _build_chat_frame(self):
        # 1. Sidebar Panel (Node Lists)
        sidebar = ttk.Frame(self.chat_frame, style="Card.TFrame", padding=20)
        sidebar.pack(side="left", fill="y")
        
        ttk.Label(sidebar, text="ACTIVE NODES", style="CardTitle.TLabel").pack(anchor="w", pady=(5, 15))
        
        self.users_listbox = tk.Listbox(
            sidebar, bg="#1E1E26", fg="#D1D5DB", highlightthickness=0, bd=0,
            selectbackground="#4F46E5", selectforeground="#FFFFFF", font=("Segoe UI", 11), 
            activestyle="none", width=22
        )
        self.users_listbox.pack(fill="both", expand=True, pady=(0, 15))
        self.users_listbox.bind("<ButtonRelease-1>", self._on_user_select)

        ttk.Button(sidebar, text="Refresh Nodes", command=self.request_online_users).pack(fill="x")

        # 2. Main Workspace Panel
        workspace = ttk.Frame(self.chat_frame, style="TFrame", padding=0)
        workspace.pack(side="right", fill="both", expand=True)

        # Top Control Bar
        topbar = ttk.Frame(workspace, style="Card.TFrame", padding=15)
        topbar.pack(fill="x")
        
        lbl_info = ttk.Frame(topbar, style="Card.TFrame")
        lbl_info.pack(side="left")
        ttk.Label(lbl_info, text="Transaction Data Pipeline", style="CardTitle.TLabel").pack(anchor="w")
        self.status_lbl = ttk.Label(lbl_info, textvariable=self.status_text, style="Status.TLabel")
        self.status_lbl.pack(anchor="w", pady=(2, 0))

        ttk.Button(topbar, text="Teardown Link", command=self.disconnect).pack(side="right", anchor="center")

        # Ledger Area (Message Streams)
        self.chat_area = ScrolledText(
            workspace, wrap="word", bg="#0F0F12", fg="#E5E7EB", insertbackground="#FFFFFF",
            relief="flat", font=("Segoe UI", 11), highlightthickness=0, borderwidth=0
        )
        self.chat_area.pack(fill="both", expand=True, padx=20, pady=15)
        self.chat_area.config(state="disabled")

        # Dynamic Color Tag Setup
        self.chat_area.tag_config("sys", foreground="#6B7280")
        self.chat_area.tag_config("msg_in", foreground="#10B981")
        self.chat_area.tag_config("msg_out", foreground="#3B82F6")
        self.chat_area.tag_config("err", foreground="#EF4444")

        # Input Control Dashboard Frame with Grid Architecture Fixed
        controls = ttk.Frame(workspace, style="ChatInput.TFrame", padding=15)
        controls.pack(fill="x", side="bottom")

        ttk.Label(controls, text="Target Address:", style="CardTitle.TLabel", background="#16161D").grid(row=0, column=0, sticky="w", padx=(0,10))
        
        self.recipient_combo = ttk.Combobox(controls, textvariable=self.recipient_var, values=["ALL"], state="readonly", width=15)
        self.recipient_combo.grid(row=0, column=1, sticky="w")

        self.message_entry = tk.Entry(controls, bg="#1E1E26", fg="#FFFFFF", insertbackground="#FFFFFF", font=("Segoe UI", 11), relief="flat", bd=8)
        self.message_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.message_entry.bind("<Return>", lambda event: self.send_message())
        
        ttk.Button(controls, text="Dispatch Packet", style="Action.TButton", command=self.send_message).grid(row=1, column=2, padx=(10, 0), sticky="ns", pady=(10, 0))
        
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=0)

    def show_login(self):
        self.chat_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)

    def show_chat(self):
        self.login_frame.pack_forget()
        self.chat_frame.pack(fill="both", expand=True)
        self.message_entry.focus_set()

    def append_chat(self, text, tag=""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {text}\n"
        self.chat_area.config(state="normal")
        
        if text.startswith("[SYSTEM") or text.startswith("[RECONNECT"): tag = "sys"
        elif text.startswith("ERROR:") or text.startswith("[WARNING"): tag = "err"
        elif text.startswith("[PRIVATE to") or (self.username.get() and text.startswith(f"[{self.username.get()}")): tag = "msg_out"
        elif tag == "": tag = "msg_in"
        
        self.chat_area.insert("end", line, tag)
        self.chat_area.see("end")
        self.chat_area.config(state="disabled")

    def update_users(self, users):
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
            messagebox.showerror("Validation Defect", "Credential fields cannot be left blank.")
            return
        try:
            port = int(port_text)
        except ValueError:
            messagebox.showerror("Format Error", "Port parameter must resolve to an integer.")
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((server_ip, port))
            sock.settimeout(None)
            
            auth_payload = f"{username}:{password}"
            sock.sendall((auth_payload + "\n").encode())

            response = sock.recv(1024).decode().strip()
            if response.startswith("ERROR:"):
                messagebox.showerror("Authorization Refused", response)
                sock.close()
                return
            
        except Exception as exc:
            messagebox.showerror("Network Fault", f"Could not bind transaction pipeline to engine host:\n{exc}")
            return

        self.client_socket = sock
        self.stop_event.clear()
        self.is_connected = True
        self.reconnect_attempts = 0
        
        style = ttk.Style(self)
        style.configure("Status.TLabel", foreground="#10B981")
        self.status_text.set(f"● Pipeline Active ({username})")
        
        self.show_chat()
        self.chat_area.config(state="normal")
        self.chat_area.delete("1.0", "end")
        self.chat_area.config(state="disabled")
        self.append_chat("[SYSTEM] Session pipeline verified and established successfully.")

        self.receiver_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receiver_thread.start()
        self.after(300, self.request_online_users)

    def request_online_users(self):
        if self.client_socket and self.is_connected:
            try: self.client_socket.sendall(b"/list\n")
            except: pass

    def _on_user_select(self, _event=None):
        sel = self.users_listbox.curselection()
        if not sel: return
        value = self.users_listbox.get(sel[0])
        self.recipient_var.set(value)
        self.message_entry.focus_set()

    def send_message(self):
        if not self.client_socket or not self.is_connected:
            return
        message = self.message_entry.get().strip()
        if not message: return
        recipient = self.recipient_var.get().strip()
        try:
            if recipient == "ALL":
                payload = message
            else:
                payload = f"/msg {recipient} {message}"
            self.client_socket.sendall((payload + "\n").encode())
            self.message_entry.delete(0, "end")
        except Exception as exc:
            self.append_chat(f"[SYSTEM ERROR] Transmission frame dropped: {exc}")
            self.handle_connection_loss()

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
        if not self.stop_event.is_set():
            self.after(0, self.handle_connection_loss)

    def process_incoming_message(self, message):
        if message.startswith("ERROR:"):
            messagebox.showerror("Engine Exception", message)
            if "timed out" in message or "blocked" in message:
                self.disconnect()
            return
        if message.startswith("SERVER_SHUTDOWN:"):
            messagebox.showwarning("Teardown Event", message)
            self.disconnect()
            return
        if message.startswith("SYSTEM_USER_LIST:"):
            raw_users = message.replace("SYSTEM_USER_LIST:", "").strip()
            users = [u.strip() for u in raw_users.split(",") if u.strip()]
            self.update_users(users)
            return
        self.append_chat(message)

    def handle_connection_loss(self):
        if not self.is_connected: return
        self.is_connected = False
        try: self.client_socket.close()
        except: pass
        
        style = ttk.Style(self)
        style.configure("Status.TLabel", foreground="#EF4444")
        self.status_text.set("● Connection Interrupted")
        self.append_chat("[WARNING] Server link dropped abruptly. Initiating recovery routine...")

        if self.auto_reconnect_enabled.get():
            threading.Thread(target=self.run_reconnection_loop, daemon=True).start()
        else:
            self.disconnect()

    def run_reconnection_loop(self):
        server_ip = self.server_ip.get().strip()
        port = int(self.server_port.get().strip())
        username = self.username.get().strip()
        password = self.password.get()

        while self.reconnect_attempts < self.max_reconnect_attempts and not self.is_connected:
            self.reconnect_attempts += 1
            self.append_chat(f"[RECONNECT] Attempting recovery cycle {self.reconnect_attempts}/{self.max_reconnect_attempts}...")
            time.sleep(self.reconnect_delay)
            
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(4.0)
                sock.connect((server_ip, port))
                sock.settimeout(None)
                
                auth_payload = f"{username}:{password}"
                sock.sendall((auth_payload + "\n").encode())
                
                response = sock.recv(1024).decode().strip()
                if not response.startswith("ERROR:"):
                    self.client_socket = sock
                    self.is_connected = True
                    self.reconnect_attempts = 0
                    self.after(0, self.reestablish_gui_state)
                    return
                else:
                    sock.close()
            except Exception:
                pass

        self.after(0, self.fallback_reconnection_failure)

    def reestablish_gui_state(self):
        style = ttk.Style(self)
        style.configure("Status.TLabel", foreground="#10B981")
        self.status_text.set(f"● Pipeline Active ({self.username.get().strip()})")
        self.append_chat("[SYSTEM] Critical alert: Network recovery routine completed successfully.")
        self.receiver_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receiver_thread.start()
        self.request_online_users()

    def fallback_reconnection_failure(self):
        messagebox.showerror("Teardown Exception", "Network recovery engine failed to re-establish connection pipes.")
        self.disconnect()

    def disconnect(self):
        self.stop_event.set()
        self.is_connected = False
        if self.client_socket:
            try: self.client_socket.sendall(b"exit\n")
            except: pass
            try: self.client_socket.close()
            except: pass
        self.client_socket = None
        style = ttk.Style(self)
        style.configure("Status.TLabel", foreground="#EF4444")
        self.status_text.set("● Engine Offline")
        self.password.set("")
        self.show_login()

    def on_close(self):
        self.disconnect()
        self.destroy()

if __name__ == "__main__":
    app = ChatClientGUI()
    app.mainloop()
