# Wildfire Health Monitoring App

## 📖 Overview
The **Wildfire Health Monitoring App** is a Flask‑based web application designed to support supervisors and incident controllers in monitoring personnel health during wildfire operations. It provides real‑time dashboards, alerts, and reporting tools to ensure safety and resource management across multiple firegrounds.

---

## 🚀 Features
- **Dashboard**: Displays personnel and their latest vitals with evaluated status (Normal, Borderline, Critical).  
- **Alerts View**: Highlights personnel with critical or borderline readings.  
- **Forms & CSV Uploads**: Add personnel and vitals individually or via bulk CSV uploads.  
- **Reports**: Download CSV reports for:
  - Full roster  
  - Alerts only  
  - Individual personnel history  
- **Dynamic Firegrounds** *(planned)*: Assign personnel to firegrounds and filter dashboards/reports by location.  
- **Roles Management** *(planned)*: Dropdown list for roles with ability to add new roles dynamically.  
- **Security** *(planned)*: Authentication, input validation, and environment‑based secrets.  
- **Branding** *(planned)*: Professional header/footer, organizational identity, and consistent styling.

---

## 🛠 Tech Stack
- **Backend**: Flask (Python)  
- **Database**: SQLite (prototype), PostgreSQL (planned for multi‑fireground support)  
- **ORM**: SQLAlchemy  
- **Deployment**: Render (Gunicorn WSGI server)  
- **Frontend**: Jinja2 templates, Bootstrap (planned for styling)

---

## ⚙️ Setup Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/wildfire-health-monitoring.git
   cd wildfire-health-monitoring
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run locally:
   ```bash
   flask run
   ```
   or
   ```bash
   gunicorn app:app
   ```
4. Deploy to Render:
   - Set **Start Command** to:
     ```
     gunicorn app:app
     ```
   - Add environment variables (`SECRET_KEY`, database URL, etc.).

---

## 📊 Database Models
- **Personnel**: name, age, role, fireground assignment.  
- **Vitals**: systolic, diastolic, heart rate, temperature, status, timestamp.  
- **Role** *(planned)*: predefined or user‑added roles.  
- **FireGround** *(planned)*: fireground name, location, status.

---

## 🧭 Roadmap
- 🔒 **Security**: Authentication and input validation.  
- 💓 **Vitals Expansion**: Separate systolic/diastolic fields.  
- 📋 **Roles Dropdown**: Dynamic role management.  
- 🌏 **FireGround Filtering**: Multi‑fireground support with ICC dashboard.  
- 🎨 **Branding**: Improved UI/UX with organizational identity.  
- 🗄️ **Database Migration**: Transition from SQLite to PostgreSQL for scalability.

---

## 👥 Intended Users
- **Fireground Supervisors**: Monitor personnel health at their assigned fireground.  
- **Incident Controllers (ICC)**: View aggregated health data across all firegrounds, filter by location, and generate reports for resource planning.

---

## 📌 Status
This is a **prototype** currently deployed on Render for supervisor review. Feedback will guide further development and refinement.

---
