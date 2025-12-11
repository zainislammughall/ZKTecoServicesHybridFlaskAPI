from flask import Flask, request, jsonify
import json, os
from datetime import datetime
from Scan_network import SCAN_PORT, load_config, save_config, scan_network
from zkteco_push_handler import handle_push
from log_store import load_logs, save_logs
from background_sync import BackgroundPoller

CONFIG = {}
if os.path.exists('config.json'):
    with open('config.json') as f:
        CONFIG = json.load(f)

app = Flask(__name__)

poller = None
if CONFIG.get('enable_polling', False):
    try:
        poller = BackgroundPoller(CONFIG)
        poller.start()
        print('[app] background poller started')
    except Exception as ex:
        print('[app] failed to start poller:', ex)


@app.route('/push/attendance', methods=['POST'])
def push_attendance():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return str(e), 400
    ok, msg = handle_push(data)
    if ok:
        return msg, 200
    return msg, 400


@app.route('/pull', methods=['GET'])
def pull_now():
    ip = request.args.get('ip')
    port = int(request.args.get('port', 4370))
    timeout = int(request.args.get('timeout', CONFIG.get('poll_timeout_seconds', 5)))
    from zkteco_poller import poll_device
    try:
        logs = poll_device(ip, port=port, timeout=timeout)
    except Exception as e:
        return { 'error': str(e) }, 500
    saved = save_logs(logs)
    return { 'pulled': len(logs), 'saved_new': len(saved) }


@app.route('/logs', methods=['GET'])
def get_logs():
    data = load_logs()
    emp = request.args.get('employee')
    frm = request.args.get('from')
    to = request.args.get('to')
    if emp:
        data = [d for d in data if d.get('employee_code') == emp]
    if frm:
        try:
            fdt = datetime.fromisoformat(frm)
            data = [d for d in data if datetime.fromisoformat(d.get('timestamp')) >= fdt]
        except:
            pass
    if to:
        try:
            tdt = datetime.fromisoformat(to)
            data = [d for d in data if datetime.fromisoformat(d.get('timestamp')) <= tdt]
        except:
            pass
    return jsonify(data)


@app.route('/logs/filter', methods=['GET'])
def filter_logs():
    from log_store import load_logs
    data = load_logs()

    ip = request.args.get('ip')
    frm = request.args.get('from')   # example: 2025-01-01
    to = request.args.get('to')      # example: 2025-01-05

    # Filter by device IP
    if ip:
        data = [d for d in data if d.get('device_ip') == ip]

    # FROM-DATE (no time required)
    if frm:
        try:
            fdt = datetime.strptime(frm, "%Y-%m-%d")
            fdt = fdt.replace(hour=0, minute=0, second=0)
            data = [d for d in data if datetime.fromisoformat(d.get('timestamp')) >= fdt]
        except:
            return {"error": "Invalid 'from' date. Format must be YYYY-MM-DD"}, 400

    # TO-DATE (no time required)
    if to:
        try:
            tdt = datetime.strptime(to, "%Y-%m-%d")
            tdt = tdt.replace(hour=23, minute=59, second=59)
            data = [d for d in data if datetime.fromisoformat(d.get('timestamp')) <= tdt]
        except:
            return {"error": "Invalid 'to' date. Format must be YYYY-MM-DD"}, 400

    return jsonify({
        "ip": ip,
        "from": frm,
        "to": to,
        "count": len(data),
        "logs": data
    })


@app.route('/', methods=['GET'])
def home():
    return {
        'status': 'running',
        'push_endpoint': '/push/attendance',
        'pull_endpoint': '/pull?ip=IP'
    }

@app.route("/scan-devices", methods=["GET"])
def scan_devices():
    config = load_config()

    # Get existing devices list
    existing_devices = config.get("devices", [])

    # Convert current device list to a set for quick duplicate check
    existing_ips = {dev["ip"] for dev in existing_devices}

    # Scan LAN for new ZK devices
    scanned_ips = scan_network("192.168.1.")

    # Add only new devices (avoid duplicates)
    new_device_entries = []
    for ip in scanned_ips:
        if ip not in existing_ips:
            new_device_entries.append({
                "ip": ip,
                "port": SCAN_PORT
            })

    # Merge new entries into config
    config["devices"].extend(new_device_entries)

    # Save updated config.json
    save_config(config)

    return jsonify({
        "status": "success",
        "found_devices": scanned_ips,
        "new_devices_added": new_device_entries,
        "all_devices": config["devices"]
    })


@app.route("/devices", methods=["GET"])
def get_devices():
    config = load_config()
    return jsonify({
        "devices": config.get("devices", [])
    })







if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)



