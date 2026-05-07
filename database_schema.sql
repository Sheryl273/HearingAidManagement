-- Hearing Clinic Management System Database Schema
-- Run this script to create/update the database structure

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS hearing_aid_dbms;
USE hearing_aid_dbms;

-- Patient table
CREATE TABLE IF NOT EXISTS Patient (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(50) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HearingAid table with stock column
CREATE TABLE IF NOT EXISTS HearingAid (
    aid_id INT AUTO_INCREMENT PRIMARY KEY,
    model VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HearingTest table
CREATE TABLE IF NOT EXISTS HearingTest (
    test_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    left_ear INT NOT NULL,
    right_ear INT NOT NULL,
    test_date DATE NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id)
);

-- Fitting table
CREATE TABLE IF NOT EXISTS Fitting (
    fitting_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    aid_id INT NOT NULL,
    fitting_date DATE NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id),
    FOREIGN KEY (aid_id) REFERENCES HearingAid(aid_id)
);

-- Add stock column to HearingAid table if it doesn't exist
ALTER TABLE HearingAid 
ADD COLUMN IF NOT EXISTS stock INT DEFAULT 0;

-- Insert sample data (optional)
INSERT IGNORE INTO Patient (name, age, gender, phone) VALUES
('John Smith', 65, 'Male', '555-0101'),
('Mary Johnson', 58, 'Female', '555-0102'),
('Robert Davis', 72, 'Male', '555-0103');

INSERT IGNORE INTO HearingAid (model, type, price, stock) VALUES
('Phonak Audéo Paradise', 'BTE', 2499.99, 5),
('Oticon More', 'RITE', 2299.99, 3),
('Widex Moment', 'ITE', 1999.99, 7);
