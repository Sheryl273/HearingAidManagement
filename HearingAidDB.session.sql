CREATE TABLE IF NOT EXISTS Patient (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    age INT,
    gender VARCHAR(10),
    phone VARCHAR(15)
);

CREATE TABLE IF NOT EXISTS HearingTest (
    test_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    left_ear INT,
    right_ear INT,
    test_date DATE,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id)
);

CREATE TABLE IF NOT EXISTS HearingAid (
    aid_id INT AUTO_INCREMENT PRIMARY KEY,
    model VARCHAR(50),
    type VARCHAR(20),
    price DECIMAL(10,2)
);

CREATE TABLE IF NOT EXISTS Fitting (
    fitting_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    aid_id INT,
    fitting_date DATE,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id),
    FOREIGN KEY (aid_id) REFERENCES HearingAid(aid_id)
);
