import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import CommandStart
from aiogram.utils.markdown import hbold
from aiohttp import ClientSession

from secret import COINMARKETCAP_API_KEY_T, TELEGRAM_BOT_TOKEN_T

# API ключ CoinMarketCap
COINMARKETCAP_API_KEY = COINMARKETCAP_API_KEY_T

# Токен бота Telegram
TELEGRAM_BOT_TOKEN = TELEGRAM_BOT_TOKEN_T

# Словарь для хранения криптовалют и их пороговых значений
cryptocurrencies = {}

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    await message.answer(
        "Привет Чтобы добавить криптовалюту для отслеживания, отправьте команду /add <имя_валюты> <максимальный_порог> <минимальный_порог>")


@dp.message()
async def add_cmd(message: types.Message) -> None:
    args = message.text.split()
    if len(args) != 4 or args[0].lower() != '/add':
        await message.answer(
            "Неправильный формат команды. Используйте /add <имя_валюты> <максимальный_порог> <минимальный_порог>")
        return
    name = args[1]
    try:
        max_threshold = float(args[2])
        min_threshold = float(args[3])
    except ValueError:
        await message.answer("Пороги должны быть числами.")
        return
    cryptocurrencies[name] = {'max': max_threshold, 'min': min_threshold, 'chat_id': message.chat.id}
    await message.answer(f"Добавлена криптовалюта {name} с порогами {max_threshold} и {min_threshold}")


async def check_prices():
    async with ClientSession() as session:
        while True:
            for name, thresholds in cryptocurrencies.items():
                async with session.get(f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest',
                                       headers={'Accepts': 'application/json',
                                                'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY},
                                       params={'symbol': name, 'convert': 'USD'}) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = data['data'][name]['quote']['USD']['price']
                        if price >= thresholds['max']:
                            await bot.send_message(chat_id=thresholds['chat_id'],
                                                   text=f"Курс {name} достиг максимального порога: {price}")
                            print(price)
                        elif price <= thresholds['min']:
                            await bot.send_message(chat_id=thresholds['chat_id'],
                                                   text=f"Курс {name} достиг минимального порога: {price}")
                            print(price)
                    else:
                        print(f"Ошибка запроса для {name}: {response.status}")
            await asyncio.sleep(600)


async def on_startup(dp):
    asyncio.create_task(check_prices())


async def main() -> None:
    await dp.start_polling(bot)
    await on_startup(dp)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
