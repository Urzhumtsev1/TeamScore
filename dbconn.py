#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

import psycopg2
import constants

# Please change 'botname.' to your schema
class PgAdmin:
    def __init__(self):
        self.connection = psycopg2.connect(database=constants.DATABASE,
                                           user=constants.USER,
                                           password=constants.PASSWORD,
                                           host=constants.HOST,
                                           port=constants.PORT)
        self.cursor = self.connection.cursor()

    def select_all1(self, column, table, parameter):
        self.cursor.execute('''SELECT {0} FROM botname.{1} WHERE {2}'''.format(column, table, parameter))
        return self.cursor.fetchall()

    def select(self, parameter):
        self.cursor.execute('''SELECT {}'''.format(parameter))
        return self.cursor.fetchone()

    def select_single(self, table, column, parameter):
        self.cursor.execute('''SELECT {0} FROM botname.{1} WHERE {2} '''.format(table, column, parameter))
        return self.cursor.fetchone()

    def delete_single(self, table, column, parameter):
        self.cursor.execute('''DELETE FROM botname.{0} WHERE {1} = {2}'''.format(table, column, parameter))
        return self.connection.commit()

    def insert(self, tablecolumns, values):
        self.cursor.execute("""INSERT INTO botname.{0} VALUES {1};""".format(tablecolumns, values))
        return self.connection.commit()

    def update(self, table, values, condition):
        self.cursor.execute("""UPDATE botname.{0} SET {1} WHERE {2}""".format(table, values, condition))
        return self.connection.commit()

    def close(self):
        self.connection.close()

