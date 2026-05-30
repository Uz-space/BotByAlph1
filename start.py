import hashlib
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS, REFERRAL_BONUS
import database as db
import keyboards as kb

router = Router()

def ref_code(uid): return hashlib.md5(str(uid).encode()).hexdigest()[:8].upper()


@router.message(CommandStart())
async def start(msg: Message, state: FSMContext):
    await state.clear()
    uid  = msg.from_user.id
    args = msg.text.split()
    code = args[1] if len(args) > 1 else None

    user = await db.get_user(uid)
    if not user:
        ref_owner = await db.get_user_by_ref(code) if code else None
        referred_by = ref_owner["user_id"] if ref_owner else None
        await db.create_user(uid, msg.from_user.username or "", msg.from_user.full_name, ref_code(uid), referred_by)

        if ref_owner:
            try:
                await msg.bot.send_message(ref_owner["user_id"],
                    f"👥 <b>Yangi referal!</b>\n{msg.from_user.full_name} ro'yxatdan o'tdi.\n"
                    f"💰 +{REFERRAL_BONUS:,} so'm bonusingiz bor!", parse_mode="HTML")
            except Exception:
                pass

    menu = kb.admin_kb() if uid in ADMIN_IDS else kb.main_kb()
    await msg.answer(f"👋 <b>Xush kelibsiz!</b>\n\nMenyu tanlang:", parse_mode="HTML", reply_markup=menu)
