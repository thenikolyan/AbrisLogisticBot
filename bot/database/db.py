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
    patronymic text not null,
    role text not null 
);


create table if not exists logistic.routes(
    id SERIAL primary key,
    route text not null
); 


create table if not exists logistic.catalog_routes(
    driver bigint not null,
    route bigint not null REFERENCES logistic.routes(id),
    PRIMARY KEY(driver, route)
);


create table if not exists logistic.list_rides(
    id bigint not null,
    id_user bigint not null,
    id_route bigint not null, 
    position bigint not null,
    date_leaving date not null,
    time_leaving time not null,
    date_arriving date not null,
    time_arriving time not null,
    address_leaving text not null,
    address_arriving text not null,
    latitude_leaving numeric not null,
    longitude_leaving numeric not null,
    latitude_arriving numeric not null,
    longitude_arriving numeric not null,
    destination numeric not null,
    act text not null,
    trn text not null, 
    consignment text not null
);

'''

# путь к файлу с данными для входа
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


# Insert data
async def insertUser(user: dict, engine):
    pd.DataFrame([user]).to_sql(name='users', schema='logistic', con=engine, if_exists='append', index=False,
                                dtype={'id': sqlalchemy.BigInteger(),
                                       'name': sqlalchemy.Text(),
                                       'surname': sqlalchemy.Text(),
                                       'patronymic': sqlalchemy.Text(),
                                       'role': sqlalchemy.Text(),
                                       })


async def insertRoute(user: dict):
    pd.DataFrame([user]).to_sql(name='routes', schema='logistic', con=engine, if_exists='append', index=False,
                                dtype={'id': sqlalchemy.Integer(), 'route': sqlalchemy.Text()})


async def insertRouteCatalog(user: dict):
    pd.DataFrame([user]).to_sql(name='catalog_routes', schema='logistic', con=engine, if_exists='append', index=False,
                                dtype={'driver': sqlalchemy.Integer(), 'route': sqlalchemy.Integer()})


async def insertOneRide(ride: dict):
    df = pd.DataFrame([ride])
    df = df.drop(columns=['name', 'surname', 'patronymic'])
    df.to_sql(name='list_rides', schema='logistic', con=engine, if_exists='append', index=False,
              dtype={
                    'id': sqlalchemy.Integer(),
                    'id_user': sqlalchemy.Integer(),
                    'id_route': sqlalchemy.Integer(),
                    'position': sqlalchemy.Integer(),
                    'date_leaving': sqlalchemy.Date(),
                    'time_leaving': sqlalchemy.Time(),
                    'date_arriving': sqlalchemy.Date(),
                    'time_arriving': sqlalchemy.Time(),
                    'address_leaving': sqlalchemy.Text(),
                    'address_arriving': sqlalchemy.Text(),
                    'latitude_leaving': sqlalchemy.Numeric(),
                    'longitude_leaving': sqlalchemy.Numeric(),
                    'latitude_arriving': sqlalchemy.Numeric(),
                    'longitude_arriving': sqlalchemy.Numeric(),
                    'destination': sqlalchemy.Numeric(),
                    'akt': sqlalchemy.Text(),
                    'trn': sqlalchemy.Text(),
                    'consignment': sqlalchemy.Text(),
                    }
                )


# Update data
async def updateUserRole(user: dict):
    query = f''' update logistic.users set "role"='{user['role']}' where "id"={int(user['id'])}'''
    cur.execute(query)
    conn.commit()


# Get data
async def getIdRoleUser(uid):
    return (pd.read_sql(f'''select id, role from logistic.users where "id" = {uid}''', conn))


async def getAdmins():
    return (pd.read_sql(f'''select id from logistic.users where "role" = 'admin' ''', conn))


async def getUnauthorizedUsers():
    return (pd.read_sql(f'''select * from logistic.users where "role" = 'unauthtorized' ''', conn))


async def getDrivers():
    return (pd.read_sql(f'''select * from logistic.users where "role" = 'driver' ''', conn))


async def getRoutes():
    return (pd.read_sql(f''' select * from logistic.routes ''', conn))


async def getCatalogRoute():
    return (pd.read_sql(''' select use.surname, use.name, use.patronymic, step.route from (select cat.driver, rou.route from ((select * from logistic.catalog_routes) as cat inner join logistic.routes as rou on (cat.route=rou.id))) as step inner join logistic.users as use on (step.driver=use.id) ''', conn))


async def getAttachedRoute(id):
    return (pd.read_sql(f'''select step1.driver, rou.id, rou.route from (select * from logistic.catalog_routes where "driver"={int(id)})as step1 left join logistic.routes as rou on (step1.route=rou.id) ''', conn))


async def getMaxIdRoutes():
    tmp = pd.read_sql(''' select max(id) as id from logistic.list_rides ''', conn).to_dict('records')[0]['id']
    if tmp is not None:
        return tmp + 1
    else:
        return 1


async def getOneRecordRoute(df: dict):
    query = f''' select * from (select id as id_user, surname, name, patronymic from logistic.users where "id"={df['user']}) as initials 
    right join (select * from logistic.list_rides where "date_leaving" = '{df['date']}' and "id_route" = '{df['route']}' and "id"={df['id']}) as listRoutes 
    on (initials.id_user=listRoutes.id_user) '''

    return (pd.read_sql(query, conn))



async def getAllRoute():
    query = f''' select * from (select id as id_user, surname, name, patronymic from logistic.users) as initials 
                    right join (select * from logistic.list_rides) as listRoutes 
                    on (initials.id_user=listRoutes.id_user) '''
    
    return (pd.read_sql(query, conn))


# Delete data
async def deleteCatalogRoute(df: dict):
    query = f''' delete from logistic.catalog_routes where "driver"={df['driver']} and "route"={df['route']} '''
    cur.execute(query)
    conn.commit()


async def deleteRoute(route: dict):
    query = f''' delete from logistic.routes where "id"={route['id']} '''
    cur.execute(query)
    conn.commit()
