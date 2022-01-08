from aiogram import filters, Dispatcher
from aiogram.utils.exceptions import TelegramAPIError, MessageNotModified, CantParseEntities
from aiogram.types import BotCommand, bot_command_scope
import logging
import json
from bot_utils import admin_notificate, check_link, admin_broadcast
from bot_routine import *
from bot_text import *


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
            await message.answer(TEXT['pausework'].format(config.get_next_watch_period_time(submission=True)))
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
                        await reply(TEXT['add_success'].format(config.get_next_watch_period_time(response)))
                    elif response.get("oldlink"):
                        await reply(TEXT['yourlink'].format(
                            response.get("oldlink"), umes,
                            config.get_next_watch_period_time(response)
                        ))
                    else:
                        await reply(TEXT['add_error'].format(
                            json.dumps(response, indent=1, ensure_ascii=False)
                        ))
                    break
                except exceptions.RetryAfter:
                    timer += 1
                    if timer > 10:
                        logging.error(f"Can't answer to link {message.from_user.id} :: {response}")
                        break
                    await asyncio.sleep(timer)
    except Exception as ex1:
        await message.reply(TEXT['text_message_error'])
        await admin_notificate(message, ex1)


async def update_settings(message: types.Message):
    config = message.bot.get("config")
    config.update()
    await set_bot_commands(message.bot)
    message.text = f"{message.html_text}\n\n{TEXT['settings_update']}\n" + config.config_to_html()
    await admin_notificate(message)


async def show_settings(message: types.Message):
    config = message.bot.get("config")
    await message.reply(config.config_to_html())


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


async def about(message: types.Message):
    config: Config = message.bot.get("config")
    await message.answer(TEXT['instruction'].format(config.get_next_watch_period_time()))


async def set_bot_commands(bot: Bot):
    commands = [BotCommand(command=k, description=i) for k, i in COMMANDS_USER.items()]
    await bot.set_my_commands(
        commands,
        scope=bot_command_scope.BotCommandScopeAllPrivateChats()
    )
    admin_commands = commands + [BotCommand(command=k, description=i) for k, i in COMMANDS_ADMIN.items()]
    for user in bot.get("config").admin_users:
        await bot.set_my_commands(
            admin_commands,
            scope=bot_command_scope.BotCommandScopeChat(chat_id=user)
        )


async def register(dp: Dispatcher):
    config: Config = dp.bot.get("config")
    ct = types.ChatType

    # async def cmd_test(message: types.Message):
    #     config: Config = message.bot.get("config")
    #     print(message, config.owner)
    #     config.owner = 465421321564
    # dp.register_message_handler(cmd_test, commands="test")
    # dp.filters_factory.bind(AdminFilter)

    await set_bot_commands(dp.bot)

    dp.register_message_handler(about, filters.CommandHelp(), state=UserChatMember.member)
    dp.register_message_handler(about, commands="about", state=UserChatMember.member)

    dp.register_callback_query_handler(
        verificate_membership_again,
        state='*'
    )
    dp.register_message_handler(
        start_command, filters.CommandStart(), chat_type=ct.PRIVATE
    )

    dp.register_message_handler(
        update_settings, commands="update_all_settings",
        chat_id=config.admin_users, state='*'
    )
    dp.register_message_handler(
        show_settings, commands="show_settings",
        chat_id=config.admin_users, state='*'
    )

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

    # Todo троттл на отправку ссылок
