USE hearing_aid_dbms;

-- Add manufacturer_id to HearingAid table (if not exists)
ALTER TABLE HearingAid 
ADD COLUMN manufacturer_id INT;

-- Add foreign key for manufacturer_id
ALTER TABLE HearingAid 
ADD FOREIGN KEY (manufacturer_id) REFERENCES Manufacturer(manufacturer_id);

-- Add doctor_id to HearingTest table (if not exists)
ALTER TABLE HearingTest 
ADD COLUMN doctor_id INT;

-- Add foreign key for doctor_id
ALTER TABLE HearingTest 
ADD FOREIGN KEY (doctor_id) REFERENCES Doctor(doctor_id);

-- Add doctor_id to Fitting table (if not exists)
ALTER TABLE Fitting 
ADD COLUMN doctor_id INT;

-- Add foreign key for doctor_id
ALTER TABLE Fitting 
ADD FOREIGN KEY (doctor_id) REFERENCES Doctor(doctor_id);
