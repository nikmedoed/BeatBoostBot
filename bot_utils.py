import logging
import traceback
from aiogram_broadcaster import MessageBroadcaster, TextBroadcaster
from aiogram import types, filters, Bot, Dispatcher
import re


async def admin_broadcast(bot: Bot,text: str):
    try:
        logging.info(text)
        admins = bot.get("config").admin_users
        await TextBroadcaster(list(admins), text).run()
    except Exception as e:
        logging.error(f"{e}")

async def admin_notificate(message: types.Message, exc: Exception = None):
    try:
        user = message.from_user
        trace = exc and traceback.format_exc()
        br = "\n"
        text = (
            f"Системное уведомление\n"
            f"Пользователь\n"
            f"<code>tg_id :: </code>{user.id}\n"
            f"<code>nik :: </code>@{user.username}\n"
            f"<code>Имя :: </code>{user.first_name} {user.last_name}\n"
            f"\nЧто произошло:\n"
            f"{ f'<pre>{trace}</pre>{br}Сообщение пользователя:' if exc else message.text}"
        )
        admins = message.bot.get("config").admin_users
        await TextBroadcaster(list(admins), text).run()
        if exc:
            logging.error(trace)
            await MessageBroadcaster(admins, message).run()
    except Exception as e:
        logging.error(f"{e}")
# con_text = f"{message.text}\n\n{TEXT['settings_update']}"
# for key, value in con_dict.items():
#     message.entities.append(types.MessageEntity("code", len(con_text), len(key) + 4))
#     con_text += f"\n{key} :: {value}"
# message.text = con_text

def check_link(link):
    return re.match("https://(www\.)?youtu(be\.com/watch\?v=|.be/)[0-9a-zA-Z_\-]{8,}", link) is not None
