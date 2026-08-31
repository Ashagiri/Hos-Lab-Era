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

**Hos-Lab-Era** is a full-stack web-based **Hospital Laboratory Management System** designed to digitize and streamline clinical laboratory operations.

The system transforms traditional paper-based laboratory workflows into a centralized digital platform for **online test booking, appointment management, payment processing, sample processing, diagnostic result management, digital report generation, email notifications, and secure report verification**.

To improve the integrity and security of medical reports, Hos-Lab-Era uses **SHA-256 cryptographic hashing with blockchain-inspired verification mechanisms** to detect unauthorized report modifications.

The platform also includes an **AI Assistant** that helps patients understand laboratory test parameters, abnormal flags, and reference ranges through simple, easy-to-understand explanations.

---

## 🌟 Key Features

### ⛓️ Secure Report Verification

* Generates a unique SHA-256 cryptographic hash for finalized laboratory reports.
* Provides QR-based report verification.
* Helps detect unauthorized modifications to generated reports.
* Provides an additional layer of trust and integrity for digital medical records.

### 🤖 AI Diagnostic Explanation Assistant

* Integrated **Ask AI** feature inside the patient dashboard.
* Helps patients understand laboratory parameters and report terminology.
* Explains abnormal/flagged values and reference ranges in simple language.
* Designed to improve patient understanding of laboratory reports.

> **Note:** The AI Assistant is intended for educational and informational purposes and does not replace professional medical diagnosis or consultation.

### 📄 Digital Laboratory Reports

* Automatically generates professional PDF laboratory reports.
* Provides digital access to finalized reports.
* Includes report verification information.
* Supports secure digital record management.

### 💳 Payment Management

* Supports online laboratory service payment workflows.
* Maintains transaction and payment history.
* Connects payment status with laboratory service processing.
* Helps reduce manual financial record management.

### 📧 Automated Email Notifications

* Sends automated email notifications for important laboratory workflow events.
* Provides patients with timely updates regarding their services and reports.
* Reduces the need for manual communication.

### 📅 Test Booking & Queue Management

* Allows patients to browse available laboratory tests.
* Supports online test booking and appointment scheduling.
* Manages patient requests and laboratory queues.
* Tracks the processing status of laboratory services.

### 🔐 Role-Based Access Control

The system provides separate access and functionality based on user roles:

* 👤 Patient
* 🧑‍⚕️ Pathologist / Laboratory Staff
* 👨‍💼 System Administrator

---

## 👥 User Roles & Access

### 👤 Patient

Patients can:

* Register and securely log into the system.
* Browse available laboratory tests and services.
* Book laboratory tests online.
* Make payments and view transaction history.
* Track test and report processing status.
* Access generated digital PDF reports.
* Verify report authenticity using the verification mechanism.
* Use the **Ask AI** assistant to understand laboratory parameters.

---

### 🧑‍⚕️ Pathologist & Laboratory Staff

Laboratory staff can:

* Manage patient test requests.
* View and manage laboratory queues.
* Process diagnostic samples.
* Enter laboratory test parameters and results.
* Identify abnormal or flagged results.
* Review and verify laboratory findings.
* Finalize digital laboratory reports.
* Generate cryptographically secured report records.

---

### 👨‍💼 System Administrator

Administrators can:

* Manage users and authentication.
* Manage user roles and permissions.
* Manage laboratory test services.
* Manage test pricing and system data.
* Monitor payment and transaction records.
* Manage application configurations.
* Oversee overall system operations.

---

## 🏗️ System Workflow

```text
                    ┌─────────────────────┐
                    │      Patient        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Test Selection    │
                    │   & Online Booking   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      Payment        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Laboratory Queue    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Sample Processing   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Result Entry &      │
                    │ Verification        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Digital PDF Report  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ SHA-256 Integrity   │
                    │ Hash + Verification │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Patient Dashboard   │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
             ┌──────────────┐     ┌──────────────┐
             │ PDF Report   │     │   Ask AI     │
             │ Verification │     │  Assistant   │
             └──────────────┘     └──────────────┘
```

