#!/usr/bin/env python3
import requests
import random
import time
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "https://api.beacondb.net/v1/geolocate"
HEADERS = {
    "User-Agent": "ratelimit-tester-multithread/1.0",
    "Content-Type": "application/json",
}


def random_bssid():
    return ":".join(f"{random.randint(0,255):02X}" for _ in range(6))


def send_request():
    bssid = random_bssid()
    payload = {
        "wifiAccessPoints": [
            {
                "macAddress": bssid,
                "signalStrength": -50
            }
        ]
    }

    try:
        resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=5)

        if resp.status_code == 200:
            data = resp.json()
            return resp.status_code, bssid, data

        return resp.status_code, bssid, None

    except Exception:
        return "network_error", bssid, None


def main():
    N = 1000
    THREADS = 20
    CSV_FILE = "results.csv"

    print(f"{N} requests with {THREADS} threads")

    statuses = {}
    start = time.time()
    found = 0

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bssid", "lat", "lon", "accuracy"])

        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            futures = [executor.submit(send_request) for _ in range(N)]

            for future in as_completed(futures):
                status, bssid, data = future.result()
                statuses[status] = statuses.get(status, 0) + 1

                if status == 200 and data is not None:
                    loc = data.get("location", {})
                    lat = loc.get("lat")
                    lon = loc.get("lng", loc.get("lon"))
                    acc = data.get("accuracy")

                    writer.writerow([bssid, lat, lon, acc])
                    found += 1

    duration = time.time() - start

    # Résumé
    print(f"\n Duration : {duration:.3f} sec")
    print("HTTP codes :")
    for status, count in statuses.items():
        print(f"  {status}: {count}")

    print(f"\nBSSIDs found : {found}")

if __name__ == "__main__":
    main()