import os
import logging
from telebot import TeleBot, types
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import requests
import io

# Configuration
API_ID = int(os.environ.get('API_ID', '22134923'))
API_HASH = os.environ.get('API_HASH', 'd3e9d2f01d3291e87ea65298317f86b8')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8285636468:AAFPRQ1oS1N3I4MBI85RFEOZXW4pwBrWHLg')
OWNER_ID = int(os.environ.get('OWNER_ID', '7383046042'))

# Initialize bot
bot = TeleBot(BOT_TOKEN)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_image(file_id):
    """Download image from Telegram"""
    try:
        file_info = bot.get_file(file_id)
        file_url = f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}'
        
        response = requests.get(file_url)
        response.raise_for_status()
        
        image = Image.open(io.BytesIO(response.content))
        return image
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return None

def add_watermark(image):
    """Add watermark to image"""
    try:
        # Convert PIL image to OpenCV format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Apply blur effect
        blurred_image = cv2.GaussianBlur(opencv_image, (25, 25), 0)
        
        # Convert back to PIL
        blurred_pil = Image.fromarray(cv2.cvtColor(blurred_image, cv2.COLOR_BGR2RGB))
        
        # Add watermark text
        draw = ImageDraw.Draw(blurred_pil)
        
        try:
            # Try to use a font
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        watermark_text = "search = @avc641"
        
        # Get text size
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position (top right corner with some margin)
        width, height = blurred_pil.size
        x = width - text_width - 10
        y = 10
        
        # Add background for better visibility
        draw.rectangle([x-5, y-5, x+text_width+5, y+text_height+5], fill=(0,0,0,128))
        
        # Add text
        draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255))
        
        return blurred_pil
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return None

def convert_to_bytes(image):
    """Convert PIL image to bytes"""
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Send welcome message"""
    welcome_text = """
🤖 **Blur Bot Welcome!**

**How to use:**
1. Send me any image
2. Forward images to me
3. I'll blur them and add watermark

**Features:**
• Automatic image blurring
• Text caption removal
• Watermark addition
• Moderate blur effect

Made with ❤️ for Telegram
    """
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    """Handle photo messages"""
    try:
        # Send processing message
        processing_msg = bot.reply_to(message, "🔄 Processing your image...")
        
        # Get the highest quality photo
        file_id = message.photo[-1].file_id
        
        # Download image
        original_image = download_image(file_id)
        if not original_image:
            bot.edit_message_text("❌ Error downloading image", 
                                chat_id=message.chat.id, 
                                message_id=processing_msg.message_id)
            return
        
        # Process image (blur + watermark)
        processed_image = add_watermark(original_image)
        if not processed_image:
            bot.edit_message_text("❌ Error processing image", 
                                chat_id=message.chat.id, 
                                message_id=processing_msg.message_id)
            return
        
        # Convert to bytes
        image_bytes = convert_to_bytes(processed_image)
        
        # Update status
        bot.edit_message_text("📤 Sending processed image...", 
                            chat_id=message.chat.id, 
                            message_id=processing_msg.message_id)
        
        # Send processed image
        bot.send_photo(message.chat.id, image_bytes, 
                      caption="✅ Image processed with blur effect\nSearch = @avc641")
        
        # Delete processing message
        bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        
    except Exception as e:
        logger.error(f"Error in handle_photos: {e}")
        bot.reply_to(message, "❌ An error occurred while processing your image")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Handle text messages"""
    if message.text.startswith('/'):
        bot.reply_to(message, "❓ Unknown command. Use /start for help")
    else:
        bot.reply_to(message, "📷 Please send me an image to process!")

def main():
    """Main function to start the bot"""
    logger.info("Starting Telegram Bot...")
    
    try:
        # Delete webhook if exists and use polling
        bot.remove_webhook()
        
        logger.info("Bot is running and waiting for messages...")
        bot.infinity_polling()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()
