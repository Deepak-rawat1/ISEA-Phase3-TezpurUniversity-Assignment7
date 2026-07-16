# Secure GUI-Based Multi-Client Chat Application Using TCP

## Assignment 7

### Submitted By

**Deepak Singh Rawat**\
**Enrollment No.: UU2409000093**\
**Program:** BCA\
**University:** Uttaranchal University

### Submitted To

**ISEA Summer Internship 2026**\
**ISEA under MeitY**\
*(In affiliation with Tezpur University, Assam)*

------------------------------------------------------------------------

# Project Title

**Secure GUI-Based Multi-Client Chat Application Using TCP with Advanced Authentication and Session Hardening**

------------------------------------------------------------------------

# Objective

This project upgrades the GUI-based Multi-Client TCP Chat Application from Assignment 6 into a secure, hardened application. It implements robust security patterns to protect user accounts, restrict unauthorized access, and record system events securely. 

Key security implementations include:
1. **User Authentication & Secure Storage**: Password authentication verified against SHA-256 hashes stored locally in `users.json` (passwords are never saved or managed in plaintext).
2. **Duplicate Login Prevention**: Rejects simultaneous active sessions for the same username.
3. **Input Validation**: Strict client and server-side validation rejecting empty, overly long, or non-alphanumeric usernames.
4. **Brute Force Lockout Protection**: Automatically locks out IP addresses for 30 seconds after 5 consecutive failed login attempts.
5. **Secure Local Logging**: Comprehensive tracking of network connections, authentications, lockouts, and disconnections inside dedicated, sanitized log files (`server_log.txt` and `security_log.txt`) without exposing sensitive user credentials.
6. **Protocol Analysis**: Verification of network handshakes and protocol boundary behavior in Mininet using Wireshark packet capture.

------------------------------------------------------------------------

# Software Requirements

- Ubuntu 22.04 LTS / 24.04 LTS
- Python 3.x
- Mininet
- Wireshark
- Tkinter (Python GUI)
- Socket Programming & Multithreading modules
- Cryptographic Hashing (Python `hashlib` module)
- JSON (for database storage)
- Git & GitHub

------------------------------------------------------------------------

# Network Topology

                    +------------------+
                    |      Switch      |
                    |        s1        |
                    +------------------+
                       |  |  |  |  |
                      h1 h2 h3 h4 h5

    h1 : Chat Server & Secure Database
    h2 : Client A (Alice)
    h3 : Client B (Bob)
    h4 : Client C
    h5 : Client D

### Mininet Command

