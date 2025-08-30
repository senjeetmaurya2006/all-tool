import logging
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from PyPDF2 import PdfMerger, PdfReader
from PIL import Image
import io

# --- BOT TOKEN DAL DIYA ---
BOT_TOKEN = "8485720896:AAHwRbEKOy_udoTUQstaKuXiGxkUM4ZB6bI"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# --- Start Command ---
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    kb = [
        [InlineKeyboardButton(text="📂 PDF Tools", callback_data="menu_pdf"),
         InlineKeyboardButton(text="🖼 Image Tools", callback_data="menu_img")],
        [InlineKeyboardButton(text="📝 Text Tools", callback_data="menu_text"),
         InlineKeyboardButton(text="🧮 Calculator", callback_data="menu_calc")],
        [InlineKeyboardButton(text="🔲 QR Tools", callback_data="menu_qr")]
    ]
    await message.answer("👋 Welcome! Choose a tool:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- Back Home ---
async def back_home(callback: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="📂 PDF Tools", callback_data="menu_pdf"),
         InlineKeyboardButton(text="🖼 Image Tools", callback_data="menu_img")],
        [InlineKeyboardButton(text="📝 Text Tools", callback_data="menu_text"),
         InlineKeyboardButton(text="🧮 Calculator", callback_data="menu_calc")],
        [InlineKeyboardButton(text="🔲 QR Tools", callback_data="menu_qr")]
    ]
    await callback.message.edit_text("👋 Welcome! Choose a tool:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- PDF MENU ---
@dp.callback_query(F.data == "menu_pdf")
async def menu_pdf(callback: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🖼 Images → PDF", callback_data="pdf_from_img")],
        [InlineKeyboardButton(text="➕ Merge PDFs", callback_data="pdf_merge")],
        [InlineKeyboardButton(text="✂️ Split PDF", callback_data="pdf_split")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_home")]
    ]
    await callback.message.edit_text("📂 PDF Tools Menu", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- Image MENU ---
@dp.callback_query(F.data == "menu_img")
async def menu_img(callback: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="📏 Resize Image", callback_data="img_resize")],
        [InlineKeyboardButton(text="📉 Compress Image", callback_data="img_compress")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_home")]
    ]
    await callback.message.edit_text("🖼 Image Tools Menu", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- Text MENU ---
@dp.callback_query(F.data == "menu_text")
async def menu_text(callback: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🔡 Uppercase", callback_data="text_upper")],
        [InlineKeyboardButton(text="🔠 Lowercase", callback_data="text_lower")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="back_home")]
    ]
    await callback.message.edit_text("📝 Text Tools Menu", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# --- Calculator MENU ---
@dp.callback_query(F.data == "menu_calc")
async def menu_calc(callback: CallbackQuery):
    await callback.message.edit_text("🧮 Send me an expression like <code>2+2*3</code> and I'll calculate it.\n\n⬅️ /start to go back")

# --- QR MENU ---
@dp.callback_query(F.data == "menu_qr")
async def menu_qr(callback: CallbackQuery):
    await callback.message.edit_text("🔲 Send me text/link, I will generate QR Code.\n\n⬅️ /start to go back")

# --- BACK HANDLER ---
@dp.callback_query(F.data == "back_home")
async def go_home(callback: CallbackQuery):
    await back_home(callback)

# --- FEATURES ---

# PDF: Merge PDFs
user_pdfs = {}
@dp.callback_query(F.data == "pdf_merge")
async def pdf_merge_start(callback: CallbackQuery):
    user_pdfs[callback.from_user.id] = []
    await callback.message.edit_text("📂 Send me PDFs one by one. Send /done when finished.")

@dp.message(F.document)
async def handle_pdf(message: Message):
    if message.document.mime_type == "application/pdf" and message.from_user.id in user_pdfs:
        file = await bot.download(message.document)
        user_pdfs[message.from_user.id].append(file)

@dp.message(F.text == "/done")
async def merge_pdfs(message: Message):
    if message.from_user.id in user_pdfs and user_pdfs[message.from_user.id]:
        merger = PdfMerger()
        for f in user_pdfs[message.from_user.id]:
            merger.append(PdfReader(f))
        output = io.BytesIO()
        merger.write(output)
        output.seek(0)
        await message.answer_document(document=output, filename="merged.pdf")
        user_pdfs.pop(message.from_user.id)
    else:
        await message.answer("⚠️ No PDFs uploaded!")

# Image: Convert to PDF
user_imgs = {}
@dp.callback_query(F.data == "pdf_from_img")
async def img_to_pdf_start(callback: CallbackQuery):
    user_imgs[callback.from_user.id] = []
    await callback.message.edit_text("🖼 Send me images. Send /done when finished.")

@dp.message(F.photo)
async def handle_img(message: Message):
    if message.from_user.id in user_imgs:
        file = await bot.download(message.photo[-1])
        user_imgs[message.from_user.id].append(Image.open(file))

@dp.message(F.text == "/done")
async def img_to_pdf(message: Message):
    if message.from_user.id in user_imgs and user_imgs[message.from_user.id]:
        output = io.BytesIO()
        imgs = user_imgs[message.from_user.id]
        imgs[0].save(output, save_all=True, append_images=imgs[1:], format="PDF")
        output.seek(0)
        await message.answer_document(document=output, filename="images.pdf")
        user_imgs.pop(message.from_user.id)
    else:
        await message.answer("⚠️ No images uploaded!")

# Text: Uppercase / Lowercase
@dp.message(F.text.regexp("^[a-zA-Z].*"))
async def text_tools(message: Message):
    if "text_upper" in (message.text or "").lower():
        await message.answer(message.text.upper())
    elif "text_lower" in (message.text or "").lower():
        await message.answer(message.text.lower())

# Calculator
@dp.message(F.text.regexp(r"^[0-9\+\-\*\/\.\(\) ]+$"))
async def calc(message: Message):
    try:
        result = eval(message.text)
        await message.answer(f"🧮 Result: <b>{result}</b>")
    except:
        await message.answer("⚠️ Invalid Expression!")

# QR Generator
import qrcode
@dp.message(F.text & ~F.text.startswith("/"))
async def qr_gen(message: Message):
    img = qrcode.make(message.text)
    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    await message.answer_photo(photo=output, caption="✅ QR Generated")

# --- Run Bot ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
