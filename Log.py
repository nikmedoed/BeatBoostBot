from bot_settings import ADMIN_USER_ID

def log(*message,bot=None):
    if bot:
        bot.send_message(ADMIN_USER_ID, message)
    print(message)