# bot.py
"""
Telegram bot that:
- Accepts forwarded photos (or any photos sent to the bot).
- Removes any caption text and returns a blurred version of the photo.
- Overlays a small banner-like text "search = @avc641" on each image.
- Runs a small Flask webserver endpoint so it can be deployed on Render (or similar).
"""

import os
import threading
import tempfile
from flask import Flask, Response

from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageFilter, ImageDraw, ImageFont

# --------------------------
# =========== CONFIG ============
# Use the credentials you provided
API_ID = 22134923
API_HASH = "d3e9d2f01d3291e87ea65298317f86b8"
BOT_TOKEN = "8285636468:AAFPRQ1oS1N3I4MBI85RFEOZXW4pwBrWHLg"
OWNER_ID = 7383046042  # not strictly required but kept

# Text for small banner
BANNER_TEXT = "search = @avc641"

# Blur settings - moderate blur. Tweak radius if you want stronger/weaker
BLUR_RADIUS = 12

# --------------------------
# Initialize Pyrogram client (bot)
app_client = Client(
    "blurbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    # workdir=os.getcwd()  # optional
)

# Helper: process image path -> output path
def process_image(input_path: str, output_path: str) -> None:
    """
    Open image, apply moderate blur, overlay a small semi-transparent banner with text,
    and save to output_path (JPEG/PNG auto).
    """
    with Image.open(input_path) as im:
        # Ensure RGBA for transparency operations
        im = im.convert("RGBA")
        w, h = im.size

        # Apply Gaussian blur
        blurred = im.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))

        # Create overlay for banner
        overlay = Image.new("RGBA", blurred.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        # Choose font size relative to image width
        try:
            # try to use a truetype font if available
            font_size = max(14, w // 25)
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        # Text size
        text_w, text_h = draw.textsize(BANNER_TEXT, font=font)

        # Banner rectangle padding
        pad_x = int(font_size * 0.6)
        pad_y = int(font_size * 0.4)

        # Position banner — try bottom-right with some margin, but it can be anywhere
        margin = int(max(8, w * 0.02))
        rect_x1 = w - text_w - pad_x * 2 - margin
        rect_y1 = h - text_h - pad_y * 2 - margin
        rect_x2 = w - margin
        rect_y2 = h - margin

        # Draw semi-transparent dark rectangle
        rect_color = (0, 0, 0, 160)  # semi-transparent black
        draw.rectangle([rect_x1, rect_y1, rect_x2, rect_y2], fill=rect_color, outline=None)

        # Draw text in white centered in the rectangle
        text_x = rect_x1 + pad_x
        text_y = rect_y1 + pad_y
        draw.text((text_x, text_y), BANNER_TEXT, font=font, fill=(255, 255, 255, 255))

        # Composite overlay onto blurred image
        result = Image.alpha_composite(blurred, overlay)

        # Convert back to RGB to save as JPEG without alpha
        if output_path.lower().endswith((".jpg", ".jpeg")):
            result = result.convert("RGB")
        result.save(output_path)

# ---------- Handlers ----------
@app_client.on_message(filters.photo)
def handle_photo(client: Client, message: Message):
    """
    When a photo is received (including forwarded), download the best size,
    process (blur + banner), remove caption, and send back to the chat.
    """
    chat_id = message.chat.id  # send reply to the same chat where photo came from

    # Use temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # download the largest available photo
            in_path = os.path.join(tmpdir, "in_image")
            out_path = os.path.join(tmpdir, "out_image.jpg")

            # message.photo.download automatically picks file name ext if provided; give path prefix
            message.download(file_name=in_path)

            # PIL needs proper extension; ensure input has extension — pyrogram may save with no ext
            # Try to open without extension; PIL can detect format, so process_image will work.
            process_image(in_path, out_path)

            # Send the processed image with NO caption (removes forwarded caption)
            # If you prefer to send to OWNER only: use OWNER_ID instead of chat_id
            client.send_photo(chat_id=chat_id, photo=out_path, caption="")

        except Exception as e:
            # On error, notify owner (optional) and inform the user minimally
            try:
                err_msg = f"Processing failed: {e}"
                client.send_message(chat_id=OWNER_ID, text=f"Error in blur-bot:\n{err_msg}")
            except Exception:
                pass
            # send a short failure message to user
            try:
                client.send_message(chat_id=chat_id, text="দুঃখিত — ছবিটি প্রক্রিয়াকরণে সমস্যা হয়েছে। আবার চেষ্টা করুন।")
            except Exception:
                pass

# Optional: ignore captions and only take image — above sending used caption="" so caption removed.

# --------------------------
# Small Flask app for Render (or other PaaS) keep-alive and health-check
flask_app = Flask(__name__)

@flask_app.route("/", methods=["GET"])
def index():
    return Response("Blur Bot is running.", mimetype="text/plain")

# Start pyrogram client in background thread so Flask can run on main thread
def start_pyrogram():
    # client.run() blocks; run it inside a thread
    app_client.run()  # this will start, idle, and stop on termination

if __name__ == "__main__":
    # Start pyrogram bot in a daemon thread
    t = threading.Thread(target=start_pyrogram, daemon=True)
    t.start()

    # Run Flask. On Render, the PORT env var is provided; else default 5000
    port = int(os.environ.get("PORT", 5000))
    # NOTE: in production you may use gunicorn; for quick Render usage Flask dev server often ok.
    flask_app.run(host="0.0.0.0", port=port)import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import io

# লগিং সেটআপ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# বটের তথ্য
API_ID = 22134923
API_HASH = 'd3e9d2f01d3291e87ea65298317f86b8'
BOT_TOKEN = '8285636468:AAFPRQ1oS1N3I4MBI85RFEOZXW4pwBrWHLg'
OWNER_ID = 7383046042

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ছবি প্রসেস করার ফাংশন"""
    try:
        if update.message.photo:
            # ছবি ডাউনলোড করুন
            photo = update.message.photo[-1]
            file = await photo.get_file()
            
            # ছবি মেমোরিতে লোড করুন
            photo_bytes = await file.download_as_bytearray()
            image = Image.open(io.BytesIO(photo_bytes))
            
            # ছবিকে RGB-তে কনভার্ট করুন (যদি প্রয়োজন হয়)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # ছবিতে blur প্রয়োগ করুন
            blurred_image = image.filter(ImageFilter.GaussianBlur(radius=8))
            
            # ওয়াটারমার্ক যোগ করুন
            draw = ImageDraw.Draw(blurred_image)
            
            try:
                # ফন্ট লোড করার চেষ্টা করুন (Render-এ available ফন্ট ব্যবহার করুন)
                font = ImageFont.truetype("arial.ttf", 30)
            except:
                # যদি ফন্ট না মেলে, ডিফল্ট ফন্ট ব্যবহার করুন
                font = ImageFont.load_default()
            
            # ওয়াটারমার্ক টেক্সট
            watermark_text = "search = @avc641"
            
            # টেক্সট সাইজ বের করুন
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # ইমেজ সাইজ
            img_width, img_height = blurred_image.size
            
            # ওয়াটারমার্কের অবস্থান (উপরের ডান কোণায়)
            x = img_width - text_width - 20
            y = 20
            
            # টেক্সট ব্যাকগ্রাউন্ড
            padding = 5
            draw.rectangle(
                [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
                fill='black'
            )
            
            # টেক্সট যোগ করুন
            draw.text((x, y), watermark_text, font=font, fill='white')
            
            # প্রসেসড ইমেজ সেভ করুন
            output = io.BytesIO()
            blurred_image.save(output, format='JPEG', quality=85)
            output.seek(0)
            
            # ইউজারকে ইমেজ পাঠান
            await update.message.reply_photo(
                photo=output,
                caption="✅ আপনার ছবিটি blur করা হয়েছে"
            )
            
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("❌ ছবি প্রসেস করতে সমস্যা হয়েছে। দয়া করে আবার চেষ্টা করুন।")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """স্টার্ট কমান্ড হ্যান্ডলার"""
    await update.message.reply_text(
        "👋 হ্যালো! আমি একটি ইমেজ ব্লারিং বট।\n\n"
        "আমাকে কোনো ছবি ফরওয়ার্ড করুন অথবা সরাসরি পাঠান, আমি সেটিকে blur করে আপনার কাছে ফেরত দিব।"
    )

def main() -> None:
    """মেইন ফাংশন"""
    # বট অ্যাপ্লিকেশন তৈরি করুন
    application = Application.builder().token(BOT_TOKEN).build()
    
    # হ্যান্ডলার যোগ করুন
    application.add_handler(MessageHandler(filters.PHOTO, process_image))
    application.add_handler(MessageHandler(filters.Command("start"), start))
    
    # Render-এ deployment এর জন্য
    port = int(os.environ.get('PORT', 5000))
    webhook_url = os.environ.get('WEBHOOK_URL', '')
    
    if webhook_url:
        # Webhook mode (Production)
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=BOT_TOKEN,
            webhook_url=f"{webhook_url}/{BOT_TOKEN}"
        )
    else:
        # Polling mode (Development)
        application.run_polling()

if __name__ == '__main__':
    main()
