import os
from dotenv import load_dotenv
from pathlib import Path

files = Path(__file__).parent.glob('*.env')
for file in files:
    load_dotenv(file)


class Config(object):
    bot_token = os.environ.get('BOT_TOKEN')
