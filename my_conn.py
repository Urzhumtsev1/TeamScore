#!/usr/bin/python3.5
# -*- coding: utf-8 -*-
import variables
import telebot
from aiohttp import web


class MyConn:
    def __init__(self):

        self.API_TOKEN = variables.TOKEN

        self.WEBHOOK_HOST = variables.WEBHOOK_HOST
        self.WEBHOOK_PORT = variables.WEBHOOK_PORT  # port need to be 'open'
        self.WEBHOOK_LISTEN = variables.WEBHOOK_LISTEN  # In some VPS you may need to put here the IP address
        self.WEBHOOK_URL_BASE = "https://{}".format(self.WEBHOOK_HOST)
        self.WEBHOOK_URL_PATH = "/{}/".format(self.API_TOKEN)

        self.bot = telebot.TeleBot(variables.TOKEN)

        self.app = web.Application()
