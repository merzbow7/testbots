import requests

import json
from _collections_abc import Callable
from settings import Config
from collections import deque


class TeleBot(object):

    def __init__(self, config):
        self.url = f"https://api.telegram.org/bot{config.bot_token}/"
        self.session = requests.session()
        self.chats = deque()
        self.update_id = {}
        self.get_updates()

    def make_url(self, method: Callable) -> str:
        array_url = [self.url]
        array_url.extend(method.__name__.split('_'))
        return ''.join(array_url)

    def load_url(self, url: str, payload: dict = None) -> json:
        with self.session as session:
            response = session.get(url, params=payload)
            return response.json()

    def get_updates(self, payload=None) -> json:
        url: str = self.make_url(self.get_updates)
        result = self.load_url(url, payload)
        return result

    def update_bot(self) -> None:
        result = self.get_updates(payload=self.update_id)
        self.parse_chat(result)

    def parse_chat(self, message):
        if message["ok"]:
            if message["result"]:
                for item in message["result"]:
                    self.chats.append(item)
                    self.update_id["offset"] = item["update_id"] + 1

    def send_message(self, chat_id: int, text: str) -> None:
        url = self.make_url(self.send_message)
        payload = {'chat_id': chat_id, 'text': text}
        self.load_url(url, payload)


if __name__ == '__main__':
    bot = TeleBot(Config)
    exit_signal = False
    while True:
        bot.update_bot()
        while len(bot.chats):
            message = bot.chats.popleft()['message']
            bot.send_message(message['chat']['id'], 'you send ' + message['text'])
