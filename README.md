# Application Optimization, Scalability and Reliability using TCP

## Assignment 8

### Submitted By

**Deepak Singh Rawat**  
**Enrollment No.: UU2409000093**  
**Program:** BCA  
**University:** Uttaranchal University

### Submitted To

**ISEA Summer Internship 2026**  
**ISEA under MeitY**  
*(In affiliation with Tezpur University, Assam)*

---

# Project Title

**Application Optimization, Scalability and Reliability Enhancement of GUI-Based Multi-Client Chat Application Using TCP**

---

# Objective

This project enhances the secure GUI-based multi-client TCP chat application developed in Assignment 7 by improving its scalability, reliability, maintainability, and overall software quality while preserving the existing client-server architecture.

The implementation focuses on efficient connection management, automatic recovery from failures, configurable application settings, optimized resource utilization, and performance evaluation under increasing client loads.

---

# Key Enhancements

## 1. Connection Management

- Automatic detection of disconnected clients
- Removal of inactive sessions
- Proper socket cleanup and resource release
- Live online user synchronization
- Meaningful error notifications

## 2. Reliability Enhancement

- Graceful client disconnect
- Automatic session timeout handling
- Improved exception handling
- Reliable message delivery
- Stable client-server communication

## 3. Scalability Enhancement

- Supports up to **10 concurrent clients**
- Optimized multithreaded server architecture
- Dynamic client management
- Efficient message routing
- Reduced server overhead

## 4. Configuration Management

All configurable parameters have been moved into **config.json**, including:

- Server IP
- Server Port
- Session Timeout
- Lockout Duration
- Maximum Failed Login Attempts
- Username Validation
- Maximum Message Length
- Log File Locations

---

# Software Requirements

- Ubuntu 22.04 LTS / 24.04 LTS
- Python 3.x
- Tkinter
- Socket Programming
- Multithreading
- JSON
- Mininet
- Wireshark
- Git
- GitHub

---

# Network Topology

```
               +-------------------+
               |      Switch s1    |
               +-------------------+
      |     |     |     |     |     |     |     |     |     |
     h1    h2    h3    h4    h5    h6    h7    h8    h9   h10   h11

h1  -> Server
h2-h11 -> Clients
```

---

# Mininet Command

```bash
sudo mn --topo single,11
```

---

# Connectivity Verification

```bash
nodes
net
pingall
```

---

# Execution Steps

## 1. Start Mininet

```bash
sudo mn --topo single,11
```

---

## 2. Open Terminal Windows

```bash
xterm h1
```

For five clients

```bash
xterm h2 h3 h4 h5 h6
```

For eight clients

```bash
xterm h2 h3 h4 h5 h6 h7 h8 h9
```

For ten clients

```bash
xterm h2 h3 h4 h5 h6 h7 h8 h9 h10 h11
```

---

## 3. Start Server

```bash
python3 server.py
```

---

## 4. Start GUI Clients

```bash
python3 client_gui.py
```

---

## 5. Performance Testing

Perform testing using:

- 5 Clients
- 8 Clients
- 10 Clients

Performance metrics collected:

- Delay (Latency)
- Throughput
- CPU Usage
- Memory Usage

Results are automatically stored in:

```
performance_results.csv
```

Graphs are generated inside

```
graphs/
```

---

## 6. Wireshark Verification

Launch Wireshark

```bash
sudo wireshark &
```

Apply filter

```
tcp.port == 5000
```

Verify

- TCP Three-way Handshake
- Message Transfer
- Session Termination
- Connection Timeout
- TCP FIN/ACK packets

---

# Performance Improvements

Compared with Assignment 7, the optimized application provides:

- Better resource utilization
- Improved thread management
- Automatic removal of inactive users
- Stable communication under heavy load
- Faster recovery after disconnections
- Configurable server settings
- Improved maintainability

---

# Testing Summary

| Test Case | Expected Result | Status |
|------------|-----------------|--------|
| Server starts successfully | Server accepts connections | ✅ Pass |
| Five clients connected | Stable communication | ✅ Pass |
| Eight clients connected | Stable communication | ✅ Pass |
| Ten clients connected | No crashes | ✅ Pass |
| Broadcast messaging | Delivered successfully | ✅ Pass |
| Private messaging | Delivered correctly | ✅ Pass |
| Client disconnection | Removed automatically | ✅ Pass |
| Session timeout | User disconnected automatically | ✅ Pass |
| Exception handling | Application continues running | ✅ Pass |
| Configuration loading | Loaded from config.json | ✅ Pass |

---

# Repository Structure

```
ISEA-Phase3-TezpurUniversity-Assignment8/

├── server.py
├── client_gui.py
├── config.json
├── users.json
├── performance_results.csv
├── graphs/
│   ├── delay_graph.png
│   ├── throughput_graph.png
│   ├── cpu_usage_graph.png
│   └── memory_usage_graph.png
├── screenshots/
├── report.pdf
└── README.md
```

---

# Sample Screenshots

The `screenshots/` directory contains experimental evidence including:

- Mininet topology
- Pingall verification
- Five client execution
- Eight client execution
- Ten client execution
- Chat communication
- Client disconnection
- Session timeout
- Configuration management
- Performance graphs
- Wireshark TCP capture
- GitHub repository update

---

# Technologies Used

- Python
- Socket Programming
- Multithreading
- Tkinter
- JSON
- CSV
- Mininet
- Wireshark
- Git
- GitHub

---

# Conclusion

Assignment 8 successfully improves the secure multi-client TCP chat application by introducing scalability enhancements, reliable connection management, automatic timeout handling, better exception handling, centralized configuration management, and performance evaluation. The optimized implementation supports up to ten concurrent clients while maintaining stable communication, efficient resource management, and improved software quality. Experimental evaluation using Mininet and Wireshark verifies the correctness and reliability of the optimized system.
