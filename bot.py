import os
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
