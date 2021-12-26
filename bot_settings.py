import datetime
import pytz
import requests
import configparser
import json

from dataclasses import dataclass, field
from typing import List
from database import sendData, verificateId

SETTINGS_FILE_PATH = "settings.ini"


def str_to_timedelta(s) -> datetime.timedelta:
    return datetime.timedelta(**json.loads(s))


def str_to_int_list(s) -> List[int]:
    return [int(i) for i in s.split(',')]


@dataclass
class Config:
    gist_link: str
    bot_token: str
    config_file_path: str
    config_file_parser: configparser
    url_links_base: str = field(default_factory=str)
    url_tilda_base: str = field(default_factory=str)
    admin_users: List[int] = field(default_factory=list)
    active_chat_ids: List[int] = field(default_factory=list)
    start_date: datetime.datetime = datetime.datetime.now()
    delta_submission: datetime.timedelta = 0
    delta_watching: datetime.timedelta = 0
    delta_sum: datetime.timedelta = 0

    @staticmethod
    def read(file=SETTINGS_FILE_PATH) -> 'Config':
        bot_data = configparser.ConfigParser()
        bot_data.read(file)
        settings = bot_data['SETTINGS']
        config: Config = Config(
            bot_token=settings['BOT_TOKEN'],
            gist_link=settings['SETTINGS_GIST_LINK'],
            config_file_parser=bot_data,
            config_file_path=file
        )
        config.update()
        return config

    def save(self, file=""):
        with open(file or self.config_file_path, 'w') as f:
            self.config_file_parser.write(f)

    def update(self):
        bot_data = configparser.ConfigParser()
        bot_data.read_string(requests.get(self.gist_link).text)
        settings = bot_data['SETTINGS']

        new = settings.get('NEW_SETTINGS_LINK')
        if new and new != self.gist_link:
            self.gist_link = new
            self.config_file_parser['SETTINGS']['SETTINGS_GIST_LINK'] = new
            self.save()
            return self.update()

        self.url_links_base: str = settings['LINKS_SHEET']
        self.url_tilda_base: str = settings['TILDA_SHEET']
        self.admin_users: List[int] = str_to_int_list(settings['ADMIN_USERS_ID'])
        self.active_chat_ids: List[int] = str_to_int_list(settings['RELATIVE_CHAT_IDS'])
        self.start_date: datetime.datetime = pytz.timezone('Europe/Moscow').localize(
            datetime.datetime.strptime(settings['START_DATE_FIRST_CYCLE'], '%Y-%m-%d %H:%M:%S'),
            is_dst=None
        )
        self.delta_submission = str_to_timedelta(settings['LEN_SUBMISSION_PERIOD'])
        self.delta_watching = str_to_timedelta(settings['LEN_WATCHING_PERIOD'])
        self.delta_sum = self.delta_submission + self.delta_watching
        return self

    def verificateId(self, user_tilda_id):
        return verificateId(self.url_tilda_base, user_tilda_id)

    def sendData(self, uid, username, link, chatid, chattitle=""):
        return sendData(self.url_links_base, uid, username, link, chatid, chattitle)

    def check_is_now_sumbmission_time(self):
        now = datetime.datetime.now(tz=pytz.timezone("Europe/Moscow"))
        cycle_time = (now - self.start_date) % self.delta_sum
        return cycle_time < self.delta_submission

    def get_next_sumbmission_time(self):
        now = datetime.datetime.now(tz=pytz.timezone("Europe/Moscow"))
        diff = now - self.start_date
        deadline = self.start_date + self.delta_sum * (diff // self.delta_sum) + self.delta_submission
        date = deadline.strftime(
            f'{"сегодня" if now.day == deadline.day else "завтра"} %d.%m.%y в %H:%M по {deadline.tzname()}'
        )
        return date

if __name__ == '__main__':
    config = Config.read()
    print(config)
