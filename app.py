import os
import csv
import io
from dateutil import parser
from flask import Flask, render_template, request, redirect, url_for, Response, flash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

# --- Flask setup ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///personnel.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "change-this-in-production"

db = SQLAlchemy(app)

# --- Database models ---
class Personnel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), index=True)
    role = db.Column(db.String(120))
    dob = db.Column(db.Date, nullable=True)
    agency = db.Column(db.String(120))
    vitals = db.relationship("Vitals", backref="personnel", lazy=True)

class Vitals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    personnel_id = db.Column(db.Integer, db.ForeignKey("personnel.id"))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    heart_rate = db.Column(db.Integer, nullable=True)
    blood_pressure = db.Column(db.String(20), nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    spo2 = db.Column(db.Integer, nullable=True)
    carboxyhemoglobin = db.Column(db.Float, nullable=True)

# --- Status and alerts logic ---
def evaluate_status(vitals):
    if not vitals:
        return "normal", []
    messages = []
    severity = "normal"

    if vitals.heart_rate is not None:
        if vitals.heart_rate < 55 or vitals.heart_rate > 110:
            messages.append(f"Critical heart rate: {vitals.heart_rate} bpm")
            severity = "alert"
        elif vitals.heart_rate < 60 or vitals.heart_rate > 100:
            messages.append(f"Borderline heart rate: {vitals.heart_rate} bpm")
            severity = "warning" if severity != "alert" else severity

    if vitals.blood_pressure:
        try:
            systolic, diastolic = map(int, vitals.blood_pressure.split("/"))
            if systolic < 95 or systolic > 160 or diastolic < 55 or diastolic > 100:
                messages.append(f"Critical blood pressure: {vitals.blood_pressure}")
                severity = "alert"
            elif systolic < 100 or systolic > 140 or diastolic < 60 or diastolic > 90:
                messages.append(f"Borderline blood pressure: {vitals.blood_pressure}")
                severity = "warning" if severity != "alert" else severity
        except Exception:
            messages.append(f"Invalid blood pressure format: {vitals.blood_pressure}")
            severity = "warning" if severity != "alert" else severity

    if vitals.temperature is not None:
        if vitals.temperature < 35.5 or vitals.temperature > 38.5:
            messages.append(f"Critical temperature: {vitals.temperature} °C")
            severity = "alert"
        elif vitals.temperature < 36.0 or vitals.temperature > 37.5:
            messages.append(f"Borderline temperature: {vitals.temperature} °C")
            severity = "warning" if severity != "alert" else severity

    if vitals.spo2 is not None:
        if vitals.spo2 < 90:
            messages.append(f"Critical SpO₂: {vitals.spo2}%")
            severity = "alert"
        elif vitals.spo2 < 94:
            messages.append(f"Borderline SpO₂: {vitals.spo2}%")
            severity = "warning" if severity != "alert" else severity

    if vitals.carboxyhemoglobin is not None:
        if vitals.carboxyhemoglobin > 10.0:
            messages.append(f"Critical Carboxyhemoglobin: {vitals.carboxyhemoglobin}%")
            severity = "alert"
        elif vitals.carboxyhemoglobin > 2.0:
            messages.append(f"Borderline Carboxyhemoglobin: {vitals.carboxyhemoglobin}%")
            severity = "warning" if severity != "alert" else severity

    return severity, messages

# --- Routes ---
@app.route("/")
def home():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    people = Personnel.query.all()
    dashboard_data = []
    for p in people:
        latest = p.vitals[-1] if p.vitals else None
        status, messages = evaluate_status(latest)
        dashboard_data.append({"person": p, "latest": latest, "status": status, "messages": messages})
    return render_template("dashboard.html", dashboard_data=dashboard_data)

@app.route("/alerts")
def alerts():
    people = Personnel.query.all()
    alerts_data = []
    for p in people:
        latest = p.vitals[-1] if p.vitals else None
        if not latest:
            continue
        status, messages = evaluate_status(latest)
        if status in ("alert", "warning"):
            alerts_data.append({"person": p, "latest": latest, "status": status, "alerts": messages})
    return render_template("alerts.html", alerts_data=alerts_data)

@app.route("/add_person", methods=["GET", "POST"])
def add_person():
    if request.method == "POST":
        name = request.form.get("name")
        role = request.form.get("role")
        agency = request.form.get("agency")
        dob = request.form.get("dob")
        dob_val = parser.parse(dob).date() if dob else None
        person = Personnel(name=name, role=role, agency=agency, dob=dob_val)
        db.session.add(person)
        db.session.commit()
        flash("Person added successfully", "success")
        return redirect(url_for("dashboard"))
    return render_template("add_person.html")

@app.route("/add_vitals/<int:person_id>", methods=["GET", "POST"])
def add_vitals(person_id):
    person = Personnel.query.get_or_404(person_id)
    if request.method == "POST":
        v = Vitals(
            personnel_id=person.id,
            heart_rate=int(request.form.get("heart_rate")) if request.form.get("heart_rate") else None,
            blood_pressure=request.form.get("blood_pressure") or None,
            temperature=float(request.form.get("temperature")) if request.form.get("temperature") else None,
            spo2=int(request.form.get("spo2")) if request.form.get("spo2") else None,
            carboxyhemoglobin=float(request.form.get("carboxyhemoglobin")) if request.form.get("carboxyhemoglobin") else None
        )
        db.session.add(v)
        db.session.commit()
        flash("Vitals recorded", "success")
        return redirect(url_for("view_vitals", person_id=person.id))
    return render_template("add_vitals.html", person=person)

@app.route("/view_vitals/<int:person_id>")
def view_vitals(person_id):
    person = Personnel.query.get_or_404(person_id)
    vitals = Vitals.query.filter_by(personnel_id=person.id).order_by(Vitals.timestamp.desc()).all()
    return render_template("view_vitals.html", person=person, vitals=vitals, evaluate_status=evaluate_status)

# --- Upload personnel ---
@app.route("/upload_personnel", methods=["GET", "POST"])
def upload_personnel():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename:
            flash("No file uploaded", "danger")
            return redirect(url_for("upload_personnel"))
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)
        with open(filepath, newline='', encoding="utf-8-sig") as csvfile:
            rows = list(csv.DictReader(csvfile))
        count = 0
        for row in rows:
            dob_val = None
            if row.get("dob"):
                try:
                    dob_val = parser.parse(row["dob"], dayfirst=True).date()
                except Exception:
                    dob_val = None
            person = Personnel(
                name=row.get("name", "").strip(),
                role=row.get("role", ""),
                dob=dob_val,
                agency=row.get("agency", "")
            )
            db.session.add(person)
            count += 1
        db.session.commit()
        flash(f"Uploaded {count} personnel records.", "success")
        return redirect(url_for("dashboard"))
    return render_template("upload_personnel.html")

