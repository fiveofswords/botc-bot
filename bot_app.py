import time

import discord
import logging
from bot_client import client, token

import bot
_ = bot.__name__  # need to reference the bot module to "install" event handlers


class BotApp:
    @staticmethod
    def run():
        print("Starting bot...")
        print("discord version is " + discord.__version__)
        while True:
            try:
                client.run(token)
                print("end")
                time.sleep(5)
            except Exception as e:
                logging.exception("Ignoring exception")
                print(str(e))
            finally:
                client.close()
                print("Restarting bot...")


if __name__ == "__main__":
    BotApp.run()