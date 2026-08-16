# 🏥 Hos-Lab-Era

## Hospital Laboratory Management System

<p align="center">
  <strong>A secure, digital, and scalable Hospital Laboratory Management System built with Django.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Django-6.x-green?logo=django" alt="Django">
  <img src="https://img.shields.io/badge/Database-SQLite3-blue?logo=sqlite" alt="SQLite">
  <img src="https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS-orange" alt="Frontend">
  <img src="https://img.shields.io/badge/Status-In%20Development-yellow" alt="Status">
</p>




---

## 📌 Overview

**Hos-Lab-Era** is a web-based **Hospital Laboratory Management System (HLMS)** developed using the **Python Django framework**.

The system is designed to digitize and streamline laboratory-related activities by providing a centralized platform for **patient management, laboratory services, diagnostic tests, payments, laboratory results, digital report generation, and automated email notifications**.

The project follows a modular and scalable architecture, making it possible to integrate advanced technologies such as **Artificial Intelligence (AI), Machine Learning, Blockchain, and cloud-based services** in future development phases.




---

# 🎯 Project Objectives


The main objectives of Hos-Lab-Era are:

* 🏥 Digitize hospital laboratory operations.
* 👤 Provide secure patient registration and authentication.
* 👥 Implement role-based access control.
* 🧪 Manage laboratory services and diagnostic tests.
* 💳 Provide an integrated payment management system.
* 📧 Send automated email notifications.
* 📊 Manage laboratory results digitally.
* 📄 Generate digital laboratory reports.
* 🔐 Improve the security and organization of laboratory information.
* ⚡ Reduce manual paperwork and administrative workload.
* 📈 Build a scalable foundation for future healthcare technologies.



---

# 🚀 Key Features


## 🔐 1. Secure User Authentication

The system uses Django's authentication framework to manage user accounts securely.

### Features

* User registration.
* Secure login.
* Logout functionality.
* Password validation.
* Session management.
* Authentication-protected pages.
* User profile management.
* Secure access to authorized resources.

---

## 👥 2. Role-Based Access Control

Hos-Lab-Era supports role-based access to ensure that users can access functionality according to their responsibilities.

### 👤 Patient

Patients can:

* Register and log in.
* Manage their profile.
* View laboratory services.
* Request laboratory tests.
* Make payments.
* Track payment status.
* View laboratory results.
* Access digital reports.
* Receive email notifications.

### 🧑‍⚕️ Pathologist / Laboratory Staff

Laboratory staff can manage laboratory-related activities such as:

* Patient laboratory information.
* Laboratory test requests.
* Diagnostic processing.
* Test results.
* Laboratory reports.
* Test status updates.

### 👨‍💼 Administrator

Administrators can manage:

* Users.
* User roles.
* Laboratory services.
* Laboratory operations.
* Payment information.
* System configuration.
* Overall system management.

---

# 🧪 3. Laboratory Management

The laboratory module provides the core functionality of the system.

It is designed to manage:

* Laboratory services.
* Diagnostic tests.
* Patient test requests.
* Test processing.
* Test status.
* Laboratory results.
* Result verification.
* Digital laboratory reports.

The modular architecture allows additional laboratory services and workflows to be integrated in the future.

---

# 💳 4. Payment Management System

The **Payment System has already been implemented** in Hos-Lab-Era.

It allows patients to make payments associated with laboratory services and provides a structured way to track transaction status.

### Payment Features

* Laboratory service payment.
* Payment processing.
* Payment status tracking.
* Transaction records.
* Patient payment history.
* Successful payment status.
* Failed payment status.
* Payment confirmation.
* Integration with laboratory service workflow.

### Payment Workflow

```text
Patient
   │
   ▼
Select Laboratory Service
   │
   ▼
View Service Fee
   │
   ▼
Initiate Payment
   │
   ▼
Payment Processing
   │
   ├───────────────┐
   ▼               ▼
Success           Failed
   │               │
   ▼               ▼
Payment           Payment
Confirmed         Failed
   │
   ▼
Transaction Recorded
   │
   ▼
Email Confirmation
   │
   ▼
Laboratory Service
```

---

# 📧 5. Email Notification System

An automated **Email Notification System has already been implemented**.

The system can notify users about important events and updates without requiring them to continuously check the application.

### Email Notifications Include

