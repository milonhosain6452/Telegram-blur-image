import os
import io
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageFilter, ImageDraw, ImageFont

# --- Bot credentials ---
API_ID = 22134923
API_HASH = "d3e9d2f01d3291e87ea65298317f86b8"
BOT_TOKEN = "8285636468:AAFgGV80OtCP-NY2HelzOPFpYfdl0RiPJ7g"
OWNER_ID = 7383046042

# --- Pyrogram client ---
app_bot = Client("blur_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def process_image(image_bytes):
    """Blur + add banner text"""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Blur (GaussianBlur)
    blurred = img.filter(ImageFilter.GaussianBlur(radius=8))

    # Draw text banner
    draw = ImageDraw.Draw(blurred)
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()

    text = "search = @avc641"
    text_w, text_h = draw.textsize(text, font=font)

    # Position top-left
    position = (10, 10)

    # Background rectangle
    draw.rectangle(
        [position, (position[0] + text_w + 20, position[1] + text_h + 10)],
        fill=(0, 0, 0, 127),
    )

    # Text
    draw.text((position[0] + 10, position[1] + 5), text, font=font, fill=(255, 255, 255))

    # Save to bytes
    output = io.BytesIO()
    blurred.save(output, format="JPEG")
    output.seek(0)
    return output


# --- Bot Handlers ---

@app_bot.on_message(filters.photo & ~filters.edited)
async def blur_photo(client: Client, message: Message):
    try:
        photo = await message.download(in_memory=True)
        processed = process_image(photo.getvalue())

        await message.reply_photo(
            processed,
            caption="✅ আপনার ছবিটি Blur করা হয়েছে"
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@app_bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text("👋 হ্যালো! আমাকে কোনো ছবি পাঠান, আমি সেটিকে blur করে দেব।")


# --- Flask web server (for Render) ---
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"


def run_bot():
    app_bot.run()


if __name__ == "__main__":
    # Start bot in a thread
    threading.Thread(target=run_bot).start()

    # Run flask server
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)
