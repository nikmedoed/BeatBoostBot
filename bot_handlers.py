from aiogram import types, filters, Bot, Dispatcher
from aiogram.types import BotCommand, bot_command_scope, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import TelegramAPIError, MessageNotModified, CantParseEntities
from bot_settings import Config
from bot_text import TEXT
import logging
import re, json
from utils import admin_notificate, check_link
from bot_routine import *


async def verificate_membership_again(call: types.CallbackQuery):
    if call.data == "repeat":
        await call.answer()
        await firstCheck(call.message)
    else:
        await call.answer("Какие странные у вас кнопочки!?")


async def start_command(message: types.Message):
    try:
        if message.chat.type == 'private':
            await firstCheck(message)
    except Exception as ex1:
        await admin_notificate(message, ex1)


async def firstCheck(message: types.Message):
    config: Config = message.bot.get("config")
    if not (await check_membership(message)):
        if not hasattr(message, 'text') or not (await validateCode(message)):
            await check_again_button(message)
    else:
        if config.check_is_now_sumbmission_time():
            await message.answer(TEXT['instruction'].format(config.get_next_sumbmission_time()))
        else:
            await message.answer(TEXT['pausework'])


async def check_again_button(message: types.Message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(TEXT['button_repeat_verification'], callback_data="repeat"))
    await message.answer(TEXT['membership'], reply_markup=markup)


async def validateCode(message: types.Message):
    unique_code = message.text.strip()
    if re.match(r"[\d]+:[\d]+", unique_code):
        await message.reply(TEXT['validate_code'])
        act = message.bot.get("config").verificateId(unique_code)
        err = act.get("error")
        if err:
            await message.answer(TEXT['start_chat_error'] + err)
        elif act.get("ok"):
            link = await get_invite_to_room(message.bot)
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(TEXT['get_invite'], url=link))
            await  message.answer(TEXT['new_room'], reply_markup=markup)
            return True
    return False


async def get_text_messages(message: types.Message):
    try:
        if message.chat.type != 'private' or len(message.text) <= 0:
            logging.info(message)
            return

        config: Config = message.bot.get("config")
        umes = message.text
        membership = await check_membership(message)
        if not membership:
            if not (await validateCode(message)):
                await check_again_button(message)
        elif not config.check_is_now_sumbmission_time():
            await message.answer(TEXT['pausework'])
        elif not check_link(umes):
            await message.reply(TEXT['wrongmessage'], parse_mode="Markdown")
        else:
            mfu = message.from_user
            uid = mfu.id
            uname = f'{mfu.first_name} {mfu.last_name} - @{mfu.username}'
            repl_mess = await message.reply(TEXT['link_in_process'])
            response = config.sendData(uid, uname, umes, *membership)
            if response.get("ok"):
                await repl_mess.edit_text(TEXT['add_success'])
                # await message.reply()
            elif response.get("link"):
                await repl_mess.edit_text(TEXT['yourlink'] % (response.get("link"), umes))
            else:
                await repl_mess.edit_text(TEXT['add_error'] % json.dumps(response, indent=1))
    except Exception as ex1:
        await message.reply(TEXT['text_message_error'])
        await admin_notificate(message, ex1)


async def new_chat_member(message: types.ChatMemberUpdated):
    if message.new_chat_member.status == "member":
        logging.info(f'new user {message.chat.id} :: {message.from_user.username}'
                     f' :: {message.from_user.first_name} {message.from_user.last_name}')


async def update_settings(message: types.Message):
    message.bot.get("config").update()


async def errors_handler(update, exception):
    """
    Exceptions handler. Catches all exceptions within task factory tasks.
    :param dispatcher:
    :param update:
    :param exception:
    :return: stdout logging
    """
    if isinstance(exception, MessageNotModified):
        logging.exception('Message is not modified')
        return True
    if isinstance(exception, CantParseEntities):
        logging.exception(f'CantParseEntities: {exception} \nUpdate: {update}')
        return True
    if isinstance(exception, TelegramAPIError):  # MUST BE THE  LAST CONDITION
        logging.exception(f'TelegramAPIError: {exception} \nUpdate: {update}')
        return True
    logging.exception(f'Update: {update} \n{exception}')


async def register(dp: Dispatcher):
    # await set_bot_commands(dp.bot)
    # config: Config = dp.bot.get("config")

    # async def cmd_test(message: types.Message):
    #     config: Config = message.bot.get("config")
    #     print(message, config.owner)
    #     config.owner = 465421321564
    # dp.register_message_handler(cmd_test, commands="test")

    # dp.filters_factory.bind(AdminFilter)
    # dp.register_message_handler(cmd_help, filters.CommandHelp())
    # dp.register_message_handler(cmd_privacy, filters.CommandPrivacy())

    dp.register_callback_query_handler(verificate_membership_again)
    dp.register_message_handler(start_command, filters.CommandStart())

    dp.register_message_handler(update_settings, commands="update_all_settings")

    dp.register_message_handler(get_text_messages, content_types=['text'])

    dp.register_chat_member_handler(new_chat_member)
    dp.register_errors_handler(errors_handler)
