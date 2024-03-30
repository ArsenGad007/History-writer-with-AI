import sqlite3
import threading


class DataBase:
    # конструктор
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self.lock = threading.Lock()

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_name)
            self.cursor = self.connection.cursor()
            print("Connected to database:", self.db_name)
        except sqlite3.Error as error:
            print("Error connecting to database:", error)

    def close(self):
        if self.connection:
            self.connection.close()
            print("Database connection closed.")

    def create_table(self, table_name: str):
        with self.lock:
            self.connect()

            try:
                sql_request = (f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    genre TEXT,
                    character TEXT,
                    location TEXT,
                    info TEXT,
                    task TEXT,
                    answers TEXT,
                    gpt_response TEXT,
                    tokens INTEGER,
                    session INT,
                    user_content TEXT,
                    debug_mode INTEGER,               
                    handler_enabled INTEGER
                ); 
                ''')
                self.cursor.execute(sql_request)
            except sqlite3.Error as error:
                print("Error creating table:", error)

            self.close()

    def insert_data(self, user_id: int, table_name: str):
        with self.lock:
            self.connect()

            try:
                sql_request = f"INSERT INTO {table_name} (user_id) VALUES (?);"
                self.cursor.execute(sql_request, (user_id,))
                self.connection.commit()
            except sqlite3.Error as error:
                print("Error inserting data:", error)

            self.close()

    def update_data(self, user_id: int, column: str, value: (str, int, float), table_name: str):
        with self.lock:
            self.connect()

            try:
                sql_request = f"UPDATE {table_name} SET {column} = ? WHERE user_id = ?;"
                self.cursor.execute(sql_request, (value, user_id,))  # применяем запрос и подставляем значения
                self.connection.commit()  # сохраняем изменения в базе данных
            except sqlite3.Error as error:
                print("Error updating data:", error)

            self.close()

    def select_data(self, user_id: int, column: str, table_name: str) -> (str, int):
        with self.lock:
            self.connect()

            try:
                results = self.cursor.execute(f"SELECT * FROM {table_name} WHERE user_id = ?;", (user_id,))
                self.cursor.row_factory = sqlite3.Row
                for result in results:
                    return result[column]
            except sqlite3.Error as error:
                print("Error selecting data:", error)

            self.close()

    def delete_data(self, user_id: int, table_name: str):
        with self.lock:
            self.connect()

            try:
                sql_query = f"DELETE FROM {table_name} WHERE user_id = ?;"
                self.cursor.execute(sql_query, (user_id,))  # применяем запрос и подставляем значения
                self.connection.commit()  # сохраняем изменения в базе данных
            except sqlite3.Error as error:
                print("Error deleting data:", error)

            self.close()
