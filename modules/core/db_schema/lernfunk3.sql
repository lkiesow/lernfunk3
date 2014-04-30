-- -----------------------------------------------------
-- Table `lf_subject`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_subject` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `language` VARCHAR(255) NOT NULL COMMENT 'ietf language tag' ,
  `name` VARCHAR(255) NOT NULL ,
  PRIMARY KEY (`id`) )
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lf_server`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_server` (
  `id` VARCHAR(255) NOT NULL COMMENT 'A meaningful name for the server' ,
  `format` VARCHAR(32) NOT NULL ,
  `uri_pattern` VARCHAR(255) NOT NULL ,
  PRIMARY KEY (`id`, `format`) )
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lf_group`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_group` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(255) NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `name_UNIQUE` (`name` ASC) )
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lf_user`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_user` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(255) NOT NULL ,
  `salt` VARCHAR(32) NULL DEFAULT NULL ,
  `passwd` BINARY(64) NULL DEFAULT NULL COMMENT 'sha-2 (512) hash of salt+passwd' ,
  `vcard_uri` VARCHAR(255) NULL DEFAULT NULL ,
  `realname` VARCHAR(255) NULL DEFAULT NULL ,
  `email` VARCHAR(255) NULL DEFAULT NULL ,
  `access` TINYINT UNSIGNED NOT NULL DEFAULT 4 COMMENT 'Meaning of values:\n1 - public access\n2 - resistered users only\n3 - editors only\n4 - administrators only' ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `name_UNIQUE` (`name` ASC) )
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lf_media`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_media` (
  `id` BINARY(16) NOT NULL DEFAULT x'00' ,
  `version` INT UNSIGNED NOT NULL DEFAULT 0 ,
  `parent_version` INT UNSIGNED NULL DEFAULT NULL ,
  `language` VARCHAR(255) NOT NULL COMMENT 'ietf language tag' ,
  `title` VARCHAR(255) NULL ,
  `description` TEXT NULL ,
  `owner` INT UNSIGNED NOT NULL ,
  `editor` INT UNSIGNED NOT NULL ,
  `timestamp_edit` TIMESTAMP NOT NULL ,
  `timestamp_created` TIMESTAMP NOT NULL DEFAULT '2000-01-01' ,
  `published` TINYINT(1) NOT NULL DEFAULT FALSE COMMENT 'Mars the currently published version of a media' ,
  `source` VARCHAR(255) NULL DEFAULT NULL COMMENT 'URI' ,
  `visible` TINYINT(1) NULL DEFAULT true ,
  `source_system` VARCHAR(255) NULL DEFAULT NULL ,
  `source_key` VARCHAR(255) NULL DEFAULT NULL ,
  `rights` VARCHAR(255) NULL DEFAULT NULL ,
  `type` SET('Collection', 'Dataset', 'Event', 'Image', 'Interactive Resource', 'Service', 'Software', 'Sound', 'Text') NOT NULL COMMENT 'http://dublincore.org/documents/2000/07/11/dcmi-type-vocabulary/' ,
  `coverage` VARCHAR(255) NULL DEFAULT NULL COMMENT 'Getty Thesaurus of Geographic Names:\nhttp://www.getty.edu/research/tools/vocabularies/tgn/index.html' ,
  `relation` VARCHAR(255) NULL DEFAULT NULL ,
  `creator` VARCHAR(2048) NULL ,
  `contributor` VARCHAR(2048) NULL DEFAULT NULL ,
  `publisher` VARCHAR(2048) NULL DEFAULT NULL ,
  PRIMARY KEY (`id`, `version`) ,
  INDEX `fk_lf_media_version_idx` (`id` ASC, `parent_version` ASC) ,
  INDEX `fk_lf_media_owner_idx` (`owner` ASC) ,
  INDEX `fk_lf_media_editor_idx` (`editor` ASC) ,
  INDEX `lf_media_id_idx` (`id` ASC) ,
  INDEX `lf_medis_version_idx` (`version` ASC) ,
  CONSTRAINT `fk_lf_media_version`
    FOREIGN KEY (`id` , `parent_version` )
    REFERENCES `lf_media` (`id` , `version` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_media_owner`
    FOREIGN KEY (`owner` )
    REFERENCES `lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_media_editor`
    FOREIGN KEY (`editor` )
    REFERENCES `lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lf_file`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_file` (
  `id` BINARY(16) NOT NULL DEFAULT x'00' ,
  `media_id` BINARY(16) NOT NULL COMMENT '					' ,
  `format` VARCHAR(32) NOT NULL COMMENT 'Mimetype of linked file' ,
  `type` VARCHAR(32) NULL DEFAULT NULL COMMENT 'Minimal description of what the linked file is about (screen, lecturer, music, speech, …). Extends format if needed.' ,
  `quality` VARCHAR(32) NULL DEFAULT NULL ,
  `server_id` VARCHAR(255) NULL DEFAULT NULL ,
  `uri` VARCHAR(255) NULL DEFAULT NULL ,
  `source` VARCHAR(255) NULL DEFAULT NULL ,
  `source_system` VARCHAR(255) NULL DEFAULT NULL ,
  `source_key` VARCHAR(255) NULL DEFAULT NULL ,
  `flavor` VARCHAR(45) NULL DEFAULT NULL ,
  `tags` VARCHAR(255) NULL DEFAULT NULL COMMENT 'JSON encoded list of tags (i.e. [\"a\",\"b\",\"c\"])' ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_lf_file_media_idx` (`media_id` ASC) ,
  INDEX `fk_lf_file_server_idx` (`server_id` ASC) ,
  CONSTRAINT `fk_lf_file_media`
    FOREIGN KEY (`media_id` )
    REFERENCES `lf_media` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_file_server`
    FOREIGN KEY (`server_id` )
    REFERENCES `lf_server` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lf_series`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_series` (
  `id` BINARY(16) NOT NULL DEFAULT x'00' ,
  `version` INT UNSIGNED NOT NULL DEFAULT 0 ,
  `parent_version` INT UNSIGNED NULL DEFAULT NULL ,
  `title` VARCHAR(255) NULL ,
  `language` VARCHAR(255) NOT NULL COMMENT 'ietf language tag\nSpec: http://tools.ietf.org/rfc/bcp/bcp47.txt\nLanguage Subtag Lookup: http://rishida.net/utils/subtags/' ,
  `description` TEXT NULL ,
  `source` VARCHAR(255) NULL DEFAULT NULL ,
  `timestamp_edit` TIMESTAMP NOT NULL ,
  `timestamp_created` TIMESTAMP NOT NULL DEFAULT '2000-01-01' ,
  `published` TINYINT(1) NOT NULL DEFAULT FALSE ,
  `owner` INT UNSIGNED NOT NULL ,
  `editor` INT UNSIGNED NOT NULL ,
  `visible` TINYINT(1) NULL DEFAULT true ,
  `source_key` VARCHAR(255) NULL DEFAULT NULL ,
  `source_system` VARCHAR(255) NULL DEFAULT NULL ,
  `creator` VARCHAR(2048) NULL DEFAULT NULL ,
  `contributor` VARCHAR(2048) NULL DEFAULT NULL ,
  `publisher` VARCHAR(2048) NULL DEFAULT NULL ,
  PRIMARY KEY (`id`, `version`) ,
  INDEX `fk_lf_series_version_idx` (`id` ASC, `parent_version` ASC) ,
  INDEX `fk_lf_series_owner_idx` (`owner` ASC) ,
  INDEX `fk_lf_series_editor_idx` (`editor` ASC) ,
  INDEX `lf_series_id_idx` (`id` ASC) ,
  INDEX `lf_series_version_idx` (`version` ASC) ,
  CONSTRAINT `fk_lf_series_version`
    FOREIGN KEY (`id` , `parent_version` )
    REFERENCES `lf_series` (`id` , `version` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_series_owner`
    FOREIGN KEY (`owner` )
    REFERENCES `lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_series_editor`
    FOREIGN KEY (`editor` )
    REFERENCES `lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lf_user_group`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_user_group` (
  `user_id` INT UNSIGNED NOT NULL ,
  `group_id` INT UNSIGNED NOT NULL ,
  PRIMARY KEY (`user_id`, `group_id`) ,
  INDEX `fk_lf_user_group_user_idx` (`user_id` ASC) ,
  INDEX `fk_lf_user_group_group_idx` (`group_id` ASC) ,
  CONSTRAINT `fk_lf_user_group_user`
    FOREIGN KEY (`user_id` )
    REFERENCES `lf_user` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_user_group_group`
    FOREIGN KEY (`group_id` )
    REFERENCES `lf_group` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lf_media_subject`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_media_subject` (
  `subject_id` INT UNSIGNED NOT NULL ,
  `media_id` BINARY(16) NOT NULL ,
  PRIMARY KEY (`subject_id`, `media_id`) ,
  INDEX `fk_lf_media_tag_media_idx` (`media_id` ASC) ,
  INDEX `fk_lf_media_tag_tag_idx` (`subject_id` ASC) ,
  CONSTRAINT `fk_lf_media_subject_media`
    FOREIGN KEY (`media_id` )
    REFERENCES `lf_media` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_media_subject_subject`
    FOREIGN KEY (`subject_id` )
    REFERENCES `lf_subject` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lf_series_subject`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_series_subject` (
  `subject_id` INT UNSIGNED NOT NULL ,
  `series_id` BINARY(16) NOT NULL ,
  PRIMARY KEY (`subject_id`, `series_id`) ,
  INDEX `fk_lf_series_subject_series_idx` (`series_id` ASC) ,
  INDEX `fk_lf_series_subject_subject_idx` (`subject_id` ASC) ,
  CONSTRAINT `fk_lf_series_subject_series`
    FOREIGN KEY (`series_id` )
    REFERENCES `lf_series` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_series_subject_subject`
    FOREIGN KEY (`subject_id` )
    REFERENCES `lf_subject` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lf_media_series`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_media_series` (
  `series_id` BINARY(16) NOT NULL ,
  `media_id` BINARY(16) NOT NULL ,
  `series_version` INT UNSIGNED NOT NULL DEFAULT 0 ,
  PRIMARY KEY (`series_id`, `media_id`, `series_version`) ,
  INDEX `fk_lf_media_series_series_idx` (`series_id` ASC, `series_version` ASC) ,
  INDEX `fk_lf_media_series_media_idx` (`media_id` ASC) ,
  CONSTRAINT `fk_lf_media_series_series`
    FOREIGN KEY (`series_id` , `series_version` )
    REFERENCES `lf_series` (`id` , `version` )
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_media_series_media`
    FOREIGN KEY (`media_id` )
    REFERENCES `lf_media` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lf_prepared_file`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_prepared_file` (
  `id` BINARY(16) NOT NULL ,
  `media_id` BINARY(16) NOT NULL COMMENT '					' ,
  `format` VARCHAR(32) NOT NULL ,
  `type` VARCHAR(32) NULL DEFAULT NULL ,
  `quality` VARCHAR(32) NULL DEFAULT NULL ,
  `uri` VARCHAR(255) NULL DEFAULT NULL ,
  `source` VARCHAR(255) NULL DEFAULT NULL ,
  `source_key` VARCHAR(255) NULL DEFAULT NULL ,
  `source_system` VARCHAR(255) NULL DEFAULT NULL ,
  `flavor` VARCHAR(32) NULL DEFAULT NULL ,
  `tags` VARCHAR(255) NULL DEFAULT NULL COMMENT 'JSON encoded list of tags (i.e. [\"a\",\"b\",\"c\"])' ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_lf_prepared_file_media_idx` (`media_id` ASC) ,
  CONSTRAINT `fk_lf_prepared_file_media`
    FOREIGN KEY (`media_id` )
    REFERENCES `lf_media` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
COMMENT = 'IMPORTANT: This table is used as a temporary storage for the /* comment truncated */ /* complicated merge of lf_file and lf_server. All insertes and updates on this table will be prohibited by triggers and result in errors.*/';


-- -----------------------------------------------------
-- Table `lf_organization`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_organization` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(255) NOT NULL ,
  `vcard_uri` VARCHAR(255) NULL DEFAULT NULL ,
  `parent_organization` INT UNSIGNED NULL DEFAULT NULL ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_lf_organization_parent_idx` (`parent_organization` ASC) ,
  CONSTRAINT `fk_lf_organization_parent`
    FOREIGN KEY (`parent_organization` )
    REFERENCES `lf_organization` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lf_user_organization`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_user_organization` (
  `organization_id` INT UNSIGNED NOT NULL ,
  `user_id` INT UNSIGNED NOT NULL ,
  PRIMARY KEY (`organization_id`, `user_id`) ,
  INDEX `fk_lf_user_organization_user_idx` (`user_id` ASC) ,
  INDEX `fk_lf_user_organization_organization_idx` (`organization_id` ASC) ,
  CONSTRAINT `fk_lf_user_organization_user`
    FOREIGN KEY (`user_id` )
    REFERENCES `lf_user` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_lf_user_organization_organization`
    FOREIGN KEY (`organization_id` )
    REFERENCES `lf_organization` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lf_access`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `lf_access` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `media_id` BINARY(16) NULL DEFAULT NULL ,
  `series_id` BINARY(16) NULL DEFAULT NULL ,
  `group_id` INT UNSIGNED NULL DEFAULT NULL ,
  `user_id` INT UNSIGNED NULL DEFAULT NULL ,
  `read_access` TINYINT(1) NULL DEFAULT False ,
  `write_access` TINYINT(1) NULL DEFAULT False ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_lf_access_media_idx` (`media_id` ASC) ,
  INDEX `fk_lf_access_series_idx` (`series_id` ASC) ,
  INDEX `fk_lf_access_user_idx` (`user_id` ASC) ,
  INDEX `fk_lf_access_group_idx` (`group_id` ASC) ,
  CONSTRAINT `fk_lf_access_media`
    FOREIGN KEY (`media_id` )
    REFERENCES `lf_media` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_lf_access_series`
    FOREIGN KEY (`series_id` )
    REFERENCES `lf_series` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_lf_access_user`
    FOREIGN KEY (`user_id` )
    REFERENCES `lf_user` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_lf_access_group`
    FOREIGN KEY (`group_id` )
    REFERENCES `lf_group` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- View `lf_latest_media`
-- -----------------------------------------------------
CREATE VIEW `lf_latest_media` AS
    select * from lf_media m where version = (
		select max(version) from lf_media where id = m.id);


-- -----------------------------------------------------
-- View `lf_latest_published_media`
-- -----------------------------------------------------
CREATE VIEW `lf_latest_published_media` AS
    select * from lf_media m where published and version = (
		select max(version) from lf_media where id = m.id);


-- -----------------------------------------------------
-- View `lf_latest_series`
-- -----------------------------------------------------
CREATE VIEW `lf_latest_series` AS
    select * from lf_series m where version = (
		select max(version) from lf_series where id = m.id);


-- -----------------------------------------------------
-- View `lf_latest_published_series`
-- -----------------------------------------------------
CREATE VIEW `lf_latest_published_series` AS
    select * from lf_series m where published and version = (
		select max(version) from lf_series where id = m.id);


-- -----------------------------------------------------
-- procedure prepare_file
-- -----------------------------------------------------

DELIMITER $$
CREATE PROCEDURE `prepare_file`
	(
		p_id            BINARY(16),
		p_media_id      BINARY(16),
		p_format        VARCHAR(32),
		p_type          VARCHAR(32),
		p_quality       VARCHAR(32),
		p_server_id     VARCHAR(255),
		p_uri           VARCHAR(255),
		p_source        VARCHAR(255),
		p_source_system VARCHAR(255),
		p_source_key    VARCHAR(255),
		p_flavor        VARCHAR(32),
		p_tags          VARCHAR(255)
	)
BEGIN
REPLACE INTO lf_prepared_file SET
	id            = p_id,
	media_id      = p_media_id,
	format        = p_format,
	type          = p_type,
	quality       = p_quality,
	source        = p_source,
	source_key    = p_source_key,
	source_system = p_source_system,
	flavor        = p_flavor,
	tags          = p_tags,
	uri           = ifnull( p_uri,
			if( isnull(p_server_id),
				NULL,
				replace( replace( replace( replace( replace( replace( (SELECT uri_pattern from lf_server
						where id = p_server_id and format = p_format ),
					'{file_id}', bin2uuid(p_id) ),
					'{format}', p_format ),
					'{media_id}', bin2uuid(p_media_id) ),
					'{source_key}', ifnull(p_source_key,'') ),
					'{media_source_key}', ifnull((select source_key from lf_latest_media where id = p_media_id limit 0, 1),'') ),
					'{type}', ifnull(p_type,'') )
			)
		);
END$$

DELIMITER ;

-- -----------------------------------------------------
-- function uuid2bin
-- -----------------------------------------------------

DELIMITER $$


CREATE FUNCTION `uuid2bin`( uuid VARCHAR(36) )
RETURNS BINARY(16)
BEGIN
	RETURN unhex(REPLACE(uuid,'-',''));
END$$

DELIMITER ;

-- -----------------------------------------------------
-- function binuuid
-- -----------------------------------------------------

DELIMITER $$


CREATE FUNCTION `binuuid`()
RETURNS BINARY(16)
BEGIN
	RETURN unhex(REPLACE(uuid(),'-',''));
END$$

DELIMITER ;

-- -----------------------------------------------------
-- function bin2uuid
-- -----------------------------------------------------

DELIMITER $$


CREATE FUNCTION `bin2uuid`( bin BINARY(16) )
RETURNS VARCHAR(36)
BEGIN
	SET @id = hex(bin);
	RETURN concat(
		substring(@id, 1, 8 ), '-',
		substring(@id, 9, 4 ), '-',
		substring(@id, 13, 4 ), '-',
		substring(@id, 17, 4 ), '-',
		substring(@id, 21 ) );
END$$

DELIMITER ;

-- -----------------------------------------------------
-- View `lf_published_media`
-- -----------------------------------------------------
CREATE OR REPLACE ALGORITHM = MERGE VIEW `lf_published_media` AS
    select m.* from lf_media m where m.published;

-- -----------------------------------------------------
-- View `lf_published_series`
-- -----------------------------------------------------
CREATE OR REPLACE ALGORITHM = MERGE VIEW `lf_published_series` AS
    select s.* from lf_series s where s.published;

-- -----------------------------------------------------
-- View `lfh_file`
-- -----------------------------------------------------
create  OR REPLACE view `lfh_file` as
	select bin2uuid(id) as id, bin2uuid(media_id) as media_id, format, type,
		quality, server_id, uri, source, source_key, source_system, flavor, tags from lf_file;

-- -----------------------------------------------------
-- View `lfh_prepared_file`
-- -----------------------------------------------------
CREATE  OR REPLACE VIEW `lfh_prepared_file` AS
	select bin2uuid(id), bin2uuid(media_id), format, uri, source, source_key, source_system, flavor, tags from lf_prepared_file;

-- -----------------------------------------------------
-- View `lfh_media`
-- -----------------------------------------------------
CREATE  OR REPLACE VIEW `lfh_media` AS
	select bin2uuid(id) as id, version, parent_version, language, title, description,
		owner, editor, timestamp_edit, timestamp_created, published, source,
		visible, source_system, source_key, rights, type, coverage, relation,
		creator, contributor, publisher
		from lf_media;

-- -----------------------------------------------------
-- View `lfh_latest_media`
-- -----------------------------------------------------
CREATE  OR REPLACE VIEW `lfh_latest_media` AS
	select bin2uuid(id), version, parent_version, language, title, description,
		owner, editor, timestamp_edit, timestamp_created, published, source,
		visible, source_system, source_key, rights, type, coverage, relation,
		creator, contributor, publisher
		from lf_latest_media;

-- -----------------------------------------------------
-- View `lfh_latest_published_media`
-- -----------------------------------------------------
CREATE  OR REPLACE VIEW `lfh_latest_published_media` AS
	select bin2uuid(id), version, parent_version, language, title, description,
		owner, editor, timestamp_edit, timestamp_created, published, source,
		visible, source_system, source_key, rights, type, coverage, relation,
		creator, contributor, publisher
		from lf_latest_published_media;

-- -----------------------------------------------------
-- View `lfh_series`
-- -----------------------------------------------------
CREATE  OR REPLACE VIEW `lfh_series` AS
	select bin2uuid(id) as id, version, parent_version, title, language,
		description, source, timestamp_edit, timestamp_created,
		published, owner, editor, visible, source_key, source_system,
		creator, contributor, publisher
		from lf_series;

-- -----------------------------------------------------
-- View `lfh_latest_series`
-- -----------------------------------------------------
CREATE  OR REPLACE VIEW `lfh_latest_series` AS
	select bin2uuid(id), version, parent_version, title, language,
		description, source, timestamp_edit, timestamp_created,
		published, owner, editor, visible, source_key, source_system
		from lf_latest_series;

-- -----------------------------------------------------
-- View `lfh_latest_published_series`
-- -----------------------------------------------------
CREATE  OR REPLACE VIEW `lfh_latest_published_series` AS
	select bin2uuid(id), version, parent_version, title, language,
		description, source, timestamp_edit, timestamp_created,
		published, owner, editor, visible, source_key, source_system,
		creator, contributor, publisher
		from lf_latest_published_series;

-- -----------------------------------------------------
-- View `lfh_access`
-- -----------------------------------------------------
CREATE  OR REPLACE VIEW `lfh_access` AS
	select id, bin2uuid(media_id) as media_id, bin2uuid(series_id) as series_id,
		group_id, user_id, read_access, write_access
		from lf_access;

-- -----------------------------------------------------
-- View `lfh_media_series`
-- -----------------------------------------------------
CREATE  OR REPLACE VIEW `lfh_media_series` AS
	select bin2uuid(series_id), bin2uuid(media_id), series_version
	from lf_media_series;

-- -----------------------------------------------------
-- View `lfh_media_subject`
-- -----------------------------------------------------
CREATE  OR REPLACE VIEW `lfh_media_subject` AS
	select subject_id, bin2uuid(media_id)
	from lf_media_subject;

-- -----------------------------------------------------
-- View `lfh_series_subject`
-- -----------------------------------------------------
CREATE  OR REPLACE VIEW `lfh_series_subject` AS
	select subject_id, bin2uuid(series_id)
	from lf_series_subject;

DELIMITER $$

CREATE TRIGGER check_server_update AFTER UPDATE ON lf_server
    FOR EACH ROW
    BEGIN
		update lf_file
			set server_id = NEW.id
			where server_id = NEW.id
				and format = NEW.format;
    END;$$


CREATE TRIGGER propagate_delete AFTER DELETE ON lf_file
    FOR EACH ROW
    BEGIN
        DELETE FROM lf_prepared_file WHERE id = OLD.id;
    END;$$


CREATE TRIGGER check_insert BEFORE UPDATE ON lf_file
    FOR EACH ROW
    BEGIN
        IF isnull(NEW.uri) and isnull(NEW.server_id) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Not both uri and server_id can be NULL!';

		/* Check if URL is valid */
        ELSEIF not isnull(NEW.uri) and NEW.uri not like '%://%' THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Not a valid URI!';
        END IF;
    END;$$


CREATE TRIGGER file_default_values BEFORE INSERT ON lf_file
    FOR EACH ROW
    BEGIN
		/* Check if either the URL or the server_id is set */
        IF isnull(NEW.uri) and isnull(NEW.server_id) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Not both uri and server_id can be NULL!';

		/* Check if URL is valid */
        ELSEIF not isnull(NEW.uri) and NEW.uri not like '%://%' THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Not a valid URI!';

        /* Create new UUID */
		ELSEIF NEW.id = x'00000000000000000000000000000000' then
            SET NEW.id = binuuid();

        END IF;
    END;$$


CREATE TRIGGER propagate_insert AFTER INSERT ON lf_file
    FOR EACH ROW
    BEGIN
        CALL prepare_file(
			NEW.id,
			NEW.media_id,
			NEW.format,
			NEW.type,
			NEW.quality,
			NEW.server_id,
			NEW.uri,
			NEW.source,
			NEW.source_system,
			NEW.source_key,
			NEW.flavor,
			NEW.tags );
    END;$$


CREATE TRIGGER propagate_update AFTER UPDATE ON lf_file
    FOR EACH ROW
    BEGIN
		CALL prepare_file(
			NEW.id,
			NEW.media_id,
			NEW.format,
			NEW.type,
			NEW.quality,
			NEW.server_id,
			NEW.uri,
			NEW.source,
			NEW.source_system,
			NEW.source_key,
			NEW.flavor,
			NEW.tags );
    END;$$


CREATE TRIGGER series_default_values BEFORE INSERT ON lf_series
    FOR EACH ROW
    BEGIN
        /* Create new UUID */
		IF NEW.id = x'00000000000000000000000000000000' then
            SET NEW.id = binuuid();

        /* Set parent_version to last version if not set. */
        ELSEIF ISNULL( NEW.parent_version ) THEN
            SET NEW.parent_version = (select max(version) from lf_series where id = NEW.id );
        END IF;

        /* Enter current timestamp as creation date */
        IF NEW.timestamp_created = '2000-01-01' THEN
            SET NEW.timestamp_created = NOW();
        END IF;

        /* Increase version by one if not set */
        IF NEW.version = 0 THEN
            SET NEW.version = IFNULL( (select max(version) from lf_series where id = NEW.id ), -1 ) + 1;
        END IF;
    END;$$


CREATE TRIGGER default_values BEFORE INSERT ON lf_media
    FOR EACH ROW
    BEGIN
        /* Create new UUID */
        IF NEW.id = x'00000000000000000000000000000000' then
            SET NEW.id = binuuid();

        /* Set parent_version to last version if not set. */
        ELSEIF ISNULL( NEW.parent_version ) THEN
            SET NEW.parent_version = (select max(version) from lf_media where id = NEW.id );
        END IF;

        /* Enter current timestamp as creation date */
        IF NEW.timestamp_created = '2000-01-01' THEN
            SET NEW.timestamp_created = NOW();
        END IF;

        /* Increase version by one if not set */
        IF NEW.version = 0 THEN
            SET NEW.version = IFNULL( (select max(version) from lf_media where id = NEW.id ), -1 ) + 1;
        END IF;
    END;$$


CREATE TRIGGER prevent_insert BEFORE UPDATE ON lf_prepared_file
    FOR EACH ROW
    BEGIN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Updates on this table are forbidden.';
    END;$$