# --- Upload vitals ---
@app.route("/upload_vitals", methods=["GET", "POST"])
def upload_vitals():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename:
            flash("No file uploaded", "danger")
            return redirect(url_for("upload_vitals"))

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)

        with open(filepath, newline='', encoding="utf-8-sig") as csvfile:
            rows = list(csv.DictReader(csvfile))

        added, skipped = 0, 0
        for row in rows:
            # Normalize keys and strip whitespace
            row = {k.lower().strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}

            # Find matching person by name
            person = Personnel.query.filter_by(name=row.get("name", "").strip()).first()
            if not person:
                skipped += 1
                continue

            # Parse timestamp safely
            ts = None
            if row.get("timestamp"):
                try:
                    ts = parser.parse(row["timestamp"])
                except Exception:
                    ts = None

            vitals = Vitals(
                personnel_id=person.id,
                heart_rate=int(row["heart_rate"]) if row.get("heart_rate") else None,
                blood_pressure=row.get("blood_pressure") if row.get("blood_pressure") else None,
                temperature=float(row["temperature"]) if row.get("temperature") else None,
                spo2=int(row["spo2"]) if row.get("spo2") else None,
                carboxyhemoglobin=float(row["carboxyhemoglobin"]) if row.get("carboxyhemoglobin") else None,
                timestamp=ts
            )
            db.session.add(vitals)
            added += 1

        db.session.commit()
        flash(f"Uploaded {added} vitals rows. Skipped {skipped} (no matching name).", "info")
        return redirect(url_for("dashboard"))

    return render_template("upload_vitals.html")