``` bash
sudo mn --topo single,5
Connectivity Verification
Bash
nodes
net
pingall

Execution Steps:

1. Start Mininet
Bash
sudo mn --topo single,5

2. Open Terminals
Bash
mininet> xterm h1 h2 h3

3. Start the Server (on Host h1)
Bash
python3 server.py

4. Start the GUI Clients (on Hosts h2 and h3)
Bash
python3 client_gui.py

5. Verify Security Implementations
Secure Storage Check: Open a separate terminal on your Ubuntu host and run cat users.json to verify that passwords are encrypted using 64-character SHA-256 hashes.

Duplicate Login Check: Log in as alice on Host h2. Attempt to log in as alice again on Host h3. Verify that the second client displays an error popup.

Input Validation Check: Attempt to register/log in with special characters in the username. Check that the client rejects the request.

Failed Login Protection Check: Attempt to log in with the correct username but an incorrect password 5 consecutive times to trigger and verify the lockout popup.

6. Capture Network Traffic via Wireshark
Launch Wireshark as root from your main host terminal:

Bash
sudo wireshark &
Select the any or loopback lo interface to capture virtual Mininet traffic.

Apply the display filter:

Plaintext
tcp.port == 5000
Perform chat operations and capture the network payloads. Follow the TCP stream (Right-click a packet -> Follow -> TCP Stream) to view the connection flow.

Assignment Questions & Answers:
Q1. Explain the difference between authentication and authorization.
Authentication is the process of verifying who a user is (e.g., checking their credentials during login to confirm identity).

Authorization is the process of verifying what an authenticated user is allowed to do (e.g., granting permissions to send private messages, view specific logs, or access admin commands).

Q2. Why should passwords never be stored in plain text?
Storing passwords in plain text leaves them completely exposed. If an attacker gains unauthorized access to the database or if a system administrator views the files, every user account is immediately compromised. Additionally, because users frequently reuse their passwords across multiple sites, a leak on one system puts their accounts on other platforms at risk.

Q3. What is the purpose of password hashing?
Password hashing uses a one-way mathematical algorithm to convert plaintext passwords into a fixed-length, irreversible string of characters (a hash). Since hashes are mathematically impossible to reverse back into plaintext, the server can safely verify a login by comparing the hash of the entered password with the stored hash, ensuring that even if the database is leaked, the actual passwords remain hidden.

Q4. How duplicate login prevention improves security?
It stops session hijacking and unauthorized account sharing. If an attacker steals a user's active credentials, they cannot log in and eavesdrop on private messages or impersonate them while the legitimate user is online. It also alerts the legitimate user immediately; if they see an "already online" error when trying to log in, they instantly know their credentials have been compromised.

Q5. Suggest two additional security improvements for your application.
Transport Layer Encryption (SSL/TLS): Wrapping the raw TCP socket connection in SSL/TLS. This encrypts all transit data, preventing attackers from reading raw usernames, passwords, and chat messages using packet-sniffing tools like Wireshark.

Salted Hashing: Adding a unique, random string of characters (a "salt") to each password before hashing it. This prevents attackers from using precomputed lookup tables (Rainbow Tables) to crack identical passwords across the database.

Sample Screenshots:
The following verification screenshots are saved inside the screenshots/ directory:

-UserAuthentication_And_SecurePassStorage.png: Verifies that user database credentials are encrypted securely using SHA-256 signatures instead of plaintext.

-DuplicateLoginPrevention.png: Displays the rejection alert pop-up when attempting a concurrent active login.

-InputValidation.png: Shows the system interface blocking malformed or improperly formatted user input payloads.

-FailedLogInProtection.png: Documents the triggered client-side window block following continuous security authentication errors.

-SessionManagament_SecureLogin.png: Proves system transactions and user connection records are securely maintained in server logfiles.

-ConnectionSetup(TheThreeWayHandshake).png: Displays the baseline TCP protocol handshake initialization captured in Wireshark.

-Connection(TheThreeWayHandshake).png: Highlights the established socket streams tracking raw network frames.

-AuthenticatedCommunication.png: Captures active data payload transfers over Port 5000 streams.

-FailedLogIn.png: Displays Wireshark packets reflecting rejected credential transmissions.

-Logout.png: Verifies the final TCP tear-down packet flow closing down the host socket cleanly.

Brief Description of the Implementation:
-The application builds on top of the robust client-server TCP architecture developed in Assignment 6. The core socket communication and multithreaded message handling remain, while a new security layer protects both the data-at-rest and state-in-transit.

-The server checks credentials using secure hashed verification. The application state prevents double sessions by tracking connected sockets in a synchronized hash map. Brute-force detection tracks failed login attempts mapped to client IP addresses, applying an automated rate-limiting lockout of 30 seconds upon the 5th consecutive failure. Logging processes are completely sanitized: critical connection changes, failed login details, and lockouts are saved to independent logs on the server side without printing raw input fields. The application also logs transaction traces into dedicated CSV sheets for historical record maintenance.

Repository Structure:
ISEA-Phase3-TezpurUniversity-Assignment7/

├── server.py
├── client_gui.py
├── users.json
├── server_log.txt
├── security_log.txt
├── chat_history.csv
├── performance_results.csv
├── report.pdf
├── README.md
└── screenshots/
    ├── UserAuthentication_And_SecurePassStorage.png
    ├── DuplicateLoginPrevention.png
    ├── InputValidation.png
    ├── FailedLogInProtection.png
    ├── SessionManagament_SecureLogin.png
    ├── ConnectionSetup(TheThreeWayHandshake).png
    ├── Connection(TheThreeWayHandshake).png
    ├── AuthenticatedCommunication.png
    ├── FailedLogIn.png
    └── Logout.png

Conclusion
This assignment successfully demonstrates how to design and secure a multi-client TCP network chat application. By introducing industry-standard security mechanisms—such as SHA-256 cryptographic hashing, duplicate-login boundaries, automated IP-lockout thresholds, sanitized system logs, and input validation—the system is hardened against common security threats like brute-force guessing and session hijacking. The entire implementation was validated inside Mininet, with transit packet behaviors verified and inspected using Wireshark.
