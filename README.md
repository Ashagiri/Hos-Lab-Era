# 🏥 Hos-Lab-Era

### Hospital Laboratory Management System

**Hos-Lab-Era** is a web-based **Hospital Laboratory Management System** developed using the **Django framework** to simplify and digitize laboratory-related activities within a healthcare environment.

The system provides a centralized platform where patients can create accounts, securely authenticate, access personalized dashboards, and interact with laboratory-related services. The project is designed with a modular architecture so that additional laboratory workflows and healthcare services can be integrated in the future.

---

## 📌 Project Overview

Traditional laboratory management can involve manual registration, paper-based records, and inefficient communication between patients and laboratory staff.

**Hos-Lab-Era** aims to address these challenges by providing a digital platform that can help organize patient information and laboratory operations in a structured and secure manner.

### 🎯 Main Objectives

* Digitize hospital laboratory management processes.
* Provide secure patient registration and authentication.
* Maintain organized patient profiles and records.
* Provide personalized dashboards based on user roles.
* Reduce dependency on manual record management.
* Create a scalable foundation for future laboratory services.
* Improve accessibility and organization of laboratory information.

---

## 🚀 Key Features

### 🔐 User Authentication

* Secure user registration and login.
* Django-based authentication system.
* Password validation and secure password handling.
* Session-based user authentication.
* Logout functionality.

### 👥 Role-Based Access Control

The system is designed to support different user roles, allowing access to features based on the user's permissions.

Potential roles include:

* **Patient** — Access personal profile and laboratory-related information.
* **Pathologist/Laboratory Staff** — Manage laboratory-related operations.
* **Administrator** — Manage users and system-level configurations.

> Role-specific laboratory functionality can be extended as the project develops.

### 👤 Patient Dashboard

The dashboard provides a personalized experience for authenticated users.

Features include:

* Dynamic user greeting.
* User profile information.
* Account status.
* Role-based content.
* Navigation to available laboratory services.

### 🧩 Modular Django Architecture

The application is divided into independent Django applications to improve:

* Maintainability
* Scalability
* Code organization
* Reusability
* Future development

### 🎨 Responsive Frontend

The frontend is developed using:

* HTML5
* CSS3
* CSS Flexbox
* CSS Grid

The interface is designed to provide a clean and simple user experience.

---

## 🛠️ Technology Stack

| Category                | Technology                 |
| ----------------------- | -------------------------- |
| Programming Language    | Python                     |
| Backend Framework       | Django 6.x                 |
| Database                | SQLite3                    |
| Frontend                | HTML5, CSS3                |
| Layout                  | Flexbox, CSS Grid          |
| Authentication          | Django Authentication      |
| Version Control         | Git & GitHub               |
| Development Environment | Python Virtual Environment |

---

## 🏗️ System Architecture

The project follows Django's **Model-Template-View (MTV)** architecture.

```text
                ┌──────────────────────┐
                │       User           │
                │ Patient / Staff      │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │     Web Browser      │
                │ HTML + CSS Interface │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │       Django         │
                │      Framework       │
                └──────────┬───────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
       ┌──────────┐  ┌──────────┐  ┌───────────┐
       │ Accounts │  │Laboratory│  │   Core    │
       │   App    │  │   App    │  │   App     │
       └────┬─────┘  └────┬─────┘  └─────┬─────┘
            │             │              │
            └─────────────┼──────────────┘
                          ▼
                 ┌──────────────────┐
                 │    SQLite3 DB    │
                 └──────────────────┘
```

---

## 📂 Project Structure

```text
Hos-Lab-Era/
│
├── core/
│   ├── templates/
│   │   └── ...
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
├── manage.py
├── db.sqlite3
├── requirements.txt
└── README.md
```

### 📁 Directory Description

**`core/`**
Contains global project configuration, URL routing, settings, and shared templates.

**`accounts/`**
Handles authentication, registration, user profiles, and account-related functionality.

**`laboratory/`**
Contains the core laboratory management functionality and laboratory dashboard logic.

**`manage.py`**
Django's command-line utility for administrative and development tasks.

**`db.sqlite3`**
Local SQLite database used during development.

---

# ⚙️ Installation & Setup

Follow these steps to run the project locally.

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/Hos-Lab-Era.git
```

Move into the project directory:

```bash
cd Hos-Lab-Era
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate the environment:

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

If `requirements.txt` is available:

```bash
pip install -r requirements.txt
```

Otherwise, install Django:

```bash
pip install django
```

---

## 4. Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 5. Create a Superuser

```bash
python manage.py createsuperuser
```

Follow the terminal instructions to create an administrator account.

---

## 6. Run the Development Server

```bash
python manage.py runserver
```

Open the application in your browser:

```text
http://127.0.0.1:8000/
```

---

# 🔑 Authentication Flow

