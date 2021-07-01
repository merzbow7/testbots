import logging

from aiohttp import web
from aiohttp.web_request import BaseRequest
from aiohttp import ClientSession
from settings import Config
from cbr import Currency
import asyncio


async def post_handler(request: BaseRequest):
    if request.body_exists:
        response = await request.json()
        await send_message(response)
        data = {"status": "ok"}
    else:
        logging.warning("Incorrect request")
        data = {"status": "error"}
    return web.json_response(data)


async def send_message(response):
    app.setdefault("send_task", asyncio.create_task(send_worker(app["send_queue"])))
    app["send_queue"].put_nowait(response)


async def send_worker(from_queue: asyncio.Queue, workers: int = 4):
    async with ClientSession() as session:
        currency = Currency(session)
        await asyncio.gather(*[sub_send_worker(session, from_queue, currency) for _ in range(workers)])


async def sub_send_worker(session: ClientSession, from_queue: asyncio.Queue, currency: Currency):
    url = f"https://api.telegram.org/bot{Config.bot_token}/sendMessage"
    while True:
        response = await from_queue.get()
        message = response.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text')
        if all([chat_id, text]):
            currency_dict = await currency.currency
            if text.upper() in currency_dict:
                text = currency_dict[text.upper()]
            elif text.upper()[1:] in currency_dict:
                text = currency_dict[text.upper()[1:]]
            params = {'chat_id': chat_id, 'text': text}
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    print(await response.json())

        else:
            logging.warning("Incorrect request")
        from_queue.task_done()


def create_app():
    current_app = web.Application()
    current_app.add_routes([web.post(Config.post_handler, post_handler)])
    current_app["send_queue"] = asyncio.Queue()
    return current_app


app = create_app()

if __name__ == '__main__':
    web.run_app(app)
