import threading, time
from zkteco_poller import poll_device
from log_store import save_logs

class BackgroundPoller(threading.Thread):
    def __init__(self, config):
        super().__init__(daemon=True)
        self.config = config
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        interval = self.config.get('poll_interval_seconds', 30)
        devices = self.config.get('devices', [])
        timeout = self.config.get('poll_timeout_seconds', 5)
        while not self._stop.is_set():
            for d in devices:
                ip = d.get('ip') if isinstance(d, dict) else d
                port = d.get('port', 4370) if isinstance(d, dict) else 4370
                try:
                    logs = poll_device(ip, port=port, timeout=timeout)
                    if logs:
                        save_logs(logs)
                        print(f"[poller] saved {len(logs)} logs from {ip}")
                    else:
                        print(f"[poller] no logs from {ip}")
                except Exception as e:
                    print(f"[poller] error polling {ip}: {e}")
            time.sleep(interval)
