#!/usr/bin/python3.5
# -*- coding: utf-8 -*-
import psycopg2
import variables


class PGadmin:
    def __init__(self):
        self.connection = psycopg2.connect(database=variables.DATABASE,
                                    user=variables.USER,
                                    password=variables.PASSWORD,
                                    host=variables.HOST,
                                    port=variables.PORT)
        self.cursor = self.connection.cursor()

    def select_all(self, table):
        self.cursor.execute('''SELECT * FROM {}'''.format(table))
        return self.cursor.fetchall()

    def select_all1(self, column, table, parameter):
        self.cursor.execute('''SELECT {0} FROM {1} WHERE {2}'''.format(column, table, parameter))
        return self.cursor.fetchall()

    def select_all2(self, column, table):
        self.cursor.execute('''SELECT {0} FROM {1}'''.format(column, table))
        return self.cursor.fetchall()

    def select_all3(self, parameter):
        self.cursor.execute('''SELECT {}'''.format(parameter))
        return self.cursor.fetchall()

    def select(self, parameter):
        self.cursor.execute('''SELECT {}'''.format(parameter))
        return self.cursor.fetchone()

    def select_single(self, table, column, parameter):
        self.cursor.execute('''SELECT {0} FROM {1} WHERE {2} '''.format(table, column, parameter))
        return self.cursor.fetchone()

    def delete_single(self, table, column, parameter):
        self.cursor.execute('''DELETE FROM {0} WHERE {1} = {2}'''.format(table, column, parameter))
        return self.connection.commit()

    def delete(self, table, parameter):
        self.cursor.execute('''DELETE FROM {0} WHERE {1}'''.format(table, parameter))
        return self.connection.commit()

    def insert(self, tablecolumns, values):
        self.cursor.execute("""INSERT INTO {0} VALUES {1};""".format(tablecolumns, values))
        return self.connection.commit()

    def update(self, table, values, condition):
        self.cursor.execute("""UPDATE {0} SET {1} WHERE {2}""".format(table, values, condition))
        return self.connection.commit()

    def close(self):
        self.connection.close()

