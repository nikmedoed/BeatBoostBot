import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2

import bot_handlers
from bot_settings import Config
from updatesworker import get_handled_updates_list


async def main(config):
    logging.basicConfig(
        level=logging.INFO,
        # format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    bot = Bot(config.bot_token, parse_mode="HTML")
    bot["config"]: Config = config
    config.bot = bot

    storage = RedisStorage2(**config.redis)
    bot["storage"] = storage
    dp = Dispatcher(bot, storage=storage)

    await bot_handlers.register(dp)
    try:
        await dp.start_polling(allowed_updates=get_handled_updates_list(dp))
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


#  периодические задачи можно делать так
#     dp.loop.create_task(periodic())
# Now periodic can be formulated as in your initial attempt:
# async def periodic(sleep_for, queue):
#     while True:
#         await asyncio.sleep(sleep_for)
#         now = datetime.utcnow()
#         for id in chat_ids:
#             await bot.send_message(id, f"{now}",
#                                    disable_notification=True)


if __name__ == '__main__':
    try:
        asyncio.run(main(config=Config.read()))
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