# --- CSV download: full roster ---
@app.route("/download_report")
def download_report():
    people = Personnel.query.all()
    output = io.StringIO()
    writer = csv.writer(output)

    header = ["Name","Role","Agency","Heart Rate","Blood Pressure","Temperature","SpO2","Carboxyhemoglobin","Status","Timestamp"]
    writer.writerow(header)

    for p in people:
        latest = p.vitals[-1] if p.vitals else None
        status, _ = evaluate_status(latest)
        writer.writerow([
            p.name or "",
            p.role or "",
            p.agency or "",
            latest.heart_rate if latest and latest.heart_rate is not None else "",
            latest.blood_pressure if latest and latest.blood_pressure else "",
            latest.temperature if latest and latest.temperature is not None else "",
            latest.spo2 if latest and latest.spo2 is not None else "",
            latest.carboxyhemoglobin if latest and latest.carboxyhemoglobin is not None else "",
            status if latest else "normal",
            latest.timestamp.isoformat() if latest and latest.timestamp else ""
        ])

    csv_data = output.getvalue()
    return Response(csv_data, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=report.csv"})


# --- CSV download: alerts only ---
@app.route("/download_alerts_report")
def download_alerts_report():
    people = Personnel.query.all()
    output = io.StringIO()
    writer = csv.writer(output)

    header = ["Name","Role","Agency","Heart Rate","Blood Pressure","Temperature","SpO2","Carboxyhemoglobin","Status","Alerts","Timestamp"]
    writer.writerow(header)

    for p in people:
        latest = p.vitals[-1] if p.vitals else None
        if not latest:
            continue
        status, messages = evaluate_status(latest)
        if status in ("alert", "warning"):
            writer.writerow([
                p.name or "",
                p.role or "",
                p.agency or "",
                latest.heart_rate if latest.heart_rate is not None else "",
                latest.blood_pressure if latest.blood_pressure else "",
                latest.temperature if latest.temperature is not None else "",
                latest.spo2 if latest.spo2 is not None else "",
                latest.carboxyhemoglobin if latest.carboxyhemoglobin is not None else "",
                status,
                "; ".join(messages),
                latest.timestamp.isoformat() if latest.timestamp else ""
            ])

    csv_data = output.getvalue()
    return Response(csv_data, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=alerts_report.csv"})


# --- CSV download: per-person history ---
@app.route("/download_person_report/<int:person_id>")
def download_person_report(person_id):
    person = Personnel.query.get_or_404(person_id)
    vitals_list = Vitals.query.filter_by(personnel_id=person.id).order_by(Vitals.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    header = ["Timestamp","Heart Rate","Blood Pressure","Temperature","SpO2","Carboxyhemoglobin","Status"]
    writer.writerow(header)

    for v in vitals_list:
        status, _ = evaluate_status(v)
        writer.writerow([
            v.timestamp.isoformat() if v.timestamp else "",
            v.heart_rate if v.heart_rate is not None else "",
            v.blood_pressure or "",
            v.temperature if v.temperature is not None else "",
            v.spo2 if v.spo2 is not None else "",
            v.carboxyhemoglobin if v.carboxyhemoglobin is not None else "",
            status
        ])

    csv_data = output.getvalue()
    filename = f"{person.name.replace(' ', '_')}_report.csv"
    return Response(csv_data, mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment;filename={filename}"})


# --- Run app ---
if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)


