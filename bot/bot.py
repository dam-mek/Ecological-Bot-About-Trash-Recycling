import os
from aiogram import Bot

API_TOKEN = os.getenv('TOKENPIDARASBOT')
bot = Bot(token=API_TOKEN, parse_mode='html')
