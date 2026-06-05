import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# 1. SETUP & CONFIGURATION
load_dotenv()

# เปิดระบบการบันทึก Log ของระบบ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ดึงข้อมูล API Tokens จากค่า Environment Variables บน Render
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# เริ่มต้นเปิดใช้งานโมเดล Gemini AI Client
ai_client = genai.Client(api_key=GEMINI_API_KEY)


# 2. BOT COMMAND HANDLERS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ส่งข้อความต้อนรับเมื่อผู้ใช้พิมพ์คำสั่ง /start"""
    # ข้อความต้อนรับภาษาไทยสำหรับตั้งค่าโฆษณา (ใช้ระบบ HTML ป้องกันสัญลักษณ์จม)
    welcome_text = (
        "👋 ยินดีต้อนรับสู่ <b>ufa343_bot</b>!\n\n"
        "ฉันคือระบบแปลภาษาอัจฉริยะ AI ขั้นสูง 🤖✨\n"
        "เพียงแค่คุณส่งข้อความหรือประโยคใด ๆ ที่ต้องการแปลมาให้ฉัน "
        "พร้อมระบุภาษาที่ต้องการ (เช่น แปลเป็นภาษาไทย: ...) "
        "หรือพิมพ์ข้อความทั่วไปเข้ามา ระบบจะแปลเป็นภาษาไทยให้คุณโดยอัตโนมัติทันที!"
    )
    await update.message.reply_text(welcome_text, parse_mode="HTML")


# 3. AI TRANSLATION LOGIC
async def handle_translation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ประมวลผลข้อความที่ส่งเข้ามา และใช้ Gemini AI ในการแปลภาษา"""
    user_text = update.message.text
    
    # ส่งข้อความสถานะแจ้งให้ผู้ใช้ทราบว่าระบบกำลังทำงาน
    processing_msg = await update.message.reply_text("🔄 ระบบ AI กำลังดำเนินการแปลภาษาของคุณ...")

    try:
        # คำสั่งสเปกสำหรับให้ AI ตรวจสอบและแปลภาษาต้นทางออกมาเป็นภาษาไทยอย่างเป็นธรรมชาติ
        prompt = (
            f"You are an expert AI translator engine operating inside a Telegram bot named ufa343_bot. "
            f"Analyze the following text, detect its source language, and translate it fluently. "
            f"If the user specifies a target language in their text (e.g., 'แปลเป็นภาษาญี่ปุ่น: ...'), "
            f"translate it into that requested language. Otherwise, translate it into clear, natural, and fluent Thai (ภาษาไทย) by default.\n\n"
            f"Text to translate:\n\"{user_text}\"\n\n"
            f"Return ONLY the translated final text. Do not add conversational remarks, explanations, or extra quotes."
        )

        # เรียกใช้งานโมเดಲ Gemini AI (gemini-2.5-flash)
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        translated_result = response.text.strip()

        # อัปเดตเปลี่ยนข้อความจากเดิมที่เป็นสถานะกำลังโหลด ให้เป็นผลลัพธ์การแปลที่เสร็จสิ้น
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
            text="⚠️ ขออภัยด้วยค่ะ เกิดข้อผิดพลาดในระบบระหว่างประอยประมวลผลแปลภาษา กรุณาลองใหม่อีกครั้งในภายหลัง"
        )


# 4. APPLICATION INITIALIZATION
def main() -> None:
    """เริ่มต้นระบบการทำงานหลักของบอตเบื้องหลัง"""
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("Missing TELEGRAM_BOT_TOKEN environment variable.")
        return

    # สร้างแอปพลิเคชันเชื่อมโยงกับทาง Telegram API
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # ลงทะเบียนคำสั่งและตัวดักจับข้อความ
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_translation))

    # คำสั่งเคลียร์คิวข้อความเก่าตกค้างเพื่อป้องกันระบบบอตค้างตอนรันเซิร์ฟเวอร์ใหม่
    logger.info("ufa343_bot is starting active polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
