import aiohttp
import asyncio
from settings import Config


async def fetch_async(session: aiohttp.ClientSession, read_queue: asyncio.Queue, update_id: int) -> int:
    url = f"https://api.telegram.org/bot{Config.bot_token}/getUpdates"
    params = {"offset": update_id}
    async with session.get(url, params=params) as response:
        data = await response.json()
        if data['ok']:
            for item in data['result']:
                if item['update_id'] > update_id:
                    params["offset"] = item['update_id']
                read_queue.put_nowait(item)
            if data['result'] and params["offset"] >= update_id:
                return params["offset"] + 1
    return params["offset"]


async def send_worker(from_queue: asyncio.Queue, session: aiohttp.ClientSession) -> None:
    url = f"https://api.telegram.org/bot{Config.bot_token}/sendMessage"
    while True:
        item: dict = await from_queue.get()
        message = item['message']
        params = {'chat_id': message['chat']['id'], 'text': message['text'],
                  "parse_mode": "HTML"}
        async with session.get(url, params=params):
            await asyncio.sleep(0)
        from_queue.task_done()


async def main(workers: int = 4) -> None:
    write_queue = asyncio.Queue()
    offset: int = 0
    async with aiohttp.ClientSession() as session:
        for _ in range(workers):
            asyncio.create_task(send_worker(write_queue, session))
        while True:
            offset = await fetch_async(session, write_queue, offset)
            await asyncio.sleep(0.001)


if __name__ == '__main__':
    asyncio.run(main(16))
