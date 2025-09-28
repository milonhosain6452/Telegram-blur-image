import os
import io
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageFilter, ImageDraw, ImageFont

# আপনার ইনফরমেশন
API_ID = 22134923
API_HASH = "d3e9d2f01d3291e87ea65298317f86b8"
BOT_TOKEN = "8285636468:AAFgGV80OtCP-NY2HelzOPFpYfdl0RiPJ7g"
OWNER_ID = 7383046042

# Pyrogram client
app = Client("blur_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def process_image(image_bytes):
    """Blur + add banner text"""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Blur (GaussianBlur)
    blurred = img.filter(ImageFilter.GaussianBlur(radius=8))

    # Draw text banner
    draw = ImageDraw.Draw(blurred)

    try:
        font = ImageFont.truetype("arial.ttf", 36)  # server-এ ডিফল্ট ফন্ট নাও থাকতে পারে
    except:
        font = ImageFont.load_default()

    text = "search = @avc641"
    text_w, text_h = draw.textsize(text, font=font)

    # ছবির উপরে random position না, সবসময় উপরে বসাই
    position = (10, 10)

    # ব্যাকগ্রাউন্ড rectangle
    draw.rectangle(
        [position, (position[0] + text_w + 20, position[1] + text_h + 10)],
        fill=(0, 0, 0, 127),
    )

    # টেক্সট বসানো
    draw.text((position[0] + 10, position[1] + 5), text, font=font, fill=(255, 255, 255))

    # Save to bytes
    output = io.BytesIO()
    blurred.save(output, format="JPEG")
    output.seek(0)
    return output


@app.on_message(filters.photo & ~filters.edited)
async def blur_photo(client: Client, message: Message):
    """Blur incoming photo"""
    try:
        # আসল caption বাদ দিই
        photo = await message.download(in_memory=True)
        processed = process_image(photo.getvalue())

        await message.reply_photo(
            processed,
            caption="✅ আপনার ছবিটি Blur করা হয়েছে",
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text("👋 হ্যালো! আমাকে কোনো ছবি পাঠান, আমি সেটিকে blur করে দেব।")


if __name__ == "__main__":
    app.run()
