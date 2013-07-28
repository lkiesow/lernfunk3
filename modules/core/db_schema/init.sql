select '### Cleanup';

SET foreign_key_checks = 0;
delete from lf_media_series;
DELETE from lf_series;
delete from lf_file;
delete from lf_media;
delete from lf_latest_media;
delete from lf_latest_published_media;
DELETE from lf_user;
DELETE from lf_group;
DELETE from lf_user_group;
delete from lf_server;
delete from lf_media_subject;
delete from lf_series_subject;
delete from lf_subject;
delete from lf_organization;
SET foreign_key_checks = 1;

select '### Create user admin and public';

set @passwd_a = 'secret';
set @salt_a   = '234';

insert into lf_user set
	name   = 'admin',
	salt   = @salt_a,
	passwd = unhex(sha2( concat(@passwd_a,@salt_a), 512 ));

insert into lf_user set
	name   = 'public';


select '### Create groups admin, editor and public';

insert into lf_group set
	name   = 'admin';

insert into lf_group set
	name   = 'editor';

insert into lf_group set
	name   = 'public';


select '### Add user to group';

insert into lf_user_group set
	user_id  = (select id from lf_user  where name = 'admin'),
	group_id = (select id from lf_group where name = 'admin');

insert into lf_user_group set
	user_id  = (select id from lf_user  where name = 'public'),
	group_id = (select id from lf_group where name = 'public');
