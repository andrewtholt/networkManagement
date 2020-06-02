update node set name = 'NanoPi-NEO.lan' where ip_address='192.168.10.221';

update node set checkport = 2812 where name like 'Nano%.lan';
update node set checkport = 2812 where name = 'punch.lan';
update node set checkport = 2812 where name = 'StarLite.lan';
update node set checkport = 2812 where name = 'labpi.lan';
update node set checkport = 2812 where name = 'rpi3.lan';
update node set checkport = 2812 where name = 'raspberrypi0.lan';

update node set notify='NO' where name like 'Galaxy%.lan';
update node set notify='NO' where name like 'Annes-iPhone.lan';
update node set notify='NO' where name like 'Andrews-MBP.lan';
update node set notify='NO' where name like 'iPad.lan';
