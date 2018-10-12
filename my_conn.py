#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

import telebot
from aiohttp import web
import constants


class MyConn:
    def __init__(self):

        self.API_TOKEN = constants.TOKEN

        self.WEBHOOK_HOST = constants.WEBHOOK_HOST
        self.WEBHOOK_PORT = constants.WEBHOOK_PORT  # port need to be 'open'
        self.WEBHOOK_LISTEN = constants.WEBHOOK_LISTEN  # In some VPS you may need to put here the IP address
        self.WEBHOOK_URL_BASE = "https://{}".format(self.WEBHOOK_HOST)
        self.WEBHOOK_URL_PATH = "/{}/".format(self.API_TOKEN)

        self.bot = telebot.TeleBot(constants.TOKEN)  # Your bot token here

        self.app = web.Application()
