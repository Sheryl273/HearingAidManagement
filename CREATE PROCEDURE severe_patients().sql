CREATE PROCEDURE severe_patients()
BEGIN
DECLARE done INT DEFAULT FALSE;
DECLARE p_name VARCHAR(100);
DECLARE l_ear INT;

DECLARE patient_cursor CURSOR FOR
SELECT p.name, h.left_ear
FROM Patient p
JOIN HearingTest h
ON p.patient_id = h.patient_id;

DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

OPEN patient_cursor;

read_loop: LOOP
FETCH patient_cursor INTO p_name, l_ear;

IF done THEN
LEAVE read_loop;
END IF;

IF l_ear > 70 THEN
SELECT p_name AS Severe_Hearing_Loss;
END IF;

END LOOP;

CLOSE patient_cursor;

END;
CALL severe_patients();