---

## 🛠️ Technology Stack

| Domain                   | Technology                          |
| ------------------------ | ----------------------------------- |
| **Programming Language** | Python 3.x                          |
| **Backend Framework**    | Django 6.x                          |
| **Frontend**             | HTML5, CSS3, JavaScript             |
| **UI Layout**            | Flexbox / CSS Grid                  |
| **Database**             | SQLite3                             |
| **Production Database**  | PostgreSQL Ready                    |
| **Report Generation**    | Dynamic PDF Generation              |
| **Security & Integrity** | SHA-256 Cryptographic Hashing       |
| **Report Verification**  | QR Code Verification                |
| **AI Integration**       | AI Diagnostic Explanation Assistant |
| **Notifications**        | Django Email System                 |
| **Authentication**       | Django Authentication & RBAC        |

---

## 🔒 Security & Data Integrity

Hos-Lab-Era is designed with security and data integrity as important components of the system.

### Security mechanisms include:

* 🔐 Django authentication
* 👥 Role-Based Access Control (RBAC)
* 🔑 Secure password handling
* 🛡️ SHA-256 cryptographic hashing
* ⛓️ Blockchain-inspired report integrity verification
* 📱 QR-based report verification
* 🔒 Environment-based secret configuration
* 🚫 Protection of sensitive credentials through `.env`

The SHA-256 hash generated from a finalized report can be used to verify whether the report content has been modified after generation.

---

## 📄 Digital Report Verification

The report verification workflow follows these general steps:

```text
Laboratory Result
       ↓
Report Generation
       ↓
SHA-256 Hash Generation
       ↓
Hash Associated With Report
       ↓
QR Verification Information
       ↓
Digital Report Delivered
       ↓
User Scans / Verifies Report
       ↓
Hash Validation
       ↓
Authenticity / Modification Status
```

---

## 🤖 AI Assistant

The integrated **Ask AI** feature provides patients with understandable explanations of laboratory report information.

### Example questions:

```text
What does this test measure?

Why is this value marked high?

What is the normal reference range?

What does this laboratory parameter mean?
```

The assistant is designed to make technical laboratory information easier for patients to understand.

> ⚠️ **Medical Disclaimer:** AI-generated explanations are informational only and should not be considered a medical diagnosis. Patients should consult qualified healthcare professionals for medical advice.

---

## 📧 Automated Email Notifications

Hos-Lab-Era includes automated email communication for important workflow events.

Possible notification events include:

* ✅ Booking confirmation
* 💳 Payment confirmation
* 🧪 Laboratory processing updates
* 📄 Report availability
* 🔔 Important service notifications

---

## 💳 Payment Workflow

```text
Patient
   ↓
Select Laboratory Test
   ↓
Book Appointment
   ↓
Payment Processing
   ↓
Transaction Recorded
   ↓
Payment Confirmation
   ↓
Laboratory Processing
   ↓
Report Generation
```

Payment records are maintained to support transaction tracking and laboratory service management.

---

## 📊 Current Development Status

| Module                        |   Status   |
| ----------------------------- | :--------: |
| Authentication & RBAC         | ✅ Complete |
| Patient Management            | ✅ Complete |
| Test Booking                  | ✅ Complete |
| Queue Management              | ✅ Complete |
| Payment Workflow              | ✅ Complete |
| Payment History               | ✅ Complete |
| Automated Email Notifications | ✅ Complete |
| Digital PDF Report Generator  | ✅ Complete |
| SHA-256 Report Integrity Seal | ✅ Complete |
| QR-Based Report Verification  | ✅ Complete |
| Ask AI Diagnostic Assistant   | ✅ Complete |

---

## ⚡ Quick Start

### 1. Clone the Repository

```bash
<<<<<<< HEAD
git clone [https://github.com/YOUR-USERNAME/Hos-Lab-Era.git](https://github.com/YOUR-USERNAME/Hos-Lab-Era.git)
=======
git clone https://github.com/YOUR-USERNAME/Hos-Lab-Era.git
>>>>>>> cf5f37116c8f270a43372a6ea0232ae7529e8e0e
cd Hos-Lab-Era
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / macOS

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a Superuser

```bash
python manage.py createsuperuser
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

