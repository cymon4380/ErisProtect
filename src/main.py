import logging
from os import getenv
from models.bot import ErisProtectBot
from utils.plugin_manager import load_plugins

logging.basicConfig(
    filename='erisprotect.log',
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

bot = ErisProtectBot()

if __name__ == '__main__':
    load_plugins(bot)
    bot.run(getenv('DISCORD_TOKEN'))
