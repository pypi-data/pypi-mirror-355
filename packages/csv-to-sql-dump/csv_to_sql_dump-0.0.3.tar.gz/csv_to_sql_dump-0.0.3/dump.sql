DROP DATABASE IF EXISTS testdb;
CREATE DATABASE testdb;
USE testdb;

CREATE TABLE dogs (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255),
    `age` INT,
    `gender` VARCHAR(255),
    `breed` VARCHAR(255),
    `dob` DATETIME
);

INSERT INTO dogs (`name`, `age`, `gender`, `breed`, `dob`) VALUES ('rocky', 4, 'male', 'german shepherd', Timestamp('2025-01-15 00:00:00'));
INSERT INTO dogs (`name`, `age`, `gender`, `breed`, `dob`) VALUES ('fifi', 5, 'female', 'german shepherd', Timestamp('2023-09-09 00:00:00'));
INSERT INTO dogs (`name`, `age`, `gender`, `breed`, `dob`) VALUES ('baaron', 6, 'male', 'german shepherd', Timestamp('2017-07-31 00:00:00'));