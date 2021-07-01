from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import aiohttp
import asyncio


class Currency(object):

    def __init__(self, session, offset=3):
        self.session = session
        self.url = 'https://www.cbr.ru/currency_base/daily/'
        self.offset = offset
        self.update = self.get_time()
        self._dict = {}
        self._commands = {}

    def get_time(self):
        return datetime.now(timezone(timedelta(hours=self.offset)))

    async def get_page_cbr(self):
        async with self.session.get(self.url) as response:
            return await response.text()

    async def get_currency(self):
        html = await self.get_page_cbr()
        soup = BeautifulSoup(html, 'lxml')
        return soup.findAll('tr')

    async def update_state(self):
        for tr in await self.get_currency():
            line = [td.text for td in tr.findChildren()]
            if any(item.isdigit() for item in line):
                self._dict[line[1]] = float(line[-1].replace(",", "."))
                self._commands.update({line[1].lower(): line[3]})

    async def get_currency_dict(self):
        if not self._dict or self.update.date() != self.get_time().date():
            self.update = self.get_time()
            await self.update_state()
        return self._dict

    @property
    async def currency(self):
        if not self._dict or self.update.date() != self.get_time().date():
            await self.update_state()
        return self._dict


async def main():
    async with aiohttp.ClientSession() as session:
        currency = Currency(session)
        await currency.update_state()
        print(currency.currency)


if __name__ == '__main__':
    asyncio.run(main())
