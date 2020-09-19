CREATE TABLE node (
    time_stamp varchar(32),
    state varchar(8),
    ip_address varchar(32) NOT NULL UNIQUE,
    unknown varchar(32),
    name varchar(32),
    mac_address varchar(32),
    maker varchar(32),
    notify varchar(4) default "YES" NOT NULL,
    -- checkport: connect to this port to verify up, ignore if 0
    check_port integer default 0,
    -- If tru connect via monit to verify.
    check_monit integer default false,
    event_time integer
);

