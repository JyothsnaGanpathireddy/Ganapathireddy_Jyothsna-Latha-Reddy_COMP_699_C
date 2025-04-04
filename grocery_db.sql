-- table for users

CREATE TABLE users (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NULL,
    email VARCHAR(100) UNIQUE NULL,
    number VARCHAR(20) UNIQUE NULL,
    password VARCHAR(255) NULL
);