import os
from dotenv import load_dotenv
from pathlib import Path

import sqlalchemy
import psycopg2
import pandas as pd

from schema import schema

#путь к файлу с данными для входа
dotenv_path = Path(rf'.\.env')
load_dotenv(dotenv_path=dotenv_path)


engine = sqlalchemy.create_engine(os.getenv('engine', 'default') % os.getenv('dp_port', 'default'))
autocommit_engine = engine.execution_options(isolation_level="AUTOCOMMIT")


def server(flag):

    params = {
        'database': os.getenv('db_name', 'default'),
        'user': os.getenv('db_un', 'default'),
        'password': os.getenv('db_pw', 'default'),
        'host': os.getenv('host', 'default'),
        'port': os.getenv('dp_port', 'default')
    }

    connection = psycopg2.connect(**params)
    cursor = connection.cursor()

    connection.autocommit = True

    if flag:
        return connection
    else:
        return cursor
    

def dbCreate():
    cur = server(False)
    conn = server(True)

    cur.execute(schema)
    conn.commit()  


def insertUser(user: dict):

    pd.DataFrame(user).to_sql(name='users', schema='logistic', con=engine, if_exists='append', index=False,
                                dtype={'id': sqlalchemy.BigInteger(),
                                       'name': sqlalchemy.Text(),
                                       'surname': sqlalchemy.Text(),
                                       'second_name': sqlalchemy.Text(),
                                       'role': sqlalchemy.Text(),
                                       })
    