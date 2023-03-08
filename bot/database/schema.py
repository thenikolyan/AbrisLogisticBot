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