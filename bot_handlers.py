from aiogram import filters, Dispatcher
from aiogram.utils.exceptions import TelegramAPIError, MessageNotModified, CantParseEntities
import logging
import json
from bot_utils import admin_notificate, check_link
from bot_routine import *


async def text_messages_not_member(message: types.Message, state: FSMContext):
    try:
        if not (await check_membership(message, state)):
            if not (await validate_code(message)):
                await check_again_button(message)
        else:
            await text_messages_member(message, state)
    except Exception as ex1:
        await message.reply(TEXT['text_message_error'])
        await admin_notificate(message, ex1)


async def verificate_membership_again(call: types.CallbackQuery, state: FSMContext):
    if call.data == "repeat":
        await call.answer()
        await first_check(call.message, state)
    else:
        await call.answer("Какие странные у вас кнопочки!?")


async def start_command(message: types.Message, state: FSMContext):
    try:
        await first_check(message, state)
    except Exception as ex1:
        await admin_notificate(message, ex1)


async def change_chat_membership(message: types.ChatMemberUpdated, state: FSMContext):
    config: Config = message.bot.get("config")
    chid = message.chat.id
    if message.new_chat_member.status == "member":
        await config.add_member(chid)
        await set_membership(state, chid)
        logging.info(f'new user {chid} :: {message.from_user.id} :: {message.from_user.username}'
                     f' :: {message.from_user.first_name} {message.from_user.last_name}')
    if message.new_chat_member.status == "left":
        await config.sub_member(chid)
        await state.finish()


async def text_messages_member(message: types.Message, state: FSMContext):
    user_chat_id = (await state.get_data())['chatid']
    config: Config = message.bot.get("config")

    if user_chat_id not in config.active_chat_ids:
        await state.finish()
        return await text_messages_not_member(message, state)

    try:
        umes = message.text
        if not config.check_is_now_sumbmission_time():
            await message.answer(TEXT['pausework'])
        elif not check_link(umes):
            await message.reply(TEXT['wrongmessage'], parse_mode="Markdown")
        else:
            mfu = message.from_user
            uname = f'{mfu.first_name} {mfu.last_name} - @{mfu.username}'
            try:
                repl_mess = await message.reply(TEXT['link_in_process'])
                reply = repl_mess.edit_text
            except exceptions.RetryAfter:
                logging.info(f"Flood block user: {mfu.id}, {uname}, {umes}")
                reply = message.reply
            response = await config.send_linkdata_to_sheet(
                mfu.id, uname, umes,
                *(await config.get_chat_name(user_chat_id))
            )
            timer = 0
            while 1:
                try:
                    if response.get("ok"):
                        await reply(TEXT['add_success'])
                    elif response.get("link"):
                        await reply(TEXT['yourlink'].format(response.get("link"), umes))
                    else:
                        await reply(TEXT['add_error'].format(json.dumps(response, indent=1)))
                    break
                except exceptions.RetryAfter:
                    timer += 1
                    await asyncio.sleep(timer)
    except Exception as ex1:
        await message.reply(TEXT['text_message_error'])
        await admin_notificate(message, ex1)


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


async def unhandled_message(message: types.Message):
    await message.reply(TEXT['unhandled_message'])


async def register(dp: Dispatcher):
    # await set_bot_commands(dp.bot)
    config: Config = dp.bot.get("config")
    ct = types.ChatType
    # async def cmd_test(message: types.Message):
    #     config: Config = message.bot.get("config")
    #     print(message, config.owner)
    #     config.owner = 465421321564
    # dp.register_message_handler(cmd_test, commands="test")

    # dp.filters_factory.bind(AdminFilter)
    # dp.register_message_handler(cmd_help, filters.CommandHelp())

    dp.register_callback_query_handler(
        verificate_membership_again,
        state='*'
    )
    dp.register_message_handler(
        start_command, filters.CommandStart(), chat_type=ct.PRIVATE
    )

    dp.register_message_handler(
        update_settings,
        chat_id=config.admin_users,
        commands="update_all_settings",
        state='*'
    )
    # dp.register_message_handler(
    #     update_settings,
    #     chat_id=config.admin_users,
    #     commands="clean_membership_chache",
    #     state='*'
    # )

    dp.register_message_handler(
        text_messages_not_member, chat_type=ct.PRIVATE,
        content_types=['text']
    )
    dp.register_message_handler(
        text_messages_member, chat_type=ct.PRIVATE,
        state=UserChatMember.member,
        content_types=['text']
    )

    dp.register_chat_member_handler(
        change_chat_membership, state='*',
        chat_type=[ct.CHANNEL, ct.GROUP, ct.SUPERGROUP]
    )
    dp.register_message_handler(
        unhandled_message, chat_type=ct.PRIVATE,
        state='*',
    )
    dp.register_errors_handler(errors_handler)

    #Todo троттл на отправку ссылок
