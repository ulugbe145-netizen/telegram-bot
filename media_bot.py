import os
import re
import subprocess
from pathlib import Path

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

TOKEN = "7888337225:AAGxWPQI9IAdvlbgOl6ATbmO1-pD4bNPUWA"

WORKDIR = Path("work")
WORKDIR.mkdir(exist_ok=True)

MUSIC_TRIGGERS = re.compile(
    r"^(muzika|musiqa|music|song|audio|музыка|песня|трек|اغنية|أغنية|موسيقى|نشيد)$",
    re.IGNORECASE
)

def run_ffmpeg_extract_mp3(input_path: Path, output_path: Path) -> None:
    """
    Extract audio to MP3. Requires ffmpeg installed & in PATH.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-vn",                  # no video
        "-acodec", "libmp3lame",
        "-q:a", "2",            # good quality VBR
        str(output_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
      pass
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Video yuboring — men sizga 🎬 Video va 🎵 Muzika tugmalarini chiqaraman."
    )

async def on_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    tg_file = None

    if msg.video:
        tg_file = msg.video
    elif msg.document and (msg.document.mime_type or "").startswith("video/"):
        tg_file = msg.document
    else:
        return

    file_id = tg_file.file_id
    context.user_data["last_file_id"] = file_id

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 Video", callback_data="send_video"),
            InlineKeyboardButton("🎵 Muzika", callback_data="send_audio"),
        ]
    ])

    await msg.reply_text("Tanlang:", reply_markup=keyboard)

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    if not MUSIC_TRIGGERS.match(txt):
        return

    if "last_file_id" not in context.user_data:
        await update.message.reply_text("Avval video yuboring, keyin 🎵 Muzika.")
        return

    await send_audio_from_last(update, context)

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "send_video":
        await send_video_from_last(update, context)
    elif data == "send_audio":
        await send_audio_from_last(update, context)

async def send_video_from_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    file_id = context.user_data.get("last_file_id")
    if not file_id:
        await query.message.reply_text("Avval video yuboring.")
        return
    await query.message.reply_video(video=file_id, caption="🎬 Mana video.")

async def send_audio_from_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat = query.message.chat if query else update.message.chat

    file_id = context.user_data.get("last_file_id")
    if not file_id:
        if query:
            await query.message.reply_text("Avval video yuboring.")
        else:
            await update.message.reply_text("Avval video yuboring.")
        return

    tg = context.bot
    tg_file = await tg.get_file(file_id)

    input_path = WORKDIR / f"{file_id}.mp4"
    output_path = WORKDIR / f"{file_id}.mp3"

    await tg_file.download_to_drive(custom_path=str(input_path))
    try:
        run_ffmpeg_extract_mp3(input_path, output_path)
    except Exception:
        await tg.send_message(chat_id=chat.id, text="Audio tayyorlashda muammo bo‘ldi. Boshqa video yuboring.")
        return
    finally:
        if input_path.exists():
            try:
                input_path.unlink()
            except Exception:
                pass

    await tg.send_audio(
        chat_id=chat.id,
        audio=open(output_path, "rb"),
        filename="audio.mp3",
        caption="🎵 Mana audio.",
    )

    try:
        output_path.unlink()
    except Exception:
        pass

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.VIDEO | (filters.Document.VIDEO), on_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling()

if __name__ == "__main__":
    main()