import sqlite3


class User_database:
    def __init__(self, database_file):
        self.connection = sqlite3.connect(database_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT
                         UNIQUE
                         NOT NULL,
        user_id  INTEGER UNIQUE
                         NOT NULL,
        datetime INTEGER,
        status   INTEGER NOT NULL
                         DEFAULT (0));""")
        self.connection.commit()

    def add_user(self, user_id, datetime, status):
        with self.connection:
            self.cursor.execute("""INSERT INTO `users` (`user_id`, `datetime`, `status`) VALUES (?, ?, ?)""", (user_id, datetime, status))

    def upd_user(self, user_id, datetime, status):
        with self.connection:
            self.cursor.execute("""UPDATE `users` SET `datetime` = ?, `status` = ? WHERE `user_id` = ?""", (user_id, datetime, status))

    def check_user_datetime(self, user_id):
        with self.connection:
            result = self.cursor.execute("""SELECT `datetime` FROM `users` WHERE `user_id` = ?""", (user_id,)).fetchone()
            return result[0]

    def check_user_status(self, user_id):
        with self.connection:
            result = self.cursor.execute("""SELECT `status` FROM `users` WHERE `user_id` = ?""", (user_id,)).fetchone()
            return result[0]

    def upd_user_status(self, user_id, status):
        with self.connection:
            return self.cursor.execute("""UPDATE `users` SET `status` = ? WHERE `user_id` = ?""", (status, user_id,))

    def get_all_users(self, status=1):
        with self.connection:
            result = self.cursor.execute("""SELECT `user_id` FROM `users` WHERE `status` = ?""", (status,)).fetchall()
            return result

    def get_all(self):
        with self.connection:
            result = self.cursor.execute("""SELECT * FROM `users`""").fetchall()
            return result

    def check_user(self, user_id):
        with self.connection:
            result = self.cursor.execute("""SELECT * FROM `users` WHERE `user_id` = ?""", (user_id,)).fetchall()
            return bool(len(result))

    def close(self):
        self.connection.close()


class Banned_users:
    def __init__(self, database_file):
        self.connection = sqlite3.connect(database_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS bans (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id  INTEGER UNIQUE,
        nickname STRING  UNIQUE,
        datetime INTEGER DEFAULT (0),
        reason   TEXT);""")
        self.connection.commit()

    def add_user(self, user_id, nickname, datetime, reason):
        with self.connection:
            self.cursor.execute("""INSERT INTO `bans` (`user_id`, `nickname`, `datetime`, `reason`) VALUES (?, ?, ?, ?)""", (user_id, nickname, datetime, reason))

    def delete_user(self, user_id):
        with self.connection:
            self.cursor.execute("""DELETE FROM `bans` WHERE `user_id` = ?""", (user_id,))
            self.connection.commit()

    def upd_user_time(self, user_id, datetime):
        with self.connection:
            return self.cursor.execute("""UPDATE `bans` SET `datetime` = ? WHERE `user_id` = ?""", (datetime, user_id,))

    def check_user(self, user_id):
        with self.connection:
            result = self.cursor.execute("""SELECT * FROM `bans` WHERE `user_id` = ?""", (user_id,)).fetchall()
            return bool(len(result))

    def get_users(self):
        with self.connection:
            result = self.cursor.execute("""SELECT `nickname`, `user_id` FROM `bans`""").fetchall()
            return result

    def get_all_users(self):
        with self.connection:
            result = self.cursor.execute("""SELECT * FROM `bans`""").fetchall()
            return result

    def get_user_info(self, user_id):
        with self.connection:
            result = self.cursor.execute("""SELECT `datetime`, `reason` FROM `bans` WHERE `user_id` = ?""", (user_id,)).fetchone()
            return result

    def close(self):
        self.connection.close()