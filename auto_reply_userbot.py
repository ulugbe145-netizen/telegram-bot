from telethon import TelegramClient, events
import json, os

api_id = 37672232  
api_hash = "5085bf7e8d8fab841a1b7084ef93929f"  
client = TelegramClient("session", api_id, api_hash)

AUTO_TEXT = "Bu avto javob ✅ Men hozir bandman, keyinroq javob beraman."

DB_FILE = "answered_users.json"
answered_users = set()

def load_db():
    global answered_users
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            answered_users = set(data.get("answered_users", []))
        except Exception:
            answered_users = set()

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({"answered_users": list(answered_users)}, f, ensure_ascii=False)

@client.on(events.NewMessage(incoming=True))
async def handler(event):
   
    if not event.is_private:
        return

    sender = await event.get_sender()

    
    if getattr(sender, "bot", False):
        return

        if getattr(sender, "contact", False):
        return

    
    if sender.id in answered_users:
        return

    await event.respond(AUTO_TEXT)
    answered_users.add(sender.id)
    save_db()

def main():
    load_db()
    client.start()
    client.run_until_disconnected()

if name == "main":
    main()