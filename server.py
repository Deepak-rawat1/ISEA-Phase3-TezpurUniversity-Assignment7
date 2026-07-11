import csv
import os
import socket
import threading
import time

HOST = "0.0.0.0"
PORT = 5000

SERVER_LOG_FILE = "server_log.txt"
CHAT_HISTORY_FILE = "chat_history.csv"
PERFORMANCE_FILE = "performance_results.csv"

# socket -> client info
active_clients = {}
# username -> latest known client info (persistent state)
user_states = {}
# username -> socket for online users
username_to_socket = {}

lock = threading.Lock()

# Session statistics (per experiment/run)
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

print(f"[*] Chat Server started on port {PORT}")


def ensure_csv_header(path, header):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)


ensure_csv_header(
    CHAT_HISTORY_FILE,
    ["timestamp", "sender", "receiver", "message_type", "message"]
)
ensure_csv_header(
    PERFORMANCE_FILE,
    ["clients", "broadcast_messages", "private_messages", "avg_delay_ms", "throughput_msgs_per_sec"]
)


def now():
    return time.strftime("%H:%M:%S")


def safe_send(sock, text):
    try:
        sock.send(text.encode())
        return True
    except Exception:
        return False


def log_server(event, username, ip):
    with open(SERVER_LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([now(), event, username, ip])


def log_history(sender, receiver, message_type, message):
    ensure_csv_header(
        CHAT_HISTORY_FILE,
        ["timestamp", "sender", "receiver", "message_type", "message"]
    )
    with open(CHAT_HISTORY_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([now(), sender, receiver, message_type, message])


def print_server_stats():
    online_users = len(active_clients)
    print("\n========== SERVER STATUS ==========")
    print(f"Connected Users   : {online_users}")
    print(f"Messages Processed : {session_message_count}")
    print(f"Broadcast Messages : {session_broadcast_count}")
    print(f"Private Messages   : {session_private_count}")
    print("===================================\n")


def append_performance_row():
    global session_start_time, session_message_count, session_total_delay
    global session_broadcast_count, session_private_count, peak_clients

    if session_start_time is None or session_message_count == 0:
        return

    elapsed = max(time.time() - session_start_time, 1e-6)
    avg_delay_ms = (session_total_delay / session_message_count) * 1000.0
    throughput = session_message_count / elapsed

    ensure_csv_header(
        PERFORMANCE_FILE,
        ["clients", "broadcast_messages", "private_messages", "avg_delay_ms", "throughput_msgs_per_sec"]
    )

    with open(PERFORMANCE_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            peak_clients,
            session_broadcast_count,
            session_private_count,
            round(avg_delay_ms, 3),
            round(throughput, 3),
        ])

    print(f"[*] Performance summary saved for {peak_clients} client(s).")


def get_online_usernames():
    with lock:
        usernames = [info["username"] for info in active_clients.values() if info["status"] == "ONLINE"]
    return sorted(usernames, key=str.lower)


def send_online_users(sock):
    usernames = get_online_usernames()
    if not usernames:
        safe_send(sock, "Online Users:\n(none)")
        return

    msg = "Online Users:\n" + "\n".join(usernames)
    safe_send(sock, msg)


def send_recent_messages(sock, username, limit=5):
    if not os.path.exists(CHAT_HISTORY_FILE):
        safe_send(sock, "No previous chat history found.")
        return

    rows = []
    with open(CHAT_HISTORY_FILE, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("sender") == username:
                rows.append(row)

    if not rows:
        safe_send(sock, f"No previous messages found for {username}.")
        return

    recent = rows[-limit:]
    lines = [f"Last {len(recent)} messages sent by {username}:"]
    for row in recent:
        receiver = row.get("receiver", "ALL")
        message_type = row.get("message_type", "BROADCAST")
        message = row.get("message", "")
        lines.append(f"[{row.get('timestamp', '')}] ({message_type} -> {receiver}) {message}")

    safe_send(sock, "\n".join(lines))


def broadcast(message, sender=None):
    dead_sockets = []
    with lock:
        sockets = list(active_clients.keys())

    for client_sock in sockets:
        if sender is not None and client_sock == sender:
            continue
        try:
            client_sock.send(message.encode())
        except Exception:
            dead_sockets.append(client_sock)

    if dead_sockets:
        with lock:
            for client_sock in dead_sockets:
                info = active_clients.pop(client_sock, None)
                if info:
                    username = info.get("username")
                    if username in username_to_socket and username_to_socket[username] == client_sock:
                        username_to_socket.pop(username, None)
                    if username in user_states:
                        user_states[username]["status"] = "OFFLINE"


def private_message(sender_socket, receiver_name, message):
    global session_message_count, session_total_delay, session_private_count

    sender_info = active_clients.get(sender_socket)
    if not sender_info:
        return

    receiver_socket = None
    with lock:
        receiver_socket = username_to_socket.get(receiver_name)

    if receiver_socket is None:
        safe_send(sender_socket, f"User '{receiver_name}' not found.")
        return

    sender_name = sender_info["username"]

    send_start = time.time()
    ok1 = safe_send(receiver_socket, f"[PRIVATE][{sender_name}] {message}")
    ok2 = safe_send(sender_socket, f"[PRIVATE to {receiver_name}] {message}")
    send_end = time.time()

    if ok1 or ok2:
        log_history(sender_name, receiver_name, "PRIVATE", message)
        with lock:
            session_message_count += 1
            session_private_count += 1
            session_total_delay += (send_end - send_start)


def handle_list_command(client_sock):
    send_online_users(client_sock)


def register_client(client_sock):
    username = client_sock.recv(1024).decode().strip()
    if not username:
        return None, None, None

    ip, port = client_sock.getpeername()

    with lock:
        if username in username_to_socket:
            return username, ip, port

        info = {
            "username": username,
            "ip": ip,
            "port": port,
            "login_time": now(),
            "status": "ONLINE",
        }
        active_clients[client_sock] = info
        user_states[username] = info.copy()
        user_states[username]["status"] = "ONLINE"
        username_to_socket[username] = client_sock

    return username, ip, port


def remove_client(client_sock):
    with lock:
        info = active_clients.pop(client_sock, None)
        if not info:
            return None
        username = info["username"]
        if username in username_to_socket and username_to_socket[username] == client_sock:
            username_to_socket.pop(username, None)
        if username in user_states:
            user_states[username]["status"] = "OFFLINE"
            user_states[username]["logout_time"] = now()
        return info


def finalize_session_if_needed():
    global session_start_time, session_message_count, session_total_delay
    global session_broadcast_count, session_private_count, peak_clients

    with lock:
        online_count = len(active_clients)

    if online_count == 0 and session_start_time is not None:
        append_performance_row()
        session_start_time = None
        session_message_count = 0
        session_total_delay = 0.0
        session_broadcast_count = 0
        session_private_count = 0
        peak_clients = 0


def handle_client(client_sock):
    global session_start_time, session_broadcast_count, session_message_count
    global session_total_delay, peak_clients

    username, ip, port = register_client(client_sock)

    if not username:
        client_sock.close()
        return

    # Reject duplicate active usernames
    with lock:
        if username in username_to_socket and username_to_socket[username] != client_sock:
            safe_send(client_sock, f"Username '{username}' is already online.")
            client_sock.close()
            return

        # Re-register after duplicate check
        active_clients[client_sock] = {
            "username": username,
            "ip": ip,
            "port": port,
            "login_time": now(),
            "status": "ONLINE",
        }
        user_states[username] = active_clients[client_sock].copy()
        username_to_socket[username] = client_sock
        if session_start_time is None:
            session_start_time = time.time()
        peak_clients = max(peak_clients, len(active_clients))

    log_server("CONNECTED", username, ip)
    print(f"{username} connected ({ip}:{port})")

    # Inform the client
    safe_send(client_sock, f"Welcome {username}! Type /list, /msg <user> <message>, or exit to quit.")

    # Send recent messages if this username has history
    send_recent_messages(client_sock, username, limit=5)

    # Join notification to everyone else
    broadcast(f"*** {username} joined the chat ***", sender=client_sock)
    print_server_stats()

    while True:
        try:
            data = client_sock.recv(1024)
            if not data:
                break

            text = data.decode(errors="ignore").strip()
            if not text:
                continue

            if text.lower() == "exit" or text.lower() == "/exit":
                break

            # /list command
            if text == "/list":
                handle_list_command(client_sock)
                continue

            # /msg private message
            if text.startswith("/msg "):
                parts = text.split(" ", 2)
                if len(parts) < 3 or not parts[1].strip() or not parts[2].strip():
                    safe_send(client_sock, "Usage: /msg <username> <message>")
                    continue

                receiver_name = parts[1].strip()
                message = parts[2].strip()
                private_message(client_sock, receiver_name, message)
                print_server_stats()
                continue

            # Normal broadcast message
            sender_info = active_clients.get(client_sock)
            if not sender_info:
                break

            sender_name = sender_info["username"]
            log_history(sender_name, "ALL", "BROADCAST", text)

            msg = f"[{sender_name}] {text}"
            send_start = time.time()
            broadcast(msg, sender=client_sock)
            send_end = time.time()

            with lock:
                session_message_count += 1
                session_broadcast_count += 1
                session_total_delay += (send_end - send_start)

            print_server_stats()

        except Exception:
            break

    info = remove_client(client_sock)
    if info:
        username = info["username"]
        log_server("DISCONNECTED", username, ip)
        broadcast(f"*** {username} left the chat ***", sender=client_sock)
        print(f"{username} disconnected")

    try:
        client_sock.close()
    except Exception:
        pass

    print_server_stats()
    finalize_session_if_needed()


def main():
    try:
        while True:
            client_sock, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client_sock,), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\n[*] Server shutting down...")
    finally:
        try:
            if len(active_clients) == 0:
                finalize_session_if_needed()
        except Exception:
            pass
        try:
            server.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
