#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

# TODO - branch with CSV
class GgCredits:
    def __init__(self):
        self.CREDENTIALS_FILE = "/var/www/telegrambots/kpi/table-b0cc9ceed3d8.json" 
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name(self.CREDENTIALS_FILE,
                                                                            ['https://www.googleapis.com/auth/spreadsheets',
                                                                             'https://www.googleapis.com/auth/drive'])
        self.httpAuth = self.credentials.authorize(httplib2.Http())
        self.service = apiclient.discovery.build('sheets', 'v4', http=self.httpAuth)
        self.service1 = apiclient.discovery.build('drive', 'v3', http=self.httpAuth)


class Spreadsheet(GgCredits):
    def create_document(self, length, user):
        # Setting parameters to the spreadsheet
        document_create = {'properties': {'title': 'Report for ' + user,
                                          'locale': 'ru_RU'},
                           'sheets': [{'properties': {'sheetType': 'GRID',
                                                      'sheetId': 0, 'title': user,
                                                      'gridProperties': {'rowCount': length + 1,
                                                                         'columnCount': 6
                                                                         }
                                                      }
                                       }]
                           }
        # Create it
        spreadsheet = self.service.spreadsheets().create(body=document_create).execute()
        # Setting permissions to spreadsheet. Object service(which v4) has no attribute permissions, so we use v3.
        self.service1.permissions().create(fileId=spreadsheet['spreadsheetId'],
                                           body={'type': 'anyone', 'role': 'reader'},
                                           fields='id').execute()
        return spreadsheet

    def add_rows(self, length, statement, user):
        new_spreadsheet = self.create_document(length, user)
        url = ''
        for i in range(length):
            data_to_add = {
                "valueInputOption": "USER_ENTERED",
                "data": [{"range": user + "!A" + str(i + 1) + ":F" + str(i + 1),
                          "majorDimension": "ROWS",
                          "values": [[statement[i][0],
                                      statement[i][1],
                                      statement[i][2],
                                      statement[i][3],
                                      statement[i][4],
                                      statement[i][5]
                                      ]]
                          }]
            }
            request = self.service.spreadsheets().values().batchUpdate(spreadsheetId=new_spreadsheet['spreadsheetId'],
                                                                       body=data_to_add).execute()
            url = 'https://docs.google.com/spreadsheets/d/' + request['spreadsheetId']
        return url
