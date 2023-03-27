import os
from dotenv import load_dotenv
from pathlib import Path

import sqlalchemy
import psycopg2
import pandas as pd

description = '''
create schema if not exists logistic;

create table if not exists logistic.users(
    id bigint primary key,
    name text not null,
    surname text not null,
    second_name text not null,
    role text not null 
) 
'''

#путь к файлу с данными для входа
dotenv_path = Path(rf'.\.env')
load_dotenv(dotenv_path=dotenv_path)


engine = sqlalchemy.create_engine(os.getenv('engine', 'default') % os.getenv('dp_port', 'default'))
autocommit_engine = engine.execution_options(isolation_level="AUTOCOMMIT")


def server(flag: bool):

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
    global cur, conn
    cur = server(False)
    conn = server(True)

    cur.execute(description)
    conn.commit()  


async def insertUser(user: dict, engine):

    pd.DataFrame([user]).to_sql(name='users', schema='logistic', con=engine, if_exists='append', index=False,
                                dtype={'id': sqlalchemy.BigInteger(),
                                       'name': sqlalchemy.Text(),
                                       'surname': sqlalchemy.Text(),
                                       'patronymic': sqlalchemy.Text(),
                                       'role': sqlalchemy.Text(),
                                       })

async def updateUserRole(user: dict):
    query = f''' update logistic.users set "role"='{user['role']}' where "id"={int(user['id'])}'''
    cur.execute(query)
    conn.commit()

async def getIdRoleUser(uid):
    return (pd.read_sql(f'''select id, role from logistic.users where "id" = {uid}''', conn))


async def getUnauthorizedUsers():
    return (pd.read_sql(f'''select * from logistic.users where "role" = 'unauthtorized' ''', conn))
async def getDrivers():
    return (pd.read_sql(f'''select * from logistic.users where "role" = 'driver' ''', conn))
async def updateUnauthorizedUsers(id, role):
    return (pd.read_sql(f'''update logistic.users set role='{role}' where "id"={id}''', conn))

async def insertRoute(user: dict, engine):
    pd.DataFrame([user]).to_sql(name='routes', schema='logistic', con=engine, if_exists='append', index=False,
                                dtype={'route' : sqlalchemy.Text()})
