import socket
import threading
import time
import json
import os
import hashlib
import csv

HOST = "0.0.0.0"
PORT = 5000

SERVER_LOG_FILE = "server_log.txt"
SECURITY_LOG_FILE = "security_log.txt"
CHAT_HISTORY_FILE = "chat_history.csv"
PERFORMANCE_FILE = "performance_results.csv"
CREDENTIALS_FILE = "users.json"

# In-memory security states
active_clients = {}      # socket -> client info
username_to_socket = {}  # username -> socket
login_attempts = {}      # IP -> {"count": int, "locked_until": float}
user_activity = {}       # socket -> float (timestamp of last activity)

# Security Configs
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = 30  # seconds
SESSION_TIMEOUT = 300  # 5 minutes idle timeout

lock = threading.Lock()

# Statistics
session_start_time = None
session_message_count = 0
session_total_delay = 0.0
session_broadcast_count = 0
session_private_count = 0
peak_clients = 0

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

print(f"[*] Secure Chat Server running on port {PORT}")


def ensure_file_headers():
    if not os.path.exists(CHAT_HISTORY_FILE) or os.path.getsize(CHAT_HISTORY_FILE) == 0:
        with open(CHAT_HISTORY_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "sender", "receiver", "message_type", "message"])
    if not os.path.exists(PERFORMANCE_FILE) or os.path.getsize(PERFORMANCE_FILE) == 0:
        with open(PERFORMANCE_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["clients", "broadcast_messages", "private_messages", "avg_delay_ms", "throughput_msgs_per_sec"])

ensure_file_headers()

# Seed default credentials if missing
if not os.path.exists(CREDENTIALS_FILE):
    default_users = {
        "alice": hashlib.sha256("Password123".encode()).hexdigest(),
        "bob": hashlib.sha256("SecurePassword456".encode()).hexdigest()
    }
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(default_users, f, indent=4)


def load_credentials():
    try:
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def safe_send(sock, text):
    try:
        # Delimited transmission to protect TCP stream boundaries
        sock.sendall((text + "\n").encode())
        return True
    except Exception:
        return False


def log_security(event, username, ip, status):
    # Strictly avoids displaying or logging plaintext passwords
    with open(SECURITY_LOG_FILE, "a") as f:
        f.write(f"[{now()}] EVENT: {event} | USERNAME: {username} | IP: {ip} | STATUS: {status}\n")


