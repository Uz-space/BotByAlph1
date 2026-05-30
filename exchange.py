from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import CRYPTOS, PRICES, EXCHANGE_FEE_PERCENT
import database as db
import keyboards as kb
from states import Order

router = Router()


def get_price(crypto, action):
    prices_db = {}  # sync placeholder — db.get_prices() called async below
    base = PRICES.get(crypto, {})
    return base.get("buy" if action == "buy" else "sell", 0)


@router.message(F.text == "💱 Ayirboshlash")
async def exchange(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "💱 <b>Ayirboshlash</b>\n\nNima qilmoqchisiz?",
        parse_mode="HTML",
        reply_markup=kb.action_kb()
    )


@router.callback_query(F.data.startswith("action:"))
async def choose_action(call: CallbackQuery, state: FSMContext):
    action = call.data.split(":")[1]
    await state.update_data(action=action)
    label = "📥 Sotib olish" if action == "buy" else "📤 Sotish"
    await call.message.edit_text(
        f"<b>{label}</b>\n\nQaysi kriptoni tanlaysiz?",
        parse_mode="HTML",
        reply_markup=kb.crypto_kb(action)
    )


@router.callback_query(F.data == "back:action")
async def back_action(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "💱 <b>Ayirboshlash</b>\n\nNima qilmoqchisiz?",
        parse_mode="HTML",
        reply_markup=kb.action_kb()
    )


@router.callback_query(F.data.startswith("crypto:"))
async def choose_crypto(call: CallbackQuery, state: FSMContext):
    _, action, crypto = call.data.split(":")
    await state.update_data(action=action, crypto=crypto)

    db_prices = await db.get_prices()
    price = db_prices.get(crypto, {}).get("buy" if action == "buy" else "sell") or \
            PRICES.get(crypto, {}).get("buy" if action == "buy" else "sell", 0)

    info = CRYPTOS[crypto]
    action_text = "sotib olish" if action == "buy" else "sotish"

    await call.message.edit_text(
        f"{info['emoji']} <b>{info['name']} ({crypto})</b>\n\n"
        f"💰 1 {crypto} = <b>{price:,.0f} so'm</b>\n\n"
        f"📝 {crypto} {action_text} uchun <b>so'm miqdorini</b> kiriting:",
        parse_mode="HTML"
    )
    await state.set_state(Order.amount)


@router.message(Order.amount)
async def enter_amount(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        await msg.answer("❌ Bekor qilindi.", reply_markup=kb.main_kb())
        return

    try:
        amount = float(msg.text.replace(" ", "").replace(",", ""))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await msg.answer("❌ Noto'g'ri miqdor. Faqat raqam kiriting:")
        return

    data = await state.get_data()
    action = data["action"]
    crypto = data["crypto"]

    db_prices = await db.get_prices()
    price = db_prices.get(crypto, {}).get("buy" if action == "buy" else "sell") or \
            PRICES.get(crypto, {}).get("buy" if action == "buy" else "sell", 0)

    fee = amount * EXCHANGE_FEE_PERCENT / 100
    net = amount - fee
    qty = net / price if price else 0

    await state.update_data(amount_uzs=amount, fee=fee, crypto_qty=qty, price=price)
    await state.set_state(Order.confirm)

    action_text = "Sotib olasiz" if action == "buy" else "Sotasiz"
    await msg.answer(
        f"📋 <b>Buyurtma ma'lumotlari</b>\n\n"
        f"🔄 Amal: {'📥 Sotib olish' if action == 'buy' else '📤 Sotish'}\n"
        f"🪙 Kripto: <b>{crypto}</b>\n"
        f"💵 Miqdor: <b>{amount:,.0f} so'm</b>\n"
        f"💼 Komissiya ({EXCHANGE_FEE_PERCENT}%): <b>{fee:,.0f} so'm</b>\n"
        f"📦 {action_text}: <b>{qty:.6f} {crypto}</b>\n\n"
        f"Tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=kb.confirm_kb()
    )


@router.callback_query(Order.confirm, F.data == "confirm")
async def confirm_order(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    uid  = call.from_user.id

    await db.add_order(uid, data["action"], data["crypto"],
                       data["amount_uzs"], data["crypto_qty"], data["fee"])
    await state.clear()

    action_text = "📥 Sotib olish" if data["action"] == "buy" else "📤 Sotish"
    await call.message.edit_text(
        f"✅ <b>Buyurtma qabul qilindi!</b>\n\n"
        f"{action_text}: <b>{data['crypto_qty']:.6f} {data['crypto']}</b>\n"
        f"💵 To'lov: <b>{data['amount_uzs']:,.0f} so'm</b>\n\n"
        f"<i>Operator tez orada siz bilan bog'lanadi.</i>",
        parse_mode="HTML"
    )
    await call.message.answer("🏠 Menyu:", reply_markup=kb.main_kb())


@router.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Bekor qilindi.")
    await call.message.answer("🏠 Menyu:", reply_markup=kb.main_kb())
