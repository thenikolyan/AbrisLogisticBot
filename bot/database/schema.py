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

create table if not exists logistic.drivers_with_routes(
    id_driver bigint not null,
    id_route bigint not null
);
'''