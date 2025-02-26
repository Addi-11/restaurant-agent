import json

def load_restaurant_kb():
    with open("knowledge_base/restaurant_db.json", "r") as f:
        return json.load(f)

def load_menu_kb():
    with open("knowledge_base/menu.json", "r") as f:
        return json.load(f)

restaurant_kb = load_restaurant_kb()
menu_kb = load_menu_kb()