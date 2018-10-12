#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials


class GgCredits:
    def __init__(self):
        self.CREDENTIALS_FILE = "/var/www/telegrambots/kpi/table-b0cc9ceed3d8.json" 
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name(self.CREDENTIALS_FILE,
                                                                            ['https://www.googleapis.com/auth/spreadsheets',
                                                                             'https://www.googleapis.com/auth/drive'])
        self.httpAuth = self.credentials.authorize(httplib2.Http())
        self.service = apiclient.discovery.build('sheets', 'v4', http=self.httpAuth)
