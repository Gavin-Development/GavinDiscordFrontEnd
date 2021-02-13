import sqlite3
import os
import re

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
        connection.commit()
    return connection, cursor


async def sql_insert_into(guild: int, channel: str, model: str, author: str, message: str, reply: str, date: int, connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    if None not in (connection, cursor):
        sql = f"""INSERT INTO chat_logs (guild, channel, model, author, ctx, reply, date) VALUES ({guild}, '{channel}', '{model}', '{author}', '{message}', '{reply}', {date})"""
        try:
            cursor.execute(sql)
            connection.commit()
        except Exception as e:
            return f"Insertion Error: {e}"
        else:
            return True
    else:
        return f"Insertion Error: You have not connected the database!"


def sql_retrieve_last_10_messages(guild: int, connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    if None not in (connection, cursor):
        sql = f"""SELECT * FROM chat_logs WHERE guild == {guild} ORDER BY date LIMIT 10;"""
        try:
            cursor.execute(sql)
            results = cursor.fetchall()
        except Exception as e:
            return f"Retrieval Error: {e}."
        else:
            return results


def sql_update_setting(guild: int, setting: str, value: str, cursor: sqlite3.Cursor, connection: sqlite3.Connection) -> bool:
    sql = """SELECT value from settings WHERE guildID == {} and setting = "{}";""".format(guild, setting)
    pattern = re.compile(r"[<>#]")
    value = re.sub(pattern, "", value)
    cursor.execute(sql)
    results = cursor.fetchall()
    for result in results:
        if value in result:
            raise SettingAlreadySet()
        else:
            continue
    else:
        sql = """UPDATE settings SET value = {} WHERE setting = {} AND guildID = {};""".format(value, setting, guild)
        try:
            cursor.execute(sql)
            connection.commit()
        except sqlite3.OperationalError:
            sql = """INSERT INTO settings (guildID, setting, value) VALUES ({}, "{}", "{}");""".format(guild, setting, value)
            try:
                cursor.execute(sql)
                connection.commit()
            except Exception as e:
                raise e
        except Exception as e:
            raise e
        else:
            return True


def sql_retrieve_setting(guild: int, setting: str, cursor: sqlite3.Cursor) -> str or None:
    sql = """SELECT value from settings where guildID == {} AND setting == "{}";""".format(guild, setting)
    cursor.execute(sql)
    results = cursor.fetchall()
    try:
        return results[0]
    except IndexError:
        return None


def returnDisabled(guild, cursor: sqlite3.Cursor) -> list:
    sql = """SELECT moduleName, commandName, channelID FROM disabled_commands WHERE guildID == {}""".format(guild)
    cursor.execute(sql)
    return cursor.fetchall()


def sql_insert_command_disabled_commands(guild: int, channel: int, module: str, command: str, cursor: sqlite3.Cursor, d_connection: sqlite3.Connection) -> bool or str:
    check = sql_check_disabled_commands(guild, channel, command, module, cursor)
    if check:
        sql = """INSERT INTO disabled_commands (guildID, channelID, moduleName, commandName) VALUES (?, ?, ?, ?)""".format(guild, channel, module, command)
        try:
            cursor.execute(sql)
            d_connection.commit()
        except Exception as e:
            return f"Insertion error: {e}"
        else:
            return True
    else:
        return f"Error: Already in database."


def sql_check_disabled_commands(guild: int, channel: int, command: str, module: str, cursor: sqlite3.Cursor) -> bool:
    sql = """SELECT commandName FROM disabled_commands WHERE guildID == ? AND channelID == ? AND moduleName == ?;""".format(guild, channel, module)
    cursor.execute(sql)
    results = cursor.fetchall()
    for returns in results:
        if command in returns:
            return False
        else:
            continue
    else:
        return True
