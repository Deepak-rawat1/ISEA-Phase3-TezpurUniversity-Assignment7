# GUI-Based Multi-Client Chat Application Using TCP

## Assignment 6

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

**GUI-Based Multi-Client Chat Application Using TCP**

------------------------------------------------------------------------

# Objective

This project converts the terminal-based Multi-Client TCP Chat
Application developed in Assignment 5 into a graphical desktop
application using Python Tkinter. The application reuses the existing
server implementation while introducing an intuitive graphical interface
for communication. It supports multiple clients, broadcast messaging,
private messaging, online user management, persistent chat history, and
background message handling using multithreading. The project was tested
in Mininet and verified using Wireshark packet analysis.

------------------------------------------------------------------------

# Software Requirements

-   Ubuntu 22.04 LTS
-   Python 3.x
-   Mininet
-   Wireshark
-   Tkinter
-   Socket Programming
-   Threading Module
-   CSV Module
-   Git & GitHub

------------------------------------------------------------------------

# Network Topology

                    +------------------+
                    |      Switch      |
                    |        s1        |
                    +------------------+
                       |  |  |  |  |
                      h1 h2 h3 h4 h5

    h1 : Chat Server
    h2 : Client A
    h3 : Client B
    h4 : Client C
    h5 : Client D

### Mininet Command

``` bash
sudo mn --topo single,5
```

### Connectivity Verification

``` bash
nodes
net
pingall
```

------------------------------------------------------------------------

# Execution Steps

## 1. Start Mininet

``` bash
sudo mn --topo single,5
```

## 2. Open terminals

``` bash
xterm h1 h2 h3 h4 h5
```

## 3. Start the Server

``` bash
python3 server.py
```

## 4. Start the GUI Client

``` bash
python3 client_gui.py
```

## 5. Connect Clients

-   Server IP: **10.0.0.1**
-   Port: **5000**
-   Enter a unique username.
-   Click **Connect**.

## 6. Perform Chat Operations

-   Broadcast messaging
-   Private messaging
-   View online users
-   Join notifications
-   Leave notifications
-   Disconnect and reconnect

## 7. Capture Network Traffic

Apply the Wireshark filter:

``` text
tcp.port == 5000
```

Capture:

-   Client Connection
-   Broadcast Message
-   Private Message
-   Client Disconnect

------------------------------------------------------------------------

# Sample Screenshots

Include the following screenshots in the `screenshots/` folder:

-   Network Topology
-   Server Dashboard
-   Login Window
-   Successful Client Connection
-   Broadcast Messaging
-   Private Messaging
-   User Joining
-   User Leaving
-   Wireshark Client Connection
-   Wireshark Broadcast Packet
-   Wireshark Private Packet
-   Wireshark Client Disconnect

------------------------------------------------------------------------

# Brief Description of the Implementation

The application follows a client-server architecture using TCP sockets.
The server manages all connected clients, routes broadcast and private
messages, maintains online user information, stores chat history, and
records server events. The graphical client is implemented using Tkinter
and provides a user-friendly interface consisting of a login window,
chat display area, online users panel, recipient selection, message
input, and connection controls.

A dedicated background thread continuously receives messages from the
server, ensuring that the graphical interface remains responsive while
users continue typing or interacting with the application. The
networking logic developed in Assignment 5 was reused with minimal
modifications, making the GUI a presentation layer built on top of the
existing communication framework.

------------------------------------------------------------------------

# Repository Structure

    ISEA-Phase3-TezpurUniversity-Assignment6/

    ├── server.py
    ├── client_gui.py
    ├── report.pdf
    ├── README.md
    └── screenshots/
        ├── network.png
        ├── server_gui.png
        ├── client_gui.png
        ├── successful_connection.png
        ├── user_joining.png
        ├── broadcast_message.png
        ├── private_message.png
        ├── user_leaving.png
        ├── client_connection.png
        ├── broadcast_packet.png
        ├── private_packet.png
        └── client_disconnect.png

------------------------------------------------------------------------

# Conclusion

This assignment successfully demonstrates the conversion of a
terminal-based TCP chat application into a GUI-based desktop application
while preserving the networking architecture developed previously. The
implementation satisfies the assignment requirements through graphical
interaction, multithreaded communication, private messaging, online user
management, and Wireshark-based verification.
