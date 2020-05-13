
drop table if exists node;

create table node (
    time_stamp varchar(32),
    state varchar(8),
    ip_address varchar(32) NOT NULL UNIQUE,
    unknown varchar(32),
    name varchar(32),
    mac_address varchar(32),
    maker varchar(32),
    notify varchar(4) default "YES" NOT NULL
);


