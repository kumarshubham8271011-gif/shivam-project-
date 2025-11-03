import os, replicate, asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# Load env
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# Safety checks
if not BOT_TOKEN or not REPLICATE_API_TOKEN:
    raise SystemExit("Error: Please set TELEGRAM_BOT_TOKEN and REPLICATE_API_TOKEN in the .env file before running.")

# Bot username (for captions / link) - kept for display, not used to control bot
BOT_USERNAME = "@ReminiAIPhotoEnhancer_bot"
CREDIT_HANDLE = "@CipherShivamX"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def enhance_with_replicate(image_url):
    """
    Uses Replicate to run Real-ESRGAN (upscale) then GFPGAN (face restore).
    This function returns a URL (or bytes) depending on the model response.
    Make sure your Replicate token has access and usage limits accordingly.
    """
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    # Real-ESRGAN upscale
    try:
        realesrgan = client.models.get("nightmareai/real-esrgan")
        enhanced = realesrgan.predict(image=image_url, scale=4)
    except Exception as e:
        raise RuntimeError(f"Real-ESRGAN call failed: {e}")

    # GFPGAN face restore (optional)
    try:
        gfpgan = client.models.get("tencentarc/gfpgan")
        restored = gfpgan.predict(img=enhanced)
    except Exception as e:
        # If GFPGAN fails, we fallback to the upscaled image
        restored = enhanced

    return restored

@dp.message(commands=["start"])
async def cmd_start(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📸 Send a Photo", callback_data="send_photo")],
        [InlineKeyboardButton("💠 Follow @CipherShivamX", url="https://t.me/CipherShivamX")]
    ])
    await m.reply(
        "👋 Welcome to *Remini-Style AI Enhancer Bot*\n\n"
        "🪄 Send me any low-quality photo, and I’ll upscale & restore it!\n\n"
        f"✨ Created by {CREDIT_HANDLE}",
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.message(content_types=[types.ContentType.PHOTO])
async def photo_handler(m: types.Message):
    status = await m.reply("🪄 Processing your photo... please wait ⏳")
    try:
        file = await m.photo[-1].get_file()
        image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"

        # Call replicate pipeline
        result = enhance_with_replicate(image_url)

        # Build caption (stylish, fixed)
        caption = (
            "✨ 𝐄𝐧𝐡𝐚𝐧𝐜𝐞𝐝 𝐁𝐲 𝐀𝐈\n\n"
            f"🧠 𝐏𝐨𝐰𝐞𝐫𝐞𝐝 𝐛𝐲 𝐑𝐞𝐦𝐢𝐧𝐢 𝐒𝐭𝐲𝐥𝐞 𝐁𝐨𝐭 ({BOT_USERNAME})\n"
            f"👤 𝐂𝐫𝐞𝐝𝐢𝐭𝐬: {CREDIT_HANDLE}"
        )

        # result may be a URL string or bytes-like; aiogram accepts both
        await m.reply_photo(photo=result, caption=caption, parse_mode="Markdown")
    except Exception as e:
        await m.reply(f"❌ Processing error: {e}")
    finally:
        # try to delete the processing status message
        try:
            await status.delete()
        except:
            pass

@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    if callback.data == "send_photo":
        await callback.message.answer("📸 Send another photo to enhance it!")
    await callback.answer()

if __name__ == "__main__":
    # Start polling
    print("Bot starting... (polling)")
    asyncio.run(dp.start_polling(bot))
