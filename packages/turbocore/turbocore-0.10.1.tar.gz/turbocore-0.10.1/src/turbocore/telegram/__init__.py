import time
import requests
import os
from rich.pretty import pprint as PP

# max msg size 4k


def rq_get(method):
    url = "https://api.telegram.org/bot" + os.environ.get("BT", "None") + "/" + method
    res = requests.get(url, headers={"Accept": "application/json", "Content-Type": "application/json"})
    return res


def rq_post_json(method, obj):
    url = "https://api.telegram.org/bot" + os.environ.get("BT", "None") + "/" + method
    #res = requests.post(url, json=obj, headers={"Accept": "application/json", "Content-Type": "application/json"})
    res = requests.post(url, json=obj)
    return res

# last_update_id
lui = 0

def safe_parse_text(src):
    return src


def download_updates(timeout=0):
    global lui
    lui += 1
    res = rq_get("getUpdates?offset=%d&timeout=%d" % (lui, timeout))
    if res.status_code == 200:
        data = res.json()
        res = []
        if len(data["result"]) > 0:
            for u in data["result"]:
                entry = {}
                lui = int(u["update_id"])

                try:
                    entry["chat_id"] = int(u["message"]["chat"]["id"])
                    entry["from_id"] = int(u["message"]["from"]["id"])
                    entry["t"] = int(u["message"]["date"])
                    entry["text"] = safe_parse_text(u["message"]["text"])
                    if u["message"]["chat"]["type"] in ["group", "supergroup"]:
                        res.append(entry)
                except:
                    pass
            return res
    return []


def process_updates():
    u = download_updates(10)
    if len(u) > 0:
        PP(u)
    time.sleep(1)


def main():
    #PP(rq_get("getMe").json())
    while True:
        process_updates()
    return
    res = rq_post_json("sendMessage", {
        "chat_id": os.environ.get("COCO"),
        "parse_mode": "MarkdownV2",
        "text": """__okay__ and more

```bash
print(ok)
```

|| spoiler ||
"""
    })
    PP(res.json())
