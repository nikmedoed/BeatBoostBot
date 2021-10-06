import datetime
import pytz
import requests

def getTargetUrl():
    return requests.get('гист со ссылкой на специальную таблицу').text

TARGET_SHEET_URL = getTargetUrl()

TELEGRAM_TOKEN = "..."
RELATIVE_CHAT_IDS = [ "...", '...']
TARGET_SHEET_URL = "googleappscriptlink"

START_DATE_FIRST_CYCLE = datetime.datetime(2021, 9, 4, hour=16, tzinfo=pytz.timezone("Europe/Moscow"))

LEN_SUBMISSION_PERIOD = datetime.timedelta(days=0,
                                           seconds=0,
                                           microseconds=0,
                                           milliseconds=0,
                                           minutes=0,
                                           hours=24,
                                           weeks=0)

LEN_WATCHING_PERIOD = datetime.timedelta(days=0,
                                         seconds=0,
                                         microseconds=0,
                                         milliseconds=0,
                                         minutes=0,
                                         hours=24,
                                         weeks=0)