* Account-related notifications.
* Laboratory test updates.
* Payment confirmations.
* Payment status updates.
* Laboratory result notifications.
* Digital report availability.
* Important system updates.

### Notification Workflow

```text
System Event
     │
     ▼
Django Backend
     │
     ▼
Event Validation
     │
     ▼
Email Service
     │
     ▼
Patient Email
     │
     ▼
Notification Received
```

---

# 📊 6. Patient Dashboard

The system provides a personalized dashboard for authenticated patients.

The dashboard can provide access to:

* 👤 Patient profile.
* 🧪 Laboratory services.
* 📋 Test requests.
* 💳 Payment information.
* 📄 Laboratory results.
* 📑 Digital reports.
* 📧 Notifications.
* 🔐 Account information.

The dashboard is dynamically generated using information stored in the database.

---

# 📄 7. Digital Laboratory Report Generation

The **Digital Report Generation system has already been completed**.

The system allows laboratory results to be organized into structured digital reports.

### Features

* Digital laboratory report generation.
* Patient-specific reports.
* Laboratory test information.
* Diagnostic result details.
* Result status.
* Structured report format.
* Digital access to laboratory reports.
* Integration with laboratory results.
* Patient report availability.

### Report Workflow

```text
Laboratory Test
       │
       ▼
Result Processing
       │
       ▼
Result Verification
       │
       ▼
Digital Report Generated
       │
       ▼
Email Notification
       │
       ▼
Patient Accesses Report
```

---

# 🔄 Complete System Workflow

The overall Hos-Lab-Era workflow is:

```text
                         ┌───────────────┐
                         │    Patient    │
                         └───────┬───────┘
                                 │
                                 ▼
                       ┌──────────────────┐
                       │ Register / Login │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Patient Dashboard│
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Laboratory Test  │
                       │     Request      │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │     Payment      │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Laboratory       │
                       │    Processing    │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Result Generated │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Digital Report   │
                       │    Generated     │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Email Notification│
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Patient Views    │
                       │     Report       │
                       └──────────────────┘
```

---

# 🏗️ System Architecture

Hos-Lab-Era follows the **Django Model-Template-View (MTV)** architecture.

```text
                         USERS
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
         Patient       Laboratory      Admin
                          Staff
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                    ┌─────────────┐
                    │ Web Browser │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Django    │
                    │ Application │
                    └──────┬──────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
       ▼                   ▼                   ▼
 ┌────────────┐     ┌────────────┐     ┌────────────┐
 │  Accounts  │     │ Laboratory │     │  Payments  │
 │    App     │     │    App     │     │    App     │
 └─────┬──────┘     └─────┬──────┘     └─────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Database   │
                    │  SQLite3    │
                    └──────┬──────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ Email Notification│
                 └───────────────────┘
```

---

# 🛠️ Technology Stack

## Current Technologies

| Category             | Technology                 |
| -------------------- | -------------------------- |
| Programming Language | Python                     |
| Backend Framework    | Django 6.x                 |
| Frontend             | HTML5                      |
| Styling              | CSS3                       |
| Layout               | Flexbox / CSS Grid         |
| Database             | SQLite3                    |
| Authentication       | Django Authentication      |
| Email                | Django Email System        |
| Payment              | Integrated Payment System  |
| Version Control      | Git                        |
| Repository Hosting   | GitHub                     |
| Environment          | Python Virtual Environment |

## Planned Technologies

| Technology              | Planned Purpose                                            |
| ----------------------- | ---------------------------------------------------------- |
| Artificial Intelligence | Intelligent laboratory assistance and healthcare analytics |
| Machine Learning        | Data analysis and predictive support                       |
| Blockchain              | Secure and tamper-resistant record verification            |
| PostgreSQL              | Production database                                        |
| Cloud Computing         | Scalable deployment and storage                            |

---

# 📂 Project Structure

```text
Hos-Lab-Era/
│
├── core/
│   ├── templates/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── accounts/
│   ├── migrations/
│   ├── templates/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── laboratory/
│   ├── migrations/
│   ├── templates/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── payments/
│   ├── migrations/
│   ├── templates/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── manage.py
├── db.sqlite3
├── requirements.txt
├── .gitignore
└── README.md
```

> The exact structure may evolve as additional modules are introduced.

---

# 🗄️ Database

The current development environment uses **SQLite3**.

SQLite is useful during development because it is:

