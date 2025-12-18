import datetime

try:
    from zk import ZK, const
    _HAS_ZK = True
except Exception:
    ZK = None
    const = None
    _HAS_ZK = False


def poll_device(ip, port=4370, timeout=5):
    results = []

    if not _HAS_ZK:
        raise RuntimeError("python package 'zk' not installed. Install: pip install zk")

    conn = None

    try:
        zk = ZK(ip, port=port, timeout=timeout)
        conn = zk.connect()
        attendance = conn.get_attendance()

        for att in attendance:
            try:
                user_id = att[0]
                ts = att[1]
                status = att[2] if len(att) > 2 else 0
                transaction_code = att[3] if len(att) > 3 else None

                if isinstance(ts, str):
                    try:
                        ts = datetime.datetime.fromisoformat(ts)
                    except:
                        pass

                results.append({
                    "employee_code": str(user_id),
                    "in_out_mode": int(status) if status is not None else 0,
                    "transaction_code": int(transaction_code) if transaction_code is not None else None,
                    "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                    "device_ip": ip
                })

            except Exception:
                continue

        try:
            conn.disconnect()
        except:
            pass

    except Exception:
        raise

    return results
