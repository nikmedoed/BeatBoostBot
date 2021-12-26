from aiogram import types, Bot


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