Open the application in your browser:

```text
http://127.0.0.1:8000/
```

---

## 🔧 Environment Configuration

Create a `.env` file in the root directory of the project.

```env
SECRET_KEY=your-custom-django-secret-key
DEBUG=True

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

PAYMENT_API_KEY=your-payment-api-key
```

<<<<<<< HEAD
# 📊 Current Development Status
ModuleStatusUser Authentication & RBAC✅ CompleteTest Booking & Queue Management✅ CompletePayment Workflow & History✅ CompleteAutomated Email Notifications✅ CompleteDigital PDF Report Generator✅ CompleteSHA-256 Blockchain Integrity Seal✅ CompleteAsk AI Diagnostic Assistant✅ Complete
=======
### ⚠️ Security Note

**Never commit your ****.env**** file, API keys, passwords, secret keys, or other private credentials to GitHub.**

Add `.env` to your `.gitignore` file:

```gitignore
.env
venv/
__pycache__/
*.pyc
db.sqlite3
```

---

## 📁 Suggested Project Structure

```text
Hos-Lab-Era/
│
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
├── db.sqlite3
│
├── project/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── authentication/
│   ├── patients/
│   ├── laboratory/
│   ├── payments/
│   ├── reports/
│   ├── notifications/
│   └── ai_assistant/
│
├── templates/
├── static/
├── media/
└── README.md
```

> The exact folder structure may vary depending on the implementation of the project.

---

## 🚀 Future Enhancements

Hos-Lab-Era is designed to support future technologies and advanced healthcare features.

Planned enhancements include:

* 🤖 Advanced AI-powered laboratory report analysis
* ⛓️ Expanded blockchain-based medical record verification
* ☁️ Cloud deployment and scalable infrastructure
* 🗄️ Distributed database architecture
* 📱 Mobile application
* 🔔 Real-time notifications
* 📊 Advanced laboratory analytics and dashboards
* 🔐 Enhanced security and audit logging
* 🧠 Machine Learning-based health insights
* 🔗 Interoperability with external healthcare systems

---

## 🎯 Project Objectives

The main objectives of Hos-Lab-Era are to:

1. Digitize traditional laboratory management processes.
2. Reduce paperwork and manual record management.
3. Improve laboratory workflow efficiency.
4. Provide patients with convenient online test booking.
5. Simplify payment and transaction management.
6. Provide secure digital laboratory reports.
7. Improve medical report integrity and verification.
8. Provide understandable laboratory information through AI.
9. Improve communication through automated notifications.
10. Build a foundation for future intelligent healthcare technologies.

---

## 🌍 Impact

Hos-Lab-Era aims to contribute toward a more **digital, efficient, secure, and patient-friendly laboratory environment**.

By combining:

**Django + Digital Healthcare + Secure Reports + AI + Cryptographic Verification**

the project provides a foundation for modernizing traditional laboratory management workflows.
>>>>>>> cf5f37116c8f270a43372a6ea0232ae7529e8e0e

--- 

<<<<<<< HEAD
#👩‍💻 Author
Asha Giri
Komal Basnet
=======
## 👩‍💻 Authors
>>>>>>> cf5f37116c8f270a43372a6ea0232ae7529e8e0e

### Asha Giri

<<<<<<< HEAD
Nepal College of Information Technology (NCIT)
=======
**IT Engineering Student | Python & Django Developer**

### Komal Basnet

**IT Engineering Student**

**Nepal College of Information Technology (NCIT)**

---

## ⭐ Support the Project

If you find **Hos-Lab-Era** useful or interesting, consider giving the repository a ⭐ on GitHub.

---

<p align="center">
  <strong>🏥 Hos-Lab-Era — Building a Smarter, Safer & More Digital Laboratory Experience</strong>
</p>
>>>>>>> cf5f37116c8f270a43372a6ea0232ae7529e8e0e
