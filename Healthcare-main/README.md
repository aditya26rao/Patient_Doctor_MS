# Healthcare
# 🏥 Healthcare Appointment Booking System

A fully functional and responsive web application built with **Django** that allows patients to book appointments with doctors. Admins can manage doctors, patients, and view analytics, while users receive appointment email confirmations and can download appointment summaries as PDFs.

---

## 🚀 Features

- 👨‍⚕️ User Roles: Admin, Doctor, Patient
- 🔐 Authentication: Register/Login with role selection
- 📅 Book Appointments with doctors
- 📧 Email reminders to doctors on appointment booking
- 🧾 PDF Appointment Summaries (generated using xhtml2pdf)
- 📊 Admin Dashboard with Analytics (Chart.js)
- 🌐 Responsive UI using Bootstrap 5
- 🛡️ Role-based Dashboard (Doctor vs Patient)

---

## 🖼️ Screenshots

> _Add your own screenshots here if you'd like_

---

## 📁 Tech Stack

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS, Bootstrap
- **Database**: SQLite (default)
- **Other Libraries**:
  - `crispy-bootstrap4` – for beautiful forms
  - `xhtml2pdf` – to generate PDFs
  - `Chart.js` – for admin analytics

---

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/healthcare-booking-system.git
cd healthcare-booking-system


python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt

## Email Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_app_password'

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
