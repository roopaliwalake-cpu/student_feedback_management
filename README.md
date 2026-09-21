# BANGALORE UNIVERSITY Student Feedback Management System

A local full-stack student feedback website built with Python and MySQL.

## Features

- Single fixed admin login
- Admin can add departments
- Admin can assign one faculty member as the HOD for each department
- Admin can add faculty login credentials
- Faculty can login only with credentials created by admin
- Admin can add department-wise student login credentials
- Students login with the username and password set by admin
- Admin can set the feedback form timeline for each department
- Faculty and students can change their password after login using a one-time email OTP
- Students must select the same department during login
- Faculty also select their department during login
- Students can submit faculty feedback
- Students can submit feedback only for faculty in their own department
- Faculty can view feedback summaries
- Admin can download faculty-wise and department-wise reports

## Run In CMD

Install the Python dependency first:

```cmd
pip install -r requirements.txt
```

Make sure MySQL Server is running, then configure `.env` with your MySQL credentials:

```text
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=student_feedback
```

```cmd
cd "C:\Users\roopa\OneDrive\Documents\StudentFeedbackManagementSystem"
python app.py
```

Then open:

```text
http://127.0.0.1:8000
```

If `python` is not recognized, run with the bundled Python used by Codex:

```cmd
"C:\Users\roopa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" app.py
```

## First Use

1. Open the website.
2. Login as admin with:
   - Email: `roopaliwalake@gmail.com`
   - Password: `roopali@123`
3. Add departments.
4. Add faculty with email and temporary password.
5. Assign one faculty member as the HOD for each department.
6. Add students for their department with email, username, and temporary password.
7. Set the feedback timeline for the department.
8. Students login with the admin-provided username/password and submit feedback.

## Email OTP Setup

Password changes use email OTP. Configure SMTP before running the app.

For Gmail:

1. Turn on 2-Step Verification for the sender Gmail account.
2. Create a Gmail app password from Google Account > Security > App passwords.
3. Copy `.env.example` to a new file named `.env`.
4. Put the sender Gmail address and Gmail app password in `.env`.

Example `.env`:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM=your-email@gmail.com
```

Then run:

```cmd
start_app.cmd
```

You can also configure SMTP directly in CMD:

```cmd
set SMTP_HOST=smtp.gmail.com
set SMTP_PORT=587
set SMTP_USER=your-email@gmail.com
set SMTP_PASSWORD=your-app-password
set SMTP_FROM=your-email@gmail.com
python app.py
```

For Gmail, use an app password instead of your normal Gmail password. If SMTP is not configured, the app cannot send OTP reset emails.

The app creates the configured MySQL database and tables automatically if the MySQL user has permission.
