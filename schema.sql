create database manga_cafe;

use manga_cafe;

create table users(id int(8) AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(32),
    email VARCHAR(128),
    username VARCHAR(32),
    password VARCHAR(128),
    register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

create table article(id int AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(32),
    body VARCHAR(256),
    author VARCHAR(32),
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