def log_server(event, username, ip):
    with open(SERVER_LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([now(), event, username, ip])


def log_history(sender, receiver, message_type, message):
    with open(CHAT_HISTORY_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([now(), sender, receiver, message_type, message])


# --- Real-time User List Sync ---
def broadcast_user_list():
    """System message to instantly update the sidebars of all online clients."""
    with lock:
        usernames = sorted(username_to_socket.keys(), key=str.lower)
    payload = f"SYSTEM_USER_LIST:{','.join(usernames)}"
    broadcast(payload)


# --- Idle Timeout Monitor ---
def monitor_idle_sessions():
    while True:
        time.sleep(5)
        current_time = time.time()
        expired_sockets = []

        with lock:
            for sock, last_active in list(user_activity.items()):
                if current_time - last_active > SESSION_TIMEOUT:
                    expired_sockets.append(sock)

        for sock in expired_sockets:
            info = active_clients.get(sock)
            username = info["username"] if info else "Unknown"
            log_security("SESSION_TIMEOUT", username, "N/A", "DISCONNECTED")
            safe_send(sock, "ERROR: Session timed out due to inactivity.")
            disconnect_socket(sock)


def update_activity(sock):
    with lock:
        user_activity[sock] = time.time()


def disconnect_socket(sock):
    info = remove_client(sock)
    if info:
        username = info["username"]
        log_server("DISCONNECTED", username, info["ip"])
        broadcast(f"*** {username} left the chat ***", sender=sock)
        print(f"[-] {username} disconnected.")
        # Trigger an updated user sync broadcast instantly
        broadcast_user_list()
    try:
        sock.close()
    except Exception:
        pass


def broadcast(message, sender=None):
    with lock:
        sockets = list(active_clients.keys())

    for client_sock in sockets:
        if sender is not None and client_sock == sender:
            continue
        safe_send(client_sock, message)


def private_message(sender_socket, receiver_name, message):
    global session_message_count, session_private_count, session_total_delay

    sender_info = active_clients.get(sender_socket)
    if not sender_info:
        return

    receiver_socket = None
    with lock:
        receiver_socket = username_to_socket.get(receiver_name)

    if receiver_socket is None:
        safe_send(sender_socket, f"ERROR: User '{receiver_name}' not found.")
        return

    sender_name = sender_info["username"]
    send_start = time.time()
    
    # Private chat presentation update
    ok1 = safe_send(receiver_socket, f"[PRIVATE][{sender_name}]: {message}")
    ok2 = safe_send(sender_socket, f"[PRIVATE to {receiver_name}]: {message}")
    send_end = time.time()

    if ok1 or ok2:
        log_history(sender_name, receiver_name, "PRIVATE", message)
        with lock:
            session_message_count += 1
            session_private_count += 1
            session_total_delay += (send_end - send_start)


def validate_inputs(username, password):
    if not username.isalnum() or len(username) < 3 or len(username) > 15:
        return False, "ERROR: Username must be alphanumeric and between 3-15 characters long."
    if not password:
        return False, "ERROR: Password field cannot be empty."
    return True, ""


def handle_login(client_sock, ip):
    # Task 5: Check lockout state
    with lock:
        lock_info = login_attempts.get(ip)
        if lock_info and lock_info["count"] >= MAX_FAILED_ATTEMPTS:
            remaining = lock_info["locked_until"] - time.time()
            if remaining > 0:
                log_security("LOGIN_ATTEMPT", "BLOCKED", ip, f"REJECTED_LOCKOUT_{int(remaining)}s")
                safe_send(client_sock, f"ERROR: Too many failed attempts. Try again in {int(remaining)} seconds.")
                return None
            else:
                login_attempts[ip] = {"count": 0, "locked_until": 0.0}

    try:
        payload = client_sock.recv(2048).decode().strip()
        if not payload or ":" not in payload:
            safe_send(client_sock, "ERROR: Invalid handshake format.")
            return None
        
        username, password = payload.split(":", 1)
        username = username.strip()
    except Exception:
        return None

    # Task 4: Validate Input Strings
    is_valid, err_msg = validate_inputs(username, password)
    if not is_valid:
        safe_send(client_sock, err_msg)
        log_security("INPUT_VALIDATION", username, ip, "FAILED_VALIDATION")
        return None

    credentials = load_credentials()
    hashed_pwd = hash_password(password)

    # Validate Match
    if username not in credentials or credentials[username] != hashed_pwd:
        with lock:
            attempts = login_attempts.get(ip, {"count": 0, "locked_until": 0.0})
            attempts["count"] += 1
            if attempts["count"] >= MAX_FAILED_ATTEMPTS:
                attempts["locked_until"] = time.time() + LOCKOUT_DURATION
                log_security("BRUTE_FORCE_LOCKOUT", username, ip, "LOCKED")
                safe_send(client_sock, "ERROR: Account locked due to too many failed attempts.")
            else:
                log_security("LOGIN_ATTEMPT", username, ip, "FAILED_INVALID_CREDENTIALS")
                safe_send(client_sock, f"ERROR: Invalid credentials. Attempt {attempts['count']}/{MAX_FAILED_ATTEMPTS}")
            login_attempts[ip] = attempts
        return None

    # Task 3: Duplicate Login Check
    with lock:
        if username in username_to_socket:
            log_security("LOGIN_ATTEMPT", username, ip, "FAILED_DUPLICATE_LOGIN")
            safe_send(client_sock, f"ERROR: User '{username}' is already online.")
            return None

    # Clear lockout status on successful login
    with lock:
        if ip in login_attempts:
            login_attempts[ip] = {"count": 0, "locked_until": 0.0}

    log_security("LOGIN_SUCCESS", username, ip, "AUTHENTICATED")
    return username


def remove_client(client_sock):
    with lock:
        info = active_clients.pop(client_sock, None)
        user_activity.pop(client_sock, None)
        if not info:
            return None
        username = info["username"]
        if username in username_to_socket and username_to_socket[username] == client_sock:
            username_to_socket.pop(username, None)
        return info


def handle_client(client_sock):
    global session_start_time, session_broadcast_count, session_message_count, peak_clients, session_total_delay
    
    ip, port = client_sock.getpeername()
    username = handle_login(client_sock, ip)

    if not username:
        client_sock.close()
        return

    # Add authenticated client to session lists
    with lock:
        active_clients[client_sock] = {
            "username": username,
            "ip": ip,
            "port": port,
            "login_time": now(),
        }
        username_to_socket[username] = client_sock
        user_activity[client_sock] = time.time()
        
        if session_start_time is None:
            session_start_time = time.time()
        peak_clients = max(peak_clients, len(active_clients))

    log_server("CONNECTED", username, ip)
    safe_send(client_sock, "SUCCESS: Authenticated successfully.")
    
    # Send system broadcast join message
    broadcast(f"*** {username} joined the chat ***", sender=client_sock)
    
    # Broadcast updated user list to all online clients
    broadcast_user_list()

    while True:
        try:
            data = client_sock.recv(4096)
            if not data:
                break

            update_activity(client_sock)
            text = data.decode(errors="ignore").strip()
            if not text:
                continue

            # Check maximum payload bounds
            if len(text) > 1000:
                safe_send(client_sock, "ERROR: Message payload exceeds limit of 1000 characters.")
                log_security("INPUT_VALIDATION", username, ip, "OVERSIZED_MESSAGE_REJECTED")
                continue

            if text.lower() in ("exit", "/exit"):
                break

            if text == "/list":
                with lock:
                    usernames = sorted(username_to_socket.keys(), key=str.lower)
                safe_send(client_sock, f"SYSTEM_USER_LIST:{','.join(usernames)}")
                continue

            # Command syntax extraction
            if text.startswith("/msg "):
                parts = text.split(" ", 2)
                if len(parts) < 3 or not parts[1].strip() or not parts[2].strip():
                    safe_send(client_sock, "ERROR: Format private messages as: /msg <username> <message>")
                    continue

                receiver_name = parts[1].strip()
                message = parts[2].strip()
                private_message(client_sock, receiver_name, message)
                continue

            # Input validation filter against raw commands
            if text.startswith("/") and not (text.startswith("/msg ") or text == "/list"):
                safe_send(client_sock, "ERROR: Command unrecognized or syntax invalid.")
                continue

            # Standard broadcast message
            log_history(username, "ALL", "BROADCAST", text)
            msg = f"[{username}]: {text}"
            
            send_start = time.time()
            broadcast(msg, sender=client_sock)
            send_end = time.time()

            with lock:
                session_message_count += 1
                session_broadcast_count += 1
                session_total_delay += (send_end - send_start)

        except Exception:
            break

    disconnect_socket(client_sock)


def main():
    # Start background session inactivity monitor
    threading.Thread(target=monitor_idle_sessions, daemon=True).start()
    
    try:
        while True:
            client_sock, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_sock,), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[*] Server shutting down...")
    finally:
        server.close()


if __name__ == "__main__":
    main()
