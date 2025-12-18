from flask import Flask, request, jsonify
import json, os
from datetime import datetime

from Scan_network import SCAN_PORT, load_config, save_config, scan_network
from zkteco_push_handler import handle_push
from log_store import load_logs, save_logs
from background_sync import BackgroundPoller

CONFIG = {}
if os.path.exists("config.json"):
    with open("config.json") as f:
        CONFIG = json.load(f)

app = Flask(__name__)

poller = None
if CONFIG.get("enable_polling", False):
    try:
        poller = BackgroundPoller(CONFIG)
        poller.start()
        print("[app] background poller started")
    except Exception as ex:
        print("[app] failed to start poller:", ex)

def sync_devices_before_read(timeout=None):
    from zkteco_poller import poll_device

    config = load_config()
    devices = config.get("devices", [])
    total_pulled = 0
    total_saved = 0

    for dev in devices:
        ip = dev.get("ip")
        port = dev.get("port", 4370)

        try:
            logs = poll_device(ip, port=port, timeout=timeout or 5)
            saved = save_logs(logs)
            total_pulled += len(logs)
            total_saved += len(saved)
        except Exception as ex:
            print(f"[sync] device {ip} skipped:", ex)

    return {
        "devices": len(devices),
        "pulled": total_pulled,
        "saved": total_saved
    }


# ---------------- PUSH ----------------
@app.route("/push/attendance", methods=["POST"])
def push_attendance():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return str(e), 400

    ok, msg = handle_push(data)
    return (msg, 200) if ok else (msg, 400)


# ---------------- PULL ----------------
@app.route("/pull", methods=["GET"])
def pull_now():
    ip = request.args.get("ip")
    port = int(request.args.get("port", 4370))
    timeout = int(request.args.get("timeout", CONFIG.get("poll_timeout_seconds", 5)))

    if not ip:
        return {"error": "ip is required"}, 400

    from zkteco_poller import poll_device

    try:
        logs = poll_device(ip, port=port, timeout=timeout)
    except Exception as e:
        return {"error": str(e)}, 500

    saved = save_logs(logs)
    return {
        "pulled": len(logs),
        "saved_new": len(saved)
    }


# ---------------- LOGS ----------------
@app.route("/logs", methods=["GET"])
def get_logs():
    sync_devices_before_read()

    data = load_logs()

    emp = request.args.get("employee")
    frm = request.args.get("from")
    to = request.args.get("to")

    if emp:
        data = [d for d in data if d.get("employee_code") == emp]

    if frm:
        try:
            fdt = datetime.fromisoformat(frm)
            data = [d for d in data if datetime.fromisoformat(d["timestamp"]) >= fdt]
        except:
            pass

    if to:
        try:
            tdt = datetime.fromisoformat(to)
            data = [d for d in data if datetime.fromisoformat(d["timestamp"]) <= tdt]
        except:
            pass

    return jsonify({
        "count": len(data),
        "logs": data
    })


@app.route("/logs/filter", methods=["GET"])
def filter_logs():
    # 🔥 fetch new logs before returning
    sync_devices_before_read()

    data = load_logs()

    ip = request.args.get("ip")
    frm = request.args.get("from")
    to = request.args.get("to")

    if ip:
        data = [d for d in data if d.get("device_ip") == ip]

    if frm:
        try:
            fdt = datetime.strptime(frm, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            data = [d for d in data if datetime.fromisoformat(d["timestamp"]) >= fdt]
        except:
            return {"error": "Invalid from date"}, 400

    if to:
        try:
            tdt = datetime.strptime(to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            data = [d for d in data if datetime.fromisoformat(d["timestamp"]) <= tdt]
        except:
            return {"error": "Invalid to date"}, 400

    return jsonify({
        "count": len(data),
        "logs": data
    })



# ---------------- DEVICE SCAN ----------------
@app.route("/scan-devices", methods=["GET"])
def scan_devices():
    config = load_config()
    devices = config.get("devices", [])
    existing_ips = {d["ip"] for d in devices}

    scanned_ips = scan_network("192.168.1.")

    new_devices = []
    for ip in scanned_ips:
        if ip not in existing_ips:
            new_devices.append({
                "ip": ip,
                "port": SCAN_PORT
            })

    config["devices"].extend(new_devices)
    save_config(config)

    return jsonify({
        "found": scanned_ips,
        "added": new_devices,
        "all_devices": config["devices"]
    })


# ---------------- ADD DEVICE MANUALLY (NEW) ----------------
@app.route("/devices/add", methods=["POST"])
def add_device():
    data = request.get_json(force=True)

    ip = data.get("ip")
    port = int(data.get("port", 4370))

    if not ip:
        return {"error": "ip is required"}, 400

    config = load_config()
    devices = config.get("devices", [])

    for d in devices:
        if d.get("ip") == ip:
            return {
                "status": "exists",
                "message": "device already exists"
            }, 200

    device = {
        "ip": ip,
        "port": port
    }

    devices.append(device)
    config["devices"] = devices
    save_config(config)

    return {
        "status": "success",
        "message": "device added",
        "device": device
    }


@app.route("/devices", methods=["GET"])
def get_devices():
    config = load_config()
    return jsonify(config.get("devices", []))


@app.route("/", methods=["GET"])
def home():
    return {
        "status": "running",
        "push": "/push/attendance",
        "pull": "/pull?ip=IP",
        "add_device": "/devices/add"
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
