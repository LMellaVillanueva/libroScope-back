import os
import pymysql.cursors
from dotenv import load_dotenv

load_dotenv()  # carga las variables de .env

class MySQLConnection:
    def __init__(self, db=None):
        connection = pymysql.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            db=os.getenv("MYSQL_DATABASE", db or "railway"),
            port=int(os.getenv("MYSQL_PORT", 3306)), 
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        self.connection = connection

    def query_db(self, query, data=None):
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, data)
                if query.lower().startswith("insert"):
                    self.connection.commit()
                    return cursor.lastrowid
                elif query.lower().startswith("select"):
                    return cursor.fetchall()
                else:
                    self.connection.commit()
            except Exception as e:
                print("Error en la consulta:", e)
                return False

def connectToMySQL(db=None):
    return MySQLConnection(db)
