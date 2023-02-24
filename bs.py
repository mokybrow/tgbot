import psycopg2
from psycopg2 import OperationalError


connection = psycopg2.connect(
            database="users",
            user="postgres",
            password="admin",
            host="127.0.0.1",
            port="5432",
        )


query = '''CREATE TABLE IF NOT EXISTS users 
     (id BIGINT PRIMARY KEY NOT NULL,
     NAME TEXT NOT NULL,
     sgroup TEXT,
     podgroup INT);'''

cursor = connection.cursor()
cursor.execute(query)
connection.commit()


def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except OperationalError as e:
        print(f"The error '{e}' occurred")

cursor = connection.cursor()
select_users = "SELECT * FROM users"
cursor.execute(select_users)
result = cursor.fetchall()

for user in result:
    print(user)
def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except OperationalError as e:
        print(f"The error '{e}' occurred")

