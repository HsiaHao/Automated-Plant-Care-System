import sqlite3 as lite
import sys
from time import sleep

DB_NAME = 'sensorData.db'
TABLE_NAME = 'PlantTable'

conn = lite.connect('sensorData.db')
curs = conn.cursor()


# class TableService:
#     def __init__(self, db, table):
#         self.db = db
#         self.table = table

def create_table2(name):
    curs.execute("DROP TABLE IF EXISTS {}".format(name))
    curs.execute(
        "CREATE TABLE {}(id NUMERIC, timestamp DATETIME, height NUMERIC, greenness NUMERIC)".format(name))


def create_table(name):
    curs.execute("DROP TABLE IF EXISTS {}".format(name))

    curs.execute(
        "CREATE TABLE {}(id NUMERIC, timestamp DATETIME, temp NUMERIC, hum NUMERIC, light NUMERIC)".format(name))


# data is (temp, hum, light) in this example
# table is table name
def add_data(table, id, data):
    temp, hum, light = data
    curs.execute(
        "INSERT INTO {} values({}, datetime('now'), {}, {}, {})".format(table, id, temp, hum, light))
    conn.commit()


def print_data(table):
    print("Printing {}".format(table))
    for row in curs.execute("SELECT * FROM {}".format(table)):
        print(row)


# create_table2("CameraTable")
add_data(TABLE_NAME, 1, (12, 56, 3))
sleep(1)
add_data(TABLE_NAME, 2, (2, 1, 10))
sleep(1)
add_data(TABLE_NAME, 1, (6, 9, 10))
sleep(1)
add_data(TABLE_NAME, 1, (50, 1, 45))
sleep(1)

print_data("PlantTable")
print_data("CameraTable")

conn.close()
