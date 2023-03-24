import sqlite3


class User_database:
    def __init__(self, database_file):
        self.connection = sqlite3.connect(database_file)
        self.cursor = self.connection.cursor()

    def add_user(self, id_, user_id, datetime, status):
        with self.connection:
            self.cursor.execute("""INSERT INTO `users` (`id`, `user_id`, `datetime`, `status`) VALUES (?, ?, ?, ?)""", (id_, user_id, datetime, status))

    def check_user_status(self, user_id):
        with self.connection:
            result = self.cursor.execute("""SELECT `status` FROM `users` WHERE `user_id` = ?""", (user_id,)).fetchone()
            return result

    def upd_user_status(self, user_id, status):
        with self.connection:
            return self.cursor.execute("""UPDATE `users` SET `status` = ? WHERE `user_id` = ?""", (status, user_id,))

    def close(self):
        self.connection.close()