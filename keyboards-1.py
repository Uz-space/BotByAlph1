from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import CRYPTOS


def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="💱 Ayirboshlash"), KeyboardButton(text="📊 Kurslar")],
        [KeyboardButton(text="👥 Referal"),       KeyboardButton(text="👤 Profil")],
        [KeyboardButton(text="💬 Aloqa")],
    ], resize_keyboard=True)


def admin_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📊 Statistika"),  KeyboardButton(text="📈 Narx o'zgartir")],
        [KeyboardButton(text="📢 Xabar yuborish"), KeyboardButton(text="🔙 Orqaga")],
    ], resize_keyboard=True)


def action_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📥 Sotib olish", callback_data="action:buy"),
            InlineKeyboardButton(text="📤 Sotish",      callback_data="action:sell"),
        ]
    ])


def crypto_kb(action: str):
    rows = []
    row = []
    for code, info in CRYPTOS.items():
        row.append(InlineKeyboardButton(
            text=f"{info['emoji']} {code}",
            callback_data=f"crypto:{action}:{code}"
        ))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back:action")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm"),
            InlineKeyboardButton(text="❌ Bekor",      callback_data="cancel"),
        ]
    ])


def cancel_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="❌ Bekor qilish")]
    ], resize_keyboard=True)
