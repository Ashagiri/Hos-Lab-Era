# 🏥 Hos-Lab-Era

### Hospital Laboratory Management System

<p align="center">
  A secure and digital laboratory management platform built with
  <strong>Python & Django</strong>.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python">
  <img src="https://img.shields.io/badge/Django-6.x-green?logo=django">
  <img src="https://img.shields.io/badge/SQLite-3-blue?logo=sqlite">
  <img src="https://img.shields.io/badge/AI-Integrated-purple">
  <img src="https://img.shields.io/badge/Blockchain-Integrated-black">
  <img src="https://img.shields.io/badge/Status-Active%20Development-yellow">
</p>

---

## 📌 About

**Hos-Lab-Era** is a web-based **Hospital Laboratory Management System (HLMS)** designed to digitize and simplify laboratory operations.

The system allows patients to book laboratory tests, make payments, receive notifications, view results, and access digital laboratory reports from one platform.

It also includes **AI-assisted report understanding, blockchain-based record integrity, analytics, and cloud deployment**.

---

## ✨ Features

- 🔐 Secure Authentication & Authorization
- 👤 Patient Profile & Dashboard
- 🧪 Laboratory Test Management
- 📅 Online Test Booking
- 💳 Payment Management
- 📧 Automated Email Notifications
- 📊 Laboratory Result Management
- 📄 Digital PDF Report Generation
- 🤖 Ask AI for Report Understanding
- ⛓️ Blockchain Record Integrity
- 📈 Advanced Analytics
- ☁️ Cloud Deployment

---

## 👥 User Roles

### 👤 Patient
- Register and login
- Manage profile
- Book laboratory tests
- Make payments
- Track test status
- View results
- Download reports
- Use Ask AI
- Receive email notifications

### 🧑‍⚕️ Laboratory Staff
- Manage laboratory tests
- Process test requests
- Manage results
- Verify results
- Generate reports
- Update test status

### 👨‍💼 Administrator
- Manage users
- Manage laboratory services
- Manage payments
- Manage system operations

---

## 🔄 System Workflow

```text
Patient
   ↓
Register / Login
   ↓
Patient Dashboard
   ↓
Book Laboratory Test
   ↓
Payment
   ↓
Laboratory Processing
   ↓
Result Verification
   ↓
Digital PDF Report
   ↓
Email Notification
   ↓
Patient Access


🛠️ Technology Stack
Category	Technology
Language	Python
Backend	Django 6.x
Frontend	HTML5, CSS3, JavaScript
Database	SQLite3
Authentication	Django Authentication
Payment	Integrated Payment System
Email	Django Email System
Reports	Digital PDF Generation
AI	AI-Assisted Report Explanation
Blockchain	Record Integrity & Verification
Analytics	Data Visualization
Version Control	Git & GitHub
Deployment	Cloud
🏗️ Architecture

Hos-Lab-Era follows the Django MTV architecture.

                Web Browser
                     │
                     ▼
              Django Application
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    Accounts     Laboratory    Payments
        │            │            │
        └────────────┼────────────┘
                     │
                     ▼
                  Database
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
        Email       AI      Blockchain
📂 Project Structure
Hos-Lab-Era/
│
├── core/
├── accounts/
├── laboratory/
├── payments/
│
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
🚀 Installation
1. Clone the repository
git clone https://github.com/YOUR-USERNAME/Hos-Lab-Era.git
cd Hos-Lab-Era
2. Create virtual environment
python -m venv venv
3. Activate environment

Windows

venv\Scripts\activate

Linux / macOS

source venv/bin/activate
4. Install dependencies
pip install -r requirements.txt
5. Run migrations
python manage.py makemigrations
python manage.py migrate
6. Create admin account
python manage.py createsuperuser
7. Start the server
python manage.py runserver

Open:

http://127.0.0.1:8000/
🔐 Environment Variables

Store sensitive configuration in environment variables.

SECRET_KEY=your-secret-key
DEBUG=True

EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

PAYMENT_API_KEY=
PAYMENT_SECRET_KEY=

Never commit real credentials, API keys, passwords, or secret keys to GitHub.

📸 Screenshots
My Reports

Ask AI

Patient Dashboard

Payment

📊 Project Status
Module	Status
Authentication	✅ Completed
Patient Dashboard	✅ Completed
Laboratory Management	✅ Completed
Test Booking	✅ Completed
Payment System	✅ Completed
Email Notifications	✅ Completed
Laboratory Results	✅ Completed
Digital Reports	✅ Completed
Ask AI	✅ Completed
Blockchain	✅ Completed
Advanced Analytics	✅ Completed
Cloud Deployment	✅ Completed
PostgreSQL Migration	🔜 Planned
🔒 Security

The system uses Django security mechanisms including:

Password hashing
Authentication sessions
CSRF protection
Server-side validation
Protected routes
Role-based access control
Permission-based access

Sensitive healthcare and payment information should be handled using appropriate security and privacy practices.

🔮 Future Enhancements
🗄️ PostgreSQL production database
🤖 Advanced AI & Machine Learning
📊 Advanced healthcare analytics
🔐 Multi-factor authentication
📝 Audit logging
☁️ Improved cloud scalability
📱 Mobile application
🔗 Enhanced blockchain verification
🤝 Contributing

Contributions and suggestions are welcome.

git checkout -b feature/your-feature
git add .
git commit -m "Add: your feature"
git push origin feature/your-feature

Then create a Pull Request.

📄 License

This project is currently developed for educational and academic purposes.

👩‍💻 Author
Asha Giri

IT Engineering Student | Python & Django Developer

Nepal College of Information Technology (NCIT)

Interests: Python • Django • Web Development • Cloud • AI • Machine Learning • Blockchain

⭐ Support

If you find Hos-Lab-Era useful:

⭐ Star the repository
🍴 Fork the project
🐛 Report issues
💡 Suggest improvements

<p align="center">
🏥 Hos-Lab-Era

<strong>From Digital Laboratory Management to an Intelligent & Secure Healthcare Platform.</strong>

Built with ❤️ using Python & Django 🚀

</p> ```