from log_store import save_logs

def handle_push(data):
    if data is None:
        return False, "empty payload"
    records = []
    if isinstance(data, list):
        items = data
    else:
        items = [data]

    for item in items:
        sn = item.get('sn') or item.get('device_sn') or item.get('sn')
        user_id = item.get('id') or item.get('user') or item.get('pin') or item.get('employee_code')
        timestamp = item.get('timestamp') or item.get('time') or item.get('datetime')
        punch_type = item.get('type') or item.get('status') or item.get('verified')

        if user_id is None or timestamp is None:
            continue

        try:
            itype = int(punch_type) if punch_type is not None else 0
        except:
            itype = 0

        records.append({
            "employee_code": str(user_id),
            "in_out_mode": itype,
            "timestamp": timestamp,
            "device_sn": sn,
            "device_ip": item.get('device_ip')
        })

    if records:
        saved = save_logs(records)
        return True, f"saved {len(saved)} logs"
    return False, "no valid records"
