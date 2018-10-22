-- create role dbuser with login password 'strongpassword';

-- create database dbname ;

START TRANSACTION ;

create schema if not exists botname ;

create table botname.users (
    user_num      bigserial not null primary key,
    telegram_id   bigint,
    name          text,
    reg_key       int not null default 1,
    user_position int default 0,
    user_name     text,
    company       text,
    coin          bigint,
    sum           int default 0,
    manager       int,
    quantity      int default 0,
    my_manager    int
) ;

create table botname.store (
    item    text,
    price   int,
    manager int
) ;

create table botname.operations (
    who     text,
    to_whom text,
    date    text,
    command text,
    sum     int,
    reason  text,
    num     int default 1,
    company text
) ;

create table botname.managers (
    user_name text,
    num       int default 0
) ;

create table botname.companies (
    num     bigserial not null primary key,
    name    text,
    manager text,
    coin  text
) ;

create table botname.chats (
    telegram_id bigint,
    user_name   text,
    chat_id     bigint,
    company     text,
    num         bigserial not null primary key
) ;
grant all on schema botname to dbuser ;

grant all on all sequences in schema botname to dbuser ;

grant select, insert, update, delete on all tables in schema botname to dbuser ;

COMMIT TRANSACTION ;