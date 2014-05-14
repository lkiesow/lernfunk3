select '### Cleanup';

SET foreign_key_checks = 0;
delete from lf_media_series;
DELETE from lf_series;
delete from lf_file;
delete from lf_media;
DELETE from lf_user_group;
DELETE from lf_user;
DELETE from lf_group;
delete from lf_media_subject;
delete from lf_series_subject;
delete from lf_subject;
delete from lf_organization;
SET foreign_key_checks = 1;

select '### Create user';

set @passwd_a = 'secret';
set @salt_a   = '234';

insert into lf_user set
	id     = 1,
	name   = 'admin',
	salt   = @salt_a,
	passwd = unhex(sha2( concat(@passwd_a,@salt_a), 512 ));

insert into lf_user set
	id     = 2,
	name   = 'public';

set @passwd_b = 'test';
set @salt_b   = '345';

insert into lf_user set
	name     = 'lkiesow',
	salt     = @salt_b,
	passwd   = unhex(sha2( concat(@passwd_b,@salt_b), 512 )),
	realname = 'Lars Kiesow',
	email    = 'lkiesow@uos.de',
	access   = 1; /* 1 means public access*/

insert into lf_user set
	name   = 'test',
	salt   = '---',
	passwd = unhex(sha2( concat('test','---'), 512 ));

SET @user_id = ( select id from lf_user where name = 'lkiesow' limit 0, 1 );

select '### Create group';

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

insert into lf_user_group set
	user_id  = (select id from lf_user  where name = 'lkiesow'),
	group_id = (select id from lf_group where name = 'admin');


select '### Create media';

insert into lf_media set
	language    = 'de',
	source_key  = '123456789',
	title       = 'test',
	description = 'some text…',
	owner       = @user_id,
	editor      = @user_id,
	published   = true,
	rights      = 'cc-by',
	type        = 'Image',
	coverage    = 'World, Europe, Germany, Lower Saxony, Weser-Ems, Osnabrück',
	creator     = '["Lars Kiesow"]',
	publisher   = '["University of Osnabrück"]';

SET @media_id = ( select id from lf_media limit 0, 1 );
SET @media_version = ( select version from lf_media where id = @media_id limit 0,1 );

select bin2uuid(@media_id);

insert into lf_media set
	id          = @media_id,
	source_key  = '123456789',
	language    = 'de',
	title       = 'test',
	description = 'some text…',
	owner       = @user_id,
	editor      = @user_id,
	published   = false,
	rights      = 'cc-by',
	type        = 'Image',
	coverage    = 'World, Europe, Germany, Lower Saxony, Weser-Ems, Osnabrück',
	creator     = '["Lars Kiesow"]',
	publisher   = '["University of Osnabrück"]';

START TRANSACTION;

	update lf_media
		set published = false
		where id = @media_id and published = true;

	insert into lf_media set
		id          = @media_id,
		source_key  = '123456789',
		language    = 'de',
		title       = 'test',
		description = 'some text…',
		owner       = @user_id,
		editor      = @user_id,
		published   = true,
		rights      = 'cc-by',
		type        = 'Image',
		coverage    = 'World, Europe, Germany, Lower Saxony, Weser-Ems, Osnabrück',
		creator     = '["Lars Kiesow"]',
		publisher   = '["University of Osnabrück"]';

commit;

insert into lf_media set
	id          = @media_id,
	source_key  = '123456789',
	parent_version = 1,
	language    = 'en',
	title       = 'test',
	description = 'some english text…',
	owner       = @user_id,
	editor      = @user_id,
	published   = true,
	rights      = 'cc-by',
	type        = 'Image',
	coverage    = 'World, Europe, Germany, Lower Saxony, Weser-Ems, Osnabrück',
	creator     = '["Lars Kiesow"]',
	publisher   = '["University of Osnabrück"]';

insert into lf_media set
	id          = @media_id,
	source_key  = '123456789',
	parent_version = 1,
	language    = 'en-US',
	title       = 'test',
	description = 'some english text (US version)…',
	owner       = @user_id,
	editor      = @user_id,
	published   = true,
	rights      = 'cc-by',
	type        = 'Image',
	coverage    = 'World, Europe, Germany, Lower Saxony, Weser-Ems, Osnabrück',
	creator     = '["Lars Kiesow"]',
	publisher   = '["University of Osnabrück"]';

