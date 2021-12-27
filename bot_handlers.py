import types

from aiogram import filters, Dispatcher
from aiogram.utils.exceptions import TelegramAPIError, MessageNotModified, CantParseEntities
import logging
import json
from bot_utils import admin_notificate, check_link
from bot_routine import *


async def verificate_membership_again(call: types.CallbackQuery):
    if call.data == "repeat":
        await call.answer()
        await first_check(call.message)
    else:
        await call.answer("Какие странные у вас кнопочки!?")


async def start_command(message: types.Message):
    try:
        if message.chat.type == 'private':
            await first_check(message)
    except Exception as ex1:
        await admin_notificate(message, ex1)


async def get_text_messages(message: types.Message):
    try:
        if message.chat.type != 'private' or len(message.text) <= 0:
            logging.info(message)
            return

        config: Config = message.bot.get("config")
        umes = message.text
        membership = await check_membership(message)
        if not membership:
            if not (await validate_code(message)):
                await check_again_button(message)
        elif not config.check_is_now_sumbmission_time():
            await message.answer(TEXT['pausework'])
        elif not check_link(umes):
            await message.reply(TEXT['wrongmessage'], parse_mode="Markdown")
        else:
            #TODO не просерать ссылку, если что-то пошло не так
            mfu = message.from_user
            uid = mfu.id
            uname = f'{mfu.first_name} {mfu.last_name} - @{mfu.username}'
            repl_mess = await message.reply(TEXT['link_in_process'])
            response = await config.send_linkdata_to_sheet(uid, uname, umes, *membership)
            if response.get("ok"):
                await repl_mess.edit_text(TEXT['add_success'])
            elif response.get("link"):
                await repl_mess.edit_text(TEXT['yourlink'].format(response.get("link"), umes))
            else:
                await repl_mess.edit_text(TEXT['add_error'].format(json.dumps(response, indent=1)))
    except Exception as ex1:
        await message.reply(TEXT['text_message_error'])
        await admin_notificate(message, ex1)


async def new_chat_member(message: types.ChatMemberUpdated):
    if message.new_chat_member.status == "member":
        logging.info(f'new user {message.chat.id} :: {message.from_user.username}'
                     f' :: {message.from_user.first_name} {message.from_user.last_name}')


async def update_settings(message: types.Message):
    config = message.bot.get("config")
    config.update()
    message.text = f"{message.html_text}\n\n{TEXT['settings_update']}\n" + config.config_to_html()
    await admin_notificate(message)


# except exceptions.RetryAfter as e:
#      log.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
#      await asyncio.sleep(e.timeout)
#      return await send_message(user_id, text)  # Recursive call

async def errors_handler(update, exception):
    """
    Exceptions handler. Catches all exceptions within task factory tasks.
    :param dispatcher:
    :param update:
    :param exception:
    :return: stdout logging
    """
    await admin_notificate(update, exception)
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
