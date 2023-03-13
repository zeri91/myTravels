import sqlite3

connection = sqlite3.connect('./instance/user.db')


with open('user_schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

connection.commit()
connection.close()