* Lightweight.
* Easy to configure.
* Serverless.
* Suitable for prototyping.
* Well supported by Django.

### Future Database

For production deployment, the system can be migrated to **PostgreSQL** for improved scalability, reliability, and concurrent database operations.

---

# 🔒 Security

Security is an important consideration because the system handles healthcare and payment-related information.

Hos-Lab-Era uses Django's security mechanisms, including:

* Password hashing.
* Authentication sessions.
* CSRF protection.
* Server-side validation.
* Protected routes.
* Role-based access control.
* Permission-based access.

### Planned Security Improvements

* HTTPS.
* Secure cookies.
* Environment-based secret management.
* Multi-factor authentication.
* Advanced permissions.
* Audit logging.
* Database encryption.
* API authentication.
* Regular security updates.

> Sensitive credentials such as email passwords, payment keys, API keys, and Django secret keys should never be committed to the repository.

---

# ⚙️ Installation & Setup

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/Hos-Lab-Era.git
```

Navigate into the project:

```bash
cd Hos-Lab-Era
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate:

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
```

Activate:

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not available:

```bash
pip install django
```

---

## 4. Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 5. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the instructions provided in the terminal.

---

## 6. Run the Development Server

```bash
python manage.py runserver
```

Open the application:

```text
http://127.0.0.1:8000/
```

---

# 🔧 Environment Configuration

Sensitive configuration should be stored using environment variables.

Example:

```env
SECRET_KEY=your-secret-key
DEBUG=True

EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True

PAYMENT_API_KEY=
PAYMENT_SECRET_KEY=
```

> Do not commit `.env` files containing real credentials to GitHub.

---

# 🧪 Development Workflow

```text
Requirement Analysis
        │
        ▼
System Design
        │
        ▼
Django Development
        │
        ▼
Database Modeling
        │
        ▼
Frontend Integration
        │
        ▼
Authentication & Authorization
        │
        ▼
Payment Integration
        │
        ▼
Email Integration
        │
        ▼
Laboratory & Report Management
        │
        ▼
Testing
        │
        ▼
Git & GitHub
        │
        ▼
Future AI & Blockchain Integration
```

---

# 📈 Project Development Status

| Module                       | Status            |
| ---------------------------- | ----------------- |
| Project Setup                | ✅ Completed       |
| Django Configuration         | ✅ Completed       |
| User Registration            | ✅ Completed       |
| User Login                   | ✅ Completed       |
| Authentication               | ✅ Completed       |
| User Profiles                | ✅ Completed       |
| Patient Dashboard            | ✅ Completed       |
| Role-Based Access Control    | ✅ Completed       |
| Laboratory Services          | 🚧 In Development |
| Laboratory Test Management   | 🚧 In Development |
| Payment System               | ✅ Completed       |
| Payment Tracking             | ✅ Completed       |
| Email Notification System    | ✅ Completed       |
| Payment Confirmation Email   | ✅ Completed       |
| Laboratory Result Management | ✅ Completed       |
| Digital Report Generation    | ✅ Completed       |
| AI Integration               | 🔮 Future         |
| Blockchain Integration       | 🔮 Future         |
| Advanced Analytics           | 📌 Planned        |
| Cloud Deployment             | 📌 Planned        |
| PostgreSQL Migration         | 📌 Planned        |

### Status Legend

* ✅ **Completed**
* 🚧 **In Development**
* 📌 **Planned**
* 🔮 **Future**

---

# 🔮 Future Enhancements

The next phase of Hos-Lab-Era will focus on improving intelligence, security, scalability, and usability.

## 🤖 Artificial Intelligence

Planned AI features include:

* AI-assisted laboratory analysis.
* Intelligent diagnostic support.
* Laboratory data analysis.
* Predictive healthcare analytics.
* AI-powered patient assistance chatbot.
* Automated report summarization.
* Anomaly detection.
* Intelligent search and recommendations.

> AI features will be designed as **decision-support functionality** and will not replace qualified healthcare professionals.

---

# ⛓️ Blockchain Integration

Blockchain technology is planned for a future version of Hos-Lab-Era.

Potential applications include:

* Tamper-resistant laboratory records.
* Secure report verification.
* Laboratory result authenticity.
* Data integrity verification.
* Trusted medical record sharing.
* Blockchain-based transaction verification.

### Proposed Blockchain Workflow

```text
Laboratory Result
       │
       ▼
