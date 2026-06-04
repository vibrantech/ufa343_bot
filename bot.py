import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# 1. SETUP & CONFIGURATION
# Load environment variables for local testing (Render ignores this and uses dashboard variables)
load_dotenv()

# Enable system logging so you can monitor bot activities in the Render logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Retrieve API tokens securely from Render environment configurations
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize the official Gemini AI Client
ai_client = genai.Client(api_key=GEMINI_API_KEY)


# 2. BOT COMMAND HANDLERS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcoming greeting when a user types /start."""
    # Using HTML tags (<b>) here so underscores like ufa343_bot won't break the parser
    welcome_text = (
        "👋 Welcome to <b>ufa343_bot</b>!\n\n"
        "I am an advanced AI Translator. Simply send me any text or phrase, "
        "and tell me what language you want it translated to, or just type standard text "
        "and I will instantly translate it to English by default!"
    )
    await update.message.reply_text(welcome_text, parse_mode="HTML")


# 3. AI TRANSLATION LOGIC
async def handle_translation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processes incoming text and utilizes Gemini AI to translate it."""
    user_text = update.message.text
    
    # Send an interim placeholder message to show the bot is actively processing
    processing_msg = await update.message.reply_text("🔄 Processing AI Translation...")

    try:
        # Prompt instructing the AI model to behave specifically as a precise translator engine
        prompt = (
            f"You are an expert AI translator engine operating inside a Telegram bot named ufa343_bot. "
            f"Analyze the following text, detect its source language, and translate it fluently. "
            f"If the user specifies a target language in their text (e.g., 'Translate this to Spanish: ...'), "
            f"translate it into that language. Otherwise, translate it into clear, natural English.\n\n"
            f"Text to translate:\n\"{user_text}\"\n\n"
            f"Return ONLY the translated final text. Do not add conversational remarks or extra quotes."
        )

        # Call the Gemini AI model (gemini-2.5-flash)
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        translated_result = response.text.strip()

        # Update the placeholder message with the real answer
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_msg.message_id,
            text=translated_result
        )

    except Exception as e:
        logger.error(f"Translation Error: {e}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_msg.message_id,
            text="⚠️ Sorry, an error occurred while processing your AI translation. Please try again later."
        )


# 4. APPLICATION INITIALIZATION
def main() -> None:
    """Starts the application background engine."""
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("Missing TELEGRAM_BOT_TOKEN environment variable.")
        return

    # Build the core telegram application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register workflow application handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_translation))

    # Drop pending updates on startup ensures the bot doesn't crash on backlogs
    logger.info("ufa343_bot is starting active polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