insert into lf_media set
	language    = 'de',
	source_key  = '123456789',
	title       = 'test2',
	description = 'a second text…',
	owner       = @user_id,
	editor      = @user_id,
	published   = true,
	rights      = 'cc-by-sa',
	type        = 'Image',
	coverage    = 'World, Europe, Germany, Lower Saxony, Weser-Ems, Osnabrück',
	creator     = '["John Doe"]';

set @media_id_b = (select id from lf_media where title = 'test2' limit 0, 1);

insert into lf_media set
	id          = @media_id_b,
	source_key  = '123456789',
	language    = 'de',
	title       = 'test2',
	description = 'a second text…',
	owner       = @user_id,
	editor      = @user_id,
	published   = false,
	rights      = 'cc-by',
	type        = 'Image',
	coverage    = 'World, Europe, Germany, Lower Saxony, Weser-Ems, Osnabrück';

/* Invisible mediaobject */
insert into lf_media set
	language    = 'de',
	source_key  = '123456789',
	title       = 'Invisibilitytest',
	description = 'This media object cannot be seen.',
	owner       = @user_id,
	editor      = @user_id,
	published   = true,
	visible     = false,
	rights      = 'cc-by-sa',
	type        = 'Image',
	coverage    = 'World, Europe, Germany, Lower Saxony, Weser-Ems, Osnabrück';

select '### Create series';

insert into lf_series set
	title       = 'testseries',
	language    = 'de',
	description = 'some text…',
	owner       = @user_id,
	editor      = @user_id,
	published   = true,
	creator     = '["Lars Kiesow"]';

SET @series_id_a = ( select id from lf_series limit 0, 1 );
SET @series_version_a = ( select version from lf_series limit 0, 1 );

insert into lf_series set
	title       = 'testseries2',
	language    = 'en',
	description = 'some more text…',
	owner       = @user_id,
	editor      = @user_id,
	published   = true;

SET @series_id_b = ( select id from lf_series limit 1, 1 );
SET @series_version_b = ( select version from lf_series limit 1, 1 );

insert into lf_series set
	title       = 'testseries2',
	language    = 'en',
	description = 'text…',
	owner       = @user_id,
	editor      = @user_id,
	published   = true,
	id          = @series_id_b;

SET @series_version_bb = ( select max(version) from lf_series where title = 'testseries2' );

insert into lf_series set
	title       = 'InvisibleSeries',
	language    = 'de',
	description = 'Should not be seen…',
	owner       = @user_id,
	editor      = @user_id,
	published   = true,
	visible     = false;



select '### Connect media and series';

insert into lf_media_series set
	series_id      = @series_id_a,
	media_id       = @media_id,
	series_version = @series_version_a;

insert into lf_media_series set
	series_id      = @series_id_b,
	media_id       = @media_id,
	series_version = @series_version_b;

insert into lf_media_series set
	series_id      = @series_id_b,
	media_id       = @media_id,
	series_version = @series_version_bb;

select '### Create file';

insert into lf_file set
	media_id   = @media_id,
	format     = 'application/matterhorn13',
	uri        = 'http://example.com/',
	source_key = UUID();

select '### Create some subjects';

insert into lf_subject set
	language = 'en',
	name     = 'Computer Science';

set @subject_id_a = (select id from lf_subject where language = 'en' limit 0, 1);

insert into lf_subject set
	language = 'de',
	name     = 'Informatik';

set @subject_id_b = (select id from lf_subject where language = 'de' limit 0, 1);

select '### Connect subjects, media and series';

insert into lf_series_subject set
	subject_id = @subject_id_a,
	series_id  = @series_id_a;

insert into lf_series_subject set
	subject_id = @subject_id_b,
	series_id  = @series_id_a;

insert into lf_series_subject set
	subject_id = @subject_id_a,
	series_id  = @series_id_b;

insert into lf_series_subject set
	subject_id = @subject_id_b,
	series_id  = @series_id_b;

insert into lf_media_subject set
	subject_id = @subject_id_a,
	media_id  = @media_id;

insert into lf_media_subject set
	subject_id = @subject_id_b,
	media_id   = @media_id;

select '### Add organization';

insert into lf_organization set
	name = 'Universität Osnabrück';

select '### Add some access rights';

insert into lf_access set
	media_id = @media_id,
	user_id  = @user_id,
	read_access = 1;

select '### Connect user and organization';

insert into lf_user_organization set
	user_id         = @user_id,
	organization_id = (select id from lf_organization limit 0,1);
