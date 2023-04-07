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

    def check_user_status(self, user_id):
        with self.connection:
            result = self.cursor.execute("""SELECT `status` FROM `users` WHERE `user_id` = ?""", (user_id,)).fetchone()
            return result

    def upd_user_status(self, user_id, status):
        with self.connection:
            return self.cursor.execute("""UPDATE `users` SET `status` = ? WHERE `user_id` = ?""", (status, user_id,))

    def get_users(self, status=1):
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


class Hidden_continuation_database:
    def __init__(self, database_file):
        self.connection = sqlite3.connect(database_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS hidden_continuation (
        callback  INTEGER PRIMARY KEY AUTOINCREMENT,
        sub       TEXT,
        no_sub    TEXT,
        condition TEXT    DEFAULT None);""")
        self.connection.commit()

    def add_button(self, sub_text, no_sub_text, condition):
        with self.connection:
            self.cursor.execute("""INSERT INTO `hidden_continuation` (`sub`, `no_sub`, `condition`) VALUES (?, ?, ?)""", (sub_text, no_sub_text, condition))

    def get_button(self, callback):
        with self.connection:
            result = self.cursor.execute("""SELECT * FROM `hidden_continuation` WHERE `callback` = ?""", (callback,)).fetchone()
            return result

    def get_last_button(self):
        with self.connection:
            last_id = self.cursor.execute("""SELECT max(callback) FROM `hidden_continuation`""").fetchone()[0]
            print(last_id)
            result = self.cursor.execute("""SELECT * FROM `hidden_continuation` WHERE `callback` = ?""", (last_id,)).fetchone()
            return result

    def check_button(self, callback):
        with self.connection:
            result = self.cursor.execute("""SELECT * FROM `hidden_continuation` WHERE `callback` = ?""", (callback,)).fetchall()
            return bool(len(result))