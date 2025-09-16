# relay_bot.py
import telebot
import json
import os

# ====== Настройки ======
TOKEN = "8264933479:AAGF-ewCvb_tWYxIxAfZN3yY1fFxWpwIv5U"  # <- токен бота
OWNER_ID = 7228049767  # <- твой Telegram user id (число без кавычек)

MAPPINGS_FILE = "mappings.json"

bot = telebot.TeleBot(TOKEN, parse_mode=None)

# ====== Загрузка/сохранение соответствий ======
if os.path.exists(MAPPINGS_FILE):
    try:
        with open(MAPPINGS_FILE, "r", encoding="utf-8") as f:
            mappings = json.load(f)
    except Exception:
        mappings = {}
else:
    mappings = {}

def save_mappings():
    with open(MAPPINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(mappings, f, ensure_ascii=False, indent=2)

# ====== Утилиты ======
def forward_message_to_owner(from_chat_id, msg):
    try:
        forwarded = bot.forward_message(OWNER_ID, from_chat_id, msg.message_id)
        owner_mid = str(forwarded.message_id)
        mappings[owner_mid] = {"chat_id": from_chat_id, "orig_msg_id": msg.message_id}
        save_mappings()
        print(f"✅ Переслал сообщение от {from_chat_id} владельцу.")
    except Exception as e:
        print("❌ Ошибка при пересылке владельцу:", e)

def send_content_to_target(target_chat_id, owner_reply):
    try:
        ct = owner_reply.content_type
        if ct == "text":
            bot.send_message(target_chat_id, owner_reply.text)
        elif ct == "photo":
            bot.send_photo(target_chat_id, owner_reply.photo[-1].file_id, caption=owner_reply.caption)
        elif ct == "video":
            bot.send_video(target_chat_id, owner_reply.video.file_id, caption=owner_reply.caption)
        elif ct == "document":
            bot.send_document(target_chat_id, owner_reply.document.file_id, caption=owner_reply.caption)
        elif ct == "voice":
            bot.send_voice(target_chat_id, owner_reply.voice.file_id, caption=getattr(owner_reply, "caption", None))
        elif ct == "audio":
            bot.send_audio(target_chat_id, owner_reply.audio.file_id, caption=getattr(owner_reply, "caption", None))
        elif ct == "video_note":
            bot.send_video_note(target_chat_id, owner_reply.video_note.file_id)
        elif ct == "sticker":
            bot.send_sticker(target_chat_id, owner_reply.sticker.file_id)
        elif ct == "animation":
            bot.send_animation(target_chat_id, owner_reply.animation.file_id, caption=getattr(owner_reply, "caption", None))
        else:
            # fallback — переслать как есть
            bot.forward_message(target_chat_id, owner_reply.chat.id, owner_reply.message_id)
        print(f"📤 Отправлено сообщение пользователю {target_chat_id}")
    except Exception as e:
        print("❌ Ошибка отправки пользователю:", e)

# ====== Хендлеры ======
@bot.message_handler(commands=['start'])
def handle_start(message):
    # Просто фиксируем факт старта, ничего не отвечаем
    print(f"▶️ /start от {message.from_user.id}")

@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.from_user.id != OWNER_ID,
                     content_types=['text','photo','document','voice','audio','video','sticker','video_note','animation'])
def handle_incoming_from_user(message):
    from_chat = message.chat.id
    print(f"📩 Сообщение от {from_chat}: {message.content_type}")
    forward_message_to_owner(from_chat, message)

@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.from_user.id == OWNER_ID)
def handle_owner_message(message):
    if not message.reply_to_message:
        bot.send_message(OWNER_ID, "ℹ️ Чтобы ответить пользователю — сделай Reply на пересланное сообщение.")
        return

    replied_mid = str(message.reply_to_message.message_id)
    info = mappings.get(replied_mid)
    if not info:
        bot.send_message(OWNER_ID, "⚠️ Не нашёл кому отвечать (возможно старое сообщение).")
        return

    target_chat = info["chat_id"]
    send_content_to_target(target_chat, message)

# ====== Запуск ======
if __name__ == "__main__":
    print("🤖 Relay bot запущен. OWNER_ID =", OWNER_ID)
    bot.infinity_polling(timeout=10, long_polling_timeout=60)
