CREATE DATABASE IF NOT EXISTS testdb;
USE testdb;

DROP TABLE IF EXISTS dogs;
CREATE TABLE dogs (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255),
    `age` INT,
    `gender` VARCHAR(255),
    `breed` VARCHAR(255),
    `dob` DATETIME
);

INSERT INTO dogs (`name`, `age`, `gender`, `breed`, `dob`) VALUES
    ('rocky', 4, 'male', 'german shepherd', '2025-01-15'),
    ('fifi', 5, 'female', 'german shepherd', '2023-09-09'),
    ('baaron', 6, 'male', NULL, '2017-07-31')
;