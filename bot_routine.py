import asyncio
import re

from aiogram import types, Bot
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import exceptions
from aiogram.dispatcher import FSMContext

from bot_settings import Config
from bot_text import TEXT


class UserChatMember(StatesGroup):
    member = State()


async def set_membership(state: FSMContext, chat_id: int):
    await UserChatMember.member.set()
    async with state.proxy() as data:
        data['chatid'] = chat_id


async def check_membership(message: types.Message, state: FSMContext):
    bot = message.bot
    uid = message.chat.id
    for ch_id in bot.get("config").active_chat_ids:
        try:
            member = await bot.get_chat_member(ch_id, uid)
            if member.status != "left":
                await set_membership(state, ch_id)
                return ch_id
        except:
            pass
    return False


async def first_check(message: types.Message, state: FSMContext):
    config: Config = message.bot.get("config")
    if not (await check_membership(message, state)):
        await check_again_button(message)
    else:
        if config.check_is_now_sumbmission_time():
            await message.answer(TEXT['instruction'].format(config.get_next_watch_period_time()))
        else:
            await message.answer(TEXT['pausework'].format(config.get_next_watch_period_time(submission=True)))


async def validate_code(message: types.Message):
    unique_code = message.text.strip()
    config: Config = message.bot.get("config")
    if re.match(r"[\d]+:[\d]+", unique_code):
        msg = await message.reply(TEXT['validate_code'])
        fusr = message.from_user
        act = await config.verificate_tilda_code(
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
                    link = await config.get_invite_to_room()
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
