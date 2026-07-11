# File Transfer

A simple peer-to-peer desktop application for sending files between two computers over a network using TCP.

## Features

- **True P2P**: No persistent server — both peers connect directly to each other
- **Rendezvous connection**: Each side connects outbound while also accepting inbound, so neither machine needs to run a listener beforehand
- **Send or receive**: Either computer can send or receive files
- **Progress tracking**: Real-time transfer progress in the UI

## Requirements

- Python 3.10+
- PyQt6

## Installation

```bash
cd transfer_system
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Run the application

```bash
python main.py
```

### Transfer files between two computers

1. Open the app on **both** computers.
2. Each side shares their **IP address** (shown at the top).
3. Enter the other computer's IP in **Peer IP address**.
4. On the **receiving** computer: click **Receive from Peer** (waits briefly for the other side).
5. On the **sending** computer: add files and click **Send to Peer**.

Neither computer runs a background server. The receiver only opens a short-lived connection slot while waiting; the sender connects directly to the peer.

### Local testing

Run two instances on the same machine:
- Instance 1: peer IP `127.0.0.1`, click **Receive from Peer**
- Instance 2: peer IP `127.0.0.1`, add files, click **Send to Peer**

## How P2P connection works

- **Sender** connects directly to the peer's IP on port `5050`.
- **Receiver** opens a temporary inbound slot only while waiting for the transfer, then closes it when done.

Both computers are equal peers — either one can send or receive on each transfer.

## Protocol

Each file transfer uses a simple TCP protocol:

1. **Header** — 4-byte big-endian length + JSON payload:
   ```json
   {"type": "file", "filename": "example.txt", "size": 12345}
   ```
2. **Data** — Raw file bytes (`size` bytes)
3. **Done** — Final header: `{"type": "done"}`

## Project structure

```
transfer_system/
├── main.py
├── requirements.txt
└── file_transfer/
    ├── constants.py
    ├── network.py
    ├── peer.py         # P2P connection and transfer
    ├── protocol.py     # Wire protocol helpers
    └── ui/
        ├── main_window.py
        └── workers.py
```
