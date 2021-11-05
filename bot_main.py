import telebot
import Log
import json
from bot_text import TEXT
from bot_routine import *
from database import sendData, verificateId
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import types
from time import sleep
import traceback

bot = telebot.TeleBot(TELEGRAM_TOKEN)


def check_again_button(uid):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton(TEXT['button_repeat_verification'], callback_data="repeat"))
    bot.send_message(uid, TEXT['membership'], reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "repeat":
        firstCheck(call)
        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id, "Какие странные у вас кнопочки!?")


@bot.message_handler(commands=['start'])
def start(message):
    try:
        if message.chat.type == 'private':
            firstCheck(message)
    except Exception as ex1:
        Log.log("unhandled exception, send_text", str(ex1))


def validateCode(bot, uid, code):
    unique_code = code.strip()
    if re.match(r"[\d]+:[\d]+", unique_code):
        act = verificateId(unique_code)
        err = act.get("error")
        if err:
            bot.send_message(uid, TEXT['start_chat_error'] + err)
        elif act.get("ok"):
            link = get_invite_to_room(bot)
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(TEXT['get_invite'], url=link))
            bot.send_message(uid, TEXT['new_room'], reply_markup=markup)
            return True
    return False


def firstCheck(message):
    uid = message.from_user.id
    if not check_membership(bot, uid):
        if not hasattr(message, 'text') or not validateCode(bot, uid, message.text):
            check_again_button(uid)
    else:
        if check_is_now_sumbmission_time():
            bot.send_message(uid, TEXT['instruction'] % get_next_sumbmission_time())
        else:
            bot.send_message(uid, TEXT['pausework'])


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    try:
        if message.chat.type != 'private' or len(message.text) <= 0:
            Log.log(message)
            return

        mfu = message.from_user
        uid = mfu.id
        uname = f'{mfu.first_name} {mfu.last_name} - @{mfu.username}'
        umes = message.text
        membership = check_membership(bot, uid)
        if not membership:
            if not validateCode(bot, uid, message.text):
                check_again_button(uid)
        # elif not check_is_now_sumbmission_time():
        #     bot.send_message(uid, TEXT['pausework'])
        elif not check_link(umes):
            bot.reply_to(message, TEXT['wrongmessage'], parse_mode="Markdown")
        else:
            response = sendData(uid, uname, umes, *membership)
            if response.get("ok"):
                bot.reply_to(message, TEXT['add_success'])
            elif response.get("link"):
                bot.reply_to(message, TEXT['yourlink'] % (response.get("link"), umes))
            else:
                bot.reply_to(message, TEXT['add_error'] % json.dumps(response, indent=1))

    except Exception as ex1:
        Log.log("unhandled exception, send_text", str(ex1))


@bot.my_chat_member_handler()
def my_chat_m(message: types.ChatMemberUpdated):
    if message.new_chat_member.status == "member":
        Log.log(message.chat.id)


# bot.infinity_polling()

while 1:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        message = (f"Infinity polling exception: {str(e)}\n"
                   f"Exception traceback:\n{traceback.format_exc()}")
        sleep(1)
        bot.send_message(ADMIN_USER_ID, message)