The basic authentication workflow is:

```text
User
  │
  ▼
Registration
  │
  ▼
Account Created
  │
  ▼
Login
  │
  ▼
Authentication
  │
  ├───────────────┐
  ▼               ▼
Valid           Invalid
  │               │
  ▼               ▼
Dashboard       Error
  │
  ▼
Role-Based Access
```

---

# 🧪 Laboratory Management Workflow

The planned laboratory workflow can be represented as:

```text
Patient
   │
   ▼
Registration / Login
   │
   ▼
Patient Dashboard
   │
   ▼
Laboratory Services
   │
   ▼
Test / Diagnostic Request
   │
   ▼
Laboratory Processing
   │
   ▼
Result Management
   │
   ▼
Patient Result
```

---

# 🖥️ Screenshots

Add screenshots of the major interfaces here.

### 🔐 Login Page

```text
Add login page screenshot here
```

### 📝 Registration Page

```text
Add registration page screenshot here
```

### 👤 Patient Dashboard

```text
Add dashboard screenshot here
```

### 🧪 Laboratory Dashboard

```text
Add laboratory dashboard screenshot here
```

> Screenshots can be added using:

```markdown
![Login Page](screenshots/login.png)
```

---

# 🔒 Security Considerations

Since the system handles healthcare-related information, security is an important consideration.

The project uses Django's built-in security mechanisms, including:

* Password hashing.
* Authentication sessions.
* CSRF protection.
* Django form validation.
* Permission-based access control.
* Server-side validation.

For production deployment, additional security measures should be implemented, including:

* HTTPS.
* Secure cookies.
* Environment variables for secrets.
* Production database configuration.
* Proper access permissions.
* Regular dependency updates.
* Database backups.

---

# 🗄️ Database

The current development environment uses **SQLite3** because it is lightweight and easy to configure.

For production deployment and larger datasets, the system can be migrated to a database such as:

* PostgreSQL
* MySQL

The database architecture can also be extended to support distributed or cloud-based deployment in the future.

---

# 🔮 Future Enhancements

The project is currently under development. Planned improvements include:

* 🧪 Laboratory test management.
* 📋 Test request and appointment management.
* 🧑‍⚕️ Pathologist/laboratory staff dashboard.
* 📊 Laboratory result management.
* 📄 Digital laboratory report generation.
* 🔔 Notifications for patients.
* 📧 Email notifications.
* 📱 Improved responsive/mobile interface.
* 🔍 Advanced search and filtering.
* 📈 Laboratory analytics and reports.
* ☁️ Cloud deployment.
* 🗄️ PostgreSQL production database.
* 🔐 Advanced role and permission management.
* 📑 Audit logs for important system activities.

---

# 📈 Project Development Status

| Module                | Status            |
| --------------------- | ----------------- |
| Project Setup         | ✅ Completed       |
| Django Configuration  | ✅ Completed       |
| User Registration     | ✅ Completed       |
| User Login            | ✅ Completed       |
| Authentication        | ✅ Completed       |
| User Profiles         | ✅ Completed       |
| Patient Dashboard     | ✅ Completed       |
| Role-Based Access     | 🚧 In Development |
| Laboratory Management | 🚧 In Development |
| Test Management       | 📌 Planned        |
| Result Management     | 📌 Planned        |
| Report Generation     | 📌 Planned        |
| Notifications         | 📌 Planned        |
| Production Deployment | 📌 Planned        |

### Legend

* ✅ Completed
* 🚧 In Development
* 📌 Planned

---

# 🧑‍💻 Development

This project is being developed as an academic/project-based application to explore practical implementation of:

* Python programming
* Django web development
* Database management
* Authentication and authorization
* Role-based access control
* Web application architecture
* Healthcare laboratory workflows

---

# 🤝 Contribution

Contributions and suggestions are welcome.

To contribute:

```bash
git clone https://github.com/YOUR-USERNAME/Hos-Lab-Era.git
```

Create a new branch:

```bash
git checkout -b feature/your-feature
```

Make your changes and commit:

```bash
git add .
git commit -m "Add: your feature"
```

Push the branch:

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

**Asha Giri**

IT Engineering Student
Nepal College of Information Technology (NCIT)

### 💻 Areas of Interest

* Python Development
* Django
* Web Development
* Cloud Computing
* Software Engineering

---

## ⭐ Support

If you find this project useful or interesting, consider giving the repository a ⭐ on GitHub!

---

## 📌 Project Summary

**Hos-Lab-Era** aims to provide a structured, secure, and scalable digital platform for managing hospital laboratory activities. Built with Django, the project focuses on clean architecture, authentication, role-based access, and an extensible foundation for future laboratory management features.

> 🚀 **Hos-Lab-Era — Digitizing Hospital Laboratory Management, One Step at a Time.**
