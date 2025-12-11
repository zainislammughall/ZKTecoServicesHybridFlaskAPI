# ZKTeco Flask Hybrid (Push + Polling)

## Overview
This project accepts push events from ZKTeco devices (recommended) and also optionally polls devices
using the `zk` Python library (hybrid mode). Logs are saved into `logs.json`.

## Quick start
1. Create and activate a Python venv
2. pip install pyzk
3. pip install -r requirements.txt
4. Edit config.json (set devices and enable_polling)
5. python app.py

## Endpoints
- POST /push/attendance          — receive pushed logs from devices
- GET  /pull?ip=<device_Ip>       — manually poll a device
- GET  /logs                    — read all saved logs 
- GET  /logs/filter?ip=<device_Ip>&from=<yyyy-mm-dd>&to=<yyyy-mm-dd>     — read saved logs (filter with ip, from, to)

## Configure Devices
1. http://<server-ip>:5000/push/attendance
2. On device: Menu → Comm → Server → HTTP Server Settings → Server IP, Port (5000), Path /push/attendance, Enable
