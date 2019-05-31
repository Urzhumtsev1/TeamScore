#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

import psycopg2
from psycopg2 import sql
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
        self.cursor.execute(sql.SQL("select {} from {} where {} = %s")
                            .format(sql.Identifier(column), sql.Identifier(table), sql.Identifier(parameter))
        return self.cursor.fetchall()

    def select_single(self, table, column, parameter):
        self.cursor.execute(sql.SQL("select {} from {} where {} = %s")
                            .format(sql.Identifier(column), sql.Identifier(table), sql.Identifier(parameter)))
        return self.cursor.fetchone()

    def delete_single(self, table, column, parameter):
         self.cursor.execute(sql.SQL("delete from {} where {} = {}")
                            .format(sql.Identifier(table), sql.Identifier(column), sql.Identifier(parameter))
        return self.connection.commit()

    def insert(self, tablecolumns, values):
        self.cursor.execute(
            sql.SQL("insert into {} values (%s, %s, %s, %s)").format(sql.Identifier(tablecolumns)), values)
        return self.connection.commit()

    def update(self, table, values, condition):
        self.cursor.execute(sql.SQL("update botname.{} set {} where {} = {}")
                            .format(sql.Identifier(table), sql.Identifier(values), sql.Identifier(condition)))
        return self.connection.commit()

    def close(self):
        self.connection.close()

