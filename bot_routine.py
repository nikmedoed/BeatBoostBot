from bot_settings import *
import re

LEN_SUM_PERIOD = LEN_SUBMISSION_PERIOD + LEN_WATCHING_PERIOD


def check_membership(bot, userid):
    for id in RELATIVE_CHAT_IDS:
        try:
            if bot.get_chat_member(chat_id=id, user_id=userid).status != "left":
                return True
        except:
            pass
    return False


def check_is_now_sumbmission_time():
    now = datetime.datetime.now(tz=pytz.timezone("Europe/Moscow"))
    cycle_time = (now - START_DATE_FIRST_CYCLE) % LEN_SUM_PERIOD
    return cycle_time < LEN_SUBMISSION_PERIOD


def get_next_sumbmission_time():
    now = datetime.datetime.now(tz=pytz.timezone("Europe/Moscow"))
    diff = now - START_DATE_FIRST_CYCLE
    deadline = START_DATE_FIRST_CYCLE + LEN_SUM_PERIOD * (diff // LEN_SUM_PERIOD) + LEN_SUBMISSION_PERIOD
    date = deadline.strftime(
        f'{"сегодня" if now.day == deadline.day else "завтра"} %d.%m.%y в %H:%M по {deadline.tzname()}'
    )
    return date


def check_link(link):
    return re.match("https://(www\.)?youtu(be\.com/watch\?v=|.be/)[0-9a-zA-Z_\-]{8,}", link) is not None



if __name__ == "__main__":
    assert check_link("https://github.com/eternnoir/pyTelegramBotAPI") == False
    assert check_link("https://www.youtube.com/playlist?list=WL") == False
    assert check_link("https://youtu.be/M8V5Nb0ytiI") == True
    assert check_link("https://www.youtube.com/watch?v=tyBvOv2ruXo") == True
    assert check_link("https://www.youtube.com/watch?v=efZ-BI5IjWE") == True
    print(check_is_now_sumbmission_time())
    print(get_next_sumbmission_time())
