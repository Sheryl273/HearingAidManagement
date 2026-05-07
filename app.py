from flask import Flask, render_template, request, redirect, jsonify, make_response, url_for
import mysql.connector
from config import MYSQL_CONFIG
from datetime import date, timedelta
import io, csv

app = Flask(__name__)

def get_db():
    return mysql.connector.connect(**MYSQL_CONFIG)

# helper: classify hearing loss by average dB
def classify_hearing(avg_db):
    try:
        avg = float(avg_db)
    except Exception:
        return 'Unknown'
    if avg <= 25:
        return 'Normal'
    if avg <= 40:
        return 'Mild'
    if avg <= 55:
        return 'Moderate'
    if avg <= 70:
        return 'Severe'
    return 'Profound'

# helper: patients needing follow-up (last test >6 months ago or never tested)
def get_followup_patients(cur):
    cur.execute("""
        SELECT p.patient_id, p.name, MAX(h.test_date) as last_test
        FROM Patient p
        LEFT JOIN HearingTest h ON p.patient_id = h.patient_id
        GROUP BY p.patient_id
        HAVING (last_test IS NULL OR last_test < DATE_SUB(CURDATE(), INTERVAL 6 MONTH))
    """)
    return cur.fetchall()

@app.route("/")
def dashboard():
    db = get_db()
    try:
        cur = db.cursor()
        # totals
        cur.execute("SELECT COUNT(*) FROM Patient")
        total_patients = cur.fetchone()[0] or 0

        # tests this week (last 7 days)
        cur.execute("SELECT COUNT(*) FROM HearingTest WHERE test_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)")
        tests_this_week = cur.fetchone()[0] or 0

        # tests this month
        cur.execute("SELECT COUNT(*) FROM HearingTest WHERE MONTH(test_date) = MONTH(CURDATE()) AND YEAR(test_date) = YEAR(CURDATE())")
        tests_this_month = cur.fetchone()[0] or 0

        # active fittings (last 30 days as a proxy)
        cur.execute("SELECT COUNT(*) FROM Fitting WHERE fitting_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)")
        active_fittings = cur.fetchone()[0] or 0

        # new statistics
        cur.execute("SELECT COUNT(*) FROM Doctor")
        total_doctors = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM Appointment WHERE appointment_date >= CURDATE() AND status = 'Scheduled'")
        upcoming_appointments = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM Payment WHERE status = 'Pending'")
        pending_payments = cur.fetchone()[0] or 0

        # recent activities: union of recent tests, fittings, and appointments (limit 8)
        cur.execute("""
            SELECT p.name, 'Hearing Test' as type, h.test_date as evt_date
            FROM HearingTest h
            JOIN Patient p ON h.patient_id = p.patient_id
            UNION ALL
            SELECT p.name, 'Fitting' as type, f.fitting_date as evt_date
            FROM Fitting f
            JOIN Patient p ON f.patient_id = p.patient_id
            UNION ALL
            SELECT p.name, 'Appointment' as type, a.appointment_date as evt_date
            FROM Appointment a
            JOIN Patient p ON a.patient_id = p.patient_id
            ORDER BY evt_date DESC
            LIMIT 8
        """)
        recent_activities = cur.fetchall()

        # patients preview
        cur.execute("SELECT patient_id, name, age FROM Patient ORDER BY patient_id DESC LIMIT 6")
        patients_preview = cur.fetchall()

        # upcoming appointments for dashboard
        cur.execute("""
            SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                   p.name as patient_name, d.name as doctor_name
            FROM Appointment a
            JOIN Patient p ON a.patient_id = p.patient_id
            JOIN Doctor d ON a.doctor_id = d.doctor_id
            WHERE a.appointment_date >= CURDATE() AND a.status = 'Scheduled'
            ORDER BY a.appointment_date, a.appointment_time
            LIMIT 5
        """)
        upcoming_appointments_list = cur.fetchall()

        # appointments per day last 7 days (from HearingTest)
        counts = []
        labels = []
        for i in range(6, -1, -1):
            d = date.today() - timedelta(days=i)
            labels.append(d.strftime('%a'))
            cur.execute("SELECT COUNT(*) FROM HearingTest WHERE test_date = %s", (d,))
            counts.append(cur.fetchone()[0] or 0)

        # most used hearing aid model
        cur.execute("""
            SELECT a.model, COUNT(*) as uses
            FROM Fitting f
            JOIN HearingAid a ON f.aid_id = a.aid_id
            GROUP BY a.aid_id
            ORDER BY uses DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        most_used_aid = {'model': row[0], 'uses': row[1]} if row else None

        # patients needing follow-up
        followups = get_followup_patients(cur)
        followup_count = len(followups)

    finally:
        db.close()

    return render_template(
        "dashboard.html",
        total_patients=total_patients,
        tests_this_week=tests_this_week,
        tests_this_month=tests_this_month,
        active_fittings=active_fittings,
        total_doctors=total_doctors,
        upcoming_appointments=upcoming_appointments,
        pending_payments=pending_payments,
        recent_activities=recent_activities,
        patients_preview=patients_preview,
        upcoming_appointments_list=upcoming_appointments_list,
        chart_labels=labels,
        chart_counts=counts,
        most_used_aid=most_used_aid,
        followup_count=followup_count,
        followups=followups
    )

# ---------------- PATIENT ----------------
@app.route("/add_patient", methods=["GET","POST"])
def add_patient():
    if request.method == "POST":
        db = get_db()
        try:
            cur = db.cursor()
            name = request.form["name"].strip()
            age = int(request.form["age"])
            gender = request.form["gender"].strip()
            phone = request.form["phone"].strip()
            cur.execute(
                "INSERT INTO Patient (name,age,gender,phone) VALUES (%s,%s,%s,%s)",
                (name, age, gender, phone)
            )
            db.commit()
        finally:
            db.close()
        return redirect("/patients")
    return render_template("patient_add.html")

@app.route('/patients')
def patients():
    q = request.args.get('q', '').strip()
    db = get_db()
    try:
        cur = db.cursor()
        if q:
            cur.execute("SELECT * FROM Patient WHERE name LIKE %s ORDER BY name", ('%'+q+'%',))
        else:
            cur.execute("SELECT * FROM Patient")
        data = cur.fetchall()
    finally:
        db.close()
    return render_template("patient_list.html", patients=data)

# Edit patient
@app.route('/edit_patient/<int:pid>', methods=['GET','POST'])
def edit_patient(pid):
    db = get_db()
    try:
        cur = db.cursor()
        if request.method == 'POST':
            name = request.form['name'].strip()
            age = int(request.form['age'])
            gender = request.form['gender'].strip()
            phone = request.form['phone'].strip()
            cur.execute("UPDATE Patient SET name=%s, age=%s, gender=%s, phone=%s WHERE patient_id=%s",
                        (name, age, gender, phone, pid))
            db.commit()
            return redirect(url_for('patients'))
        cur.execute("SELECT patient_id, name, age, gender, phone FROM Patient WHERE patient_id=%s", (pid,))
        p = cur.fetchone()
    finally:
        db.close()
    if not p:
        return redirect(url_for('patients'))
    return render_template('patient_edit.html', patient=p)

# Delete patient
@app.route('/delete_patient/<int:pid>', methods=['POST'])
def delete_patient(pid):
    db = get_db()
    try:
        cur = db.cursor()
        cur.execute("DELETE FROM Patient WHERE patient_id=%s", (pid,))
        db.commit()
    finally:
        db.close()
    return redirect(url_for('patients'))

@app.route('/api/patients')
def api_patients():
    q = request.args.get('q', '').strip()
    db = get_db()
    try:
        cur = db.cursor()
        if q:
            cur.execute("SELECT patient_id, name FROM Patient WHERE name LIKE %s ORDER BY name LIMIT 20", ('%'+q+'%',))
        else:
            cur.execute("SELECT patient_id, name FROM Patient ORDER BY name LIMIT 50")
        rows = cur.fetchall()
        results = [{'id': r[0], 'name': r[1]} for r in rows]
    finally:
        db.close()
    return jsonify(results)

# ---------------- HEARING TEST ----------------
@app.route("/hearing_test", methods=["GET","POST"])
def hearing_test():
    db = get_db()
    try:
        cur = db.cursor()
        if request.method == "POST":
            patient_id = int(request.form["patient_id"])
            left_ear = int(request.form["left_ear"])
            right_ear = int(request.form["right_ear"])
            doctor_id = request.form.get("doctor_id")
            if doctor_id:
                doctor_id = int(doctor_id)
            cur.execute(
                "INSERT INTO HearingTest (patient_id,left_ear,right_ear,test_date,doctor_id) VALUES (%s,%s,%s,%s,%s)",
                (patient_id, left_ear, right_ear, date.today(), doctor_id)
            )
            db.commit()
        cur.execute("SELECT patient_id,name FROM Patient")
        patients = cur.fetchall()
        cur.execute("SELECT doctor_id,name FROM Doctor")
        doctors = cur.fetchall()
    finally:
        db.close()
    return render_template("hearing_test.html", patients=patients, doctors=doctors)

# ---------------- HEARING AID ----------------
@app.route("/hearing_aid", methods=["GET","POST"])
def hearing_aid():
    if request.method == "POST":
        db = get_db()
        try:
            cur = db.cursor()
            model = request.form["model"].strip()
            aid_type = request.form["type"].strip()
            price = float(request.form["price"])
            stock = int(request.form.get("stock", 0))
            manufacturer_id = request.form.get("manufacturer_id")
            if manufacturer_id:
                manufacturer_id = int(manufacturer_id)
            cur.execute(
                "INSERT INTO HearingAid (model,type,price,stock,manufacturer_id) VALUES (%s,%s,%s,%s,%s)",
                (model, aid_type, price, stock, manufacturer_id)
            )
            db.commit()
        finally:
            db.close()
    # Get manufacturers for form
    db = get_db()
    try:
        cur = db.cursor()
        cur.execute("SELECT manufacturer_id, manufacturer_name FROM Manufacturer ORDER BY manufacturer_name")
        manufacturers = cur.fetchall()
    finally:
        db.close()
    return render_template("hearing_aid.html", manufacturers=manufacturers)

# ---------------- FITTING ----------------
@app.route("/fitting", methods=["GET","POST"])
def fitting():
    db = get_db()
    try:
        cur = db.cursor()
        if request.method == "POST":
            patient_id = int(request.form["patient_id"])
            aid_id = int(request.form["aid_id"])
            doctor_id = request.form.get("doctor_id")
            if doctor_id:
                doctor_id = int(doctor_id)
            cur.execute(
                "INSERT INTO Fitting (patient_id,aid_id,fitting_date,doctor_id) VALUES (%s,%s,%s,%s)",
                (patient_id, aid_id, date.today(), doctor_id)
            )
            # decrement stock if available
            cur.execute("UPDATE HearingAid SET stock = stock - 1 WHERE aid_id=%s AND stock > 0", (aid_id,))
            db.commit()
        cur.execute("SELECT patient_id,name FROM Patient")
        patients = cur.fetchall()
        cur.execute("""
            SELECT ha.aid_id, ha.model, ha.stock, m.manufacturer_name
            FROM HearingAid ha
            LEFT JOIN Manufacturer m ON ha.manufacturer_id = m.manufacturer_id
        """)
        aids = cur.fetchall()
        cur.execute("SELECT doctor_id,name FROM Doctor")
        doctors = cur.fetchall()
    finally:
        db.close()
    return render_template("fitting.html", patients=patients, aids=aids, doctors=doctors)

# ---------------- REPORT ----------------
@app.route("/report")
def report():
    db = get_db()
    try:
        cur = db.cursor()
        # fetch latest test per patient and latest fitted model with doctor and manufacturer info
        cur.execute("""
            SELECT p.patient_id, p.name,
              (SELECT left_ear FROM HearingTest ht WHERE ht.patient_id = p.patient_id ORDER BY ht.test_date DESC LIMIT 1) as left_ear,
              (SELECT right_ear FROM HearingTest ht WHERE ht.patient_id = p.patient_id ORDER BY ht.test_date DESC LIMIT 1) as right_ear,
              (SELECT a.model FROM Fitting f JOIN HearingAid a ON f.aid_id = a.aid_id WHERE f.patient_id = p.patient_id ORDER BY f.fitting_date DESC LIMIT 1) as model,
              (SELECT m.manufacturer_name FROM Fitting f JOIN HearingAid a ON f.aid_id = a.aid_id JOIN Manufacturer m ON a.manufacturer_id = m.manufacturer_id WHERE f.patient_id = p.patient_id ORDER BY f.fitting_date DESC LIMIT 1) as manufacturer,
              (SELECT d.name FROM Fitting f JOIN Doctor d ON f.doctor_id = d.doctor_id WHERE f.patient_id = p.patient_id ORDER BY f.fitting_date DESC LIMIT 1) as doctor,
              (SELECT MAX(ht.test_date) FROM HearingTest ht WHERE ht.patient_id = p.patient_id) as last_test
            FROM Patient p
        """)
        rows = cur.fetchall()
        data = []
        for r in rows:
            left = r[2]
            right = r[3]
            avg = None
            if left is not None and right is not None:
                avg = (left + right) / 2.0
            classification = classify_hearing(avg) if avg is not None else 'Unknown'
            data.append((r[1], left, right, r[4], r[5], r[6], classification, r[7]))
    finally:
        db.close()
    return render_template("report.html", data=data)

# export report CSV
@app.route('/export_report')
def export_report():
    db = get_db()
    try:
        cur = db.cursor()
        cur.execute("""
            SELECT p.name,
              (SELECT left_ear FROM HearingTest ht WHERE ht.patient_id = p.patient_id ORDER BY ht.test_date DESC LIMIT 1) as left_ear,
              (SELECT right_ear FROM HearingTest ht WHERE ht.patient_id = p.patient_id ORDER BY ht.test_date DESC LIMIT 1) as right_ear,
              (SELECT a.model FROM Fitting f JOIN HearingAid a ON f.aid_id = a.aid_id WHERE f.patient_id = p.patient_id ORDER BY f.fitting_date DESC LIMIT 1) as model,
              (SELECT m.manufacturer_name FROM Fitting f JOIN HearingAid a ON f.aid_id = a.aid_id JOIN Manufacturer m ON a.manufacturer_id = m.manufacturer_id WHERE f.patient_id = p.patient_id ORDER BY f.fitting_date DESC LIMIT 1) as manufacturer,
              (SELECT d.name FROM Fitting f JOIN Doctor d ON f.doctor_id = d.doctor_id WHERE f.patient_id = p.patient_id ORDER BY f.fitting_date DESC LIMIT 1) as doctor,
              (SELECT MAX(ht.test_date) FROM HearingTest ht WHERE ht.patient_id = p.patient_id) as last_test
            FROM Patient p
        """)
        rows = cur.fetchall()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Patient','Left Ear','Right Ear','Hearing Aid','Manufacturer','Doctor','Classification','Last Test'])
        for r in rows:
            left = r[1]
            right = r[2]
            avg = (left + right)/2.0 if left is not None and right is not None else None
            classification = classify_hearing(avg) if avg is not None else 'Unknown'
            writer.writerow([r[0], left, right, r[3], r[4], r[5], classification, r[6]])
        csv_data = output.getvalue()
    finally:
        db.close()
    resp = make_response(csv_data)
    resp.headers['Content-Type'] = 'text/csv'
    resp.headers['Content-Disposition'] = 'attachment; filename=hearing_report.csv'
    return resp

# patient history
@app.route('/patient_history/<int:pid>')
def patient_history(pid):
    db = get_db()
    try:
        cur = db.cursor()
        cur.execute('SELECT patient_id, name FROM Patient WHERE patient_id=%s', (pid,))
        patient = cur.fetchone()
        if not patient:
            return redirect(url_for('patients'))
        cur.execute('SELECT left_ear, right_ear, test_date FROM HearingTest WHERE patient_id=%s ORDER BY test_date DESC', (pid,))
        tests = cur.fetchall()
        cur.execute('SELECT a.model, f.fitting_date FROM Fitting f JOIN HearingAid a ON f.aid_id = a.aid_id WHERE f.patient_id=%s ORDER BY f.fitting_date DESC', (pid,))
        fittings = cur.fetchall()
    finally:
        db.close()
    return render_template('patient_history.html', patient=patient, tests=tests, fittings=fittings)

# ---------------- APPOINTMENT ----------------
@app.route("/appointment", methods=["GET","POST"])
def appointment():
    db = get_db()
    try:
        cur = db.cursor()
        if request.method == "POST":
            patient_id = int(request.form["patient_id"])
            doctor_id = int(request.form["doctor_id"])
            appointment_date = request.form["appointment_date"]
            appointment_time = request.form["appointment_time"]
            notes = request.form.get("notes", "")
            cur.execute(
                "INSERT INTO Appointment (patient_id, doctor_id, appointment_date, appointment_time, notes) VALUES (%s,%s,%s,%s,%s)",
                (patient_id, doctor_id, appointment_date, appointment_time, notes)
            )
            db.commit()
        # Get data for forms
        cur.execute("SELECT patient_id, name FROM Patient")
        patients = cur.fetchall()
        cur.execute("SELECT doctor_id, name FROM Doctor")
        doctors = cur.fetchall()
        # Get appointments
        cur.execute("""
            SELECT a.appointment_id, a.appointment_date, a.appointment_time, a.status,
                   p.name as patient_name, d.name as doctor_name, a.notes
            FROM Appointment a
            JOIN Patient p ON a.patient_id = p.patient_id
            JOIN Doctor d ON a.doctor_id = d.doctor_id
            ORDER BY a.appointment_date, a.appointment_time
        """)
        appointments = cur.fetchall()
    finally:
        db.close()
    return render_template("appointment.html", patients=patients, doctors=doctors, appointments=appointments)

@app.route('/update_appointment_status/<int:aid>', methods=['POST'])
def update_appointment_status(aid):
    db = get_db()
    try:
        cur = db.cursor()
        status = request.form['status']
        cur.execute("UPDATE Appointment SET status=%s WHERE appointment_id=%s", (status, aid))
        db.commit()
    finally:
        db.close()
    return redirect(url_for('appointment'))

# ---------------- DOCTOR ----------------
@app.route("/doctor", methods=["GET","POST"])
def doctor():
    db = get_db()
    try:
        cur = db.cursor()
        if request.method == "POST":
            name = request.form["name"].strip()
            specialization = request.form["specialization"].strip()
            phone = request.form["phone"].strip()
            email = request.form["email"].strip()
            cur.execute(
                "INSERT INTO Doctor (name, specialization, phone, email) VALUES (%s,%s,%s,%s)",
                (name, specialization, phone, email)
            )
            db.commit()
        cur.execute("SELECT * FROM Doctor ORDER BY name")
        doctors = cur.fetchall()
    finally:
        db.close()
    return render_template("doctor.html", doctors=doctors)

# ---------------- MANUFACTURER ----------------
@app.route("/manufacturer", methods=["GET","POST"])
def manufacturer():
    db = get_db()
    try:
        cur = db.cursor()
        if request.method == "POST":
            manufacturer_name = request.form["manufacturer_name"].strip()
            country = request.form["country"].strip()
            contact_info = request.form["contact_info"].strip()
            cur.execute(
                "INSERT INTO Manufacturer (manufacturer_name, country, contact_info) VALUES (%s,%s,%s)",
                (manufacturer_name, country, contact_info)
            )
            db.commit()
        cur.execute("SELECT * FROM Manufacturer ORDER BY manufacturer_name")
        manufacturers = cur.fetchall()
    finally:
        db.close()
    return render_template("manufacturer.html", manufacturers=manufacturers)

# ---------------- PAYMENT ----------------
@app.route("/payment", methods=["GET","POST"])
def payment():
    db = get_db()
    try:
        cur = db.cursor()
        if request.method == "POST":
            patient_id = int(request.form["patient_id"])
            amount = float(request.form["amount"])
            payment_date = request.form["payment_date"]
            payment_method = request.form["payment_method"]
            status = request.form["status"]
            fitting_id = request.form.get("fitting_id")
            if fitting_id:
                fitting_id = int(fitting_id)
            notes = request.form.get("notes", "")
            cur.execute(
                "INSERT INTO Payment (patient_id, amount, payment_date, payment_method, status, fitting_id, notes) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (patient_id, amount, payment_date, payment_method, status, fitting_id, notes)
            )
            db.commit()
        # Get data for forms
        cur.execute("SELECT patient_id, name FROM Patient")
        patients = cur.fetchall()
        cur.execute("""
            SELECT f.fitting_id, p.name as patient_name, a.model as aid_model, f.fitting_date
            FROM Fitting f
            JOIN Patient p ON f.patient_id = p.patient_id
            JOIN HearingAid a ON f.aid_id = a.aid_id
            ORDER BY f.fitting_date DESC
        """)
        fittings = cur.fetchall()
        # Get payments
        cur.execute("""
            SELECT pa.payment_id, pa.amount, pa.payment_date, pa.payment_method, pa.status,
                   p.name as patient_name, a.model as aid_model, pa.notes
            FROM Payment pa
            JOIN Patient p ON pa.patient_id = p.patient_id
            LEFT JOIN Fitting f ON pa.fitting_id = f.fitting_id
            LEFT JOIN HearingAid a ON f.aid_id = a.aid_id
            ORDER BY pa.payment_date DESC
        """)
        payments = cur.fetchall()
    finally:
        db.close()
    return render_template("payment.html", patients=patients, fittings=fittings, payments=payments)

if __name__ == "__main__":
    app.run(debug=True)
