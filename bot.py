import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment Variables (Configured on Render)
TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://ufa343-bot.onrender.com
PORT = int(os.getenv("PORT", 8080))

# Initialize Gemini Client
if GEMINI_API_KEY:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    logger.error("GEMINI_API_KEY is missing!")
    ai_client = None

# System prompt to enforce strict translation behavior
TRANSLATION_PROMPT = (
    "You are an expert AI Translator for the Telegram bot ufa343_bot. "
    "Your sole task is to translate the provided text or image text into English. "
    "If the text is already in English, translate it into Spanish. "
    "Provide ONLY the direct translation. Do not include conversational filler, "
    "explanations, or notes."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_text = (
        "👋 Welcome to **ufa343_bot** — Your AI Translation Assistant!\n\n"
        "👉 **How to use:**\n"
        "1. Send me any text message, and I will automatically translate it.\n"
        "2. Send or forward me an image with text, and I will extract and translate it for you."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Translate incoming text messages using Gemini."""
    user_text = update.message.text
    
    if not ai_client:
        await update.message.reply_text("❌ Translation service is currently unavailable.")
        return

    # Send a typing placeholder actions for better UX
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=TRANSLATION_PROMPT,
                temperature=0.3,
            )
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"Error during text translation: {e}")
        await update.message.reply_text("⚠️ An error occurred while translating your text.")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Extract and translate text from photos."""
    if not ai_client:
        await update.message.reply_text("❌ Translation service is currently unavailable.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Get the highest resolution photo available
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        # Format image for the Google GenAI SDK
        image_part = types.Part.from_bytes(
            data=bytes(photo_bytes),
            mime_type="image/jpeg",
        )

        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_part, "Translate any text found in this image according to your system instructions."],
            config=types.GenerateContentConfig(
                system_instruction=TRANSLATION_PROMPT,
                temperature=0.3,
            )
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"Error during image translation: {e}")
        await update.message.reply_text("⚠️ Failed to extract or translate text from this image.")

def main() -> None:
    """Start the bot using Webhooks."""
    if not TOKEN or not WEBHOOK_URL:
        logger.critical("Missing vital environment variables (TOKEN or WEBHOOK_URL). Exiting.")
        return

    # Build the application
    application = Application.builder().token(TOKEN).build()

    # Register Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # Run via Webhook compatible with Render's dynamic ports
    logger.info(f"Starting webhook on port {PORT} with URL {WEBHOOK_URL}")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
