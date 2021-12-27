import asyncio
import re

from aiogram import types, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import exceptions
from bot_settings import Config
from bot_text import TEXT


async def check_membership(message: types.Message):
    # TODO кэш членства
    bot = message.bot
    uid = message.chat.id
    for ch_id in bot.get("config").active_chat_ids:
        try:
            member = await bot.get_chat_member(ch_id, uid)
            if member.status != "left":
                chat = await bot.get_chat(chat_id=ch_id)
                return ch_id, chat.title
        except:
            pass
    return False


async def get_invite_to_room(bot: Bot):
    # TODO кэш счётчиков
    counts = [(i, (await bot.get_chat_member_count(i))) for i in bot.get("config").active_chat_ids]
    minchat = min(counts, key=lambda x: x[1])
    link = await bot.create_chat_invite_link(minchat[0], member_limit=1)
    return link.invite_link


async def first_check(message: types.Message):
    config: Config = message.bot.get("config")
    if not (await check_membership(message)):
        if not hasattr(message, 'text') or not (await validate_code(message)):
            await check_again_button(message)
    else:
        if config.check_is_now_sumbmission_time():
            await message.answer(TEXT['instruction'].format(config.get_next_sumbmission_time()))
        else:
            await message.answer(TEXT['pausework'])


async def validate_code(message: types.Message):
    unique_code = message.text.strip()
    if re.match(r"[\d]+:[\d]+", unique_code):
        msg = await message.reply(TEXT['validate_code'])
        fusr = message.from_user
        act = await message.bot.get("config").verificate_tilda_code(
            unique_code,
            fusr.id,
            f"{fusr.username} :: {fusr.first_name} {fusr.last_name}"
        )
        err = act.get("error")
        if err:
            await msg.edit_text(TEXT['start_chat_error'] + str(err))
        elif act.get("ok"):
            while 1:
                try:
                    link = await get_invite_to_room(message.bot)
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton(TEXT['get_invite'], url=link))
                    await msg.edit_text(TEXT['new_room'], reply_markup=markup)
                    return True
                except exceptions.RetryAfter:
                    await asyncio.sleep(1)
    return False


async def check_again_button(message: types.Message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(TEXT['button_repeat_verification'], callback_data="repeat"))
    await message.answer(TEXT['membership'], reply_markup=markup)
