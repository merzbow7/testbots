import aiohttp
import asyncio
import contextlib
import logging
import sys

from settings import Config
from cbr import Currency


class TeleBot(object):
    def __init__(self, workers: int):
        self.workers: int = workers
        self.base_url: str = f"https://api.telegram.org/bot{Config.bot_token}"
        self.commands = []

        logger = logging.getLogger('TeleBot')
        formatter = logging.Formatter(
            '%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: "%(message)s"'
        )
        console_output_handler = logging.StreamHandler(sys.stderr)
        console_output_handler.setFormatter(formatter)
        logger.addHandler(console_output_handler)
        logger.setLevel(logging.ERROR)

    async def get_updates(self, read_queue: asyncio.Queue, update_id: int) -> int:
        url = f"{self.base_url}/getUpdates"
        params = {"offset": update_id}
        async with self.session.get(url, params=params) as response:
            data = await response.json(content_type=None)
            if data['ok']:
                for item in data['result']:
                    if item['update_id'] > update_id:
                        params["offset"] = item['update_id']
                    read_queue.put_nowait(item)
                if data['result'] and params["offset"] >= update_id:
                    return params["offset"] + 1
        return params["offset"]

    async def get_commands(self):
        url = f"{self.base_url}/getMyCommands"
        async with self.session.get(url) as response:
            data = await response.json()
            if data['ok']:
                for item in data['result']:
                    self.commands += [item.get('command')]

    async def send_worker(self, from_queue: asyncio.Queue) -> None:
        url = f"{self.base_url}/sendMessage"
        while True:
            item: dict = await from_queue.get()
            message = item['message']
            currency_dict = await self.currency.get_currency_dict()
            text: str = message.get('text', '')
            if text.startswith("/") and text[1:] in self.commands:
                text = text[1:]
            answer = currency_dict.get(text.upper(), text)
            params = {'chat_id': message['chat']['id'], 'text': answer, "parse_mode": "HTML"}
            async with self.session.get(url, params=params):
                await asyncio.sleep(0)
            from_queue.task_done()

    @contextlib.asynccontextmanager
    async def init(self):
        try:
            self.session = aiohttp.ClientSession()
            self.currency = Currency(self.session)
            await self.get_commands()
            yield
        except Exception as err:
            logging.error(err)
        finally:
            await self.session.close()

    async def _main(self) -> None:
        write_queue = asyncio.Queue()
        offset: int = 0
        async with self.init():
            for _ in range(self.workers):
                asyncio.create_task(self.send_worker(write_queue))
            while True:
                offset = await self.get_updates(write_queue, offset)
                await asyncio.sleep(0.1)

    def poll(self) -> None:
        asyncio.run(self._main())


if __name__ == '__main__':
    bot = TeleBot(8)
    bot.poll()
