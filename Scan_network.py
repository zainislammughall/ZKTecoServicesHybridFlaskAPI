from flask import Flask, jsonify
import socket
import json
import concurrent.futures
import os

CONFIG_FILE = "config.json"
SCAN_PORT = 4370

#       CONFIG HANDLERS        #

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"devices": []}
    
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

#        DEVICE SCANNER        #

def check_device(ip):
    try:
        s = socket.socket()
        s.settimeout(0.3)
        s.connect((ip, SCAN_PORT))
        s.close()
        return ip
    except:
        return None


def scan_network(base_ip="192.168.1."):
    detected = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor:
        futures = {
            executor.submit(check_device, f"{base_ip}{i}"): i
            for i in range(1, 255)
        }

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                detected.append(result)

    return detected
