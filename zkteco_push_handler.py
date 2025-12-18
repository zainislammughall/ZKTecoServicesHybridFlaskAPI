from log_store import save_logs


def handle_push(data):
    if data is None:
        return False, "empty payload"

    records = []

    items = data if isinstance(data, list) else [data]

    for item in items:
        sn = (
            item.get("sn")
            or item.get("device_sn")
            or item.get("serial")
        )

        user_id = (
            item.get("id")
            or item.get("user")
            or item.get("pin")
            or item.get("employee_code")
        )

        timestamp = (
            item.get("timestamp")
            or item.get("time")
            or item.get("datetime")
        )

        in_out = (
            item.get("type")
            or item.get("status")
            or item.get("verified")
            or item.get("in_out_mode")
        )

        transaction_code = (
            item.get("transaction_code")
            or item.get("punch")
            or item.get("workcode")
            or item.get("verify_type")
        )

        if user_id is None or timestamp is None:
            continue

        try:
            in_out_mode = int(in_out) if in_out is not None else 0
        except:
            in_out_mode = 0

        try:
            transaction_code = int(transaction_code) if transaction_code is not None else None
        except:
            transaction_code = None

        records.append({
            "employee_code": str(user_id),
            "in_out_mode": in_out_mode,
            "transaction_code": transaction_code,
            "timestamp": timestamp,
            "device_sn": sn,
            "device_ip": item.get("device_ip")
        })

    if records:
        saved = save_logs(records)
        return True, f"saved {len(saved)} logs"

    return False, "no valid records"
