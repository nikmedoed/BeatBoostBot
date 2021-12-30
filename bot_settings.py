import datetime
import pytz
import requests
import configparser
import json
from aiogram import Bot
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Union, Set
from tables import send_linkdata_to_sheet, verificate_tilda_code

SETTINGS_FILE_PATH = "settings.ini"


def str_to_timedelta(s) -> datetime.timedelta:
    return datetime.timedelta(**json.loads(s))


def str_to_int_set(s) -> Set[int]:
    return set(int(i) for i in s.split(','))


@dataclass
class Config:
    gist_link: str
    bot_token: str
    config_file_path: str
    config_file_parser: configparser
    redis: Dict[str, Union[int, str, None]]
    url_links_base: str = field(default_factory=str)
    url_tilda_base: str = field(default_factory=str)
    admin_users: Set[int] = field(default_factory=set)
    active_chat_ids: Set[int] = field(default_factory=set)
    start_date: datetime.datetime = datetime.datetime.now()
    delta_submission: datetime.timedelta = 0
    delta_watching: datetime.timedelta = 0
    delta_sum: datetime.timedelta = 0
    active_chat_names: Dict[int, str] = field(default_factory=dict)
    active_chat_counts: Dict[int, int] = field(default_factory=dict)
    bot: Bot = None

    def config_to_html(self):
        con_dict = self.__dict__
        stop_list = ('config_file_parser', 'redis', 'config_file_path',
                     'chat_names', 'bot_token', 'delta_sum', 'bot',
                     'active_chat_names', 'active_chat_counts')
        con_text = "\n".join(
            [f"<code>{key} :: </code>{value}"
             for key, value in con_dict.items() if key not in stop_list
             ])
        return con_text

    async def add_member(self, chat_id: int):
        self.active_chat_counts[chat_id] = (await self.get_active_chat_count(chat_id)) + 1

    async def sub_member(self, chat_id: int):
        self.active_chat_counts[chat_id] = (await self.get_active_chat_count(chat_id)) - 1

    async def get_active_chat_count(self, cid: int):
        count = self.active_chat_counts.get(cid)
        if not count or count < 0:
            count = self.active_chat_counts[cid] = await self.bot.get_chat_member_count(cid)
        return count

    async def get_invite_to_room(self):
        counts = [(i, (await self.get_active_chat_count(i))) for i in self.active_chat_ids]
        min_chat = min(counts, key=lambda x: x[1])
        link = await self.bot.create_chat_invite_link(min_chat[0], member_limit=1)
        return link.invite_link

    async def fill_chat_names(self):
        if self.bot:
            self.active_chat_names = {
                cid: (await self.bot.get_chat(chat_id=cid)).title for cid in self.active_chat_ids
            }
        return self.active_chat_names

    async def get_chat_name(self, chat_id):
        if not self.active_chat_names:
            await self.fill_chat_names()
        return chat_id, self.active_chat_names.get(chat_id, "unavailable")

    @staticmethod
    def read(file=SETTINGS_FILE_PATH) -> 'Config':
        bot_data = configparser.ConfigParser()
        bot_data.read(file)
        settings = bot_data['SETTINGS']
        config: Config = Config(
            bot_token=settings['BOT_TOKEN'],
            gist_link=settings['SETTINGS_GIST_LINK'],
            config_file_parser=bot_data,
            config_file_path=file,
            redis=dict(bot_data['REDIS'])
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
        self.admin_users = str_to_int_set(settings['ADMIN_USERS_ID'])
        self.active_chat_ids = str_to_int_set(settings['RELATIVE_CHAT_IDS'])
        self.start_date: datetime.datetime = pytz.timezone('Europe/Moscow').localize(
            datetime.datetime.strptime(settings['START_DATE_FIRST_CYCLE'], '%Y-%m-%d %H:%M:%S'),
            is_dst=None
        )
        self.delta_submission = str_to_timedelta(settings['LEN_SUBMISSION_PERIOD'])
        self.delta_watching = str_to_timedelta(settings['LEN_WATCHING_PERIOD'])
        self.delta_sum = self.delta_submission + self.delta_watching
        self.active_chat_names = dict()
        self.active_chat_counts = dict()
        return self

    def verificate_tilda_code(self, user_tilda_id, uid="", uname=""):
        return verificate_tilda_code(self.url_tilda_base, user_tilda_id, uid, uname)

    def send_linkdata_to_sheet(self, uid, username, link, chatid, chattitle=""):
        return send_linkdata_to_sheet(self.url_links_base, uid, username, link, chatid, chattitle)

    def check_is_now_sumbmission_time(self):
        now = datetime.datetime.now(tz=pytz.timezone("Europe/Moscow"))
        cycle_time = (now - self.start_date) % self.delta_sum
        return cycle_time < self.delta_submission

    def get_next_watch_period_time(
            self,
            shift: Union[datetime.timedelta, int, Dict[str, Union[str, int, bool]]] = 0,
            submission=False
    ):
        if type(shift) == dict:
            shift = shift.get('hours', 0) * 60 + shift.get('minutes', 0)
        if type(shift) == int:
            shift = datetime.timedelta(minutes=shift)
        now = datetime.datetime.now(tz=pytz.timezone("Europe/Moscow"))
        diff = now - self.start_date
        deadline = self.start_date + \
                   self.delta_sum * (diff // self.delta_sum) + shift + \
                   (self.delta_sum if submission else self.delta_submission)
        date = deadline.strftime(
            f'{"сегодня" if now.day == deadline.day else "завтра"} %d.%m.%y в %H:%M по {deadline.tzname()}'
        )
        return date


if __name__ == '__main__':
    config = Config.read()
    print(config)
