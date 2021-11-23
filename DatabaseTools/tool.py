import sqlite3
import os
import re

import datetime as dt

databaseName = "botDatabase.db"


class SettingAlreadySet(Exception):
    def __init__(self):
        super(SettingAlreadySet, self).__init__()


def connect():
    existed = os.path.exists(databaseName)  # file created on .connect This is much prettier way to do this.
    connection = sqlite3.connect(databaseName)
    cursor = connection.cursor()
    if not existed:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS chat_logs(guild INTEGER, channel TEXT, model TEXT, author TEXT, ctx TEXT, reply TEXT, date INTEGER)")
        cursor.execute("CREATE TABLE IF NOT EXISTS settings(guildID INT, setting TEXT, value TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS disabled_commands(guildID INT, channelID INT, moduleName TEXT, commandName TEXT)")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS message_logs(id INTEGER PRIMARY KEY AUTOINCREMENT, message_content TEXT, attachment_links TEXT, length INTEGER, positive REAL, negative REAL, neutral REAL, compound REAL, insult INTEGER, unix INTEGER)")
        connection.commit()
    return connection, cursor


def create_tables(connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    try:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS chat_logs(guild INTEGER, channel TEXT, model TEXT, author TEXT, ctx TEXT, reply TEXT, date INTEGER)")
        cursor.execute("CREATE TABLE IF NOT EXISTS settings(guildID INTEGER, setting TEXT, value TEXT)")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS disabled_commands(guildID INTEGER, channelID INTEGER, moduleName TEXT, commandName TEXT)")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS message_logs(id INTEGER PRIMARY KEY AUTOINCREMENT, message_content TEXT, attachment_links TEXT, length INTEGER, positive REAL, negative REAL, neutral REAL, compound REAL, insult INTEGER, unix INTEGER)")
        connection.commit()
    except Exception as e:
        raise e
    else:
        return True


def sql_insert_into_message_logs(message_content: str, attachment_links: str, length: int, pos: float, neg: float, neu: float, compound: float, insult: bool, connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    if insult:
        insult = 1
    else:
        insult = 0
    try:
        sql = """INSERT INTO message_logs (message_content, attachment_links, length, positive, negative, neutral, compound, insult, unix) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        cursor.execute(sql, (message_content, attachment_links, length, pos, neg, neu, compound, insult, dt.datetime.now().timestamp()))
        connection.commit()
    except Exception as e:
        raise e
        return f"Insertion Error: {e}"
    else:
        return True


async def sql_insert_into_chat_logs(guild: int, channel: str, model: str, author: str, message: str, reply: str, date: int, connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    if None not in (connection, cursor):
        sql = """INSERT INTO chat_logs (guild, channel, model, author, ctx, reply, date) VALUES (?, ?, ?, ?, ?, ?, ?);"""
        try:
            cursor.execute(sql, (guild, channel, model, author, message, reply, date))
            connection.commit()
        except Exception as e:
            return f"Insertion Error: {e}"
        else:
            return True
    else:
        return f"Insertion Error: You have not connected the database!"


def sql_retrieve_last_10_messages(guild: int, connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    if None not in (connection, cursor):
        sql = """SELECT * FROM chat_logs WHERE guild == ? ORDER BY date DESC LIMIT 10;"""
        try:
            cursor.execute(sql, (guild,))
            results = cursor.fetchall()
        except Exception as e:
            return f"Retrieval Error: {e}."
        else:
            return results


def sql_update_setting(guild: int, setting: str, value: str, cursor: sqlite3.Cursor, connection: sqlite3.Connection) -> bool:
    sql = """SELECT value from settings WHERE guildID == ? and setting = ?;"""
    cursor.execute(sql, (guild, setting))
    results = cursor.fetchall()
    update = False
    for result in results:
        if value in result:
            raise SettingAlreadySet()
        else:
            update = True
            continue
    else:
        if update:
            sql = """UPDATE settings SET value = ? WHERE setting = ? AND guildID = ?;"""
            cursor.execute(sql, (value, setting, guild))
        else:
            sql = """INSERT INTO settings (guildID, setting, value) VALUES (?, ?, ?);"""
            cursor.execute(sql, (guild, setting, value))

        connection.commit()
        return True


def sql_retrieve_setting(guild: int, setting: str, cursor: sqlite3.Cursor) -> str or None:
    sql = """SELECT value from settings where guildID == ? AND setting == ?;"""
    cursor.execute(sql, (guild, setting))
    results = cursor.fetchall()
    try:
        return results[0]
    except IndexError:
        return None


def returnDisabled(guild, cursor: sqlite3.Cursor) -> list:
    sql = """SELECT moduleName, commandName, channelID FROM disabled_commands WHERE guildID == ?"""
    cursor.execute(sql, (guild,))
    return cursor.fetchall()


def sql_insert_command_disabled_commands(guild: int, channel: int, module: str, command: str, cursor: sqlite3.Cursor, d_connection: sqlite3.Connection) -> bool or str:
    check = sql_check_disabled_commands(guild, channel, command, module, cursor)
    if check:
        sql = """INSERT INTO disabled_commands (guildID, channelID, moduleName, commandName) VALUES (?, ?, ?, ?);"""
        try:
            cursor.execute(sql, (guild, channel, module, command))
            d_connection.commit()
        except Exception as e:
            return f"Insertion error: {e}"
        else:
            return True
    else:
        return f"Error: Already in database."


def sql_check_disabled_commands(guild: int, channel: int, command: str, module: str, cursor: sqlite3.Cursor) -> bool:
    sql = """SELECT commandName FROM disabled_commands WHERE guildID == ? AND channelID == ? AND moduleName == ?;"""
    cursor.execute(sql, (guild, channel, module))
    results = cursor.fetchall()
    for returns in results:
        if command in returns:
            return False
        else:
            continue
    else:
        return True
