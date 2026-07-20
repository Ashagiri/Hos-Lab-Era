# 🏥 Hos-Lab-Era (Hospital Laboratory Management System)

**Hos-Lab-Era** is a web-based Laboratory Management System developed using the Python Django framework. The platform streamlines hospital laboratory operations by allowing patients to securely register, log in, view their account status, and dynamically check their medical lab diagnostics.

---

## 🚀 Key Features Built So Far
* **Custom Authentication Engine:** Secure registration and login workflows using Django's backend authentication.
* **Role-Based Access Control (RBAC):** Custom user profiles equipped to support specialized roles (e.g., Patient, Pathologist, Admin).
* **Dynamic Patient Dashboard:** Personalized portal layout welcoming users dynamically and showing their system profiles based on live database parameters.
* **Structured Template Architecture:** Organized frontend layout utilizing unified Django settings and custom app routing paths.
----

## 🛠️ Tech Stack Used
* **Backend:** Python, Django 6.x
* **Database:** SQLite3 (Environment setup configured for migration scaling)
* **Frontend:** Clean HTML5, Modern CSS3 Flexbox/Grid

---

## 📂 Project Structure
```text
Hos-Lab-Era/
├── core/               # Global project configuration settings & routing
│   └── templates/      # Project-wide visual user interfaces (HTML structures)
├── accounts/           # User authentication, profiles, and backend model states
├── laboratory/         # Primary application logic and dashboard engines
├── manage.py           # Django command-line execution utility
└── db.sqlite3          # Local database storage

