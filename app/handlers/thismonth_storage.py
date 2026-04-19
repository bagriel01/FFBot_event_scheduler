import json
import os
from datetime import datetime as dt

STORAGE_FILE = "thismonth_storage.json"

def load_data():
    if not os.path.exists(STORAGE_FILE):
        return {}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return {}
        return json.loads(content)  
def save_data(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_post(date: dt, message_id: int, chat_id: int):
   year = str(date.year)
   month = date.strftime("%m")
   day = date.strftime("%d")

   data = load_data()
   data.setdefault(year, {}).setdefault(month, {}). setdefault(day, [])
   data[year][month][day].append({
         "chat_id": chat_id,
         "message_id": message_id,
    })
   save_data(data)

def get_posts_this_month(year: int, month: int):
    data = load_data()
    month_data = data.get(str(year), {}).get(f"{month:02d}", {})

    return [
        (day, entry)
        for day, entries in month_data.items()
        for entry in month_data[day]
    ]
