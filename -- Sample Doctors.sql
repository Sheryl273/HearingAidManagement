-- Sample Doctors
INSERT IGNORE INTO Doctor (name, specialization, phone, email) VALUES
('Dr. Sarah Johnson', 'Audiology', '555-0101', 'sarah.j@clinic.com'),
('Dr. Michael Chen', 'Hearing Specialist', '555-0102', 'michael.c@clinic.com'),
('Dr. Emily Rodriguez', 'Pediatric Audiology', '555-0103', 'emily.r@clinic.com');

-- Sample Manufacturers
INSERT IGNORE INTO Manufacturer (manufacturer_name, country, contact_info) VALUES
('Phonak', 'Switzerland', 'contact@phonak.com'),
('Oticon', 'Denmark', 'info@oticon.com'),
('Widex', 'Denmark', 'support@widex.com'),
('Siemens', 'Germany', 'hearing@siemens.com'),
('Resound', 'Denmark', 'info@resound.com');
