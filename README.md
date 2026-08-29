# 🏥 HOS-LAB-ERA

<p align="center">
  <strong>An Intelligent, Secure & Blockchain-Verified Hospital Laboratory Management System</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Django-6.x-green?logo=django" alt="Django">
  <img src="https://img.shields.io/badge/Database-SQLite3-blue?logo=sqlite" alt="SQLite">
  <img src="https://img.shields.io/badge/AI-Integrated-purple" alt="AI Integrated">
  <img src="https://img.shields.io/badge/Security-SHA--256%20Blockchain-black" alt="Blockchain Verified">
</p>

---

## 📌 Executive Overview

**Hos-Lab-Era** is a full-stack web application designed to digitize clinical laboratory operations. Built on the **Django framework**, the platform transitions traditional paper workflows into a unified digital portal managing online test booking, payment processing, diagnostic verification, dynamic PDF generation, and automated patient alerts.

To advance digital health integrity, Hos-Lab-Era incorporates **SHA-256 cryptographic blockchain hashing** to prevent report tampering, alongside an **integrated AI Assistant** that translates complex lab parameters into plain-language explanations directly inside the patient portal.

---

## 🌟 Core Highlights

* **⛓️ Cryptographic Record Verification**: Laboratory PDFs are sealed using SHA-256 hashes and verifiable QR codes, providing immediate validation against unauthorized record alterations.
* **🤖 Integrated AI Diagnostic Explanation**: Features an in-dashboard "Ask AI" module allowing patients to query test results (e.g., flag meanings and reference ranges) in real time.
* **📄 Automated Digital Reporting**: Generates official clinical diagnostic reports on demand with live processing status updates.
* **💳 Seamless Financial & Email Workflows**: Full lifecycle management handling online service bookings, status tracking, transaction logging, and email triggers.
* **🔐 Role-Based Access Control (RBAC)**: Enforces segregated views and permissions for **Patients**, **Pathology Staff**, and **System Administrators**.

---

## 👥 User Roles & Access Hierarchy

### 👤 Patient Portal
* Browse laboratory test services and schedule appointments online.
* Process test payments and track real-time processing statuses.
* Access certified PDF reports and consult the **Ask AI** assistant for test interpretations.

### 🧑‍⚕️ Pathologist & Laboratory Staff
* Manage patient queue requests and process diagnostic samples.
* Input parameter test results, flag clinical deviations, and verify final findings.
* Sign off on digital laboratory reports to generate tamper-resistant cryptographic records.

### 👨‍💼 System Administrator
* Maintain user authentication roles, service costs, and database entries.
* Oversee transaction logs, system performance metrics, and application configurations.

---

## 🛠️ Technology Stack

| Domain | Technology |
| :--- | :--- |
| **Language** | Python 3.x |
| **Backend Framework** | Django 6.x |
| **Frontend** | HTML5, CSS3, JavaScript (Flexbox/CSS Grid Layouts) |
| **Database** | SQLite3 (Development) / PostgreSQL Ready |
| **Security Integrity** | SHA-256 Cryptographic Hashing & Verification QR Generation |
| **AI Integration** | Context-Aware Diagnostic Explanation Engine |
| **Notifications** | Django Core Email Subsystem |

---

## ⚡ Quickstart Setup

### 1. Clone & Setup Environment

```bash
git clone [https://github.com/YOUR-USERNAME/Hos-Lab-Era.git](https://github.com/YOUR-USERNAME/Hos-Lab-Era.git)
cd Hos-Lab-Era

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate


 # 2. Install Dependencies & Migrate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate

# 3. Initialize Superuser & Run Server
python manage.py createsuperuser
python manage.py runserver
Navigate to http://127.0.0.1:8000/ in your browser.

# 🔧 Environment Configuration
Create a .env file in the root project folder:
SECRET_KEY=your-custom-django-secret-key
DEBUG=True

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

PAYMENT_API_KEY=your-payment-api-key
Security Note: Never commit your active .env file or private credentials to GitHub repositories.

# 📊 Current Development Status
ModuleStatusUser Authentication & RBAC✅ CompleteTest Booking & Queue Management✅ CompletePayment Workflow & History✅ CompleteAutomated Email Notifications✅ CompleteDigital PDF Report Generator✅ CompleteSHA-256 Blockchain Integrity Seal✅ CompleteAsk AI Diagnostic Assistant✅ Complete

--- 

#👩‍💻 Author
Asha Giri
Komal Basnet

IT Engineering Student | Python & Django Developer

Nepal College of Information Technology (NCIT)