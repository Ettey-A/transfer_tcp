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

### Linux / macOS

```bash
cd transfer_system
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows (easiest)

1. Make sure Python 3 is installed from https://python.org  
   (check **Add python.exe to PATH** during install)
2. Double-click **`run.bat`**

That creates a virtual environment, installs PyQt6, and starts the app.

### Windows (PowerShell, manual)

```powershell
cd C:\Users\YOUR_NAME\Downloads\transfer_system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Usage

### Run the application

**Windows:** double-click `run.bat`  
Or: `python main.py` (auto-installs PyQt6 if missing)

**Linux / macOS:**
```bash
source .venv/bin/activate
python main.py
```

If you see `No module named 'PyQt6'`, install it once:

```bash
python -m pip install -r requirements.txt
```

### Fix: `can't open file '...\main.py': No such file or directory`

This means **`main.py` is missing** from the folder you are in. Python is working; the project files are incomplete or in the wrong place.

**Step 1 — Check what is in the folder:**

```powershell
cd C:\Users\ocran\Downloads\transfer_system
dir
```

You should see at least:

```
main.py
requirements.txt
run.bat
file_transfer\          (folder)
```

**Step 2 — If `main.py` is missing:**

- Re-download or re-copy the **full** project (not just the `file_transfer` folder).
- If you used Git: `git clone <repo-url>` then `cd transfer_system`.
- If you unzipped a file, make sure you opened the inner folder that contains `main.py` (sometimes zip files create `transfer_system\transfer_system\`).

**Step 3 — Run from the correct folder:**

```powershell
cd C:\Users\ocran\Downloads\transfer_system
python main.py
```

Or double-click **`run.bat`** — it will tell you if `main.py` is missing and list what files are in the folder.

### Transfer files between two computers

1. Open the app on **both** computers (Windows: double-click `run.bat`).
2. On the **recipient**, share the **Your IP** shown in the app.
3. On the **sender**:
   - Enter that IP in **Recipient IP**
   - Choose files
   - Click **Send to Recipient**

The recipient does not click anything — the app receives files automatically while it is open.

### Local testing

1. Open two app windows.
2. In window 2, set Recipient IP to `127.0.0.1`, choose files, click **Send to Recipient**.
3. Window 1 receives into Downloads.

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
    ├── peer.py
    ├── protocol.py
    ├── listener.py
    ├── received_store.py   # Received files history
    └── ui/
        ├── main_window.py
        ├── received_panel.py  # Received files viewer
        └── workers.py
```
