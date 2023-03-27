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
    id serial primary key,
    route text not null
); 

create table if not exists logistic.drivers_with_routes(
    id serial primary key,
    route text not null
);
'''