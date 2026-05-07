USE hearing_aid_dbms;

-- 1. Doctor / Audiologist Table
CREATE TABLE IF NOT EXISTS Doctor (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    specialization VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Manufacturer Table
CREATE TABLE IF NOT EXISTS Manufacturer (
    manufacturer_id INT AUTO_INCREMENT PRIMARY KEY,
    manufacturer_name VARCHAR(255) NOT NULL UNIQUE,
    country VARCHAR(100),
    contact_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Appointment Table
CREATE TABLE IF NOT EXISTS Appointment (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status ENUM('Scheduled','Completed','Cancelled') DEFAULT 'Scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES Doctor(doctor_id)
);

-- 4. Payment Table
CREATE TABLE IF NOT EXISTS Payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_method ENUM('Cash','Card','Online') NOT NULL,
    status ENUM('Paid','Pending') DEFAULT 'Pending',
    fitting_id INT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id),
    FOREIGN KEY (fitting_id) REFERENCES Fitting(fitting_id)
);


-- Insert sample Doctors
INSERT IGNORE INTO Doctor (name, specialization, phone, email) VALUES
('Dr. Sarah Johnson','Audiology','555-0101','sarah.j@clinic.com'),
('Dr. Michael Chen','Hearing Specialist','555-0102','michael.c@clinic.com'),
('Dr. Emily Rodriguez','Pediatric Audiology','555-0103','emily.r@clinic.com');

-- Insert sample Manufacturers
INSERT IGNORE INTO Manufacturer (manufacturer_name, country, contact_info) VALUES
('Phonak','Switzerland','contact@phonak.com'),
('Oticon','Denmark','info@oticon.com'),
('Widex','Denmark','support@widex.com'),
('Siemens','Germany','hearing@siemens.com'),
('Resound','Denmark','info@resound.com');

-- Update hearing aids with manufacturer IDs
UPDATE HearingAid SET manufacturer_id = 1 WHERE model LIKE '%Phonak%';
UPDATE HearingAid SET manufacturer_id = 2 WHERE model LIKE '%Oticon%';
UPDATE HearingAid SET manufacturer_id = 3 WHERE model LIKE '%Widex%';
UPDATE HearingAid SET manufacturer_id = 4 WHERE model LIKE '%Siemens%';
UPDATE HearingAid SET manufacturer_id = 5 WHERE model LIKE '%Resound%';

-- Sample Appointments
INSERT IGNORE INTO Appointment (patient_id, doctor_id, appointment_date, appointment_time, status, notes) VALUES
(1,1,'2024-01-20','10:00:00','Scheduled','Regular checkup'),
(2,2,'2024-01-21','14:30:00','Scheduled','Follow-up test'),
(3,3,'2024-01-22','09:00:00','Scheduled','Initial consultation');

-- Indexes for better performance
CREATE INDEX idx_appointment_date ON Appointment(appointment_date);
CREATE INDEX idx_payment_date ON Payment(payment_date);
CREATE INDEX idx_patient_appointments ON Appointment(patient_id);
CREATE INDEX idx_patient_payments ON Payment(patient_id);