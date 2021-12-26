import logging
import traceback
from aiogram_broadcaster import MessageBroadcaster, TextBroadcaster
from aiogram import types, filters, Bot, Dispatcher
import re

async def admin_notificate(message: types.Message, exc: Exception):
    user = message.from_user
    trace = traceback.format_exc()
    text = (
        f"Ошибка\n"
        f"Пользователь\n"
        f"<code>tg_id :: </code>{user.id}\n"
        f"<code>nik :: </code>@{user.username}\n"
        f"<code>Имя :: </code>{user.first_name} {user.last_name}\n"
        f"\nЧто произошло:\n"
        f"<pre>{trace}</pre>"
        f"\n\nСообщение пользователя:"
    )

    logging.error(trace)
    admins = message.bot.get("config").admin_users
    await TextBroadcaster(admins, text).run()
    await MessageBroadcaster(admins, message).run()


def check_link(link):
    return re.match("https://(www\.)?youtu(be\.com/watch\?v=|.be/)[0-9a-zA-Z_\-]{8,}", link) is not None
