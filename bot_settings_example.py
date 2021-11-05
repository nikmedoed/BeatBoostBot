import datetime
import pytz
import requests

GIT_LINK = 'https://gist.githubusercontent.com/.../raw/'

LINKS_URL = f'{GIT_LINK}Links_dev'
CHAT_URL = f'{GIT_LINK}relative_chats_dev'
TILDA_URL = f'{GIT_LINK}Tilda_dev'

def getTargetUrl():
    return requests.get(LINKS_URL).text

def getChatIds():
    return requests.get(CHAT_URL).text.split()

def getTildaSheet():
    return requests.get(TILDA_URL).text

ADMIN_USER_ID = "77966866"

TARGET_SHEET_URL = getTargetUrl()

RELATIVE_CHAT_IDS = getChatIds()

TILDA_SHEET_URL = getTildaSheet()

TELEGRAM_TOKEN = "..."

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