# Deployment Guide

This project needs two deployed services:

- A Python web app, which gives you the public website link.
- A persistent MySQL database, which stores admins, faculty, students, departments, feedback, and form windows.

Do not use the local `.env` file in public repositories. Add the same values as private environment variables on the hosting platform.

## Recommended Option: Railway

Railway is the easiest fit for this app because it can run the Python website and a MySQL database in the same project.

### 1. Put The Project On GitHub

1. Create a private GitHub repository.
2. Upload this project folder.
3. Make sure `.env` is not uploaded. The `.gitignore` already excludes it.

### 2. Create The Railway Project

1. Open Railway.
2. Create a new project from the GitHub repository.
3. Add a MySQL database in the same Railway project.
4. Open the Python app service, then add environment variables.

Railway MySQL usually provides these variables automatically:

```text
MYSQLHOST
MYSQLPORT
MYSQLUSER
MYSQLPASSWORD
MYSQLDATABASE
```

This app now supports those names directly. It also supports `MYSQL_URL` or `DATABASE_URL` if your database provider gives one connection string instead.

### 3. Add App Environment Variables

Set these on the Python app service:

```text
HOST=0.0.0.0
COOKIE_SECURE=1
ADMIN_PASSWORD=<a-strong-private-admin-password>
MYSQLHOST=<from Railway MySQL>
MYSQLPORT=<from Railway MySQL>
MYSQLUSER=<from Railway MySQL>
MYSQLPASSWORD=<from Railway MySQL>
MYSQLDATABASE=<from Railway MySQL>
```

Optional, but needed for OTP password changes:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<sender-gmail-address>
SMTP_PASSWORD=<gmail-app-password>
SMTP_FROM=<sender-gmail-address>
```

Do not set `PORT` manually unless Railway tells you to. Most hosts provide it automatically.

### 4. Deploy Settings

This repository includes:

```text
Procfile
railway.toml
runtime.txt
requirements.txt
```

Railway can use:

```text
Install command: pip install -r requirements.txt
Start command: python app.py
Health check path: /health
```

When deployment finishes, Railway will give you a public website URL. Share that URL with students and faculty.

## Render Or Other Python Hosts

Render is a good alternate host if Railway does not allow you to create resources. Use Render for the website and use a separate cloud MySQL-compatible database such as TiDB Cloud Starter for storing form submissions.

Use these settings:

```text
Build command: pip install -r requirements.txt
Start command: python app.py
Health check path: /health
```

Set:

```text
HOST=0.0.0.0
PORT=<the platform-provided port, if required>
COOKIE_SECURE=1
ADMIN_PASSWORD=<a-strong-private-admin-password>
MYSQL_HOST=<cloud-mysql-host>
MYSQL_PORT=3306
MYSQL_USER=<cloud-mysql-user>
MYSQL_PASSWORD=<cloud-mysql-password>
MYSQL_DATABASE=student_feedback
```

The app creates the database tables automatically on startup, as long as the MySQL user has permission to create tables and indexes.

### Render + TiDB Cloud Starter

1. Create a TiDB Cloud Starter database.
2. Copy the database connection details from TiDB.
3. Create a Render Web Service from your GitHub repository.
4. Use these Render settings:

```text
Runtime: Python
Build command: pip install -r requirements.txt
Start command: python app.py
Health check path: /health
```

5. Add these Render environment variables:

```text
HOST=0.0.0.0
COOKIE_SECURE=1
ADMIN_PASSWORD=<a-strong-private-admin-password>
MYSQL_HOST=<tidb-host>
MYSQL_PORT=4000
MYSQL_USER=<tidb-user>
MYSQL_PASSWORD=<tidb-password>
MYSQL_DATABASE=<tidb-database>
MYSQL_SSL=true
```

If TiDB gives you one connection string, you can use this instead:

```text
HOST=0.0.0.0
COOKIE_SECURE=1
ADMIN_PASSWORD=<a-strong-private-admin-password>
DATABASE_URL=mysql://<user>:<password>@<host>:4000/<database>?ssl=true
```

Render will give you a public URL like:

```text
https://your-service-name.onrender.com
```

## Before Sharing The Link

1. Open the deployed URL.
2. Login as admin.
3. Add departments.
4. Add faculty.
5. Assign HODs.
6. Add students.
7. Set feedback windows.
8. Ask one test student to submit feedback.
9. Check the admin report page to confirm the stored feedback appears.

## Important Notes

- Keep the MySQL service running. If the database is deleted, the submitted forms are deleted too.
- Do not share database passwords with students or faculty.
- Do not commit `.env` to GitHub.
- Use a private GitHub repository if the project contains real university data or credentials.
