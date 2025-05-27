CREATE DATABASE beautysyncpro;
USE beautysyncpro;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE vendors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE salons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vendor_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);

CREATE TABLE bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    services TEXT NOT NULL,
    booking_date DATE NOT NULL,
    details TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Sample salon data
INSERT INTO vendors (name, email, password) VALUES 
('Vendor1', 'vendor1@example.com', 'password123');
INSERT INTO salons (vendor_id, name, location) VALUES 
(1, 'BeautyBliss Spa', 'Mumbai'),
(1, 'Lookz Salon', 'Mumbai'),
(1, 'GlowUp Studio', 'Mumbai');