Django Backend
       │
       ▼
Generate Record Hash
       │
       ▼
Blockchain Network
       │
       ▼
Immutable Verification Record
       │
       ▼
Authorized Verification
```

Sensitive patient information would not be directly exposed on a public blockchain.

---

# ☁️ Cloud & Scalability Roadmap

Future deployment improvements include:

* Cloud hosting.
* PostgreSQL database.
* Automated database backups.
* Scalable infrastructure.
* Object storage for reports.
* Secure production configuration.
* Monitoring and logging.

---

# 📊 Advanced Analytics

Future analytics capabilities may include:

* Laboratory workload analytics.
* Test frequency statistics.
* Payment analytics.
* Revenue reports.
* Patient service analytics.
* Laboratory performance dashboards.
* Interactive charts and visualizations.

---

# 🖥️ Screenshots

Screenshots of the major system interfaces can be added here.

## 🔐 Login Page

```text
Add login screenshot here
```

## 📝 Registration Page

```text
Add registration screenshot here
```

## 👤 Patient Dashboard

```text
Add patient dashboard screenshot here
```

## 🧪 Laboratory Dashboard

```text
Add laboratory dashboard screenshot here
```

## 💳 Payment Page

```text
Add payment screenshot here
```

## 📄 Digital Laboratory Report

```text
Add digital report screenshot here
```

## 📧 Email Notification

```text
Add email notification screenshot here
```

### Recommended Screenshot Directory

```text
screenshots/
├── login.png
├── registration.png
├── dashboard.png
├── laboratory.png
├── payment.png
├── report.png
└── email.png
```

Example:

```markdown
![Patient Dashboard](screenshots/dashboard.png)
```

---

# 🧹 Git & Security Best Practices

Recommended `.gitignore`:

```gitignore
venv/
__pycache__/
*.pyc
.env
db.sqlite3
staticfiles/
media/
.idea/
.vscode/
```

Never commit:

* ❌ Django `SECRET_KEY`
* ❌ Email passwords
* ❌ Payment API keys
* ❌ Database credentials
* ❌ Private API tokens
* ❌ Production environment variables

---

# 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

### Fork the repository

### Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/Hos-Lab-Era.git
```

### Create a feature branch

```bash
git checkout -b feature/your-feature
```

### Make your changes

### Commit

```bash
git add .
git commit -m "Add: your feature"
```

### Push

```bash
git push origin feature/your-feature
```

Then create a Pull Request.

---

# 📄 License

This project is currently developed for **educational and academic purposes**.

A formal open-source license can be added when the project is prepared for public distribution.

---

# 👩‍💻 Author

## Asha Giri

**IT Engineering Student | Python & Django Developer**

**Nepal College of Information Technology (NCIT)**

### Technical Interests

* 🐍 Python
* 🌐 Django
* 💻 Web Development
* 🗄️ Database Management
* ☁️ Cloud Computing
* 🤖 Artificial Intelligence
* ⛓️ Blockchain Technology
* 🧠 Machine Learning
* 🏗️ Software Engineering

---

# 🌟 Project Vision

Hos-Lab-Era is being developed with a long-term vision of building a **secure, intelligent, and scalable digital laboratory ecosystem**.

The project will evolve through multiple development stages:

```text
                 ┌─────────────────┐
                 │   Hos-Lab-Era   │
                 └────────┬────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
     Authentication   Laboratory      Payments
          │               │               │
          └───────────────┼───────────────┘
                          │
                          ▼
                 Email Notifications
                          │
                          ▼
                 Laboratory Results
                          │
                          ▼
                 Digital Reports
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
        🤖 Artificial             ⛓️ Blockchain
         Intelligence              Technology
              │                       │
              └───────────┬───────────┘
                          ▼
              Intelligent & Secure
               Healthcare Platform
```

---

# ⭐ Support the Project

If you find **Hos-Lab-Era** useful or interesting:

⭐ Star the repository
🍴 Fork the project
🐛 Report issues
💡 Suggest improvements
🤝 Contribute to development

---

# 🏥 Hos-Lab-Era

### *From Digital Laboratory Management to an Intelligent & Secure Healthcare Platform.*

**Built with Python & Django.
Designed for better laboratory management.
Ready for AI & Blockchain innovation. 🚀**
