from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS, CRYPTOS, PRICES, REFERRAL_BONUS
import database as db
import keyboards as kb
from states import Feedback, Admin

router = Router()


# ── Kurslar ──────────────────────────────────────────────
@router.message(F.text == "📊 Kurslar")
async def rates(msg: Message):
    db_prices = await db.get_prices()
    lines = []
    for code, info in CRYPTOS.items():
        p = db_prices.get(code) or PRICES.get(code, {})
        lines.append(
            f"{info['emoji']} <b>{code}</b>\n"
            f"  📈 {p.get('buy', 0):>15,.0f} so'm\n"
            f"  📉 {p.get('sell', 0):>15,.0f} so'm"
        )
    await msg.answer("📊 <b>Kriptovalyuta kurslari</b>\n\n" + "\n\n".join(lines), parse_mode="HTML")


# ── Profil ───────────────────────────────────────────────
@router.message(F.text == "👤 Profil")
async def profile(msg: Message):
    uid  = msg.from_user.id
    user = await db.get_user(uid)
    if not user:
        await msg.answer("❌ Profil topilmadi.")
        return

    refs    = await db.get_referral_count(uid)
    orders  = await db.get_orders(uid, limit=3)
    bot     = await msg.bot.get_me()
    link    = f"https://t.me/{bot.username}?start={user['ref_code']}"
    joined  = user["joined_at"][:10] if user["joined_at"] else "—"

    text = (
        f"👤 <b>Profil</b>\n\n"
        f"├ {msg.from_user.full_name}\n"
        f"├ ID: <code>{uid}</code>\n"
        f"├ Sana: {joined}\n"
        f"└ Referallar: {refs} ta\n\n"
        f"🔗 Referal havola:\n<code>{link}</code>"
    )

    if orders:
        text += "\n\n📜 <b>So'nggi buyurtmalar:</b>"
        for o in orders:
            icon = "📥" if o["action"] == "buy" else "📤"
            text += f"\n{icon} {o['crypto']} — {o['amount_uzs']:,.0f} so'm"

    await msg.answer(text, parse_mode="HTML")


# ── Referal ──────────────────────────────────────────────
@router.message(F.text == "👥 Referal")
async def referral(msg: Message):
    user = await db.get_user(msg.from_user.id)
    if not user:
        await msg.answer("❌ Topilmadi.")
        return
    refs = await db.get_referral_count(msg.from_user.id)
    bot  = await msg.bot.get_me()
    link = f"https://t.me/{bot.username}?start={user['ref_code']}"

    await msg.answer(
        f"👥 <b>Referal tizimi</b>\n\n"
        f"🔗 Havola:\n<code>{link}</code>\n\n"
        f"👤 Taklif qilganlar: <b>{refs} ta</b>\n"
        f"🎁 Har bir referal uchun: <b>{REFERRAL_BONUS:,} so'm</b>",
        parse_mode="HTML"
    )


# ── Aloqa ────────────────────────────────────────────────
@router.message(F.text == "💬 Aloqa")
async def feedback_start(msg: Message, state: FSMContext):
    await state.set_state(Feedback.writing)
    await msg.answer("💬 Xabaringizni yozing:", reply_markup=kb.cancel_kb())


@router.message(Feedback.writing)
async def feedback_receive(msg: Message, state: FSMContext):
    if msg.text == "❌ Bekor qilish":
        await state.clear()
        await msg.answer("❌ Bekor qilindi.", reply_markup=kb.main_kb())
        return

    await db.add_feedback(msg.from_user.id, msg.text)
    await state.clear()
    await msg.answer("✅ Xabaringiz qabul qilindi!", reply_markup=kb.main_kb())

    for aid in ADMIN_IDS:
        try:
            await msg.bot.send_message(aid,
                f"📩 <b>Yangi xabar</b>\n"
                f"👤 {msg.from_user.full_name} (<code>{msg.from_user.id}</code>)\n\n"
                f"{msg.text}", parse_mode="HTML")
        except Exception:
            pass


# ── Admin ────────────────────────────────────────────────
def is_admin(uid): return uid in ADMIN_IDS


@router.message(F.text == "📊 Statistika")
async def stats(msg: Message):
    if not is_admin(msg.from_user.id): return
    users, orders, fees = await db.get_stats()
    await msg.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"👤 Foydalanuvchilar: <b>{users}</b>\n"
        f"📦 Buyurtmalar: <b>{orders}</b>\n"
        f"💰 Komissiya: <b>{fees:,.0f} so'm</b>",
        parse_mode="HTML"
    )


@router.message(F.text == "📈 Narx o'zgartir")
async def price_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    codes = " | ".join(CRYPTOS.keys())
    await state.set_state(Admin.price_crypto)
    await msg.answer(f"Kripto kodini kiriting:\n<code>{codes}</code>", parse_mode="HTML")


@router.message(Admin.price_crypto)
async def price_crypto(msg: Message, state: FSMContext):
    c = msg.text.upper().strip()
    if c not in CRYPTOS:
        await msg.answer("❌ Noto'g'ri kod!")
        return
    await state.update_data(crypto=c)
    await state.set_state(Admin.price_buy)
    await msg.answer(f"📈 {c} sotib olish narxi (so'm):")


@router.message(Admin.price_buy)
async def price_buy(msg: Message, state: FSMContext):
    try:
        buy = float(msg.text.replace(" ", "").replace(",", ""))
    except ValueError:
        await msg.answer("❌ Faqat raqam!")
        return
    await state.update_data(buy=buy)
    await state.set_state(Admin.price_sell)
    await msg.answer("📉 Sotish narxi (so'm):")


@router.message(Admin.price_sell)
async def price_sell(msg: Message, state: FSMContext):
    try:
        sell = float(msg.text.replace(" ", "").replace(",", ""))
    except ValueError:
        await msg.answer("❌ Faqat raqam!")
        return
    data = await state.get_data()
    await db.set_price(data["crypto"], data["buy"], sell)
    await state.clear()
    await msg.answer(
        f"✅ <b>{data['crypto']}</b> narxi yangilandi!\n"
        f"📈 {data['buy']:,} / 📉 {sell:,}",
        parse_mode="HTML", reply_markup=kb.admin_kb()
    )


@router.message(F.text == "📢 Xabar yuborish")
async def broadcast_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    await state.set_state(Admin.broadcast)
    await msg.answer("📢 Barcha foydalanuvchilarga xabar:")


@router.message(Admin.broadcast)
async def broadcast_send(msg: Message, state: FSMContext):
    await state.clear()
    uids = await db.get_all_user_ids()
    ok = 0
    for uid in uids:
        try:
            await msg.bot.send_message(uid, f"📢 {msg.text}")
            ok += 1
        except Exception:
            pass
    await msg.answer(f"✅ {ok}/{len(uids)} foydalanuvchiga yuborildi.", reply_markup=kb.admin_kb())


@router.message(F.text == "🔙 Orqaga")
async def back(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("🏠 Menyu:", reply_markup=kb.main_kb())
