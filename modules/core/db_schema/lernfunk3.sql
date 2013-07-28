SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

DROP SCHEMA IF EXISTS `lernfunk3` ;
CREATE SCHEMA IF NOT EXISTS `lernfunk3` DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci ;
USE `lernfunk3` ;

-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_subject`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_subject` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_subject` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `language` VARCHAR(255) NOT NULL COMMENT 'ietf language tag\nSpec: http://tools.ietf.org/rfc/bcp/bcp47.txt\nLanguage Subtag Lookup: http://rishida.net/utils/subtags/' ,
  `name` VARCHAR(255) NOT NULL ,
  PRIMARY KEY (`id`) )
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_server`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_server` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_server` (
  `id` VARCHAR(255) NOT NULL COMMENT 'A meaningful name for the server' ,
  `format` VARCHAR(32) NOT NULL ,
  `uri_pattern` VARCHAR(255) NOT NULL ,
  PRIMARY KEY (`id`, `format`) )
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_group`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_group` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_group` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(255) NOT NULL ,
  PRIMARY KEY (`id`) ,
  UNIQUE INDEX `name_UNIQUE` (`name` ASC) )
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_user`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_user` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_user` (
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
-- Table `lernfunk3`.`lf_media`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_media` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_media` (
  `id` BINARY(16) NOT NULL DEFAULT x'00' ,
  `version` INT UNSIGNED NOT NULL DEFAULT 0 ,
  `parent_version` INT UNSIGNED NULL DEFAULT NULL ,
  `language` VARCHAR(255) NOT NULL COMMENT 'ietf language tag\nSpec: http://tools.ietf.org/rfc/bcp/bcp47.txt\nLanguage Subtag Lookup: http://rishida.net/utils/subtags/' ,
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
    REFERENCES `lernfunk3`.`lf_media` (`id` , `version` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_media_owner`
    FOREIGN KEY (`owner` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_media_editor`
    FOREIGN KEY (`editor` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_file`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_file` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_file` (
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
    REFERENCES `lernfunk3`.`lf_media` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_file_server`
    FOREIGN KEY (`server_id` )
    REFERENCES `lernfunk3`.`lf_server` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_series`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_series` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_series` (
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
    REFERENCES `lernfunk3`.`lf_series` (`id` , `version` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_series_owner`
    FOREIGN KEY (`owner` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_series_editor`
    FOREIGN KEY (`editor` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_user_group`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_user_group` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_user_group` (
  `user_id` INT UNSIGNED NOT NULL ,
  `group_id` INT UNSIGNED NOT NULL ,
  PRIMARY KEY (`user_id`, `group_id`) ,
  INDEX `fk_lf_user_group_user_idx` (`user_id` ASC) ,
  INDEX `fk_lf_user_group_group_idx` (`group_id` ASC) ,
  CONSTRAINT `fk_lf_user_group_user`
    FOREIGN KEY (`user_id` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_user_group_group`
    FOREIGN KEY (`group_id` )
    REFERENCES `lernfunk3`.`lf_group` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_media_subject`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_media_subject` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_media_subject` (
  `subject_id` INT UNSIGNED NOT NULL ,
  `media_id` BINARY(16) NOT NULL ,
  PRIMARY KEY (`subject_id`, `media_id`) ,
  INDEX `fk_lf_media_tag_media_idx` (`media_id` ASC) ,
  INDEX `fk_lf_media_tag_tag_idx` (`subject_id` ASC) ,
  CONSTRAINT `fk_lf_media_subject_media`
    FOREIGN KEY (`media_id` )
    REFERENCES `lernfunk3`.`lf_media` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_media_subject_subject`
    FOREIGN KEY (`subject_id` )
    REFERENCES `lernfunk3`.`lf_subject` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_series_subject`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_series_subject` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_series_subject` (
  `subject_id` INT UNSIGNED NOT NULL ,
  `series_id` BINARY(16) NOT NULL ,
  PRIMARY KEY (`subject_id`, `series_id`) ,
  INDEX `fk_lf_series_subject_series_idx` (`series_id` ASC) ,
  INDEX `fk_lf_series_subject_subject_idx` (`subject_id` ASC) ,
  CONSTRAINT `fk_lf_series_subject_series`
    FOREIGN KEY (`series_id` )
    REFERENCES `lernfunk3`.`lf_series` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_series_subject_subject`
    FOREIGN KEY (`subject_id` )
    REFERENCES `lernfunk3`.`lf_subject` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_media_series`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_media_series` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_media_series` (
  `series_id` BINARY(16) NOT NULL ,
  `media_id` BINARY(16) NOT NULL ,
  `series_version` INT UNSIGNED NOT NULL DEFAULT 0 ,
  PRIMARY KEY (`series_id`, `media_id`, `series_version`) ,
  INDEX `fk_lf_media_series_series_idx` (`series_id` ASC, `series_version` ASC) ,
  INDEX `fk_lf_media_series_media_idx` (`media_id` ASC) ,
  CONSTRAINT `fk_lf_media_series_series`
    FOREIGN KEY (`series_id` , `series_version` )
    REFERENCES `lernfunk3`.`lf_series` (`id` , `version` )
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_media_series_media`
    FOREIGN KEY (`media_id` )
    REFERENCES `lernfunk3`.`lf_media` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_prepared_file`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_prepared_file` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_prepared_file` (
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
    REFERENCES `lernfunk3`.`lf_media` (`id` )
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
COMMENT = 'IMPORTANT: This table is used as a temporary storage for the /* comment truncated */ /* complicated merge of lf_file and lf_server. All insertes and updates on this table will be prohibited by triggers and result in errors.*/';


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_organization`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_organization` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_organization` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(255) NOT NULL ,
  `vcard_uri` VARCHAR(255) NULL DEFAULT NULL ,
  `parent_organization` INT UNSIGNED NULL DEFAULT NULL ,
  PRIMARY KEY (`id`) ,
  INDEX `fk_lf_organization_parent_idx` (`parent_organization` ASC) ,
  CONSTRAINT `fk_lf_organization_parent`
    FOREIGN KEY (`parent_organization` )
    REFERENCES `lernfunk3`.`lf_organization` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_user_organization`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_user_organization` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_user_organization` (
  `organization_id` INT UNSIGNED NOT NULL ,
  `user_id` INT UNSIGNED NOT NULL ,
  PRIMARY KEY (`organization_id`, `user_id`) ,
  INDEX `fk_lf_user_organization_user_idx` (`user_id` ASC) ,
  INDEX `fk_lf_user_organization_organization_idx` (`organization_id` ASC) ,
  CONSTRAINT `fk_lf_user_organization_user`
    FOREIGN KEY (`user_id` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_lf_user_organization_organization`
    FOREIGN KEY (`organization_id` )
    REFERENCES `lernfunk3`.`lf_organization` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_access`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_access` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_access` (
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
    REFERENCES `lernfunk3`.`lf_media` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_lf_access_series`
    FOREIGN KEY (`series_id` )
    REFERENCES `lernfunk3`.`lf_series` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_lf_access_user`
    FOREIGN KEY (`user_id` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_lf_access_group`
    FOREIGN KEY (`group_id` )
    REFERENCES `lernfunk3`.`lf_group` (`id` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_latest_media`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_latest_media` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_latest_media` (
  `id` BINARY(16) NOT NULL DEFAULT x'00' ,
  `version` INT UNSIGNED NOT NULL DEFAULT 0 ,
  `parent_version` INT UNSIGNED NULL DEFAULT NULL ,
  `language` VARCHAR(255) NOT NULL COMMENT 'ietf language tag\nSpec: http://tools.ietf.org/rfc/bcp/bcp47.txt\nLanguage Subtag Lookup: http://rishida.net/utils/subtags/' ,
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
  `creator` VARCHAR(2048) NULL DEFAULT NULL ,
  `contributor` VARCHAR(2048) NULL DEFAULT NULL ,
  `publisher` VARCHAR(2048) NULL ,
  PRIMARY KEY (`id`, `language`) ,
  INDEX `fk_lf_latest_media_owner_idx` (`owner` ASC) ,
  INDEX `fk_lf_latest_media_editor_idx` (`editor` ASC) ,
  CONSTRAINT `fk_lf_latest_media_owner`
    FOREIGN KEY (`owner` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_latest_media_editor`
    FOREIGN KEY (`editor` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_latest_published_media`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_latest_published_media` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_latest_published_media` (
  `id` BINARY(16) NOT NULL DEFAULT x'00' ,
  `version` INT UNSIGNED NOT NULL DEFAULT 0 ,
  `parent_version` INT UNSIGNED NULL DEFAULT NULL ,
  `language` VARCHAR(255) NOT NULL COMMENT 'ietf language tag\nSpec: http://tools.ietf.org/rfc/bcp/bcp47.txt\nLanguage Subtag Lookup: http://rishida.net/utils/subtags/' ,
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
  `creator` VARCHAR(2048) NULL DEFAULT NULL ,
  `contributor` VARCHAR(2048) NULL DEFAULT NULL ,
  `publisher` VARCHAR(45) NULL ,
  PRIMARY KEY (`id`, `language`) ,
  INDEX `fk_lf_latest_published_media_owner_idx` (`owner` ASC) ,
  INDEX `fk_lf_latest_published_media_editor_idx` (`editor` ASC) ,
  CONSTRAINT `fk_lf_latest_published_media_owner`
    FOREIGN KEY (`owner` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_latest_published_media_editor`
    FOREIGN KEY (`editor` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_latest_series`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_latest_series` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_latest_series` (
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
  PRIMARY KEY (`id`, `language`) ,
  INDEX `fk_lf_series_owner_idx` (`owner` ASC) ,
  INDEX `fk_lf_series_editor_idx` (`editor` ASC) ,
  CONSTRAINT `fk_lf_latest_series_owner`
    FOREIGN KEY (`owner` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_latest_series_editor`
    FOREIGN KEY (`editor` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `lernfunk3`.`lf_latest_published_series`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `lernfunk3`.`lf_latest_published_series` ;

CREATE  TABLE IF NOT EXISTS `lernfunk3`.`lf_latest_published_series` (
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
  PRIMARY KEY (`id`, `language`) ,
  INDEX `fk_lf_series_owner_idx` (`owner` ASC) ,
  INDEX `fk_lf_series_editor_idx` (`editor` ASC) ,
  CONSTRAINT `fk_lf_latest_published_series_owner`
    FOREIGN KEY (`owner` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE,
  CONSTRAINT `fk_lf_latest_published_series_editor`
    FOREIGN KEY (`editor` )
    REFERENCES `lernfunk3`.`lf_user` (`id` )
    ON DELETE RESTRICT
    ON UPDATE CASCADE)
ENGINE = InnoDB;

USE `lernfunk3` ;

-- -----------------------------------------------------
-- Placeholder table for view `lernfunk3`.`lf_published_media`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lernfunk3`.`lf_published_media` (`id` INT, `version` INT, `parent_version` INT, `language` INT, `title` INT, `description` INT, `owner` INT, `editor` INT, `timestamp_edit` INT, `timestamp_created` INT, `published` INT, `source` INT, `visible` INT, `source_system` INT, `source_key` INT, `rights` INT, `type` INT, `coverage` INT, `relation` INT, `creator` INT, `contributor` INT, `publisher` INT);

-- -----------------------------------------------------
-- Placeholder table for view `lernfunk3`.`lf_published_series`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lernfunk3`.`lf_published_series` (`id` INT, `version` INT, `parent_version` INT, `title` INT, `language` INT, `description` INT, `source` INT, `timestamp_edit` INT, `timestamp_created` INT, `published` INT, `owner` INT, `editor` INT, `visible` INT, `source_key` INT, `source_system` INT, `creator` INT, `contributor` INT, `publisher` INT);

-- -----------------------------------------------------
-- Placeholder table for view `lernfunk3`.`lfh_file`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lernfunk3`.`lfh_file` (`id` INT, `media_id` INT, `format` INT, `type` INT, `quality` INT, `server_id` INT, `uri` INT, `source` INT, `source_key` INT, `source_system` INT, `flavor` INT, `tags` INT);

-- -----------------------------------------------------
-- Placeholder table for view `lernfunk3`.`lfh_prepared_file`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lernfunk3`.`lfh_prepared_file` (`bin2uuid(id)` INT, `bin2uuid(media_id)` INT, `format` INT, `uri` INT, `source` INT, `source_key` INT, `source_system` INT, `flavor` INT, `tags` INT);

-- -----------------------------------------------------
-- Placeholder table for view `lernfunk3`.`lfh_media`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lernfunk3`.`lfh_media` (`id` INT, `version` INT, `parent_version` INT, `language` INT, `title` INT, `description` INT, `owner` INT, `editor` INT, `timestamp_edit` INT, `timestamp_created` INT, `published` INT, `source` INT, `visible` INT, `source_system` INT, `source_key` INT, `rights` INT, `type` INT, `coverage` INT, `relation` INT, `creator` INT, `contributor` INT, `publisher` INT);

-- -----------------------------------------------------
-- Placeholder table for view `lernfunk3`.`lfh_latest_media`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lernfunk3`.`lfh_latest_media` (`bin2uuid(id)` INT, `version` INT, `parent_version` INT, `language` INT, `title` INT, `description` INT, `owner` INT, `editor` INT, `timestamp_edit` INT, `timestamp_created` INT, `published` INT, `source` INT, `visible` INT, `source_system` INT, `source_key` INT, `rights` INT, `type` INT, `coverage` INT, `relation` INT, `creator` INT, `contributor` INT, `publisher` INT);

-- -----------------------------------------------------
-- Placeholder table for view `lernfunk3`.`lfh_latest_published_media`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lernfunk3`.`lfh_latest_published_media` (`bin2uuid(id)` INT, `version` INT, `parent_version` INT, `language` INT, `title` INT, `description` INT, `owner` INT, `editor` INT, `timestamp_edit` INT, `timestamp_created` INT, `published` INT, `source` INT, `visible` INT, `source_system` INT, `source_key` INT, `rights` INT, `type` INT, `coverage` INT, `relation` INT, `creator` INT, `contributor` INT, `publisher` INT);

-- -----------------------------------------------------
-- Placeholder table for view `lernfunk3`.`lfh_series`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lernfunk3`.`lfh_series` (`id` INT, `version` INT, `parent_version` INT, `title` INT, `language` INT, `description` INT, `source` INT, `timestamp_edit` INT, `timestamp_created` INT, `published` INT, `owner` INT, `editor` INT, `visible` INT, `source_key` INT, `source_system` INT, `creator` INT, `contributor` INT, `publisher` INT);

-- -----------------------------------------------------
-- Placeholder table for view `lernfunk3`.`lfh_latest_series`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lernfunk3`.`lfh_latest_series` (`bin2uuid(id)` INT, `version` INT, `parent_version` INT, `title` INT, `language` INT, `description` INT, `source` INT, `timestamp_edit` INT, `timestamp_created` INT, `published` INT, `owner` INT, `editor` INT, `visible` INT, `source_key` INT, `source_system` INT);

-- -----------------------------------------------------
-- Placeholder table for view `lernfunk3`.`lfh_latest_published_series`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lernfunk3`.`lfh_latest_published_series` (`bin2uuid(id)` INT, `version` INT, `parent_version` INT, `title` INT, `language` INT, `description` INT, `source` INT, `timestamp_edit` INT, `timestamp_created` INT, `published` INT, `owner` INT, `editor` INT, `visible` INT, `source_key` INT, `source_system` INT, `creator` INT, `contributor` INT, `publisher` INT);

-- -----------------------------------------------------
-- Placeholder table for view `lernfunk3`.`lfh_access`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lernfunk3`.`lfh_access` (`id` INT, `media_id` INT, `series_id` INT, `group_id` INT, `user_id` INT, `read_access` INT, `write_access` INT);

-- -----------------------------------------------------
-- Placeholder table for view `lernfunk3`.`lfh_media_series`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lernfunk3`.`lfh_media_series` (`bin2uuid(series_id)` INT, `bin2uuid(media_id)` INT, `series_version` INT);

-- -----------------------------------------------------
-- Placeholder table for view `lernfunk3`.`lfh_media_subject`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lernfunk3`.`lfh_media_subject` (`subject_id` INT, `bin2uuid(media_id)` INT);

-- -----------------------------------------------------
-- Placeholder table for view `lernfunk3`.`lfh_series_subject`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `lernfunk3`.`lfh_series_subject` (`subject_id` INT, `bin2uuid(series_id)` INT);

-- -----------------------------------------------------
-- procedure prepare_file
-- -----------------------------------------------------

USE `lernfunk3`;
DROP procedure IF EXISTS `lernfunk3`.`prepare_file`;

DELIMITER $$
USE `lernfunk3`$$
CREATE PROCEDURE `lernfunk3`.`prepare_file` 
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

USE `lernfunk3`;
DROP function IF EXISTS `lernfunk3`.`uuid2bin`;

DELIMITER $$
USE `lernfunk3`$$


CREATE FUNCTION `lernfunk3`.`uuid2bin`( uuid VARCHAR(36) )
RETURNS BINARY(16)
BEGIN
	RETURN unhex(REPLACE(uuid,'-',''));
END$$

DELIMITER ;

-- -----------------------------------------------------
-- function binuuid
-- -----------------------------------------------------

USE `lernfunk3`;
DROP function IF EXISTS `lernfunk3`.`binuuid`;

DELIMITER $$
USE `lernfunk3`$$


CREATE FUNCTION `lernfunk3`.`binuuid`()
RETURNS BINARY(16)
BEGIN
	RETURN unhex(REPLACE(uuid(),'-',''));
END$$

DELIMITER ;

-- -----------------------------------------------------
-- function bin2uuid
-- -----------------------------------------------------

USE `lernfunk3`;
DROP function IF EXISTS `lernfunk3`.`bin2uuid`;

DELIMITER $$
USE `lernfunk3`$$


CREATE FUNCTION `lernfunk3`.`bin2uuid`( bin BINARY(16) )
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
-- View `lernfunk3`.`lf_published_media`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `lernfunk3`.`lf_published_media` ;
DROP TABLE IF EXISTS `lernfunk3`.`lf_published_media`;
USE `lernfunk3`;
CREATE OR REPLACE ALGORITHM = MERGE VIEW `lernfunk3`.`lf_published_media` AS
    select m.* from lf_media m where m.published;

-- -----------------------------------------------------
-- View `lernfunk3`.`lf_published_series`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `lernfunk3`.`lf_published_series` ;
DROP TABLE IF EXISTS `lernfunk3`.`lf_published_series`;
USE `lernfunk3`;
CREATE OR REPLACE ALGORITHM = MERGE VIEW `lernfunk3`.`lf_published_series` AS
    select s.* from lf_series s where s.published;

-- -----------------------------------------------------
-- View `lernfunk3`.`lfh_file`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `lernfunk3`.`lfh_file` ;
DROP TABLE IF EXISTS `lernfunk3`.`lfh_file`;
USE `lernfunk3`;
create  OR REPLACE view `lernfunk3`.`lfh_file` as
	select bin2uuid(id) as id, bin2uuid(media_id) as media_id, format, type,
		quality, server_id, uri, source, source_key, source_system, flavor, tags from lf_file;

-- -----------------------------------------------------
-- View `lernfunk3`.`lfh_prepared_file`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `lernfunk3`.`lfh_prepared_file` ;
DROP TABLE IF EXISTS `lernfunk3`.`lfh_prepared_file`;
USE `lernfunk3`;
CREATE  OR REPLACE VIEW `lernfunk3`.`lfh_prepared_file` AS
	select bin2uuid(id), bin2uuid(media_id), format, uri, source, source_key, source_system, flavor, tags from lf_prepared_file;

-- -----------------------------------------------------
-- View `lernfunk3`.`lfh_media`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `lernfunk3`.`lfh_media` ;
DROP TABLE IF EXISTS `lernfunk3`.`lfh_media`;
USE `lernfunk3`;
CREATE  OR REPLACE VIEW `lernfunk3`.`lfh_media` AS
	select bin2uuid(id) as id, version, parent_version, language, title, description, 
		owner, editor, timestamp_edit, timestamp_created, published, source, 
		visible, source_system, source_key, rights, type, coverage, relation, 
		creator, contributor, publisher
		from lf_media;

-- -----------------------------------------------------
-- View `lernfunk3`.`lfh_latest_media`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `lernfunk3`.`lfh_latest_media` ;
DROP TABLE IF EXISTS `lernfunk3`.`lfh_latest_media`;
USE `lernfunk3`;
CREATE  OR REPLACE VIEW `lernfunk3`.`lfh_latest_media` AS
	select bin2uuid(id), version, parent_version, language, title, description, 
		owner, editor, timestamp_edit, timestamp_created, published, source, 
		visible, source_system, source_key, rights, type, coverage, relation, 
		creator, contributor, publisher
		from lf_latest_media;

-- -----------------------------------------------------
-- View `lernfunk3`.`lfh_latest_published_media`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `lernfunk3`.`lfh_latest_published_media` ;
DROP TABLE IF EXISTS `lernfunk3`.`lfh_latest_published_media`;
USE `lernfunk3`;
CREATE  OR REPLACE VIEW `lernfunk3`.`lfh_latest_published_media` AS
	select bin2uuid(id), version, parent_version, language, title, description, 
		owner, editor, timestamp_edit, timestamp_created, published, source, 
		visible, source_system, source_key, rights, type, coverage, relation, 
		creator, contributor, publisher
		from lf_latest_published_media;

-- -----------------------------------------------------
-- View `lernfunk3`.`lfh_series`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `lernfunk3`.`lfh_series` ;
DROP TABLE IF EXISTS `lernfunk3`.`lfh_series`;
USE `lernfunk3`;
CREATE  OR REPLACE VIEW `lernfunk3`.`lfh_series` AS
	select bin2uuid(id) as id, version, parent_version, title, language, 
		description, source, timestamp_edit, timestamp_created, 
		published, owner, editor, visible, source_key, source_system, 
		creator, contributor, publisher
		from lf_series;

-- -----------------------------------------------------
-- View `lernfunk3`.`lfh_latest_series`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `lernfunk3`.`lfh_latest_series` ;
DROP TABLE IF EXISTS `lernfunk3`.`lfh_latest_series`;
USE `lernfunk3`;
CREATE  OR REPLACE VIEW `lernfunk3`.`lfh_latest_series` AS
	select bin2uuid(id), version, parent_version, title, language, 
		description, source, timestamp_edit, timestamp_created, 
		published, owner, editor, visible, source_key, source_system 
		from lf_latest_series;

-- -----------------------------------------------------
-- View `lernfunk3`.`lfh_latest_published_series`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `lernfunk3`.`lfh_latest_published_series` ;
DROP TABLE IF EXISTS `lernfunk3`.`lfh_latest_published_series`;
USE `lernfunk3`;
CREATE  OR REPLACE VIEW `lernfunk3`.`lfh_latest_published_series` AS
	select bin2uuid(id), version, parent_version, title, language, 
		description, source, timestamp_edit, timestamp_created, 
		published, owner, editor, visible, source_key, source_system, 
		creator, contributor, publisher
		from lf_latest_published_series;

-- -----------------------------------------------------
-- View `lernfunk3`.`lfh_access`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `lernfunk3`.`lfh_access` ;
DROP TABLE IF EXISTS `lernfunk3`.`lfh_access`;
USE `lernfunk3`;
CREATE  OR REPLACE VIEW `lernfunk3`.`lfh_access` AS
	select id, bin2uuid(media_id) as media_id, bin2uuid(series_id) as series_id, 
		group_id, user_id, read_access, write_access 
		from lf_access;

-- -----------------------------------------------------
-- View `lernfunk3`.`lfh_media_series`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `lernfunk3`.`lfh_media_series` ;
DROP TABLE IF EXISTS `lernfunk3`.`lfh_media_series`;
USE `lernfunk3`;
CREATE  OR REPLACE VIEW `lernfunk3`.`lfh_media_series` AS
	select bin2uuid(series_id), bin2uuid(media_id), series_version
	from lf_media_series;

-- -----------------------------------------------------
-- View `lernfunk3`.`lfh_media_subject`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `lernfunk3`.`lfh_media_subject` ;
DROP TABLE IF EXISTS `lernfunk3`.`lfh_media_subject`;
USE `lernfunk3`;
CREATE  OR REPLACE VIEW `lernfunk3`.`lfh_media_subject` AS
	select subject_id, bin2uuid(media_id)
	from lf_media_subject;

-- -----------------------------------------------------
-- View `lernfunk3`.`lfh_series_subject`
-- -----------------------------------------------------
DROP VIEW IF EXISTS `lernfunk3`.`lfh_series_subject` ;
DROP TABLE IF EXISTS `lernfunk3`.`lfh_series_subject`;
USE `lernfunk3`;
CREATE  OR REPLACE VIEW `lernfunk3`.`lfh_series_subject` AS
	select subject_id, bin2uuid(series_id)
	from lf_series_subject;
USE `lernfunk3`;

DELIMITER $$

USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`check_server_update` $$
USE `lernfunk3`$$


CREATE TRIGGER check_server_update AFTER UPDATE ON lf_server
    FOR EACH ROW
    BEGIN
		update lf_file 
			set server_id = NEW.id
			where server_id = NEW.id
				and format = NEW.format;
    END;$$


DELIMITER ;

DELIMITER $$

USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`propagate_delete` $$
USE `lernfunk3`$$


CREATE TRIGGER propagate_delete AFTER DELETE ON lf_file
    FOR EACH ROW
    BEGIN
        DELETE FROM lf_prepared_file WHERE id = OLD.id;
    END;$$


USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`check_insert` $$
USE `lernfunk3`$$


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


USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`file_default_values` $$
USE `lernfunk3`$$


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


USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`propagate_insert` $$
USE `lernfunk3`$$


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


USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`propagate_update` $$
USE `lernfunk3`$$


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


DELIMITER ;

DELIMITER $$

USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`series_default_values` $$
USE `lernfunk3`$$




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


USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`set_latest_series_version` $$
USE `lernfunk3`$$


CREATE TRIGGER set_latest_series_version AFTER INSERT ON lf_series
    FOR EACH ROW
    BEGIN
		/**
		 * An insert should always produce the „latest“ version. 
		 * Thus we can put these data sets into lf_latest_series
		 * without any further confirmation
		**/
        INSERT INTO lf_latest_series SET
				id                = NEW.id,
				version           = NEW.version,
				parent_version    = NEW.parent_version,
				title             = NEW.title,
				language          = NEW.language,
				description       = NEW.description,
				source            = NEW.source,
				timestamp_edit    = NEW.timestamp_edit,
				timestamp_created = NEW.timestamp_created,
				published         = NEW.published,
				owner             = NEW.owner,
				editor            = NEW.editor,
				visible           = NEW.visible,
				source_system     = NEW.source_system,
				source_key        = NEW.source_key,
				creator           = NEW.creator,
				contributor       = NEW.contributor,
				publisher         = NEW.publisher
			ON DUPLICATE KEY UPDATE
				id                = NEW.id,
				version           = NEW.version,
				parent_version    = NEW.parent_version,
				title             = NEW.title,
				language          = NEW.language,
				description       = NEW.description,
				source            = NEW.source,
				timestamp_edit    = NEW.timestamp_edit,
				timestamp_created = NEW.timestamp_created,
				published         = NEW.published,
				owner             = NEW.owner,
				editor            = NEW.editor,
				visible           = NEW.visible,
				source_system     = NEW.source_system,
				source_key        = NEW.source_key,
				creator           = NEW.creator,
				contributor       = NEW.contributor,
				publisher         = NEW.publisher;
		/**
		 * Check if the new series version is published. 
		 * If so, then put it in lf_latest_published_series, too.
		 **/
		if NEW.published then
			INSERT INTO lf_latest_published_series SET
					id                = NEW.id,
					version           = NEW.version,
					parent_version    = NEW.parent_version,
					title             = NEW.title,
					language          = NEW.language,
					description       = NEW.description,
					source            = NEW.source,
					timestamp_edit    = NEW.timestamp_edit,
					timestamp_created = NEW.timestamp_created,
					published         = NEW.published,
					owner             = NEW.owner,
					editor            = NEW.editor,
					visible           = NEW.visible,
					source_system     = NEW.source_system,
					source_key        = NEW.source_key,
					creator           = NEW.creator,
					contributor       = NEW.contributor,
					publisher         = NEW.publisher
				ON DUPLICATE KEY UPDATE
					id                = NEW.id,
					version           = NEW.version,
					parent_version    = NEW.parent_version,
					title             = NEW.title,
					language          = NEW.language,
					description       = NEW.description,
					source            = NEW.source,
					timestamp_edit    = NEW.timestamp_edit,
					timestamp_created = NEW.timestamp_created,
					published         = NEW.published,
					owner             = NEW.owner,
					editor            = NEW.editor,
					visible           = NEW.visible,
					source_system     = NEW.source_system,
					source_key        = NEW.source_key,
					creator           = NEW.creator,
					contributor       = NEW.contributor,
					publisher         = NEW.publisher;
		end if;
    END;$$


USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`update_latest_series_version` $$
USE `lernfunk3`$$


CREATE TRIGGER update_latest_series_version AFTER UPDATE ON lf_series
    FOR EACH ROW
    BEGIN
		/**
		 * We permit the change of the published flag of an already 
		 * existing mediaobject version. In that case we have to 
		 * update lf_latest_published_media, too.
		**/
		if NEW.published then
			/* Get last pulished version… */
			set @current_latest_pub_version = -1;
			if exists( (select version from lf_latest_published_series
					where id = NEW.id and language = NEW.language) ) then
				set @current_latest_pub_version = 
					(select version from lf_latest_published_series
						where id = NEW.id and language = NEW.language);
			end if;
			/* …and check if this one is „newer” */
			if NEW.version >= @current_latest_pub_version then
				INSERT INTO lf_latest_published_series SET 
					id                = NEW.id,
					version           = NEW.version,
					parent_version    = NEW.parent_version,
					title             = NEW.title,
					language          = NEW.language,
					description       = NEW.description,
					source            = NEW.source,
					timestamp_edit    = NEW.timestamp_edit,
					timestamp_created = NEW.timestamp_created,
					published         = NEW.published,
					owner             = NEW.owner,
					editor            = NEW.editor,
					visible           = NEW.visible,
					source_system     = NEW.source_system,
					source_key        = NEW.source_key,
					creator           = NEW.creator,
					contributor       = NEW.contributor,
					publisher         = NEW.publisher
				ON DUPLICATE KEY UPDATE
					id                = NEW.id,
					version           = NEW.version,
					parent_version    = NEW.parent_version,
					title             = NEW.title,
					language          = NEW.language,
					description       = NEW.description,
					source            = NEW.source,
					timestamp_edit    = NEW.timestamp_edit,
					timestamp_created = NEW.timestamp_created,
					published         = NEW.published,
					owner             = NEW.owner,
					editor            = NEW.editor,
					visible           = NEW.visible,
					source_system     = NEW.source_system,
					source_key        = NEW.source_key,
					creator           = NEW.creator,
					contributor       = NEW.contributor,
					publisher         = NEW.publisher;
			end if;
		else
			/**
			 * The updated version is not published. 
			 * So we have to check if it was the published version before.
			 **/
			if exists( (select version from lf_latest_published_series
					where id = NEW.id and version = NEW.version) ) then
				/** 
				 * We know now that the data in lf_latest_published_media is invalid.
				 * So we remove the invalid data set.
				 **/
				delete from lf_latest_published_series where id = NEW.id and language = NEW.language;
				/* Now we check if there is a new published version: */
				if exists( (select version from lf_series where id = NEW.id and language = NEW.language and published) ) then
					/* Ok, there is a published version. So get the version id: */
					set @latest_pub_version = (select max(version) from lf_series where id = NEW.id 
						and language = NEW.language and published);
					/* Insert latest published version: */
					insert into lf_latest_published_series
						( id, version, parent_version, title, language, description, source, 
							timestamp_edit, timestamp_created,published, owner, editor, visible,
							source_system, source_key, creator, contributor, publisher )
						select id, version, parent_version, title, language, description, source, 
							timestamp_edit, timestamp_created,published, owner, editor, visible,
							source_system, source_key, creator, contributor, publisher
							from lf_series where id = NEW.id and version = @latest_pub_version;
				end if;
			end if;
		end if;
    END;$$


USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`delete_latest_series_version` $$
USE `lernfunk3`$$


CREATE TRIGGER delete_latest_series_version AFTER DELETE ON lf_series
    FOR EACH ROW
    BEGIN
		/**
		 * We have to check if the deleted version is in lf_latest_media 
		 * or lf_latest_published_media
		 **/
		if exists( (select version from lf_latest_published_series
				where id = OLD.id and version = OLD.version) ) then
			/** 
			 * We know now that the data in lf_latest_published_media is invalid.
			 * So we remove the invalid data set.
			 **/
			delete from lf_latest_published_series where id = OLD.id and language = OLD.language;
			/* Now we check if there is a new published version: */
			if exists( (select version from lf_series 
				where id = OLD.id and language = OLD.language and published) ) then
				/* Ok, there is a published version. So get the version id: */
				set @latest_pub_version = (select max(version) from lf_series where id = OLD.id 
					and language = OLD.language and published);
				/* Insert latest published version: */
				insert into lf_latest_published_series
					( id, version, parent_version, title, language, description, source, 
						timestamp_edit, timestamp_created,published, owner, editor, visible,
						source_system, source_key, creator, contributor, publisher )
					select id, version, parent_version, title, language, description, source, 
						timestamp_edit, timestamp_created,published, owner, editor, visible,
						source_system, source_key, creator, contributor, publisher
						from lf_series where id = OLD.id and version = @latest_pub_version;
			end if;
		end if;
		
		if exists( (select version from lf_latest_series
				where id = OLD.id and version = OLD.version) ) then
			/** 
			 * We know now that the data in lf_latest_media is invalid.
			 * So we remove the invalid data set.
			 **/
			delete from lf_latest_series where id = OLD.id and language = OLD.language;
			/* Now we check if there is a new published version: */
			if exists( (select version from lf_series 
					where id = OLD.id and language = OLD.language) ) then
				/* Ok, there is a published version. So get the version id: */
				set @latest_pub_version = (select max(version) from lf_series
						where id = OLD.id and language = OLD.language);
				/* Insert latest version: */
				insert into lf_latest_series
					( id, version, parent_version, title, language, description, source, 
						timestamp_edit, timestamp_created, published, owner, editor, visible,
						source_system, source_key, creator, contributor, publisher )
					select id, version, parent_version, title, language, description, source, 
						timestamp_edit, timestamp_created,published, owner, editor, visible,
						source_system, source_key, creator, contributor, publisher
						from lf_series where id = OLD.id and version = @latest_pub_version;
			end if;
		end if;
    END;$$


DELIMITER ;

DELIMITER $$

USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`default_values` $$
USE `lernfunk3`$$


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


USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`set_latest_version` $$
USE `lernfunk3`$$


CREATE TRIGGER set_latest_version AFTER INSERT ON lf_media
    FOR EACH ROW
    BEGIN
		/**
		 * An insert should always produce the „latest“ version. 
		 * Thus we can put these data sets into lf_latest_media 
		 * without any further confirmation
		**/
        INSERT INTO lf_latest_media SET 
			id                = NEW.id,
			version           = NEW.version,
			parent_version    = NEW.parent_version,
			language          = NEW.language,
			title             = NEW.title,
			description       = NEW.description,
			owner             = NEW.owner,
			editor            = NEW.editor,
			timestamp_edit    = NEW.timestamp_edit,
			timestamp_created = NEW.timestamp_created,
			published         = NEW.published,
			source            = NEW.source,
			visible           = NEW.visible,
			source_system     = NEW.source_system,
			source_key        = NEW.source_key,
			rights            = NEW.rights,
			type              = NEW.type,
			coverage          = NEW.coverage,
			relation          = NEW.relation,
			creator           = NEW.creator,
			contributor       = NEW.contributor,
			publisher         = NEW.publisher
			ON DUPLICATE KEY UPDATE
			id                = NEW.id,
			version           = NEW.version,
			parent_version    = NEW.parent_version,
			language          = NEW.language,
			title             = NEW.title,
			description       = NEW.description,
			owner             = NEW.owner,
			editor            = NEW.editor,
			timestamp_edit    = NEW.timestamp_edit,
			timestamp_created = NEW.timestamp_created,
			published         = NEW.published,
			source            = NEW.source,
			visible           = NEW.visible,
			source_system     = NEW.source_system,
			source_key        = NEW.source_key,
			rights            = NEW.rights,
			type              = NEW.type,
			coverage          = NEW.coverage,
			relation          = NEW.relation,
			creator           = NEW.creator,
			contributor       = NEW.contributor,
			publisher         = NEW.publisher;
		/**
		 * Check if the new media version is published. 
		 * If so, then put it in lf_latest_published_media, too.
		 **/
		if NEW.published then
			INSERT INTO lf_latest_published_media SET 
				id                = NEW.id,
				version           = NEW.version,
				parent_version    = NEW.parent_version,
				language          = NEW.language,
				title             = NEW.title,
				description       = NEW.description,
				owner             = NEW.owner,
				editor            = NEW.editor,
				timestamp_edit    = NEW.timestamp_edit,
				timestamp_created = NEW.timestamp_created,
				published         = NEW.published,
				source            = NEW.source,
				visible           = NEW.visible,
				source_system     = NEW.source_system,
				source_key        = NEW.source_key,
				rights            = NEW.rights,
				type              = NEW.type,
				coverage          = NEW.coverage,
				relation          = NEW.relation,
				creator           = NEW.creator,
				contributor       = NEW.contributor,
				publisher         = NEW.publisher
				ON DUPLICATE KEY UPDATE
				id                = NEW.id,
				version           = NEW.version,
				parent_version    = NEW.parent_version,
				language          = NEW.language,
				title             = NEW.title,
				description       = NEW.description,
				owner             = NEW.owner,
				editor            = NEW.editor,
				timestamp_edit    = NEW.timestamp_edit,
				timestamp_created = NEW.timestamp_created,
				published         = NEW.published,
				source            = NEW.source,
				visible           = NEW.visible,
				source_system     = NEW.source_system,
				source_key        = NEW.source_key,
				rights            = NEW.rights,
				type              = NEW.type,
				coverage          = NEW.coverage,
				relation          = NEW.relation,
				creator           = NEW.creator,
				contributor       = NEW.contributor,
				publisher         = NEW.publisher;
		end if;
    END;$$


USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`update_latest_version` $$
USE `lernfunk3`$$


CREATE TRIGGER update_latest_version AFTER UPDATE ON lf_media
    FOR EACH ROW
    BEGIN
		/**
		 * We permit the change of the published flag of an already 
		 * existing mediaobject version. In that case we have to 
		 * update lf_latest_published_media, too.
		**/
		if NEW.published then
			/* Get last pulished version… */
			set @current_latest_pub_version = -1;
			if exists( (select version from lf_latest_published_media 
					where id = NEW.id and language = NEW.language) ) then
				set @current_latest_pub_version = 
					(select version from lf_latest_published_media 
						where id = NEW.id and language = NEW.language);
			end if;
			/* …and check if this one is „newer” */
			if NEW.version >= @current_latest_pub_version then
				INSERT INTO lf_latest_published_media SET 
					id                = NEW.id,
					version           = NEW.version,
					parent_version    = NEW.parent_version,
					language          = NEW.language,
					title             = NEW.title,
					description       = NEW.description,
					owner             = NEW.owner,
					editor            = NEW.editor,
					timestamp_edit    = NEW.timestamp_edit,
					timestamp_created = NEW.timestamp_created,
					published         = NEW.published,
					source            = NEW.source,
					visible           = NEW.visible,
					source_system     = NEW.source_system,
					source_key        = NEW.source_key,
					rights            = NEW.rights,
					type              = NEW.type,
					coverage          = NEW.coverage,
					relation          = NEW.relation,
					creator           = NEW.creator,
					contributor       = NEW.contributor,
					publisher         = NEW.publisher
					ON DUPLICATE KEY UPDATE
					id                = NEW.id,
					version           = NEW.version,
					parent_version    = NEW.parent_version,
					language          = NEW.language,
					title             = NEW.title,
					description       = NEW.description,
					owner             = NEW.owner,
					editor            = NEW.editor,
					timestamp_edit    = NEW.timestamp_edit,
					timestamp_created = NEW.timestamp_created,
					published         = NEW.published,
					source            = NEW.source,
					visible           = NEW.visible,
					source_system     = NEW.source_system,
					source_key        = NEW.source_key,
					rights            = NEW.rights,
					type              = NEW.type,
					coverage          = NEW.coverage,
					relation          = NEW.relation,
					creator           = NEW.creator,
					contributor       = NEW.contributor,
					publisher         = NEW.publisher;
			end if;
		else
			/**
			 * The updated version is not published. 
			 * So we have to check if it was the published version before.
			 **/
			if exists( (select version from lf_latest_published_media 
					where id = NEW.id and version = NEW.version) ) then
				/** 
				 * We know now that the data in lf_latest_published_media is invalid.
				 * So we remove the invalid data set.
				 **/
				delete from lf_latest_published_media where id = NEW.id and language = NEW.language;
				/* Now we check if there is a new published version: */
				if exists( (select version from lf_media where id = NEW.id and language = NEW.language and published) ) then
					/* Ok, there is a published version. So get the version id: */
					set @latest_pub_version = (select max(version) from lf_media where id = NEW.id 
						and language = NEW.language and published);
					/* Insert latest published version: */
					insert into lf_latest_published_media 
						( id, version, parent_version, language, title, description, 
							owner, editor, timestamp_edit, timestamp_created, published, 
							source, visible, source_system, source_key, rights, type, 
							coverage, relation, creator, contributor, publisher )
						select id, version, parent_version, language, title, description, 
							owner, editor, timestamp_edit, timestamp_created, published, 
							source, visible, source_system, source_key, rights, type, 
							coverage, relation, creator, contributor, publisher
							from lf_media where id = NEW.id and version = @latest_pub_version;
				end if;
			end if;
		end if;
    END;$$


USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`delete_latest_version` $$
USE `lernfunk3`$$


CREATE TRIGGER delete_latest_version AFTER DELETE ON lf_media
    FOR EACH ROW
    BEGIN
		/**
		 * We have to check if the deleted version is in lf_latest_media 
		 * or lf_latest_published_media
		 **/
		if exists( (select version from lf_latest_published_media 
				where id = OLD.id and version = OLD.version) ) then
			/** 
			 * We know now that the data in lf_latest_published_media is invalid.
			 * So we remove the invalid data set.
			 **/
			delete from lf_latest_published_media where id = OLD.id and language = OLD.language;
			/* Now we check if there is a new published version: */
			if exists( (select version from lf_media where id = OLD.id and language = OLD.language and published) ) then
				/* Ok, there is a published version. So get the version id: */
				set @latest_pub_version = (select max(version) from lf_media where id = OLD.id 
					and language = OLD.language and published);
				/* Insert latest published version: */
				insert into lf_latest_published_media 
					( id, version, parent_version, language, title, description, 
						owner, editor, timestamp_edit, timestamp_created, published, 
						source, visible, source_system, source_key, rights, type, 
						coverage, relation, creator, contributor, publisher )
					select id, version, parent_version, language, title, description, 
						owner, editor, timestamp_edit, timestamp_created, published, 
						source, visible, source_system, source_key, rights, type, 
						coverage, relation, creator, contributor, publisher
						from lf_media where id = OLD.id and version = @latest_pub_version;
			end if;
		end if;
		
		if exists( (select version from lf_latest_media 
				where id = OLD.id and version = OLD.version) ) then
			/** 
			 * We know now that the data in lf_latest_media is invalid.
			 * So we remove the invalid data set.
			 **/
			delete from lf_latest_media where id = OLD.id and language = OLD.language;
			/* Now we check if there is a new published version: */
			if exists( (select version from lf_media 
					where id = OLD.id and language = OLD.language) ) then
				/* Ok, there is a published version. So get the version id: */
				set @latest_pub_version = (select max(version) from lf_media 
						where id = OLD.id and language = OLD.language);
				/* Insert latest version: */
				insert into lf_latest_media 
					( id, version, parent_version, language, title, description, 
						owner, editor, timestamp_edit, timestamp_created, published, 
						source, visible, source_system, source_key, rights, type, 
						coverage, relation, creator, contributor, publisher )
					select id, version, parent_version, language, title, description, 
						owner, editor, timestamp_edit, timestamp_created, published, 
						source, visible, source_system, source_key, rights, type, 
						coverage, relation, creator, contributor, publisher
						from lf_media where id = OLD.id and version = @latest_pub_version;
			end if;
		end if;
    END;$$


DELIMITER ;

DELIMITER $$

USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`prevent_insert` $$
USE `lernfunk3`$$


CREATE TRIGGER prevent_insert BEFORE UPDATE ON lf_prepared_file
    FOR EACH ROW
    BEGIN
        SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'Updates on this table are forbidden.';
    END;$$


DELIMITER ;

DELIMITER $$

USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`series_default_values` $$
USE `lernfunk3`$$




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


DELIMITER ;

DELIMITER $$

USE `lernfunk3`$$
DROP TRIGGER IF EXISTS `lernfunk3`.`series_default_values` $$
USE `lernfunk3`$$




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


DELIMITER ;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
