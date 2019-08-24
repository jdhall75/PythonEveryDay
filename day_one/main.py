import sqlite3
from sqlite3 import Error


def sql_connection():
    try:
        con = sqlite3.connect('db/tut.db')
        return con
    except Error:
        print(Error)


def sql_table_init(con):
    # define some SQL for the table
    try:
        employeeTable = "CREATE TABLE IF NOT EXISTS employees(id integer PRIMARY KEY, name text, salary real, department text, position text, hireDate text)"
        cursorObj = con.cursor()
        cursorObj.execute(employeeTable)
        con.commit()
        return True
    except Error:
        print(Error)
        return False


def sql_insert(con, entities):
    cursorObj = con.cursor()
    sql = "INSERT INTO employees(id, name, salary, department, position, hireDate) values (?,?,?,?,?,?)"
    cursorObj.execute(sql, entities)
    con.commit()


if __name__ == '__main__':
    con = sql_connection()
    if sql_table_init(con):
        # insert that data here
        entities = (2, 'Andrew', 800, 'IT', 'Tech', '2018-02-06')
        sql_insert(con, entities)
