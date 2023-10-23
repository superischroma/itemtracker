import http.client
import json
import time
import numpy
from win10toast import ToastNotifier

PERIOD = 1

items: dict[str, list[int]] = {"Ender Artifact": [], "Bedrock": []}

def req_ah(page: int=0):
    conn = http.client.HTTPSConnection("api.hypixel.net", 443)
    try:
        conn.request("GET", f"/skyblock/auctions?page={page}")
    except Exception:
        return None
    resp = conn.getresponse()
    if resp.status != 200:
        return None
    return json.loads(resp.read().decode())

def send_notif(message: str, duration: int=5):
    toast.show_toast("Item Tracker", message, duration=duration, icon_path="icon.ico")
    print(f"[Notification] {message}")

def wait(secs):
    t = time.time()
    while time.time() < t + secs:
        time_diff = time.gmtime(t + secs - time.time())
        next_update = time.localtime(t + secs)
        print(f"{time_diff.tm_hour}:{time_diff.tm_min:02}:{time_diff.tm_sec:02} left until next update ({next_update.tm_hour}:{next_update.tm_min:02}:{next_update.tm_sec:02})")
        time.sleep(10)
    time.sleep(5)

toast = ToastNotifier()
while True:
    test = req_ah()
    if test is None:
        send_notif("Hypixel API down", 3)
        wait(300)
        continue
    send_notif("Pulling item data...", 3)
    pages = int(test["totalPages"])
    broke = False
    for i in range(pages):
        data = req_ah(i)
        if data is None:
            send_notif("Hypixel API down", 3)
            broke = True
            break
        auctions = data["auctions"]
        for auction in auctions:
            if not auction["bin"]:
                continue
            if auction["start"] < (time.time() * 1000) - (8.64e7 * PERIOD):
                continue
            item_name = auction["item_name"]
            if item_name in items:
                items[item_name].append(auction["starting_bid"])
    if broke:
        wait(300)
        continue
    for item in items:
        if len(items[item]) == 0:
            send_notif(f"No {item}s found currently", 3)
        else:
            q3, q1 = numpy.percentile(items[item], [75, 25])
            iqr = q3 - q1
            items[item] = [i for i in items[item] if q1 - iqr * 1.5 < i < q3 + iqr * 1.5]
            send_notif(f"{item}: {(sum(items[item]) / len(items[item])):,.0f} coins")
        items[item].clear()
    next_update = time.localtime(time.time() + 3600)
    send_notif(f"Next update at {next_update.tm_hour}:{next_update.tm_min:02}:{next_update.tm_sec:02}", 3)
    wait(3600)