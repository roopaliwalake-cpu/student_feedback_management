from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, unquote_plus, urlparse
import csv
import contextvars
import hashlib
import html
import io
import json
import math
import mimetypes
import os
import re
import secrets
import smtplib
import statistics
import time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    pymysql = None


APP_NAME = "BANGALORE UNIVERSITY Student Feedback Management System"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
ADMIN_NAME = "Roopali Walake"
ADMIN_EMAIL = "roopaliwalake@gmail.com"
SESSIONS = {}
PASSWORD_OTPS = {}
ENV_LOADED = False
SESSION_SECONDS = 86400
INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30), "IST")
REQUEST_LANGUAGE = contextvars.ContextVar("REQUEST_LANGUAGE", default="en")
REQUEST_PATH = contextvars.ContextVar("REQUEST_PATH", default="/")
DB_INTEGRITY_ERRORS = (pymysql.err.IntegrityError,) if pymysql else ()
LANGUAGES = {
    "en": "English",
    "kn": "Kannada",
}
ROLE_TABLES = {
    "admin": "admins",
    "faculty": "faculty",
    "student": "students",
}

COURSE_REASONS = [
    "Interested in this subject",
    "Parents/Friends forced me",
    "UG marks was high in this subject",
    "Easy to get admission to this course",
    "Easy to pass in this subject",
    "Department has good name / reputation",
    "Jobs are easier to get",
    "Scholarship/stipend is available",
]
FACILITIES = [
    "Class Rooms space available",
    "Chairs/Desks / Cupboards etc.",
    "Lighting / Ventilation",
    "Drinking water",
    "Toilets / Sanitation",
    "Ladies room",
    "Cooperation of the office staff",
]
FORM_A_CHOICES = [
    ("syllabus", "Syllabus for this course is", ["Challenging", "Adequate", "Inadequate", "Boring/dull"]),
    ("syllabus_taught", "Quantum of the syllabus taught in the class", ["90%-100%", "75%-90%", "50%-75%", "Less than 50%"]),
    ("library", "Library facilities to support the course are", ["Excellent", "Adequate", "Not so good", "Poor/inadequate"]),
    ("textbooks", "Prescribed text books and references for the course are available", ["Easily", "Often", "Inadequately", "Not at all"]),
    ("classes_held", "Classes are held", ["Very regularly", "Fairly regularly", "Irregularly", "Very irregularly"]),
    ("internal_fairness", "Internal assessment evaluations are", ["Very fair", "Fair", "Unfair", "Not sure"]),
    ("internal_help", "Internal assessment helps to improve grades / performance", ["Yes", "To some extent", "I don't think so", "Not at all useful"]),
    ("outline_given", "Outlines of course/syllabus were given at the beginning", ["Most of the time", "To some extent", "Rarely", "Never"]),
    ("career", "Would you say the course prepares you for your future career?", ["Very well", "Well", "Not much", "Not at all relevant"]),
    ("other_institutions", "When you meet students in similar courses studying in other institutions, do you feel", ["Better off", "Equal", "Not sure", "Worse than them"]),
    ("after_leaving", "After leaving this institution how will you talk about it?", ["With pride", "With satisfaction", "Indifferently", "Not sure"]),
    ("programme_rating", "On the whole, how would you rate the programme/course?", ["Excellent", "Good", "Poor", "Very poor"]),
    ("admin_support", "University administrative support related to your studies is", ["Excellent", "Good", "Satisfactory", "Not satisfactory"]),
]
TEACHER_QUESTIONS = [
    "Is regular in taking classes",
    "Has good command over language",
    "Knows the subject well",
    "Generates interest in the subjects",
    "Encourages to ask questions",
    "Is punctual and maintains class decorum",
    "Takes the class for full period",
    "Provides course outline in the beginning",
    "Provides summary at the end of lecture / course",
    "Uses instructional aids like audiovisuals / OHP",
    "Does not merely dictate notes, explains well",
    "Provides a broader perspective of the subject",
    "Clarifies doubts / questions raised",
    "Is impartial in evaluation / giving marks",
    "Always completes the syllabus",
    "Is available after class for discussion",
    "Explains applicability of concepts",
    "Gives latest information",
    "Motivates",
    "Is a good role model",
]

KN_TRANSLATIONS = {
    APP_NAME: "ಬೆಂಗಳೂರು ವಿಶ್ವವಿದ್ಯಾಲಯ ವಿದ್ಯಾರ್ಥಿ ಪ್ರತಿಕ್ರಿಯೆ ನಿರ್ವಹಣಾ ವ್ಯವಸ್ಥೆ",
    "Bangalore University": "ಬೆಂಗಳೂರು ವಿಶ್ವವಿದ್ಯಾಲಯ",
    "Student Feedback Management System": "ವಿದ್ಯಾರ್ಥಿ ಪ್ರತಿಕ್ರಿಯೆ ನಿರ್ವಹಣಾ ವ್ಯವಸ್ಥೆ",
    "Knowledge | Progress | Excellence": "ಜ್ಞಾನ | ಪ್ರಗತಿ | ಶ್ರೇಷ್ಠತೆ",
    "Home": "ಮುಖಪುಟ",
    "Admin": "ನಿರ್ವಾಹಕ",
    "Faculty": "ಅಧ್ಯಾಪಕರು",
    "Student": "ವಿದ್ಯಾರ್ಥಿ",
    "Language": "ಭಾಷೆ",
    "English": "ಇಂಗ್ಲಿಷ್",
    "Kannada": "ಕನ್ನಡ",
    "Change Password": "ಪಾಸ್ವರ್ಡ್ ಬದಲಿಸಿ",
    "Logout": "ಲಾಗ್ ಔಟ್",
    "Login": "ಲಾಗಿನ್",
    "Forgot password?": "ಪಾಸ್ವರ್ಡ್ ಮರೆತಿರಾ?",
    "Back to login": "ಲಾಗಿನ್‌ಗೆ ಹಿಂದಿರುಗಿ",
    "Password": "ಪಾಸ್ವರ್ಡ್",
    "Email": "ಇಮೇಲ್",
    "Registered Email": "ನೋಂದಾಯಿತ ಇಮೇಲ್",
    "Student Name": "ವಿದ್ಯಾರ್ಥಿಯ ಹೆಸರು",
    "Select your name": "ನಿಮ್ಮ ಹೆಸರನ್ನು ಆಯ್ಕೆಮಾಡಿ",
    "Select Department": "ವಿಭಾಗ ಆಯ್ಕೆಮಾಡಿ",
    "Select department": "ವಿಭಾಗ ಆಯ್ಕೆಮಾಡಿ",
    "Select language": "ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ",
    "Continue": "ಮುಂದುವರಿಸಿ",
    "Show": "ತೋರಿಸಿ",
    "Hide": "ಮರೆಮಾಡಿ",
    "Admin Portal": "ನಿರ್ವಾಹಕ ಪೋರ್ಟಲ್",
    "Faculty Portal": "ಅಧ್ಯಾಪಕರ ಪೋರ್ಟಲ್",
    "Student Portal": "ವಿದ್ಯಾರ್ಥಿ ಪೋರ್ಟಲ್",
    "Go": "ಹೋಗಿ",
    "Student Feedback": "ವಿದ್ಯಾರ್ಥಿ ಪ್ರತಿಕ್ರಿಯೆ",
    "Management System": "ನಿರ್ವಹಣಾ ವ್ಯವಸ್ಥೆ",
    "Admin Login": "ನಿರ್ವಾಹಕ ಲಾಗಿನ್",
    "Faculty Login": "ಅಧ್ಯಾಪಕರ ಲಾಗಿನ್",
    "Student Login": "ವಿದ್ಯಾರ್ಥಿ ಲಾಗಿನ್",
    "Admin Forgot Password": "ನಿರ್ವಾಹಕ ಪಾಸ್ವರ್ಡ್ ಮರೆತಿದೆ",
    "Faculty Forgot Password": "ಅಧ್ಯಾಪಕರ ಪಾಸ್ವರ್ಡ್ ಮರೆತಿದೆ",
    "Student Forgot Password": "ವಿದ್ಯಾರ್ಥಿ ಪಾಸ್ವರ್ಡ್ ಮರೆತಿದೆ",
    "Collect feedback from admin-added students, manage departments, assign HODs, set feedback timelines, and download reports.": "ನಿರ್ವಾಹಕರು ಸೇರಿಸಿದ ವಿದ್ಯಾರ್ಥಿಗಳಿಂದ ಪ್ರತಿಕ್ರಿಯೆ ಸಂಗ್ರಹಿಸಿ, ವಿಭಾಗಗಳನ್ನು ನಿರ್ವಹಿಸಿ, HOD ಗಳನ್ನು ನೇಮಿಸಿ, ಪ್ರತಿಕ್ರಿಯೆ ಸಮಯರೇಖೆಗಳನ್ನು ನಿಗದಿಪಡಿಸಿ ಮತ್ತು ವರದಿಗಳನ್ನು ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ.",
    "Your feedback drives a better tomorrow": "ನಿಮ್ಮ ಪ್ರತಿಕ್ರಿಯೆ ಉತ್ತಮ ನಾಳೆಯನ್ನು ರೂಪಿಸುತ್ತದೆ",
    "Students shape stronger universities": "ವಿದ್ಯಾರ್ಥಿಗಳು ಬಲಿಷ್ಠ ವಿಶ್ವವಿದ್ಯಾಲಯಗಳನ್ನು ರೂಪಿಸುತ್ತಾರೆ",
    "Better Feedback": "ಉತ್ತಮ ಪ್ರತಿಕ್ರಿಯೆ",
    "Improved Learning": "ಸುಧಾರಿತ ಕಲಿಕೆ",
    "Stronger Communities": "ಬಲಿಷ್ಠ ಸಮುದಾಯಗಳು",
    "Education Today, A Brighter Tomorrow": "ಇಂದಿನ ಶಿಕ್ಷಣ, ಉಜ್ವಲ ನಾಳೆ",
    "Share | Suggest | Improve": "ಹಂಚಿಕೊಳ್ಳಿ | ಸೂಚಿಸಿ | ಸುಧಾರಿಸಿ",
    "Your Feedback Builds a Better Tomorrow": "ನಿಮ್ಮ ಪ್ರತಿಕ್ರಿಯೆ ಉತ್ತಮ ನಾಳೆಯನ್ನು ನಿರ್ಮಿಸುತ್ತದೆ",
    "A responsive, transparent and student-friendly campus starts with clear feedback.": "ಸ್ಪಂದನಶೀಲ, ಪಾರದರ್ಶಕ ಮತ್ತು ವಿದ್ಯಾರ್ಥಿ ಸ್ನೇಹಿ ಕ್ಯಾಂಪಸ್ ಸ್ಪಷ್ಟ ಪ್ರತಿಕ್ರಿಯೆಯಿಂದ ಆರಂಭವಾಗುತ್ತದೆ.",
    "Share Your Feedback": "ನಿಮ್ಮ ಪ್ರತಿಕ್ರಿಯೆ ಹಂಚಿಕೊಳ್ಳಿ",
    "Suggest Ideas": "ಆಲೋಚನೆಗಳನ್ನು ಸೂಚಿಸಿ",
    "Help Us Improve": "ಸುಧಾರಿಸಲು ಸಹಾಯ ಮಾಡಿ",
    "Stronger University": "ಬಲಿಷ್ಠ ವಿಶ್ವವಿದ್ಯಾಲಯ",
    "Students Today": "ಇಂದಿನ ವಿದ್ಯಾರ್ಥಿಗಳು",
    "A Stronger Bangalore University Tomorrow": "ನಾಳೆಯ ಬಲಿಷ್ಠ ಬೆಂಗಳೂರು ವಿಶ್ವವಿದ್ಯಾಲಯ",
    "Education | Feedback | Better Tomorrow": "ಶಿಕ್ಷಣ | ಪ್ರತಿಕ್ರಿಯೆ | ಉತ್ತಮ ನಾಳೆ",
    "Together for a better University.": "ಉತ್ತಮ ವಿಶ್ವವಿದ್ಯಾಲಯಕ್ಕಾಗಿ ಒಟ್ಟಾಗಿ.",
    "Welcome back. Please login to continue.": "ಮತ್ತೆ ಸ್ವಾಗತ. ಮುಂದುವರಿಸಲು ದಯವಿಟ್ಟು ಲಾಗಿನ್ ಮಾಡಿ.",
    "Use the registered admin email:": "ನೋಂದಾಯಿತ ನಿರ್ವಾಹಕ ಇಮೇಲ್ ಬಳಸಿ:",
    "Need an account? Contact the admin office.": "ಖಾತೆ ಬೇಕೇ? ನಿರ್ವಾಹಕ ಕಚೇರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ.",
    "Admin Registration Closed": "ನಿರ್ವಾಹಕ ನೋಂದಣಿ ಮುಚ್ಚಲಾಗಿದೆ",
    "Student Registration Closed": "ವಿದ್ಯಾರ್ಥಿ ನೋಂದಣಿ ಮುಚ್ಚಲಾಗಿದೆ",
    "Admin registration is disabled. Use the fixed admin account below.": "ನಿರ್ವಾಹಕ ನೋಂದಣಿ ನಿಷ್ಕ್ರಿಯವಾಗಿದೆ. ಕೆಳಗಿನ ನಿಗದಿತ ನಿರ್ವಾಹಕ ಖಾತೆಯನ್ನು ಬಳಸಿ.",
    "Student accounts are created department-wise by admin. Please contact the admin office for your login ID and default password.": "ವಿದ್ಯಾರ್ಥಿ ಖಾತೆಗಳನ್ನು ವಿಭಾಗವಾರು ನಿರ್ವಾಹಕರು ಸೃಷ್ಟಿಸುತ್ತಾರೆ. ನಿಮ್ಮ ಲಾಗಿನ್ ID ಮತ್ತು ಡೀಫಾಲ್ಟ್ ಪಾಸ್ವರ್ಡ್‌ಗಾಗಿ ನಿರ್ವಾಹಕ ಕಚೇರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ.",
    "Go to Admin Login": "ನಿರ್ವಾಹಕ ಲಾಗಿನ್‌ಗೆ ಹೋಗಿ",
    "Go to Student Login": "ವಿದ್ಯಾರ್ಥಿ ಲಾಗಿನ್‌ಗೆ ಹೋಗಿ",
    "Forgot Password": "ಪಾಸ್ವರ್ಡ್ ಮರೆತಿದೆ",
    "Enter your registered email to receive a verification code.": "ಪರಿಶೀಲನಾ ಕೋಡ್ ಪಡೆಯಲು ನಿಮ್ಮ ನೋಂದಾಯಿತ ಇಮೇಲ್ ನಮೂದಿಸಿ.",
    "Send Verification Code": "ಪರಿಶೀಲನಾ ಕೋಡ್ ಕಳುಹಿಸಿ",
    "Verification Code": "ಪರಿಶೀಲನಾ ಕೋಡ್",
    "New Password": "ಹೊಸ ಪಾಸ್ವರ್ಡ್",
    "Confirm New Password": "ಹೊಸ ಪಾಸ್ವರ್ಡ್ ದೃಢೀಕರಿಸಿ",
    "Send Reset Email": "ರಿಸೆಟ್ ಇಮೇಲ್ ಕಳುಹಿಸಿ",
    "Admin Dashboard": "ನಿರ್ವಾಹಕ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
    "Choose one admin task to open its separate page.": "ಪ್ರತ್ಯೇಕ ಪುಟ ತೆರೆಯಲು ಒಂದು ನಿರ್ವಾಹಕ ಕಾರ್ಯ ಆಯ್ಕೆಮಾಡಿ.",
    "Add Department": "ವಿಭಾಗ ಸೇರಿಸಿ",
    "Add Faculty": "ಅಧ್ಯಾಪಕರನ್ನು ಸೇರಿಸಿ",
    "Assign HOD": "HOD ನೇಮಿಸಿ",
    "Add Student": "ವಿದ್ಯಾರ್ಥಿ ಸೇರಿಸಿ",
    "Feedback Timeline": "ಪ್ರತಿಕ್ರಿಯೆ ಸಮಯರೇಖೆ",
    "Reports": "ವರದಿಗಳು",
    "Back to Admin Dashboard": "ನಿರ್ವಾಹಕ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಹಿಂದಿರುಗಿ",
    "Departments": "ವಿಭಾಗಗಳು",
    "Faculty Accounts": "ಅಧ್ಯಾಪಕರ ಖಾತೆಗಳು",
    "Student Accounts": "ವಿದ್ಯಾರ್ಥಿ ಖಾತೆಗಳು",
    "Save HOD": "HOD ಉಳಿಸಿ",
    "Add Faculty Login": "ಅಧ್ಯಾಪಕರ ಲಾಗಿನ್ ಸೇರಿಸಿ",
    "Add Student Login": "ವಿದ್ಯಾರ್ಥಿ ಲಾಗಿನ್ ಸೇರಿಸಿ",
    "Save Timeline": "ಸಮಯರೇಖೆ ಉಳಿಸಿ",
    "Current Timelines": "ಪ್ರಸ್ತುತ ಸಮಯರೇಖೆಗಳು",
    "Faculty Feedback Review": "ಅಧ್ಯಾಪಕರ ಪ್ರತಿಕ್ರಿಯೆ ಪರಿಶೀಲನೆ",
    "Overall Feedback Report": "ಒಟ್ಟಾರೆ ಪ್ರತಿಕ್ರಿಯೆ ವರದಿ",
    "Department-wise CSV": "ವಿಭಾಗವಾರು CSV",
    "Open Report": "ವರದಿ ತೆರೆಯಿರಿ",
    "Download CSV": "CSV ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
    "Student Dashboard": "ವಿದ್ಯಾರ್ಥಿ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
    "Feedback Completed": "ಪ್ರತಿಕ್ರಿಯೆ ಪೂರ್ಣಗೊಂಡಿದೆ",
    "Feedback Not Available": "ಪ್ರತಿಕ್ರಿಯೆ ಲಭ್ಯವಿಲ್ಲ",
    "Feedback Form Closed": "ಪ್ರತಿಕ್ರಿಯೆ ಫಾರ್ಮ್ ಮುಚ್ಚಲಾಗಿದೆ",
    "Language Preference": "ಭಾಷಾ ಆದ್ಯತೆ",
    "Please select the language for your feedback form.": "ನಿಮ್ಮ ಪ್ರತಿಕ್ರಿಯೆ ಫಾರ್ಮ್‌ಗಾಗಿ ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ.",
    "Change Language": "ಭಾಷೆ ಬದಲಿಸಿ",
    "Your Submissions": "ನಿಮ್ಮ ಸಲ್ಲಿಕೆಗಳು",
    "Faculty": "ಅಧ್ಯಾಪಕರು",
    "Selected Department": "ಆಯ್ಕೆಯಾದ ವಿಭಾಗ",
    "Teacher Avg": "ಅಧ್ಯಾಪಕರ ಸರಾಸರಿ",
    "Reason": "ಕಾರಣ",
    "Date": "ದಿನಾಂಕ",
    "No feedback submitted yet.": "ಇನ್ನೂ ಪ್ರತಿಕ್ರಿಯೆ ಸಲ್ಲಿಸಲಾಗಿಲ್ಲ.",
    "How this works": "ಇದು ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ",
    "Part A": "ಭಾಗ A",
    "Part B": "ಭಾಗ B",
    "Part A already submitted": "ಭಾಗ A ಈಗಾಗಲೇ ಸಲ್ಲಿಸಲಾಗಿದೆ",
    "Teacher Rating": "ಅಧ್ಯಾಪಕರ ಮೌಲ್ಯಮಾಪನ",
    "Select faculty": "ಅಧ್ಯಾಪಕರನ್ನು ಆಯ್ಕೆಮಾಡಿ",
    "Select department first": "ಮೊದಲು ವಿಭಾಗ ಆಯ್ಕೆಮಾಡಿ",
    "Faculty Dashboard": "ಅಧ್ಯಾಪಕರ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
    "Feedbacks": "ಪ್ರತಿಕ್ರಿಯೆಗಳು",
    "Print / Save PDF": "ಮುದ್ರಿಸಿ / PDF ಉಳಿಸಿ",
    "Page not found": "ಪುಟ ಕಂಡುಬಂದಿಲ್ಲ",
    "Assessment of the Curriculum/Course/Academic Programme by Students - Form A": "ವಿದ್ಯಾರ್ಥಿಗಳಿಂದ ಪಠ್ಯಕ್ರಮ/ಕೋರ್ಸ್/ಶೈಕ್ಷಣಿಕ ಕಾರ್ಯಕ್ರಮದ ಮೌಲ್ಯಮಾಪನ - ಫಾರ್ಮ್ A",
    "Department": "ವಿಭಾಗ",
    "The most important reason for selecting the course (tick only one)": "ಈ ಕೋರ್ಸ್ ಆಯ್ಕೆಮಾಡಲು ಅತ್ಯಂತ ಪ್ರಮುಖ ಕಾರಣ (ಒಂದನ್ನು ಮಾತ್ರ ಗುರುತಿಸಿ)",
    "2. Department Facilities": "2. ವಿಭಾಗದ ಸೌಲಭ್ಯಗಳು",
    "Rate each facility on a 5 point scale: 1 - Very poor, 2 - Poor, 3 - Satisfactory, 4 - Good, 5 - Very good.": "ಪ್ರತಿ ಸೌಲಭ್ಯವನ್ನು 5 ಅಂಕಗಳ ಮಾಪಕದಲ್ಲಿ ಮೌಲ್ಯಮಾಪನ ಮಾಡಿ: 1 - ತುಂಬಾ ಕಳಪೆ, 2 - ಕಳಪೆ, 3 - ತೃಪ್ತಿಕರ, 4 - ಉತ್ತಮ, 5 - ತುಂಬಾ ಉತ್ತಮ.",
    "Select Faculty for Part B": "ಭಾಗ B ಗಾಗಿ ಅಧ್ಯಾಪಕರನ್ನು ಆಯ್ಕೆಮಾಡಿ",
    "Assessment of the Teachers by Students - Form B": "ವಿದ್ಯಾರ್ಥಿಗಳಿಂದ ಅಧ್ಯಾಪಕರ ಮೌಲ್ಯಮಾಪನ - ಫಾರ್ಮ್ B",
    "Rate the selected teacher on each statement from 1 - Very poor to 5 - Very good.": "ಆಯ್ಕೆ ಮಾಡಿದ ಅಧ್ಯಾಪಕರನ್ನು ಪ್ರತಿ ಹೇಳಿಕೆಗೆ 1 - ತುಂಬಾ ಕಳಪೆ ರಿಂದ 5 - ತುಂಬಾ ಉತ್ತಮದವರೆಗೆ ಮೌಲ್ಯಮಾಪನ ಮಾಡಿ.",
    "Comments": "ಟಿಪ್ಪಣಿಗಳು",
    "Submit Feedback": "ಪ್ರತಿಕ್ರಿಯೆ ಸಲ್ಲಿಸಿ",
    "Question": "ಪ್ರಶ್ನೆ",
    "Marks (1-5)": "ಅಂಕಗಳು (1-5)",
    "Interested in this subject": "ಈ ವಿಷಯದಲ್ಲಿ ಆಸಕ್ತಿ ಇದೆ",
    "Parents/Friends forced me": "ಪೋಷಕರು/ಸ್ನೇಹಿತರು ಒತ್ತಾಯಿಸಿದರು",
    "UG marks was high in this subject": "ಈ ವಿಷಯದಲ್ಲಿ ಪದವಿ ಅಂಕಗಳು ಹೆಚ್ಚು ಇದ್ದವು",
    "Easy to get admission to this course": "ಈ ಕೋರ್ಸ್‌ಗೆ ಪ್ರವೇಶ ಪಡೆಯುವುದು ಸುಲಭ",
    "Easy to pass in this subject": "ಈ ವಿಷಯದಲ್ಲಿ ಉತ್ತೀರ್ಣರಾಗುವುದು ಸುಲಭ",
    "Department has good name / reputation": "ವಿಭಾಗಕ್ಕೆ ಉತ್ತಮ ಹೆಸರು / ಖ್ಯಾತಿ ಇದೆ",
    "Jobs are easier to get": "ಉದ್ಯೋಗ ಪಡೆಯುವುದು ಸುಲಭ",
    "Scholarship/stipend is available": "ವಿದ್ಯಾರ್ಥಿವೇತನ/ಸ್ಟೈಪೆಂಡ್ ಲಭ್ಯವಿದೆ",
    "Class Rooms space available": "ತರಗತಿ ಕೊಠಡಿಗಳ ಸ್ಥಳ ಲಭ್ಯವಿದೆ",
    "Chairs/Desks / Cupboards etc.": "ಕುರ್ಚಿಗಳು/ಮೇಜುಗಳು/ಅಲಮಾರಿಗಳು ಇತ್ಯಾದಿ",
    "Lighting / Ventilation": "ಬೆಳಕು / ಗಾಳಿಯಾಡುವಿಕೆ",
    "Drinking water": "ಕುಡಿಯುವ ನೀರು",
    "Toilets / Sanitation": "ಶೌಚಾಲಯಗಳು / ಸ್ವಚ್ಛತೆ",
    "Ladies room": "ಮಹಿಳೆಯರ ಕೊಠಡಿ",
    "Cooperation of the office staff": "ಕಚೇರಿ ಸಿಬ್ಬಂದಿಯ ಸಹಕಾರ",
    "Syllabus for this course is": "ಈ ಕೋರ್ಸ್‌ನ ಪಠ್ಯಕ್ರಮವು",
    "Quantum of the syllabus taught in the class": "ತರಗತಿಯಲ್ಲಿ ಬೋಧಿಸಲಾದ ಪಠ್ಯಕ್ರಮದ ಪ್ರಮಾಣ",
    "Library facilities to support the course are": "ಕೋರ್ಸ್‌ಗೆ ಬೆಂಬಲ ನೀಡುವ ಗ್ರಂಥಾಲಯ ಸೌಲಭ್ಯಗಳು",
    "Prescribed text books and references for the course are available": "ಕೋರ್ಸ್‌ಗೆ ನಿಗದಿಪಡಿಸಿದ ಪಠ್ಯಪುಸ್ತಕಗಳು ಮತ್ತು ಉಲ್ಲೇಖ ಗ್ರಂಥಗಳು ಲಭ್ಯವಿವೆ",
    "Classes are held": "ತರಗತಿಗಳು ನಡೆಯುತ್ತವೆ",
    "Internal assessment evaluations are": "ಆಂತರಿಕ ಮೌಲ್ಯಮಾಪನಗಳು",
    "Internal assessment helps to improve grades / performance": "ಆಂತರಿಕ ಮೌಲ್ಯಮಾಪನವು ಅಂಕಗಳು / ಕಾರ್ಯಕ್ಷಮತೆಯನ್ನು ಸುಧಾರಿಸಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ",
    "Outlines of course/syllabus were given at the beginning": "ಕೋರ್ಸ್/ಪಠ್ಯಕ್ರಮದ ರೂಪರೇಖೆಯನ್ನು ಆರಂಭದಲ್ಲೇ ನೀಡಲಾಯಿತು",
    "Would you say the course prepares you for your future career?": "ಈ ಕೋರ್ಸ್ ನಿಮ್ಮ ಭವಿಷ್ಯದ ವೃತ್ತಿಜೀವನಕ್ಕೆ ಸಿದ್ಧಪಡಿಸುತ್ತದೆ ಎಂದು ನೀವು ಹೇಳುವಿರಾ?",
    "When you meet students in similar courses studying in other institutions, do you feel": "ಇತರ ಸಂಸ್ಥೆಗಳಲ್ಲಿ ಇದೇ ರೀತಿಯ ಕೋರ್ಸ್‌ಗಳಲ್ಲಿ ಓದುತ್ತಿರುವ ವಿದ್ಯಾರ್ಥಿಗಳನ್ನು ಭೇಟಿಯಾದಾಗ ನಿಮಗೆ ಅನಿಸುವುದು",
    "After leaving this institution how will you talk about it?": "ಈ ಸಂಸ್ಥೆಯನ್ನು ಬಿಟ್ಟ ನಂತರ ಅದರ ಬಗ್ಗೆ ನೀವು ಹೇಗೆ ಮಾತನಾಡುವಿರಿ?",
    "On the whole, how would you rate the programme/course?": "ಒಟ್ಟಿನಲ್ಲಿ, ಕಾರ್ಯಕ್ರಮ/ಕೋರ್ಸ್ ಅನ್ನು ನೀವು ಹೇಗೆ ಮೌಲ್ಯಮಾಪನ ಮಾಡುತ್ತೀರಿ?",
    "University administrative support related to your studies is": "ನಿಮ್ಮ ಅಧ್ಯಯನಕ್ಕೆ ಸಂಬಂಧಿಸಿದ ವಿಶ್ವವಿದ್ಯಾಲಯದ ಆಡಳಿತಾತ್ಮಕ ಬೆಂಬಲವು",
    "Challenging": "ಸವಾಲಿನದು",
    "Adequate": "ಸಾಕಷ್ಟು",
    "Inadequate": "ಅಸಮರ್ಪಕ",
    "Boring/dull": "ನೀರಸ",
    "90%-100%": "90%-100%",
    "75%-90%": "75%-90%",
    "50%-75%": "50%-75%",
    "Less than 50%": "50% ಕ್ಕಿಂತ ಕಡಿಮೆ",
    "Excellent": "ಅತ್ಯುತ್ತಮ",
    "Not so good": "ಅಷ್ಟು ಉತ್ತಮವಲ್ಲ",
    "Poor/inadequate": "ಕಳಪೆ/ಅಸಮರ್ಪಕ",
    "Easily": "ಸುಲಭವಾಗಿ",
    "Often": "ಆಗಾಗ್ಗೆ",
    "Inadequately": "ಅಸಮರ್ಪಕವಾಗಿ",
    "Not at all": "ಎಂದಿಗೂ ಇಲ್ಲ",
    "Very regularly": "ತುಂಬಾ ನಿಯಮಿತವಾಗಿ",
    "Fairly regularly": "ಸಾಕಷ್ಟು ನಿಯಮಿತವಾಗಿ",
    "Irregularly": "ಅನಿಯಮಿತವಾಗಿ",
    "Very irregularly": "ತುಂಬಾ ಅನಿಯಮಿತವಾಗಿ",
    "Very fair": "ತುಂಬಾ ನ್ಯಾಯಸಮ್ಮತ",
    "Fair": "ನ್ಯಾಯಸಮ್ಮತ",
    "Unfair": "ಅನ್ಯಾಯ",
    "Not sure": "ಖಚಿತವಿಲ್ಲ",
    "Yes": "ಹೌದು",
    "To some extent": "ಸ್ವಲ್ಪ ಮಟ್ಟಿಗೆ",
    "I don't think so": "ನನಗೆ ಹಾಗೆ ಅನಿಸುವುದಿಲ್ಲ",
    "Not at all useful": "ಎಂದಿಗೂ ಉಪಯುಕ್ತವಲ್ಲ",
    "Most of the time": "ಹೆಚ್ಚಿನ ಸಮಯ",
    "Rarely": "ಅಪರೂಪವಾಗಿ",
    "Never": "ಎಂದಿಗೂ ಇಲ್ಲ",
    "Very well": "ತುಂಬಾ ಚೆನ್ನಾಗಿ",
    "Well": "ಚೆನ್ನಾಗಿ",
    "Not much": "ಹೆಚ್ಚಾಗಿಲ್ಲ",
    "Not at all relevant": "ಯಾವುದೇ ರೀತಿಯಲ್ಲಿ ಸಂಬಂಧಿಸಿಲ್ಲ",
    "Better off": "ಉತ್ತಮ ಸ್ಥಿತಿಯಲ್ಲಿ",
    "Equal": "ಸಮಾನ",
    "Worse than them": "ಅವರಿಗಿಂತ ಕೆಳಮಟ್ಟದಲ್ಲಿ",
    "With pride": "ಹೆಮ್ಮೆಯಿಂದ",
    "With satisfaction": "ತೃಪ್ತಿಯಿಂದ",
    "Indifferently": "ನಿರಾಸಕ್ತಿಯಿಂದ",
    "Good": "ಉತ್ತಮ",
    "Poor": "ಕಳಪೆ",
    "Very poor": "ತುಂಬಾ ಕಳಪೆ",
    "Satisfactory": "ತೃಪ್ತಿಕರ",
    "Not satisfactory": "ತೃಪ್ತಿಕರವಲ್ಲ",
    "Is regular in taking classes": "ತರಗತಿಗಳನ್ನು ನಿಯಮಿತವಾಗಿ ತೆಗೆದುಕೊಳ್ಳುತ್ತಾರೆ",
    "Has good command over language": "ಭಾಷೆಯ ಮೇಲೆ ಉತ್ತಮ ಹಿಡಿತವಿದೆ",
    "Knows the subject well": "ವಿಷಯವನ್ನು ಚೆನ್ನಾಗಿ ತಿಳಿದಿದ್ದಾರೆ",
    "Generates interest in the subjects": "ವಿಷಯಗಳಲ್ಲಿ ಆಸಕ್ತಿ ಮೂಡಿಸುತ್ತಾರೆ",
    "Encourages to ask questions": "ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳಲು ಪ್ರೋತ್ಸಾಹಿಸುತ್ತಾರೆ",
    "Is punctual and maintains class decorum": "ಸಮಯಪಾಲಕರು ಮತ್ತು ತರಗತಿಯ ಶಿಸ್ತನ್ನು ಕಾಯ್ದುಕೊಳ್ಳುತ್ತಾರೆ",
    "Takes the class for full period": "ಪೂರ್ಣ ಅವಧಿಗೆ ತರಗತಿ ನಡೆಸುತ್ತಾರೆ",
    "Provides course outline in the beginning": "ಆರಂಭದಲ್ಲಿ ಕೋರ್ಸ್ ರೂಪರೇಖೆಯನ್ನು ನೀಡುತ್ತಾರೆ",
    "Provides summary at the end of lecture / course": "ಉಪನ್ಯಾಸ / ಕೋರ್ಸ್ ಅಂತ್ಯದಲ್ಲಿ ಸಾರಾಂಶವನ್ನು ನೀಡುತ್ತಾರೆ",
    "Uses instructional aids like audiovisuals / OHP": "ಆಡಿಯೋವಿಜುವಲ್ / OHP ಮುಂತಾದ ಬೋಧನಾ ಸಾಧನಗಳನ್ನು ಬಳಸುತ್ತಾರೆ",
    "Does not merely dictate notes, explains well": "ಕೇವಲ ಟಿಪ್ಪಣಿಗಳನ್ನು ಹೇಳುವುದಲ್ಲ, ಚೆನ್ನಾಗಿ ವಿವರಿಸುತ್ತಾರೆ",
    "Provides a broader perspective of the subject": "ವಿಷಯದ ವಿಶಾಲ ದೃಷ್ಟಿಕೋನವನ್ನು ನೀಡುತ್ತಾರೆ",
    "Clarifies doubts / questions raised": "ಎದ್ದ ಅನುಮಾನಗಳು / ಪ್ರಶ್ನೆಗಳನ್ನು ಸ್ಪಷ್ಟಪಡಿಸುತ್ತಾರೆ",
    "Is impartial in evaluation / giving marks": "ಮೌಲ್ಯಮಾಪನ / ಅಂಕ ನೀಡುವಲ್ಲಿ ಪಕ್ಷಪಾತವಿಲ್ಲ",
    "Always completes the syllabus": "ಯಾವಾಗಲೂ ಪಠ್ಯಕ್ರಮವನ್ನು ಪೂರ್ಣಗೊಳಿಸುತ್ತಾರೆ",
    "Is available after class for discussion": "ತರಗತಿಯ ನಂತರ ಚರ್ಚೆಗೆ ಲಭ್ಯವಿರುತ್ತಾರೆ",
    "Explains applicability of concepts": "ಪರಿಕಲ್ಪನೆಗಳ ಅನ್ವಯಿಕತೆಯನ್ನು ವಿವರಿಸುತ್ತಾರೆ",
    "Gives latest information": "ಇತ್ತೀಚಿನ ಮಾಹಿತಿಯನ್ನು ನೀಡುತ್ತಾರೆ",
    "Motivates": "ಪ್ರೇರೇಪಿಸುತ್ತಾರೆ",
    "Is a good role model": "ಉತ್ತಮ ಆದರ್ಶ ವ್ಯಕ್ತಿಯಾಗಿದ್ದಾರೆ",
}


class MySQLConnection:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()
        return False

    def execute(self, sql, params=()):
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return cursor

    def executescript(self, script):
        cursor = self.conn.cursor()
        for statement in script.split(";"):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        return cursor


def env_value(*names, default=""):
    for name in names:
        value = (os.environ.get(name) or "").strip()
        if value:
            return value
    return default


def mysql_config():
    database_url = env_value("MYSQL_URL", "DATABASE_URL")
    ssl_enabled = env_value("MYSQL_SSL", "TIDB_ENABLE_SSL").lower() in ("1", "true", "yes", "on", "required")
    if database_url:
        parsed = urlparse(database_url)
        if parsed.scheme.startswith("mysql"):
            query = parse_qs(parsed.query)
            ssl_enabled = ssl_enabled or query.get("ssl", [""])[0].lower() in ("1", "true", "yes", "on", "required")
            config = {
                "host": parsed.hostname or "127.0.0.1",
                "port": parsed.port or 3306,
                "user": unquote(parsed.username or "root"),
                "password": unquote(parsed.password or ""),
                "database": unquote_plus((parsed.path or "/student_feedback").lstrip("/") or "student_feedback"),
            }
            if ssl_enabled:
                config["ssl"] = {}
            return config
    config = {
        "host": env_value("MYSQL_HOST", "MYSQLHOST", default="127.0.0.1"),
        "port": int(env_value("MYSQL_PORT", "MYSQLPORT", default="3306")),
        "user": env_value("MYSQL_USER", "MYSQLUSER", default="root"),
        "password": env_value("MYSQL_PASSWORD", "MYSQLPASSWORD"),
        "database": env_value("MYSQL_DATABASE", "MYSQLDATABASE", default="student_feedback"),
    }
    if ssl_enabled:
        config["ssl"] = {}
    return config


def mysql_connection():
    if pymysql is None:
        raise RuntimeError("PyMySQL is required for MySQL storage. Run: pip install -r requirements.txt")
    config = mysql_config()
    host = config["host"]
    port = config["port"]
    user = config["user"]
    password = config["password"]
    database = config["database"]
    ssl = config.get("ssl")
    safe_database = database.replace("`", "``")
    server = pymysql.connect(host=host, port=port, user=user, password=password, charset="utf8mb4", autocommit=True, ssl=ssl)
    try:
        with server.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{safe_database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    finally:
        server.close()
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
        ssl=ssl,
    )
    return MySQLConnection(conn)


def db():
    load_env_file()
    return mysql_connection()


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def check_password(password, stored):
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    return hash_password(password, salt).split("$", 1)[1] == digest


def student_login_id(roll_number):
    return (roll_number or "").strip()


def student_default_password(name):
    first_name = (name or "").strip().split()[0].lower()
    return f"{first_name[:3]}123"


def otp_key(user):
    return f"{user['role']}:{user['id']}"


def load_env_file(path=".env"):
    global ENV_LOADED
    if ENV_LOADED:
        return
    ENV_LOADED = True
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and not (os.environ.get(key) or "").strip():
                os.environ[key] = value


def send_otp_email(to_email, name, otp):
    load_env_file()
    subject = "Password change OTP"
    text = (
        f"Hello {name},\n\n"
        f"Your one-time OTP to change your password is {otp}.\n"
        "This OTP is valid for 10 minutes and can be used only once.\n\n"
        f"{APP_NAME}"
    )
    host = (os.environ.get("SMTP_HOST") or "").strip()
    if not host:
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = (os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER") or "noreply@localhost").strip()
    message["To"] = to_email
    message.set_content(text)

    port = int((os.environ.get("SMTP_PORT") or "587").strip())
    username = (os.environ.get("SMTP_USER") or "").strip()
    password = "".join((os.environ.get("SMTP_PASSWORD") or "").split())
    with smtplib.SMTP(host, port, timeout=15) as smtp:
        smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)
    return True


def save_password_otp(user, email, otp):
    PASSWORD_OTPS[otp_key(user)] = {
        "otp": otp,
        "email": email,
        "expires": time.time() + 600,
        "used": False,
    }


def request_password_otp(user, email, name, otp, success_message):
    try:
        sent = send_otp_email(email, name, otp)
    except Exception:
        sent = False

    if not sent:
        return flash("Could not send the verification code. Please check SMTP email settings and try again.", "bad"), False

    save_password_otp(user, email, otp)
    return flash(success_message), True


def valid_email(email):
    return "@" in (email or "") and not email.endswith("@student.local")


def normalize_otp(value):
    return re.sub(r"\D", "", value or "")


def table_columns(conn, table):
    rows = conn.execute(
        """
        SELECT COLUMN_NAME AS name
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s
        ORDER BY ORDINAL_POSITION
        """,
        (table,),
    ).fetchall()
    return {row["name"] for row in rows}


def resequence_table(conn, table, reference_updates=()):
    rows = conn.execute(f"SELECT id FROM {table} ORDER BY id").fetchall()
    moves = [(row["id"], index) for index, row in enumerate(rows, start=1) if row["id"] != index]
    if moves:
        conn.execute("SET FOREIGN_KEY_CHECKS=0")
        try:
            for old_id, new_id in moves:
                conn.execute(f"UPDATE {table} SET id=%s WHERE id=%s", (-new_id, old_id))
                for ref_table, ref_column in reference_updates:
                    conn.execute(f"UPDATE {ref_table} SET {ref_column}=%s WHERE {ref_column}=%s", (-new_id, old_id))
            for _, new_id in moves:
                conn.execute(f"UPDATE {table} SET id=%s WHERE id=%s", (new_id, -new_id))
                for ref_table, ref_column in reference_updates:
                    conn.execute(f"UPDATE {ref_table} SET {ref_column}=%s WHERE {ref_column}=%s", (new_id, -new_id))
        finally:
            conn.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.execute(f"ALTER TABLE {table} AUTO_INCREMENT={len(rows) + 1}")


def resequence_students(conn):
    resequence_table(conn, "students", (("feedback", "student_id"),))


def resequence_faculty(conn):
    resequence_table(conn, "faculty", (("feedback", "faculty_id"), ("departments", "hod_faculty_id")))


def resequence_admins(conn):
    resequence_table(conn, "admins", (("students", "created_by_admin_id"),))


def resequence_departments(conn):
    resequence_table(conn, "departments")


def resequence_feedback(conn):
    resequence_table(conn, "feedback")


def resequence_all_tables(conn):
    resequence_admins(conn)
    resequence_faculty(conn)
    resequence_students(conn)
    resequence_departments(conn)
    resequence_feedback(conn)


def ensure_students_username_index(conn):
    row = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='students' AND INDEX_NAME='idx_students_username'
        """
    ).fetchone()
    if not row["count"]:
        conn.execute("CREATE UNIQUE INDEX idx_students_username ON students(username)")


def init_db():
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS admins (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS students (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL,
                roll_number VARCHAR(255) NOT NULL UNIQUE,
                department VARCHAR(255) NOT NULL,
                username VARCHAR(255) UNIQUE,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_by_admin_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS faculty (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL,
                employee_id VARCHAR(255) NOT NULL UNIQUE,
                department VARCHAR(255) NOT NULL,
                subject VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS departments (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL UNIQUE,
                hod_faculty_id INT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INT PRIMARY KEY AUTO_INCREMENT,
                student_id INT NOT NULL,
                faculty_id INT NOT NULL,
                course VARCHAR(255) NOT NULL,
                clarity INT NOT NULL,
                punctuality INT NOT NULL,
                knowledge INT NOT NULL,
                interaction INT NOT NULL,
                overall INT NOT NULL,
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS department_feedback_windows (
                department VARCHAR(255) PRIMARY KEY,
                start_at VARCHAR(32) NOT NULL,
                end_at VARCHAR(32) NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        columns = table_columns(conn, "feedback")
        for name, definition in {
            "reason": "TEXT",
            "facilities_json": "TEXT",
            "course_answers_json": "TEXT",
            "teacher_answers_json": "TEXT",
            "language_preference": "TEXT",
        }.items():
            if name not in columns:
                conn.execute(f"ALTER TABLE feedback ADD COLUMN {name} {definition}")
        student_columns = table_columns(conn, "students")
        if "username" not in student_columns:
            conn.execute("ALTER TABLE students ADD COLUMN username VARCHAR(255)")
            conn.execute("UPDATE students SET username=roll_number WHERE username IS NULL")
        if "created_by_admin_id" not in student_columns:
            conn.execute("ALTER TABLE students ADD COLUMN created_by_admin_id INT")
        conn.execute("UPDATE students SET username=roll_number WHERE username IS NULL OR BINARY username <> BINARY roll_number")
        ensure_students_username_index(conn)
        existing_departments = [
            row["department"]
            for row in conn.execute(
                """
                SELECT DISTINCT department FROM faculty WHERE trim(department) <> ''
                UNION
                SELECT DISTINCT department FROM students WHERE trim(department) <> ''
                """
            ).fetchall()
        ]
        for department in existing_departments:
            conn.execute("INSERT IGNORE INTO departments(name) VALUES(%s)", (department,))
        admin_exists = conn.execute(
            "SELECT id FROM admins WHERE email=%s LIMIT 1", (ADMIN_EMAIL,)
        ).fetchone()
        if not admin_exists:
            admin_password = env_value("ADMIN_PASSWORD")
            if not admin_password:
                raise RuntimeError(
                    "ADMIN_PASSWORD must be set before starting a new deployment."
                )
            conn.execute(
                "INSERT INTO admins(name,email,password_hash) VALUES(%s,%s,%s)",
                (ADMIN_NAME, ADMIN_EMAIL, hash_password(admin_password)),
            )
        conn.execute("UPDATE admins SET name=%s WHERE email=%s", (ADMIN_NAME, ADMIN_EMAIL))
        resequence_all_tables(conn)


def esc(value):
    return html.escape(str(value or ""), quote=True)


CHART_COLORS = ["#0f6b63", "#b63143", "#2f3aa4", "#c95d08", "#198649", "#6b4bc3", "#0f78a8"]


def chart_legend(items):
    if not items:
        return '<p class="chart-empty">No feedback submitted yet.</p>'
    return "".join(
        f"""
        <div class="chart-legend-row">
            <span class="chart-swatch" style="background:{esc(item['color'])}"></span>
            <span>{esc(item['label'])}</span>
            <strong>{esc(item['value_label'])}</strong>
        </div>
        """
        for item in items
    )


def donut_chart(title, subtitle, data):
    total = sum(value for _, value in data)
    if total <= 0:
        return f"""
        <article class="panel chart-card">
            <h2>{esc(title)}</h2>
            <p>{esc(subtitle)}</p>
            <div class="chart-empty">No feedback submitted yet.</div>
        </article>
        """

    radius = 44
    circumference = 2 * math.pi * radius
    offset = 0
    segments = []
    legend_items = []
    for index, (label, value) in enumerate(data):
        if value <= 0:
            continue
        color = CHART_COLORS[index % len(CHART_COLORS)]
        dash = (value / total) * circumference
        gap = max(circumference - dash, 0)
        segments.append(
            f'<circle cx="60" cy="60" r="{radius}" fill="none" stroke="{color}" stroke-width="22" '
            f'stroke-dasharray="{dash:.2f} {gap:.2f}" stroke-dashoffset="-{offset:.2f}" '
            'transform="rotate(-90 60 60)" />'
        )
        offset += dash
        legend_items.append(
            {
                "label": label,
                "value_label": f"{value} ({(value / total) * 100:.1f}%)",
                "color": color,
            }
        )

    return f"""
    <article class="panel chart-card">
        <h2>{esc(title)}</h2>
        <p>{esc(subtitle)}</p>
        <div class="donut-chart">
            <svg viewBox="0 0 120 120" role="img" aria-label="{esc(title)}">
                <circle cx="60" cy="60" r="{radius}" fill="none" stroke="#e7edf4" stroke-width="22" />
                {''.join(segments)}
                <circle cx="60" cy="60" r="27" fill="#fff" />
                <text x="60" y="58" text-anchor="middle" class="chart-total">{total}</text>
                <text x="60" y="74" text-anchor="middle" class="chart-caption">total</text>
            </svg>
            <div class="chart-legend">{chart_legend(legend_items)}</div>
        </div>
    </article>
    """


def horizontal_bar_chart(title, subtitle, data):
    if not data:
        return f"""
        <article class="panel chart-card">
            <h2>{esc(title)}</h2>
            <p>{esc(subtitle)}</p>
            <div class="chart-empty">No department feedback submitted yet.</div>
        </article>
        """
    rows = []
    for index, (label, average, count) in enumerate(data):
        color = CHART_COLORS[index % len(CHART_COLORS)]
        percent = max(0, min((average / 5) * 100, 100)) if average else 0
        rows.append(
            f"""
            <div class="bar-row">
                <div class="bar-meta"><span>{esc(label)}</span><strong>{average:.2f}/5</strong></div>
                <div class="bar-track"><span style="width:{percent:.1f}%;background:{color}"></span></div>
                <small>{count} submissions</small>
            </div>
            """
        )
    return f"""
    <article class="panel chart-card">
        <h2>{esc(title)}</h2>
        <p>{esc(subtitle)}</p>
        <div class="bar-chart">{''.join(rows)}</div>
    </article>
    """


def column_chart(title, subtitle, data):
    if not data:
        return f"""
        <article class="panel chart-card">
            <h2>{esc(title)}</h2>
            <p>{esc(subtitle)}</p>
            <div class="chart-empty">No faculty feedback submitted yet.</div>
        </article>
        """
    columns = []
    for index, (label, average, count) in enumerate(data):
        color = CHART_COLORS[index % len(CHART_COLORS)]
        height = max(8, min((average / 5) * 100, 100)) if average else 8
        columns.append(
            f"""
            <div class="column-item">
                <div class="column-wrap"><span style="height:{height:.1f}%;background:{color}"></span></div>
                <strong>{average:.2f}</strong>
                <small title="{esc(label)}">{esc(label)}</small>
                <em>{count}</em>
            </div>
            """
        )
    return f"""
    <article class="panel chart-card">
        <h2>{esc(title)}</h2>
        <p>{esc(subtitle)}</p>
        <div class="column-chart">{''.join(columns)}</div>
    </article>
    """


def indian_now():
    return datetime.now(INDIA_TIMEZONE)


def academic_year_label(now=None):
    current = now or indian_now()
    start_year = current.year if current.month >= 6 else current.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def indian_datetime_label(value=None):
    if not value:
        dt = indian_now()
    elif isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        parsed = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                parsed = datetime.strptime(text.replace("Z", ""), fmt)
                break
            except ValueError:
                pass
        if parsed is None:
            try:
                parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            except ValueError:
                return text
        dt = parsed
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(INDIA_TIMEZONE).strftime("%d-%m-%Y %I:%M %p IST")


def parse_slot_datetime(value):
    text = (value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.strptime(text, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None
    return dt.replace(tzinfo=INDIA_TIMEZONE)


def slot_input_value(value):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=INDIA_TIMEZONE)
    return dt.astimezone(INDIA_TIMEZONE).strftime("%Y-%m-%dT%H:%M")


def feedback_window_status(window, now=None):
    if not window:
        return ("not_set", "Feedback time slot is not set.")
    current = now or indian_now()
    try:
        start = datetime.fromisoformat(str(window["start_at"]).replace("Z", "+00:00"))
        end = datetime.fromisoformat(str(window["end_at"]).replace("Z", "+00:00"))
    except ValueError:
        return ("not_set", "Feedback time slot is not valid.")
    if start.tzinfo is None:
        start = start.replace(tzinfo=INDIA_TIMEZONE)
    if end.tzinfo is None:
        end = end.replace(tzinfo=INDIA_TIMEZONE)
    start = start.astimezone(INDIA_TIMEZONE)
    end = end.astimezone(INDIA_TIMEZONE)
    if current < start:
        return ("upcoming", f"Feedback opens on {indian_datetime_label(start)}.")
    if current > end:
        return ("closed", f"Feedback closed on {indian_datetime_label(end)}.")
    return ("open", f"Feedback is open until {indian_datetime_label(end)}.")


def department_feedback_window_status(conn, department, now=None):
    current = now or indian_now()
    windows = conn.execute(
        """
        SELECT start_at, end_at
        FROM department_feedback_windows
        WHERE department=%s AND start_at IS NOT NULL AND end_at IS NOT NULL
        """,
        (department,),
    ).fetchall()
    if not windows:
        return ("not_set", "Feedback form is closed. The admin has not set a timeline for your department.")

    parsed_windows = []
    for window in windows:
        try:
            start = datetime.fromisoformat(str(window["start_at"]).replace("Z", "+00:00"))
            end = datetime.fromisoformat(str(window["end_at"]).replace("Z", "+00:00"))
        except ValueError:
            continue
        if start.tzinfo is None:
            start = start.replace(tzinfo=INDIA_TIMEZONE)
        if end.tzinfo is None:
            end = end.replace(tzinfo=INDIA_TIMEZONE)
        parsed_windows.append((start.astimezone(INDIA_TIMEZONE), end.astimezone(INDIA_TIMEZONE)))

    if not parsed_windows:
        return ("not_set", "Feedback form is closed. The department time slot is not valid.")

    open_windows = [(start, end) for start, end in parsed_windows if start <= current <= end]
    if open_windows:
        end = max(end for _, end in open_windows)
        return ("open", f"Feedback form is open until {indian_datetime_label(end)}.")

    upcoming_windows = [(start, end) for start, end in parsed_windows if current < start]
    if upcoming_windows:
        start = min(start for start, _ in upcoming_windows)
        return ("upcoming", f"Feedback form opens on {indian_datetime_label(start)}.")

    end = max(end for _, end in parsed_windows)
    return ("closed", f"Feedback form closed on {indian_datetime_label(end)}.")


def page(title, body, user=None, show_account_actions=True, show_guest_nav=True):
    language = current_language()
    lang_attr = "kn" if language == "kn" else "en"
    nav = ""
    if user:
        password_link = ""
        logout_link = ""
        if show_account_actions and user["role"] in ("admin", "faculty", "student"):
            password_link = f'<a class="button ghost" href="/account/password">{localized_text("Change Password", language)}</a>'
        if show_account_actions:
            logout_link = f'<a class="button ghost" href="/logout">{localized_text("Logout", language)}</a>'
        nav = f"""
        <nav class="topbar">
            <a class="brand" href="/">{localized_text(APP_NAME, language)}</a>
            <div class="nav-actions">
                <span>{esc(user['role']).title()}: {esc(user['name'])}</span>
                {language_selector(current_path())}
                {password_link}
                {logout_link}
            </div>
        </nav>
        """
    elif show_guest_nav:
        nav = f"""
        <nav class="topbar">
            <a class="brand" href="/">{localized_text(APP_NAME, language)}</a>
            <div class="nav-actions">
                {language_selector(current_path())}
                <a href="/admin/login">{localized_text("Admin", language)}</a>
                <a href="/faculty/login">{localized_text("Faculty", language)}</a>
                <a href="/student/login">{localized_text("Student", language)}</a>
            </div>
        </nav>
        """
    return f"""<!doctype html>
    <html lang="{lang_attr}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="theme-color" content="#0f6b63">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-title" content="BU Feedback">
        <link rel="manifest" href="/static/manifest.webmanifest">
        <title>{localized_text(title, language)} - {localized_text(APP_NAME, language)}</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        {nav}
        <main class="shell">{body}</main>
        {translation_script()}
    </body>
    </html>"""


def field(label, name, kind="text", required=True, value=""):
    req = "required" if required else ""
    return f"""
    <label>
        <span>{label}</span>
        <input type="{kind}" name="{name}" value="{esc(value)}" {req}>
    </label>
    """


def password_field(label="Password", name="password"):
    language = current_language()
    show = localized_text("Show", language)
    hide = localized_text("Hide", language)
    password_label = localized_text(label, language)
    return f"""
    <label class="password-label">
        <span>{password_label}</span>
        <span class="password-wrap">
            <input type="password" name="{esc(name)}" required>
            <button class="password-toggle" type="button" aria-label="{show}" data-show-label="{show}" data-hide-label="{hide}">{show}</button>
        </span>
    </label>
    """


def password_toggle_script():
    return """
    <script>
    (() => {
        for (const toggle of document.querySelectorAll('.password-toggle')) {
            const input = toggle.parentElement.querySelector('input');
            const showLabel = toggle.dataset.showLabel || 'Show';
            const hideLabel = toggle.dataset.hideLabel || 'Hide';
            toggle.addEventListener('click', () => {
                const shouldShow = input.type === 'password';
                input.type = shouldShow ? 'text' : 'password';
                toggle.textContent = shouldShow ? hideLabel : showLabel;
                toggle.setAttribute('aria-label', shouldShow ? hideLabel : showLabel);
            });
        }
    })();
    </script>
    """


def department_select(label="Department", selected=""):
    options = ['<option value="">Select Department</option>']
    departments = []
    try:
        with db() as conn:
            departments = [row["name"] for row in conn.execute("SELECT name FROM departments ORDER BY name").fetchall()]
    except Exception:
        departments = []
    for department in departments:
        mark = " selected" if department == selected else ""
        options.append(f'<option value="{esc(department)}"{mark}>{esc(department)}</option>')
    return f"""
    <label>
        <span>{label}</span>
        <select name="department" required>{"".join(options)}</select>
    </label>
    """


def textarea(label, name):
    return f"""
    <label>
        <span>{label}</span>
        <textarea name="{name}" rows="4"></textarea>
    </label>
    """


def rating(label, name):
    options = "".join(f"<option value='{n}'>{n}</option>" for n in range(1, 6))
    return f"""
    <label>
        <span>{label}</span>
        <select name="{name}" required>{options}</select>
    </label>
    """


def bilingual_text(english):
    kannada = KN_TRANSLATIONS.get(english)
    if not kannada:
        return esc(english)
    return (
        f'<span class="bilingual">'
        f'<span class="english">{esc(english)}</span>'
        f'<span class="kannada">{esc(kannada)}</span>'
        f'</span>'
    )


def localized_text(english, language="both"):
    if language == "en":
        return esc(english)
    if language == "kn":
        return esc(KN_TRANSLATIONS.get(english, english))
    return bilingual_text(english)


def selected_language(value):
    code = (value or "").strip().lower()
    return code if code in LANGUAGES else ""


def current_language():
    return REQUEST_LANGUAGE.get()


def current_path():
    return REQUEST_PATH.get()


def language_selector(path="/"):
    language = current_language()
    options = "".join(
        f'<option value="{esc(code)}"{" selected" if code == language else ""}>{esc(name)}</option>'
        for code, name in LANGUAGES.items()
    )
    return f"""
    <form class="language-switcher" method="post" action="/language">
        <input type="hidden" name="next" value="{esc(path or '/')}">
        <label>
            <span>{localized_text("Language", language)}</span>
            <select name="language" onchange="this.form.submit()" aria-label="{localized_text("Language", language)}">
                {options}
            </select>
        </label>
    </form>
    """


def translation_script():
    language = current_language()
    if language != "kn":
        return ""
    translations = json.dumps(KN_TRANSLATIONS, ensure_ascii=False)
    return f"""
    <script>
    (() => {{
        const translations = {translations};
        const translateValue = (value) => translations[value.trim()] || "";
        const translateTextNode = (node) => {{
            const text = node.nodeValue;
            const translated = translateValue(text);
            if (translated) {{
                node.nodeValue = text.replace(text.trim(), translated);
            }}
        }};
        const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {{
            acceptNode(node) {{
                const parent = node.parentElement;
                if (!parent || ["SCRIPT", "STYLE"].includes(parent.tagName)) {{
                    return NodeFilter.FILTER_REJECT;
                }}
                return node.nodeValue.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
            }}
        }});
        const nodes = [];
        while (walk.nextNode()) {{
            nodes.push(walk.currentNode);
        }}
        nodes.forEach(translateTextNode);
        document.querySelectorAll("[data-show-label], [data-hide-label]").forEach((item) => {{
            if (item.dataset.showLabel && translations[item.dataset.showLabel]) {{
                item.dataset.showLabel = translations[item.dataset.showLabel];
            }}
            if (item.dataset.hideLabel && translations[item.dataset.hideLabel]) {{
                item.dataset.hideLabel = translations[item.dataset.hideLabel];
            }}
            const translated = translateValue(item.textContent || "");
            if (translated) {{
                item.textContent = translated;
            }}
        }});
        document.title = document.title.split(" - ").map((part) => translations[part] || part).join(" - ");
    }})();
    </script>
    """


def radio_group(number, key, question, options, language="both"):
    choices = "".join(
        f"""
        <label class="choice">
            <input type="radio" name="{esc(key)}" value="{esc(option)}" required>
            <span>{localized_text(option, language)}</span>
        </label>
        """
        for option in options
    )
    return f"""
    <fieldset class="question-block">
        <legend>{number}. {localized_text(question, language)}</legend>
        <div class="choice-grid">{choices}</div>
    </fieldset>
    """


def checkbox_group(number, key, question, options, language="both"):
    choices = "".join(
        f"""
        <label class="choice">
            <input type="checkbox" name="{esc(key)}" value="{esc(option)}">
            <span>{localized_text(option, language)}</span>
        </label>
        """
        for option in options
    )
    return f"""
    <fieldset class="question-block">
        <legend>{number}. {localized_text(question, language)}</legend>
        <div class="choice-grid">{choices}</div>
    </fieldset>
    """


def marks_select(name):
    options = "".join(f"<option value='{n}'>{n}</option>" for n in range(1, 6))
    return f"<select name='{esc(name)}' required>{options}</select>"


def score_table(title, intro, rows, prefix, language="both"):
    body = "".join(
        f"<tr><td>{idx}. {localized_text(row, language)}</td><td>{marks_select(f'{prefix}_{idx}')}</td></tr>"
        for idx, row in enumerate(rows, 1)
    )
    return f"""
    <section class="form-section">
        <h3>{localized_text(title, language)}</h3>
        <p>{localized_text(intro, language)}</p>
        <div class="table-wrap compact">
            <table class="score-table">
                <thead><tr><th>{localized_text("Question", language)}</th><th>{localized_text("Marks (1-5)", language)}</th></tr></thead>
                <tbody>{body}</tbody>
            </table>
        </div>
    </section>
    """


def flash(message, kind="ok"):
    return f"<div class='flash {kind}'>{esc(message)}</div>"


def university_logo(class_name):
    return (
        f'<span class="{class_name}" aria-label="Bangalore University logo">'
        '<img src="/static/images/bangalore-university-logo.png" '
        'alt="Bangalore University logo">'
        "</span>"
    )


def auth_frame(title, card, role="admin"):
    active = {
        "admin": "",
        "faculty": "",
        "student": "",
    }
    if role in active:
        active[role] = " active"
    return f"""
    <section class="auth-page">
        <header class="auth-header">
            <a class="auth-brand" href="/">
                {university_logo("auth-seal")}
                <span>
                    <strong>Bangalore University</strong>
                    <small>Student Feedback Management System</small>
                </span>
            </a>
            <nav class="auth-nav">
                {language_selector(current_path())}
                <a href="/">Home</a>
                <a class="{active['admin']}" href="/admin/login">Admin</a>
                <a class="{active['faculty']}" href="/faculty/login">Faculty</a>
                <a class="{active['student']}" href="/student/login">Student</a>
            </nav>
        </header>

        <div class="auth-stage">
            <aside class="auth-pitch">
                <p class="auth-eyebrow">Share | Suggest | Improve</p>
                <h1>Your Feedback Builds a Better Tomorrow</h1>
                <p>A responsive, transparent and student-friendly campus starts with clear feedback.</p>
                <div class="auth-metrics">
                    <span>Share Your Feedback</span>
                    <span>Suggest Ideas</span>
                    <span>Help Us Improve</span>
                    <span>Stronger University</span>
                </div>
                <p class="auth-script">Students Today<br>A Stronger Bangalore University Tomorrow</p>
            </aside>

            {card}

        </div>

        <footer class="auth-footer">
            <span>Education | Feedback | Better Tomorrow</span>
            <span>Together for a better University.</span>
        </footer>
    </section>
    """


class App(BaseHTTPRequestHandler):
    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def routes(self):
        return {
            "/": self.home,
            "/language": self.change_language,
            "/admin/register": self.admin_register,
            "/admin/login": lambda method: self.login(method, "admin"),
            "/admin/forgot-password": lambda method: self.forgot_password(method, "admin"),
            "/faculty/login": lambda method: self.login(method, "faculty"),
            "/faculty/forgot-password": lambda method: self.forgot_password(method, "faculty"),
            "/student/register": self.student_register,
            "/student/login": lambda method: self.login(method, "student"),
            "/student/forgot-password": lambda method: self.forgot_password(method, "student"),
            "/admin/dashboard": self.admin_dashboard,
            "/student/dashboard": self.student_dashboard,
            "/faculty/dashboard": self.faculty_dashboard,
            "/admin/department/add": self.add_department,
            "/admin/department/hod": self.set_department_hod,
            "/admin/faculty/add": self.add_faculty,
            "/admin/faculty/remove": self.remove_faculty,
            "/admin/student/add": self.add_student,
            "/admin/student/remove": self.remove_student,
            "/admin/feedback-window": self.set_feedback_window,
            "/admin/feedback-review": self.admin_feedback_review,
            "/admin/reports": self.admin_reports,
            "/account/password": self.change_password,
            "/student/feedback": self.submit_feedback,
            "/reports/faculty": self.download_faculty_report,
            "/reports/department": self.download_department_report,
            "/reports/overall": self.overall_report,
        }

    def route(self, method):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path.startswith("/static/"):
            return self.static_file(path)
        language_token = REQUEST_LANGUAGE.set(self.request_language(parsed))
        path_token = REQUEST_PATH.set(self.path or "/")
        try:
            if path == "/logout":
                return self.logout()
            if path == "/health":
                return self.health()
            handler = self.routes().get(path)
            if not handler:
                return self.send_html(page("Not found", "<section class='panel'><h1>Page not found</h1></section>"), 404)
            return handler(method)
        finally:
            REQUEST_LANGUAGE.reset(language_token)
            REQUEST_PATH.reset(path_token)

    def request_language(self, parsed):
        query = parse_qs(parsed.query)
        query_language = selected_language(query.get("site_lang", [""])[0])
        if query_language:
            return query_language
        jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        saved = jar.get("site_language")
        return selected_language(saved.value if saved else "") or "en"

    def health(self):
        data = b"ok"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def change_language(self, method):
        if method == "POST":
            data = self.post_data()
            language = selected_language(data.get("language", ""))
            next_url = data.get("next", "/")
        else:
            query = parse_qs(urlparse(self.path).query)
            language = selected_language(query.get("language", [""])[0])
            next_url = query.get("next", ["/"])[0]
        language = language or "en"
        if not next_url.startswith("/") or next_url.startswith("//"):
            next_url = "/"
        self.send_response(303)
        self.send_header("Location", next_url)
        self.send_header("Set-Cookie", f"site_language={language}; Path=/; SameSite=Lax; Max-Age=31536000")
        self.end_headers()

    def post_data(self, include_lists=False):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        parsed = parse_qs(raw)
        data = {k: v[0] for k, v in parsed.items()}
        if include_lists:
            return data, parsed
        return data

    def current_user(self):
        header = self.headers.get("Cookie", "")
        jar = cookies.SimpleCookie(header)
        sid = jar.get("sid")
        if not sid:
            return None
        session = SESSIONS.get(sid.value)
        if not session:
            return None
        if session["expires"] < time.time():
            SESSIONS.pop(sid.value, None)
            return None
        table = ROLE_TABLES.get(session.get("role"))
        if not table:
            SESSIONS.pop(sid.value, None)
            return None
        with db() as conn:
            row = conn.execute(f"SELECT * FROM {table} WHERE id=%s", (session["id"],)).fetchone()
        if not row:
            SESSIONS.pop(sid.value, None)
            return None
        session["name"] = row["name"]
        if session["role"] in ("student", "faculty"):
            session["department"] = row["department"]
        return session

    def session_cookie(self, sid, max_age=SESSION_SECONDS):
        secure = ""
        if (os.environ.get("COOKIE_SECURE") or "").strip().lower() in ("1", "true", "yes", "on"):
            secure = "; Secure"
        return f"sid={sid}; HttpOnly; Path=/; SameSite=Lax; Max-Age={max_age}{secure}"

    def require(self, role):
        user = self.current_user()
        if not user or user["role"] != role:
            self.redirect(f"/{role}/login")
            return None
        return user

    def send_html(self, content, status=200):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location):
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def css(self):
        css = open("static/style.css", "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", "text/css")
        self.send_header("Content-Length", str(len(css)))
        self.end_headers()
        self.wfile.write(css)

    def static_file(self, path):
        relative_path = unquote(path.removeprefix("/static/"))
        static_root = os.path.abspath("static")
        file_path = os.path.abspath(os.path.join(static_root, relative_path))
        if not file_path.startswith(static_root + os.sep) or not os.path.isfile(file_path):
            return self.not_found()
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        with open(file_path, "rb") as file:
            data = file.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def home(self, method):
        body = f"""
        <section class="home-page" id="home">
            <header class="home-header">
                <a class="home-brand" href="/">
                    {university_logo("home-seal")}
                    <span>
                        <strong>Bangalore University</strong>
                        <small>Knowledge | Progress | Excellence</small>
                    </span>
                </a>
                {language_selector(current_path())}
            </header>

            <section class="home-hero" id="about">
                <div class="home-copy">
                    <p class="home-eyebrow">Bangalore University</p>
                    <h1>Student Feedback<br>Management System</h1>
                    <p>Collect feedback from admin-added students, manage departments, assign HODs, set feedback timelines, and download reports.</p>
                    <span class="home-note">Your feedback drives a better tomorrow</span>
                </div>
            </section>

            <section class="portal-grid">
                <a class="portal-card admin-portal" href="/admin/login">
                    <span class="portal-icon">A</span>
                    <strong>Admin</strong>
                    <span>Admin Portal</span>
                    <em>Go</em>
                </a>
                <a class="portal-card faculty-portal" href="/faculty/login">
                    <span class="portal-icon">F</span>
                    <strong>Faculty</strong>
                    <span>Faculty Portal</span>
                    <em>Go</em>
                </a>
                <a class="portal-card student-portal" href="/student/login">
                    <span class="portal-icon">S</span>
                    <strong>Student</strong>
                    <span>Student Portal</span>
                    <em>Go</em>
                </a>
            </section>

            <footer class="home-strip" id="contact">
                <span>Better Feedback</span>
                <span>Improved Learning</span>
                <span>Stronger Communities</span>
                <span>Education Today, A Brighter Tomorrow</span>
            </footer>
        </section>
        """
        self.send_html(page("Home", body, show_guest_nav=False))

    def admin_register(self, method):
        card = f"""
        <section class="auth-card">
            <span class="auth-card-icon">A</span>
            <h1>Admin Registration Closed</h1>
            <p>Admin registration is disabled. Use the fixed admin account below.</p>
            <p class="auth-hint"><strong>Email:</strong> {esc(ADMIN_EMAIL)}</p>
            <a class="button" href="/admin/login">Go to Admin Login</a>
        </section>
        """
        self.send_html(page("Admin Registration", auth_frame("Admin Registration", card, "admin"), show_guest_nav=False))

    def student_register(self, method):
        card = """
        <section class="auth-card">
            <span class="auth-card-icon">S</span>
            <h1>Student Registration Closed</h1>
            <p>Student accounts are created department-wise by admin. Please contact the admin office for your login ID and default password.</p>
            <a class="button" href="/student/login">Go to Student Login</a>
        </section>
        """
        self.send_html(page("Student Registration", auth_frame("Student Registration", card, "student"), show_guest_nav=False))

    def login(self, method, role):
        msg = ""
        table = ROLE_TABLES[role]
        students = []
        if role == "student":
            with db() as conn:
                students = conn.execute("SELECT * FROM students ORDER BY department,name").fetchall()
        if method == "POST":
            data = self.post_data()
            email = data.get("email", "").strip().lower()
            username = data.get("username", "").strip()
            with db() as conn:
                if role == "student":
                    row = conn.execute("SELECT * FROM students WHERE username=%s", (username,)).fetchone()
                else:
                    row = conn.execute(f"SELECT * FROM {table} WHERE lower(email)=%s", (email,)).fetchone()
            department_matches = True
            if role in ("student", "faculty"):
                department_matches = row and row["department"] == data.get("department")
            if row and department_matches and check_password(data.get("password", ""), row["password_hash"]):
                sid = secrets.token_urlsafe(32)
                SESSIONS[sid] = {
                    "id": row["id"],
                    "name": row["name"],
                    "role": role,
                    "department": row["department"] if role in ("student", "faculty") else "",
                    "expires": time.time() + SESSION_SECONDS,
                }
                self.send_response(303)
                self.send_header("Location", f"/{role}/dashboard")
                self.send_header("Set-Cookie", self.session_cookie(sid))
                self.end_headers()
                return
            msg = flash("Invalid account, password, or department.", "bad")
        register = ""
        if role == "admin":
            register = f'<p class="hint">Use the registered admin email: {esc(ADMIN_EMAIL)}</p>'
        if role == "student":
            register = '<p class="hint">Need an account? Contact the admin office.</p>'
        title = f"{role.title()} Login"
        if role == "student":
            student_options = "".join(
                f'<option value="{esc(s["username"])}" data-department="{esc(s["department"])}">{esc(s["name"])} - ID: {esc(s["username"])}</option>'
                for s in students
            )
            if not student_options:
                student_options = '<option value="">No students are registered yet</option>'
            login_field = f"""
                {department_select()}
                <label>
                    <span>Student Name</span>
                    <select name="username" id="student-login-name" required>
                        <option value="">Select your name</option>
                        {student_options}
                    </select>
                </label>
                <script>
                (() => {{
                    const department = document.querySelector('select[name="department"]');
                    const student = document.getElementById('student-login-name');
                    const filterStudents = () => {{
                        const selected = department.value;
                        for (const option of student.options) {{
                            if (!option.value) {{
                                option.hidden = false;
                                option.disabled = false;
                                continue;
                            }}
                            const visible = option.dataset.department === selected;
                            option.hidden = !visible;
                            option.disabled = !visible;
                        }}
                        if (student.selectedOptions[0]?.disabled) {{
                            student.value = "";
                        }}
                    }};
                    department.addEventListener('change', filterStudents);
                    filterStudents();
                }})();
                </script>
            """
        else:
            login_field = field("Email", "email", "email")
        card = f"""
        <section class="auth-card">
            <span class="auth-card-icon">{role[0].upper()}</span>
            <h1>{title}</h1>
            <p class="auth-subtitle">Welcome back. Please login to continue.</p>
            {msg}
            <form method="post">
                {login_field}
                {department_select() if role == "faculty" else ""}
                {password_field()}
                <button class="button" type="submit">Login</button>
            </form>
            <a class="forgot-link" href="/{role}/forgot-password">Forgot password?</a>
            {register}
            {password_toggle_script()}
        </section>
        """
        self.send_html(page(title, auth_frame(title, card, role), show_guest_nav=False))

    def forgot_password(self, method, role):
        table = ROLE_TABLES[role]
        form_action = f"/{role}/forgot-password"
        title = f"{role.title()} Forgot Password"
        msg = ""
        show_change_form = False
        email_value = ""

        if method == "POST":
            data = self.post_data()
            action = data.get("action", "")
            email_value = data.get("email", "").strip().lower()
            row = None
            if valid_email(email_value):
                with db() as conn:
                    row = conn.execute(f"SELECT * FROM {table} WHERE lower(email)=%s", (email_value,)).fetchone()

            if action == "request_otp":
                if not valid_email(email_value):
                    msg = flash("Enter your registered email address.", "bad")
                elif not row:
                    msg = flash("No account was found for that email address.", "bad")
                else:
                    reset_user = {"role": role, "id": row["id"]}
                    otp = f"{secrets.randbelow(1000000):06d}"
                    msg, show_change_form = request_password_otp(
                        reset_user,
                        email_value,
                        row["name"],
                        otp,
                        "Verification code sent to your registered email.",
                    )
            elif action == "change_password":
                if not valid_email(email_value) or not row:
                    msg = flash("Enter the registered email address used to request the code.", "bad")
                else:
                    reset_user = {"role": role, "id": row["id"]}
                    saved = PASSWORD_OTPS.get(otp_key(reset_user))
                    new_password = data.get("new_password", "")
                    confirm_password = data.get("confirm_password", "")
                    show_change_form = True
                    if not saved or saved["used"] or saved["expires"] < time.time():
                        msg = flash("Verification code expired. Please request a new code.", "bad")
                        show_change_form = False
                    elif saved["email"] != email_value:
                        msg = flash("That email does not match the verification request.", "bad")
                    elif normalize_otp(data.get("otp")) != saved["otp"]:
                        msg = flash("Invalid verification code. Please check your email and try again.", "bad")
                    elif len(new_password) < 6:
                        msg = flash("Password must be at least 6 characters.", "bad")
                    elif new_password != confirm_password:
                        msg = flash("New password and confirmation do not match.", "bad")
                    else:
                        with db() as conn:
                            conn.execute(
                                f"UPDATE {table} SET password_hash=%s WHERE id=%s",
                                (hash_password(new_password), row["id"]),
                            )
                        saved["used"] = True
                        PASSWORD_OTPS.pop(otp_key(reset_user), None)
                        msg = flash("Password changed successfully. Please login with your new password.")
                        show_change_form = False

        change_form = ""
        if show_change_form:
            change_form = f"""
            <form method="post" action="{esc(form_action)}">
                <input type="hidden" name="action" value="change_password">
                <input type="hidden" name="email" value="{esc(email_value)}">
                {field("Verification Code", "otp")}
                {password_field("New Password", "new_password")}
                {password_field("Confirm New Password", "confirm_password")}
                <button class="button" type="submit">Change Password</button>
            </form>
            """

        card = f"""
        <section class="auth-card">
            <span class="auth-card-icon">{role[0].upper()}</span>
            <h1>Forgot Password</h1>
            <p class="auth-subtitle">Enter your registered email to receive a verification code.</p>
            {msg}
            <form method="post" action="{esc(form_action)}">
                <input type="hidden" name="action" value="request_otp">
                {field("Registered Email", "email", "email", value=email_value)}
                <button class="button" type="submit">Send Verification Code</button>
            </form>
            {change_form}
            <a class="forgot-link" href="/{role}/login">Back to login</a>
            {password_toggle_script()}
        </section>
        """
        self.send_html(page(title, auth_frame(title, card, role), show_guest_nav=False))

    def logout(self):
        jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        sid = jar.get("sid")
        if sid:
            SESSIONS.pop(sid.value, None)
        self.send_response(303)
        self.send_header("Location", "/")
        self.send_header("Set-Cookie", self.session_cookie("", 0))
        self.end_headers()

    def admin_notice(self, query):
        if query.get("dept_exists", [""])[0] == "1":
            return flash("That department already exists.", "bad")
        if query.get("dept_added", [""])[0] == "1":
            return flash("Department added successfully.")
        if query.get("faculty_added", [""])[0] == "1":
            return flash("Faculty login added successfully.")
        if query.get("faculty_error", [""])[0] == "1":
            return flash("Could not add faculty. Create the department first and check duplicate employee ID or email.", "bad")
        if query.get("hod_saved", [""])[0] == "1":
            return flash("HOD saved successfully.")
        if query.get("hod_error", [""])[0] == "1":
            return flash("Select a faculty from the same department. A faculty can be HOD for only one department.", "bad")
        if query.get("student_error", [""])[0] == "1":
            return flash("Could not add student. Roll number, username, or email may already exist.", "bad")
        if query.get("student_added", [""])[0] == "1":
            return flash("Student login added successfully.")
        if query.get("slot_saved", [""])[0] == "1":
            return flash("Feedback timeline saved successfully.")
        if query.get("slot_error", [""])[0] == "1":
            return flash("Please select a department and valid start/end time.", "bad")
        return ""

    def admin_back_link(self):
        return '<div class="actions page-actions back-actions"><a class="button ghost" href="/admin/dashboard">Back to Admin Dashboard</a></div>'

    def feedback_review_options(self):
        return """
        <section class="feedback-review-panel">
            <div class="section-head">
                <div>
                    <h2>Feedback Review</h2>
                    <p>Select one feedback review to open.</p>
                </div>
            </div>
            <div class="grid three feedback-review-options">
                <a class="card" href="/admin/feedback-review?feedback_review=overall"><h2>Overall Feedback</h2><p>Rating distribution across all submitted feedback.</p></a>
                <a class="card" href="/admin/feedback-review?feedback_review=department"><h2>Department-wise Feedback</h2><p>Average overall score by department.</p></a>
                <a class="card" href="/admin/feedback-review?feedback_review=faculty"><h2>Faculty-wise Feedback</h2><p>Select a department, then view faculty averages.</p></a>
            </div>
            <div class="actions page-actions">
                <a class="button ghost" href="/admin/dashboard">Close</a>
            </div>
        </section>
        """

    def admin_feedback_charts(self, conn, review="", selected_department=""):
        if not review:
            return ""
        if review == "menu":
            return self.feedback_review_options()

        overall_counts = {rating: 0 for rating in range(1, 6)}
        chart = ""
        department_picker = ""
        if review == "overall":
            for row in conn.execute("SELECT overall, COUNT(*) c FROM feedback GROUP BY overall").fetchall():
                try:
                    rating = int(row["overall"])
                except (TypeError, ValueError):
                    continue
                if rating in overall_counts:
                    overall_counts[rating] = row["c"]
            overall_data = [(f"{rating} star", overall_counts[rating]) for rating in range(5, 0, -1)]
            chart = donut_chart("Overall Feedback", "Rating distribution across all submitted feedback.", overall_data)
        elif review == "department":
            department_rows = conn.execute(
                """
                SELECT faculty.department label, AVG(feedback.overall) average_score, COUNT(*) count
                FROM feedback
                JOIN faculty ON faculty.id=feedback.faculty_id
                GROUP BY faculty.department
                ORDER BY average_score DESC, count DESC, faculty.department
                LIMIT 8
                """
            ).fetchall()
            department_data = [
                (row["label"], float(row["average_score"] or 0), row["count"])
                for row in department_rows
            ]
            chart = horizontal_bar_chart("Department-wise Feedback", "Average overall score by department.", department_data)
        elif review == "faculty":
            departments = conn.execute("SELECT name FROM departments ORDER BY name").fetchall()
            if selected_department and not any(row["name"] == selected_department for row in departments):
                selected_department = ""
            options = '<option value="">Select department</option>' + "".join(
                f'<option value="{esc(row["name"])}"{" selected" if row["name"] == selected_department else ""}>{esc(row["name"])}</option>'
                for row in departments
            )
            department_picker = f"""
            <form class="inline-form feedback-filter" method="get" action="/admin/feedback-review">
                <input type="hidden" name="feedback_review" value="faculty">
                <label><span>Department</span><select name="department" required>{options}</select></label>
                <button class="button" type="submit">Show Faculty Feedback</button>
            </form>
            """
            if selected_department:
                faculty_rows = conn.execute(
                    """
                    SELECT faculty.name label, AVG(feedback.overall) average_score, COUNT(*) count
                    FROM feedback
                    JOIN faculty ON faculty.id=feedback.faculty_id
                    WHERE faculty.department=%s
                    GROUP BY faculty.id, faculty.name
                    ORDER BY average_score DESC, count DESC, faculty.name
                    LIMIT 8
                    """,
                    (selected_department,),
                ).fetchall()
                faculty_data = [
                    (row["label"], float(row["average_score"] or 0), row["count"])
                    for row in faculty_rows
                ]
                chart = column_chart(
                    "Faculty-wise Feedback",
                    f"Top faculty averages in {selected_department}.",
                    faculty_data,
                )
            else:
                chart = '<article class="panel chart-card"><h2>Faculty-wise Feedback</h2><p>Select a department to view the faculty-wise feedback chart.</p></article>'
        else:
            return self.feedback_review_options()

        return f"""
        <section class="feedback-review-panel">
            <div class="section-head">
                <div>
                    <h2>Feedback Review</h2>
                    <p>Open another review option or return to the dashboard.</p>
                </div>
            </div>
            {department_picker}
            <div class="feedback-charts single">
                {chart}
            </div>
            <div class="actions page-actions">
                <a class="button ghost" href="/admin/feedback-review">Review Options</a>
                <a class="button ghost" href="/admin/dashboard">Close</a>
            </div>
        </section>
        """

    def admin_feedback_review(self, method):
        user = self.require("admin")
        if not user:
            return
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        review = query.get("feedback_review", ["menu"])[0] or "menu"
        selected_department = query.get("department", [""])[0].strip()
        with db() as conn:
            feedback_review = self.admin_feedback_charts(conn, review, selected_department)
        self.send_html(page("Feedback Review", feedback_review, user))

    def admin_dashboard(self, method):
        user = self.require("admin")
        if not user:
            return
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        with db() as conn:
            department_count = conn.execute("SELECT COUNT(*) c FROM departments").fetchone()["c"]
            faculty_count = conn.execute("SELECT COUNT(*) c FROM faculty").fetchone()["c"]
            student_count = conn.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
            timeline_count = conn.execute("SELECT COUNT(*) c FROM department_feedback_windows").fetchone()["c"]
            feedback_count = conn.execute("SELECT COUNT(*) c FROM feedback").fetchone()["c"]
        notices = self.admin_notice(query)
        body = f"""
        <section class="dashboard-head">
            <div><h1>Admin Dashboard</h1><p>Choose one admin task to open its separate page.</p></div>
            <strong>{feedback_count} feedback submissions</strong>
        </section>
        {notices}
        <section class="grid three admin-menu">
            <a class="card" href="/admin/department/add"><h2>Add Department</h2><p>{department_count} departments</p></a>
            <a class="card" href="/admin/faculty/add"><h2>Add Faculty</h2><p>{faculty_count} faculty accounts</p></a>
            <a class="card" href="/admin/department/hod"><h2>Assign HOD</h2><p>One HOD per department</p></a>
            <a class="card" href="/admin/student/add"><h2>Add Student</h2><p>{student_count} student accounts</p></a>
            <a class="card" href="/admin/feedback-window"><h2>Feedback Timeline</h2><p>{timeline_count} department timelines</p></a>
            <a class="card" href="/admin/feedback-review"><h2>Feedback Review</h2><p>Open overall, department-wise, or faculty-wise charts</p></a>
            <a class="card" href="/admin/reports"><h2>Reports</h2><p>Open and download reports</p></a>
        </section>
        """
        self.send_html(page("Admin Dashboard", body, user))

    def add_department(self, method):
        user = self.require("admin")
        if not user:
            return
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if method != "POST":
            with db() as conn:
                departments = conn.execute(
                    """
                    SELECT departments.*, faculty.name hod_name
                    FROM departments
                    LEFT JOIN faculty ON faculty.id=departments.hod_faculty_id
                    ORDER BY departments.name
                    """
                ).fetchall()
            rows = "".join(
                f"<tr><td>{esc(d['name'])}</td><td>{esc(d['hod_name'] or '-')}</td><td>{esc(indian_datetime_label(d['created_at']))}</td></tr>"
                for d in departments
            ) or "<tr><td colspan='3'>No departments added yet.</td></tr>"
            body = f"""
            <section class="panel narrow">
                <h1>Add Department</h1>
                {self.admin_notice(query)}
                <form method="post" action="/admin/department/add">
                    {field("Department Name", "department")}
                    <button class="button" type="submit">Add Department</button>
                </form>
            </section>
            <section class="panel">
                <h2>Departments</h2>
                <div class="table-wrap"><table><thead><tr><th>Department</th><th>HOD</th><th>Created</th></tr></thead><tbody>{rows}</tbody></table></div>
            </section>
            {self.admin_back_link()}
            """
            return self.send_html(page("Add Department", body, user))
        department = self.post_data().get("department", "").strip()
        if not department:
            return self.redirect("/admin/department/add?slot_error=1")
        try:
            with db() as conn:
                conn.execute("INSERT INTO departments(name) VALUES(%s)", (department,))
                resequence_departments(conn)
        except DB_INTEGRITY_ERRORS:
            return self.redirect("/admin/department/add?dept_exists=1")
        self.redirect("/admin/department/add?dept_added=1")

    def set_department_hod(self, method):
        user = self.require("admin")
        if not user:
            return
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if method != "POST":
            with db() as conn:
                faculty = conn.execute("SELECT * FROM faculty ORDER BY department,name").fetchall()
                departments = conn.execute(
                    """
                    SELECT departments.*, faculty.name hod_name
                    FROM departments
                    LEFT JOIN faculty ON faculty.id=departments.hod_faculty_id
                    ORDER BY departments.name
                    """
                ).fetchall()
            rows = ""
            for department in departments:
                options = ['<option value="">No HOD assigned</option>']
                for f in faculty:
                    if f["department"] == department["name"]:
                        mark = " selected" if f["id"] == department["hod_faculty_id"] else ""
                        options.append(f'<option value="{f["id"]}"{mark}>{esc(f["name"])} ({esc(f["employee_id"])})</option>')
                rows += f"""
                <tr>
                    <td>{esc(department['name'])}</td>
                    <td>{esc(department['hod_name'] or '-')}</td>
                    <td>
                        <form method="post" action="/admin/department/hod" class="inline-form wide-inline">
                            <input type="hidden" name="department" value="{esc(department['name'])}">
                            <select name="hod_faculty_id">{"".join(options)}</select>
                            <button class="button small" type="submit">Save HOD</button>
                        </form>
                    </td>
                </tr>
                """
            if not rows:
                rows = "<tr><td colspan='3'>No departments added yet.</td></tr>"
            body = f"""
            <section class="dashboard-head slim">
                <div><h1>Assign HOD</h1><p>Select one faculty member as the HOD for each department.</p></div>
            </section>
            {self.admin_notice(query)}
            <section class="panel">
                <div class="table-wrap"><table><thead><tr><th>Department</th><th>Current HOD</th><th>Assign HOD</th></tr></thead><tbody>{rows}</tbody></table></div>
            </section>
            {self.admin_back_link()}
            """
            return self.send_html(page("Assign HOD", body, user))
        data = self.post_data()
        department = data.get("department", "").strip()
        hod_value = data.get("hod_faculty_id", "").strip()
        hod_id = None
        if hod_value:
            try:
                hod_id = int(hod_value)
            except ValueError:
                return self.redirect("/admin/department/hod?hod_error=1")
        try:
            with db() as conn:
                if hod_id is not None:
                    faculty = conn.execute(
                        "SELECT id FROM faculty WHERE id=%s AND department=%s",
                        (hod_id, department),
                    ).fetchone()
                    if not faculty:
                        return self.redirect("/admin/department/hod?hod_error=1")
                conn.execute("UPDATE departments SET hod_faculty_id=%s WHERE name=%s", (hod_id, department))
        except DB_INTEGRITY_ERRORS:
            return self.redirect("/admin/department/hod?hod_error=1")
        self.redirect("/admin/department/hod?hod_saved=1")

    def add_faculty(self, method):
        user = self.require("admin")
        if not user:
            return
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if method != "POST":
            with db() as conn:
                faculty = conn.execute("SELECT * FROM faculty ORDER BY department,name").fetchall()
            rows = "".join(
                f"""
                <tr>
                    <td>{esc(f['name'])}</td>
                    <td>{esc(f['employee_id'])}</td>
                    <td>{esc(f['department'])}</td>
                    <td>{esc(f['subject'])}</td>
                    <td>{esc(f['email'])}</td>
                    <td>
                        <form method="post" action="/admin/faculty/remove" class="inline-form" onsubmit="return confirm('Remove this faculty account?');">
                            <input type="hidden" name="faculty_id" value="{f['id']}">
                            <button class="button danger small" type="submit">Remove</button>
                        </form>
                    </td>
                </tr>
                """
                for f in faculty
            ) or "<tr><td colspan='6'>No faculty added yet.</td></tr>"
            body = f"""
            <section class="panel narrow">
                <h1>Add Faculty</h1>
                {self.admin_notice(query)}
                <form method="post" action="/admin/faculty/add">
                    {field("Faculty Name", "name")}
                    {field("Employee ID", "employee_id")}
                    {department_select()}
                    {field("Subject", "subject")}
                    {field("Email", "email", "email")}
                    {field("Temporary Password", "password", "password")}
                    <button class="button" type="submit">Add Faculty Login</button>
                </form>
            </section>
            <section class="panel">
                <h2>Faculty Accounts</h2>
                <div class="table-wrap"><table><thead><tr><th>Name</th><th>Employee ID</th><th>Department</th><th>Subject</th><th>Email</th><th>Action</th></tr></thead><tbody>{rows}</tbody></table></div>
            </section>
            {self.admin_back_link()}
            """
            return self.send_html(page("Add Faculty", body, user))
        data = self.post_data()
        try:
            with db() as conn:
                department = conn.execute(
                    "SELECT name FROM departments WHERE name=%s",
                    (data.get("department", "").strip(),),
                ).fetchone()
                if not department:
                    return self.redirect("/admin/faculty/add?faculty_error=1")
                conn.execute(
                    """
                    INSERT INTO faculty(name,employee_id,department,subject,email,password_hash)
                    VALUES(%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        data["name"],
                        data["employee_id"],
                        department["name"],
                        data["subject"],
                        data["email"].lower(),
                        hash_password(data["password"]),
                    ),
                )
                resequence_faculty(conn)
        except DB_INTEGRITY_ERRORS:
            return self.redirect("/admin/faculty/add?faculty_error=1")
        self.redirect("/admin/faculty/add?faculty_added=1")

    def remove_faculty(self, method):
        user = self.require("admin")
        if not user:
            return
        if method != "POST":
            return self.redirect("/admin/faculty/add")
        data = self.post_data()
        try:
            faculty_id = int(data.get("faculty_id", "0"))
        except ValueError:
            faculty_id = 0
        if faculty_id:
            with db() as conn:
                conn.execute("DELETE FROM feedback WHERE faculty_id=%s", (faculty_id,))
                conn.execute("UPDATE departments SET hod_faculty_id=NULL WHERE hod_faculty_id=%s", (faculty_id,))
                conn.execute("DELETE FROM faculty WHERE id=%s", (faculty_id,))
                resequence_faculty(conn)
                resequence_feedback(conn)
        self.redirect("/admin/faculty/add")

    def add_student(self, method):
        user = self.require("admin")
        if not user:
            return
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if method != "POST":
            with db() as conn:
                students = conn.execute("SELECT * FROM students ORDER BY department,name").fetchall()
            rows = "".join(
                f"""
                <tr>
                    <td>{esc(s['name'])}</td>
                    <td>{esc(s['roll_number'])}</td>
                    <td>{esc(s['department'])}</td>
                    <td>{esc(s['email'])}</td>
                    <td>{esc(s['username'])}</td>
                    <td>{esc(student_default_password(s['name']))}</td>
                    <td>
                        <form method="post" action="/admin/student/remove" class="inline-form" onsubmit="return confirm('Remove this student account?');">
                            <input type="hidden" name="student_id" value="{s['id']}">
                            <button class="button danger small" type="submit">Remove</button>
                        </form>
                    </td>
                </tr>
                """
                for s in students
            ) or "<tr><td colspan='7'>No students added yet.</td></tr>"
            body = f"""
            <section class="panel narrow">
                <h1>Add Student</h1>
                {self.admin_notice(query)}
                <p>Login ID is the roll number. Default password is the first three letters of the first name followed by 123.</p>
                <form method="post" action="/admin/student/add">
                    {field("Student Name", "name")}
                    {field("Roll Number", "roll_number")}
                    {department_select()}
                    {field("Student Email", "email", "email")}
                    <button class="button" type="submit">Add Student Login</button>
                </form>
            </section>
            <section class="panel">
                <h2>Student Accounts</h2>
                <div class="table-wrap"><table><thead><tr><th>Name</th><th>Roll Number</th><th>Department</th><th>Email</th><th>Login ID</th><th>Default Password</th><th>Action</th></tr></thead><tbody>{rows}</tbody></table></div>
            </section>
            {self.admin_back_link()}
            """
            return self.send_html(page("Add Student", body, user))
        data = self.post_data()
        username = student_login_id(data["roll_number"])
        password = student_default_password(data["name"])
        email = data["email"].strip().lower()
        try:
            with db() as conn:
                department = conn.execute(
                    "SELECT name FROM departments WHERE name=%s",
                    (data.get("department", "").strip(),),
                ).fetchone()
                if not department:
                    return self.redirect("/admin/student/add?student_error=1")
                conn.execute(
                    """
                    INSERT INTO students(name,roll_number,department,username,email,password_hash,created_by_admin_id)
                    VALUES(%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        data["name"],
                        data["roll_number"],
                        department["name"],
                        username,
                        email,
                        hash_password(password),
                        user["id"],
                    ),
                )
                resequence_students(conn)
        except DB_INTEGRITY_ERRORS:
            return self.redirect("/admin/student/add?student_error=1")
        self.redirect("/admin/student/add?student_added=1")

    def remove_student(self, method):
        user = self.require("admin")
        if not user:
            return
        if method != "POST":
            return self.redirect("/admin/student/add")
        data = self.post_data()
        try:
            student_id = int(data.get("student_id", "0"))
        except ValueError:
            student_id = 0
        if student_id:
            with db() as conn:
                student = conn.execute("SELECT id FROM students WHERE id=%s", (student_id,)).fetchone()
                if student:
                    conn.execute("DELETE FROM feedback WHERE student_id=%s", (student_id,))
                    conn.execute("DELETE FROM students WHERE id=%s", (student_id,))
                    resequence_students(conn)
                    resequence_feedback(conn)
        self.redirect("/admin/student/add")

    def set_feedback_window(self, method):
        user = self.require("admin")
        if not user:
            return
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if method != "POST":
            with db() as conn:
                departments = conn.execute("SELECT name FROM departments ORDER BY name").fetchall()
                windows = {
                    row["department"]: row
                    for row in conn.execute("SELECT * FROM department_feedback_windows").fetchall()
                }
            rows = ""
            for department in departments:
                window = windows.get(department["name"])
                status, status_message = feedback_window_status(window)
                start_value = indian_datetime_label(window["start_at"]) if window else "-"
                end_value = indian_datetime_label(window["end_at"]) if window else "-"
                rows += f"""
                <tr>
                    <td>{esc(department['name'])}</td>
                    <td>{esc(start_value)}</td>
                    <td>{esc(end_value)}</td>
                    <td><span class="slot-status mini {esc(status)}">{esc(status.replace('_', ' ').title())}</span><br><small>{esc(status_message)}</small></td>
                </tr>
                """
            if not rows:
                rows = "<tr><td colspan='4'>No departments added yet.</td></tr>"
            body = f"""
            <section class="panel narrow">
                <h1>Feedback Timeline</h1>
                {self.admin_notice(query)}
                <form method="post" action="/admin/feedback-window">
                    {department_select()}
                    {field("Start Time", "start_at", "datetime-local")}
                    {field("End Time", "end_at", "datetime-local")}
                    <button class="button" type="submit">Save Timeline</button>
                </form>
            </section>
            <section class="panel">
                <h2>Current Timelines</h2>
                <div class="table-wrap"><table><thead><tr><th>Department</th><th>Start</th><th>End</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></div>
            </section>
            {self.admin_back_link()}
            """
            return self.send_html(page("Feedback Timeline", body, user))
        data = self.post_data()
        start = parse_slot_datetime(data.get("start_at"))
        end = parse_slot_datetime(data.get("end_at"))
        department = data.get("department", "").strip()
        if not department or not start or not end or end <= start:
            return self.redirect("/admin/feedback-window?slot_error=1")
        with db() as conn:
            department_row = conn.execute("SELECT name FROM departments WHERE name=%s", (department,)).fetchone()
            if not department_row:
                return self.redirect("/admin/feedback-window?slot_error=1")
            conn.execute(
                """
                INSERT INTO department_feedback_windows(department,start_at,end_at,updated_at)
                VALUES(%s,%s,%s,CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE
                    start_at=VALUES(start_at),
                    end_at=VALUES(end_at),
                    updated_at=CURRENT_TIMESTAMP
                """,
                (department, start.isoformat(timespec="minutes"), end.isoformat(timespec="minutes")),
            )
        self.redirect("/admin/feedback-window?slot_saved=1")

    def admin_reports(self, method):
        user = self.require("admin")
        if not user:
            return
        with db() as conn:
            feedback_count = conn.execute("SELECT COUNT(*) c FROM feedback").fetchone()["c"]
            student_count = conn.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
            faculty_count = conn.execute("SELECT COUNT(*) c FROM faculty").fetchone()["c"]
        body = f"""
        <section class="dashboard-head slim">
            <div><h1>Reports</h1><p>Open feedback reports from the admin area.</p></div>
        </section>
        <section class="grid three">
            <div class="card report-card"><h2>Faculty Feedback Review</h2><p>{feedback_count} submissions from {faculty_count} faculty accounts.</p><a class="button" href="/reports/faculty" target="_blank" rel="noopener">Open Report</a></div>
            <div class="card report-card"><h2>Overall Feedback Report</h2><p>{student_count} student accounts included when feedback is submitted.</p><a class="button" href="/reports/overall" target="_blank" rel="noopener">Open Report</a></div>
            <div class="card report-card"><h2>Department-wise CSV</h2><p>Download all department feedback rows as a CSV file.</p><a class="button" href="/reports/department">Download CSV</a></div>
        </section>
        {self.admin_back_link()}
        """
        self.send_html(page("Reports", body, user))

    def account_row(self, user):
        table = ROLE_TABLES.get(user["role"])
        if not table:
            return None, None
        with db() as conn:
            row = conn.execute(f"SELECT * FROM {table} WHERE id=%s", (user["id"],)).fetchone()
        return table, row

    def password_change_panel(self, user, method, form_action):
        table, row = self.account_row(user)
        if not row:
            return "<section class='panel'><h1>Account not found</h1></section>"

        msg = ""
        show_change_form = otp_key(user) in PASSWORD_OTPS
        if method == "POST":
            data = self.post_data()
            action = data.get("action", "")
            if action == "request_otp":
                reset_email = data.get("email", "").strip().lower()
                account_email = str(row["email"] or "").strip().lower()
                if not valid_email(reset_email):
                    msg = flash("Enter a valid email address to receive the reset OTP.", "bad")
                elif reset_email != account_email:
                    msg = flash("That email does not match this account.", "bad")
                else:
                    otp = f"{secrets.randbelow(1000000):06d}"
                    msg, show_change_form = request_password_otp(
                        user,
                        reset_email,
                        row["name"],
                        otp,
                        "Reset OTP sent to your email.",
                    )
            elif action == "change_password":
                saved = PASSWORD_OTPS.get(otp_key(user))
                new_password = data.get("new_password", "")
                confirm_password = data.get("confirm_password", "")
                if not saved or saved["used"] or saved["expires"] < time.time():
                    msg = flash("OTP expired. Please request a new OTP.", "bad")
                elif normalize_otp(data.get("otp")) != saved["otp"]:
                    msg = flash("Invalid OTP. Please check your email and try again.", "bad")
                    show_change_form = True
                elif len(new_password) < 6:
                    msg = flash("Password must be at least 6 characters.", "bad")
                    show_change_form = True
                elif new_password != confirm_password:
                    msg = flash("New password and confirmation do not match.", "bad")
                    show_change_form = True
                else:
                    with db() as conn:
                        conn.execute(
                            f"UPDATE {table} SET password_hash=%s WHERE id=%s",
                            (hash_password(new_password), user["id"]),
                        )
                    saved["used"] = True
                    PASSWORD_OTPS.pop(otp_key(user), None)
                    msg = flash("Password changed successfully.")
                    show_change_form = False

        email_text = row["email"] if valid_email(row["email"]) else "No valid email configured"
        change_form = ""
        if show_change_form:
            change_form = f"""
            <form method="post" action="{esc(form_action)}">
                <input type="hidden" name="action" value="change_password">
                {field("Email OTP", "otp")}
                {field("New Password", "new_password", "password")}
                {field("Confirm New Password", "confirm_password", "password")}
                <button class="button" type="submit">Change Password</button>
            </form>
            """
        return f"""
        <section class="panel narrow">
            <h1>Change Password</h1>
            {msg}
            <p>Enter your registered email address. A reset OTP will be sent to that email.</p>
            <form method="post" action="{esc(form_action)}">
                <input type="hidden" name="action" value="request_otp">
                {field("Registered Email", "email", "email", value="" if email_text.startswith("No valid") else email_text)}
                <button class="button" type="submit">Send Reset Email</button>
            </form>
            {change_form}
        </section>
        """

    def change_password(self, method):
        user = self.current_user()
        if not user or user["role"] not in ("admin", "faculty", "student"):
            return self.redirect("/")
        body = self.password_change_panel(user, method, "/account/password")
        self.send_html(page("Change Password", body, user))

    def student_dashboard(self, method):
        user = self.require("student")
        if not user:
            return
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        with db() as conn:
            student = conn.execute("SELECT * FROM students WHERE id=%s", (user["id"],)).fetchone()
            student_department = str(student["department"]).strip()
            faculty = conn.execute(
                """
                SELECT faculty.*
                FROM faculty
                WHERE faculty.department=%s
                ORDER BY faculty.name
                """,
                (student_department,),
            ).fetchall()
            window_status, window_message = department_feedback_window_status(conn, student_department)
            mine = conn.execute(
                """
                SELECT feedback.*, faculty.name faculty_name, faculty.department
                FROM feedback JOIN faculty ON faculty.id=feedback.faculty_id
                WHERE student_id=%s ORDER BY feedback.created_at DESC
                """,
                (user["id"],),
            ).fetchall()
        submitted_faculty_ids = {row["faculty_id"] for row in mine}
        remaining_faculty = [f for f in faculty if f["id"] not in submitted_faculty_ids]
        part_a_completed = bool(mine)
        language = selected_language(query.get("lang", [""])[0]) or current_language()
        if not language and part_a_completed:
            language = selected_language(mine[0]["language_preference"] or "") or "en"
        department_options = '<option value="">Select department</option>' + "".join(
            f'<option value="{esc(department)}" selected>{esc(department)}</option>'
            for department in sorted({str(f["department"]).strip() for f in faculty if str(f["department"]).strip()})
        )
        faculty_options = '<option value="">Select department first</option>' + "".join(
            f'<option value="{f["id"]}" data-department="{esc(f["department"])}">{esc(f["name"])}</option>'
            for f in remaining_faculty
        )
        if not faculty:
            department_options = "<option value=''>No department available. Ask admin to add faculty.</option>"
            faculty_options = "<option value=''>No faculty available. Ask admin to add faculty.</option>"
        rows = "".join(
            f"<tr><td>{esc(r['faculty_name'])}</td><td>{esc(r['department'])}</td><td>{esc(r['course'])}</td><td>{r['overall']}/5</td><td>{esc(r['reason'])}</td><td>{esc(indian_datetime_label(r['created_at']))}</td></tr>"
            for r in mine
        ) or "<tr><td colspan='6'>No feedback submitted yet.</td></tr>"
        form_a = "".join(
            radio_group(index, key, question, options, language)
            for index, (key, question, options) in enumerate(FORM_A_CHOICES, 3)
        )
        notice = ""
        if query.get("submitted", [""])[0] == "1":
            notice = flash("Feedback submitted successfully.")
        elif query.get("already_submitted", [""])[0] == "1":
            notice = flash("You have already submitted feedback for that faculty. Please choose another faculty.", "bad")
        elif query.get("closed", [""])[0] == "1":
            notice = flash("Feedback can be submitted only during the admin-set timeline.", "bad")
        elif query.get("part_a_required", [""])[0] == "1":
            notice = flash("Please answer every question in Part A before submitting.", "bad")
        elif query.get("error", [""])[0] == "1":
            notice = flash("Could not submit feedback. Please select a department and matching faculty, then try again.", "bad")

        if faculty and not remaining_faculty:
            feedback_section = f"""
            <section class="panel">
                <h2>Feedback Completed</h2>
                <p>You have submitted Part B feedback for every faculty in your department. Part A was recorded once.</p>
            </section>
            """
        elif not faculty:
            feedback_section = """
            <section class="panel">
                <h2>Feedback Not Available</h2>
                <p>No faculty is available. Ask admin to add faculty before submitting feedback.</p>
            </section>
            """
        elif window_status != "open":
            feedback_section = f"""
            <section class="panel">
                <h2>Feedback Form Closed</h2>
                <p>{esc(window_message)}</p>
            </section>
            """
        elif not language:
            language_options = "".join(
                f'<option value="{esc(code)}">{esc(name)}</option>'
                for code, name in LANGUAGES.items()
            )
            feedback_section = f"""
            <section class="panel narrow">
                <h2>Language Preference</h2>
                <p>Please select the language for your feedback form.</p>
                <form method="get" action="/student/dashboard">
                    <label><span>Language</span><select name="lang" required>
                        <option value="">Select language</option>
                        {language_options}
                    </select></label>
                    <button class="button" type="submit">Continue</button>
                </form>
            </section>
            """
        else:
            change_language_link = '<a class="button ghost" href="/student/dashboard">Change Language</a>'
            part_a_fields = f"""
                    <section class="feedback-part">
                        <div class="feedback-part-head">
                            <span>Part A</span>
                            <div>
                                <h3>{localized_text("Assessment of the Curriculum/Course/Academic Programme by Students - Form A", language)}</h3>
                                <p>Complete this section once. All questions are required.</p>
                            </div>
                        </div>
                        <label><span>{localized_text("Department", language)}</span><select name="course" id="department-select" required>{department_options}</select></label>
                        {checkbox_group(1, "reason", "The most important reason for selecting the course (tick all that apply)", COURSE_REASONS, language)}
                        {score_table("2. Department Facilities", "Rate each facility on a 5 point scale: 1 - Very poor, 2 - Poor, 3 - Satisfactory, 4 - Good, 5 - Very good.", FACILITIES, "facility", language)}
                        {form_a}
                    </section>
            """
            if part_a_completed:
                part_a_fields = f"""
                    <input type="hidden" name="course" id="department-select" value="{esc(student_department)}">
                    <section class="feedback-part feedback-part-complete">
                        <div class="feedback-part-head">
                            <span>Part A</span>
                            <div>
                                <h3>Part A already submitted</h3>
                                <p>Your curriculum and department feedback has been recorded once. Please complete Part B for each remaining faculty.</p>
                            </div>
                        </div>
                    </section>
                """
            feedback_section = f"""
            <section class="panel">
                <div class="dashboard-head slim">
                    <div>
                        <h2>{localized_text("Assessment of the Curriculum/Course/Academic Programme by Students - Form A", language)}</h2>
                        <p>{esc(window_message)} Language: {esc(LANGUAGES[language])}</p>
                    </div>
                    {change_language_link}
                </div>
                <form method="post" action="/student/feedback" class="feedback-form">
                    <div class="feedback-helper">
                        <strong>How this works</strong>
                        <span>Part A is saved once. Part B must be submitted separately for every faculty in your department.</span>
                    </div>
                    <input type="hidden" name="language_preference" value="{esc(language)}">
                    {part_a_fields}
                    <section class="feedback-part">
                        <div class="feedback-part-head">
                            <span>Part B</span>
                            <div>
                                <h3>{localized_text("Assessment of the Teachers by Students - Form B", language)}</h3>
                                <p>Select one faculty and rate the teacher. Submit again for each remaining faculty.</p>
                            </div>
                        </div>
                        <label><span>{localized_text("Select Faculty for Part B", language)}</span><select name="faculty_id" id="faculty-select" required>{faculty_options}</select></label>
                        {score_table("Teacher Rating", "Rate the selected teacher on each statement from 1 - Very poor to 5 - Very good.", TEACHER_QUESTIONS, "teacher", language)}
                        {textarea(localized_text("Comments", language), "comments")}
                    </section>
                    <div class="feedback-submit">
                        <button class="button" type="submit">{localized_text("Submit Feedback", language)}</button>
                    </div>
                </form>
                <script>
                const departmentSelect = document.getElementById("department-select");
                const facultySelect = document.getElementById("faculty-select");
                const facultyPlaceholder = facultySelect.options[0];
                const facultyChoices = Array.from(facultySelect.options).slice(1);
                const reasonInputs = Array.from(document.querySelectorAll('input[name="reason"]'));

                function filterFacultyByDepartment() {{
                    const selectedDepartment = departmentSelect.value;
                    facultySelect.value = "";
                    facultyPlaceholder.textContent = selectedDepartment ? "Select faculty" : "Select department first";
                    facultyChoices.forEach((option) => {{
                        option.hidden = option.dataset.department !== selectedDepartment;
                    }});
                }}

                function syncReasonRequired() {{
                    if (!reasonInputs.length) {{
                        return;
                    }}
                    const hasReason = reasonInputs.some((input) => input.checked);
                    reasonInputs.forEach((input) => {{
                        input.required = false;
                    }});
                    reasonInputs[0].required = !hasReason;
                }}

                departmentSelect.addEventListener("change", filterFacultyByDepartment);
                reasonInputs.forEach((input) => input.addEventListener("change", syncReasonRequired));
                filterFacultyByDepartment();
                syncReasonRequired();
                </script>
            </section>
            """
        body = f"""
        <section class="dashboard-head"><div><h1>Student Dashboard</h1><p>Department: {esc(student['department'])}. Select a faculty for Part B while your department feedback form is open.</p></div></section>
        {notice}
        {feedback_section}
        <section class="panel">
            <h2>Your Submissions</h2>
            <div class="table-wrap"><table><thead><tr><th>Faculty</th><th>Department</th><th>Selected Department</th><th>Teacher Avg</th><th>Reason</th><th>Date</th></tr></thead><tbody>{rows}</tbody></table></div>
        </section>
        """
        self.send_html(page("Student Dashboard", body, user))

    def submit_feedback(self, method):
        user = self.require("student")
        if not user:
            return
        if method != "POST":
            return self.redirect("/student/dashboard")
        data, data_lists = self.post_data(include_lists=True)
        with db() as conn:
            part_a_existing = conn.execute(
                "SELECT * FROM feedback WHERE student_id=%s ORDER BY created_at LIMIT 1",
                (user["id"],),
            ).fetchone()
            student = conn.execute("SELECT department FROM students WHERE id=%s", (user["id"],)).fetchone()
            faculty_id = data.get("faculty_id", "")
            selected_department = data.get("course", "").strip()
            student_department = str(student["department"]).strip()
            language_preference = selected_language(data.get("language_preference", ""))
            existing_for_faculty = conn.execute(
                "SELECT id FROM feedback WHERE student_id=%s AND faculty_id=%s LIMIT 1",
                (user["id"], faculty_id),
            ).fetchone()
            if existing_for_faculty:
                return self.redirect("/student/dashboard?already_submitted=1")
            if not faculty_id or not selected_department or selected_department != student_department:
                return self.redirect("/student/dashboard?error=1")
            faculty = conn.execute(
                """
                SELECT faculty.department, faculty.subject
                FROM faculty
                WHERE faculty.id=%s
                """,
                (faculty_id,),
            ).fetchone()
            if not faculty or selected_department != str(faculty["department"]).strip():
                return self.redirect("/student/dashboard?error=1")
            status, _ = department_feedback_window_status(conn, student_department)
            if status != "open":
                return self.redirect("/student/dashboard?closed=1")
            try:
                teacher_answers = {item: int(data[f"teacher_{idx}"]) for idx, item in enumerate(TEACHER_QUESTIONS, 1)}
            except (KeyError, ValueError):
                return self.redirect("/student/dashboard?error=1")
            if any(value < 1 or value > 5 for value in teacher_answers.values()):
                return self.redirect("/student/dashboard?error=1")
            course_answers = {question: data.get(key, "") for key, question, _ in FORM_A_CHOICES}
            selected_reasons = [
                reason
                for reason in data_lists.get("reason", [])
                if reason in COURSE_REASONS
            ]
            if part_a_existing:
                selected_reasons_text = part_a_existing["reason"] or ""
                facilities_json = part_a_existing["facilities_json"] or "{}"
                course_answers_json = part_a_existing["course_answers_json"] or "{}"
                language_preference = language_preference or selected_language(part_a_existing["language_preference"] or "") or "en"
            else:
                try:
                    facilities = {item: int(data[f"facility_{idx}"]) for idx, item in enumerate(FACILITIES, 1)}
                except (KeyError, ValueError):
                    return self.redirect("/student/dashboard?part_a_required=1")
                if any(value < 1 or value > 5 for value in facilities.values()):
                    return self.redirect("/student/dashboard?part_a_required=1")
                if not selected_reasons:
                    return self.redirect("/student/dashboard?part_a_required=1")
                for key, question, options in FORM_A_CHOICES:
                    answer = data.get(key, "")
                    if answer not in options:
                        return self.redirect("/student/dashboard?part_a_required=1")
                    course_answers[question] = answer
                selected_reasons_text = ", ".join(selected_reasons)
                facilities_json = json.dumps(facilities)
                course_answers_json = json.dumps(course_answers)
                language_preference = language_preference or "en"
            teacher_values = list(teacher_answers.values())
            avg = round(sum(teacher_values) / len(teacher_values))
            conn.execute(
                """
                INSERT INTO feedback(
                    student_id,faculty_id,course,clarity,punctuality,knowledge,interaction,overall,comments,
                    reason,facilities_json,course_answers_json,teacher_answers_json,language_preference
                )
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    user["id"],
                    faculty_id,
                    selected_department,
                    teacher_answers["Clarifies doubts / questions raised"],
                    teacher_answers["Is punctual and maintains class decorum"],
                    teacher_answers["Knows the subject well"],
                    teacher_answers["Encourages to ask questions"],
                    avg,
                    data.get("comments", ""),
                    selected_reasons_text,
                    facilities_json,
                    course_answers_json,
                    json.dumps(teacher_answers),
                    language_preference or "en",
                ),
            )
            resequence_feedback(conn)
        self.redirect("/student/dashboard?submitted=1")

    def faculty_dashboard(self, method):
        user = self.require("faculty")
        if not user:
            return
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        section = query.get("section", ["feedbacks"])[0]
        if section not in ("feedbacks", "password"):
            section = "feedbacks"
        with db() as conn:
            me = conn.execute(
                "SELECT * FROM faculty WHERE id=%s",
                (user["id"],),
            ).fetchone()
            submitted_count = conn.execute(
                """
                SELECT COUNT(DISTINCT student_id) count
                FROM feedback WHERE faculty_id=%s
                """,
                (user["id"],),
            ).fetchone()["count"]

        def active(name):
            return " active" if section == name else ""

        sidebar = f"""
        <aside class="sidebar">
            <div class="sidebar-profile">
                <strong>{esc(me['name'])}</strong>
                <span>{esc(me['department'])}</span>
                <span>{esc(me['subject'])}</span>
            </div>
            <nav class="side-nav">
                <a class="{active('feedbacks')}" href="/faculty/dashboard?section=feedbacks">Feedbacks</a>
                <a class="{active('password')}" href="/faculty/dashboard?section=password">Change Password</a>
                <a href="/logout">Logout</a>
            </nav>
        </aside>
        """

        stats = f"""
        <section class="grid stats compact-stats">
            <div><span>Students Submitted Feedback</span><strong>{submitted_count or 0}</strong></div>
        </section>
        """

        if section == "password":
            content = f"""
            <section class="dashboard-head slim">
                <div><h1>Change Password</h1><p>Verify with email OTP and set a new password.</p></div>
            </section>
            {self.password_change_panel(user, method, "/faculty/dashboard?section=password")}
            """
        else:
            content = f"""
            <section class="dashboard-head slim">
                <div><h1>Feedbacks</h1><p>View how many students submitted feedback for your classes. Reports, students, and timelines are managed by admin.</p></div>
            </section>
            {stats}
            """

        body = f"""
        <section class="app-layout">
            {sidebar}
            <div class="layout-main">
                {content}
            </div>
        </section>
        """
        self.send_html(page("Faculty Dashboard", body, user, show_account_actions=False))

    def report_rows(self, scope):
        user = self.current_user()
        if not user or user["role"] != "admin":
            return None
        query = """
            SELECT faculty.name faculty_name, faculty.department, faculty.subject,
                   students.name student_name, students.roll_number, feedback.course,
                   feedback.clarity, feedback.punctuality, feedback.knowledge,
                   feedback.interaction, feedback.overall, feedback.reason,
                   feedback.facilities_json, feedback.course_answers_json, feedback.teacher_answers_json,
                   feedback.comments, feedback.created_at
            FROM feedback
            JOIN faculty ON faculty.id=feedback.faculty_id
            JOIN students ON students.id=feedback.student_id
        """
        params = ()
        query += " ORDER BY faculty.department, faculty.name, feedback.created_at DESC"
        with db() as conn:
            return conn.execute(query, params).fetchall()

    def csv_response(self, filename, rows):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Faculty",
                "Department",
                "Subject",
                "Student",
                "Roll Number",
                "Course",
                "Clarity",
                "Punctuality",
                "Knowledge",
                "Interaction",
                "Overall",
                "Course Selection Reason",
                *[f"Facility - {item}" for item in FACILITIES],
                *[f"Course - {question}" for _, question, _ in FORM_A_CHOICES],
                *[f"Teacher - {item}" for item in TEACHER_QUESTIONS],
                "Comments",
                "Date (IST)",
            ]
        )
        for row in rows:
            facilities = json.loads(row["facilities_json"] or "{}")
            course_answers = json.loads(row["course_answers_json"] or "{}")
            teacher_answers = json.loads(row["teacher_answers_json"] or "{}")
            writer.writerow(
                [
                    row["faculty_name"],
                    row["department"],
                    row["subject"],
                    row["student_name"],
                    row["roll_number"],
                    row["course"],
                    row["clarity"],
                    row["punctuality"],
                    row["knowledge"],
                    row["interaction"],
                    row["overall"],
                    row["reason"],
                    *[facilities.get(item, "") for item in FACILITIES],
                    *[course_answers.get(question, "") for _, question, _ in FORM_A_CHOICES],
                    *[teacher_answers.get(item, "") for item in TEACHER_QUESTIONS],
                    row["comments"],
                    indian_datetime_label(row["created_at"]),
                ]
            )
        data = output.getvalue().encode("utf-8-sig")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def overall_report_rows(self, faculty_id=None):
        user = self.current_user()
        if not user or user["role"] != "admin":
            return None
        query = """
            SELECT feedback.*, faculty.name faculty_name, faculty.employee_id,
                   faculty.department, faculty.subject, students.id student_id
            FROM feedback
            JOIN faculty ON faculty.id=feedback.faculty_id
            JOIN students ON students.id=feedback.student_id
        """
        params = ()
        if faculty_id:
            query += " WHERE faculty.id=%s"
            params = (faculty_id,)
        query += " ORDER BY faculty.department, feedback.course, faculty.name"
        with db() as conn:
            return conn.execute(query, params).fetchall()

    def faculty_report_options(self, selected_department="", selected_faculty_id=""):
        with db() as conn:
            departments = conn.execute("SELECT name FROM departments ORDER BY name").fetchall()
            faculty = []
            if selected_department:
                faculty = conn.execute(
                    "SELECT id, name, employee_id FROM faculty WHERE department=%s ORDER BY name",
                    (selected_department,),
                ).fetchall()
        department_options = '<option value="">Select department</option>' + "".join(
            f'<option value="{esc(row["name"])}"{" selected" if row["name"] == selected_department else ""}>{esc(row["name"])}</option>'
            for row in departments
        )
        faculty_options = '<option value="">Select faculty</option>' + "".join(
            f'<option value="{row["id"]}"{" selected" if str(row["id"]) == str(selected_faculty_id) else ""}>{esc(row["name"])} ({esc(row["employee_id"])})</option>'
            for row in faculty
        )
        faculty_picker = ""
        submit_label = "Show Faculty Names"
        if selected_department:
            faculty_picker = f"""
            <label><span>Faculty</span><select name="faculty_id" required>{faculty_options}</select></label>
            """
            submit_label = "Open Individual Report"
        return f"""
        <section class="dashboard-head slim">
            <div><h1>Faculty Feedback Review</h1><p>Select the faculty report type to open.</p></div>
        </section>
        <section class="grid two">
            <div class="card report-card">
                <h2>Overall Faculty Report</h2>
                <p>Show all faculty names and ratings in one report.</p>
                <a class="button" href="/reports/faculty?type=overall">Open Overall Report</a>
            </div>
            <div class="card report-card">
                <h2>Individual Faculty Report</h2>
                <p>Choose a department, then choose one faculty member.</p>
                <form class="inline-form stacked" method="get" action="/reports/faculty">
                    <input type="hidden" name="type" value="individual">
                    <label><span>Department</span><select name="department" required>{department_options}</select></label>
                    {faculty_picker}
                    <button class="button" type="submit">{submit_label}</button>
                </form>
            </div>
        </section>
        {self.admin_back_link()}
        """

    def percent_table(self, label, values, options):
        total = len(values)
        cells = "".join(f"<th>{esc(option)}</th>" for option in options)
        numbers = ""
        for option in options:
            count = sum(1 for value in values if value == option)
            pct = "-" if total == 0 else f"{(count / total) * 100:.2f}"
            numbers += f"<td>{pct}</td>"
        return f"""
        <table class="report-table">
            <thead><tr><th>{esc(label)}</th>{cells}<th>Not Answered</th></tr></thead>
            <tbody><tr><td>In %</td>{numbers}<td>-</td></tr></tbody>
        </table>
        """

    def overall_report(self, method):
        user = self.current_user()
        if not user or user["role"] != "admin":
            return self.redirect("/")
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        report_path = parsed.path.rstrip("/") or "/reports/overall"
        is_faculty_review = report_path == "/reports/faculty"
        faculty_report_type = query.get("type", [""])[0] if is_faculty_review else ""
        selected_department = query.get("department", [""])[0].strip()
        selected_faculty_id = query.get("faculty_id", [""])[0].strip()
        if is_faculty_review and faculty_report_type not in ("overall", "individual"):
            return self.send_html(page("Faculty Feedback Review", self.faculty_report_options(selected_department, selected_faculty_id), user))
        faculty_id = None
        selected_faculty = None
        if is_faculty_review and faculty_report_type == "individual":
            if not selected_department or not selected_faculty_id.isdigit():
                return self.send_html(page("Faculty Feedback Review", self.faculty_report_options(selected_department, selected_faculty_id), user))
            with db() as conn:
                selected_faculty = conn.execute(
                    "SELECT id, name, employee_id, department FROM faculty WHERE id=%s AND department=%s",
                    (int(selected_faculty_id), selected_department),
                ).fetchone()
            if not selected_faculty:
                return self.send_html(page("Faculty Feedback Review", self.faculty_report_options(selected_department, selected_faculty_id), user))
            faculty_id = selected_faculty["id"]
        rows = self.overall_report_rows(faculty_id)
        if rows is None:
            return self.redirect("/")
        download = query.get("download", [""])[0] == "1"
        part_a_by_student = {}
        for row in rows:
            part_a_by_student.setdefault(row["student_id"], row)
        part_a_rows = list(part_a_by_student.values())
        part_a_total = len(part_a_rows)
        departments = sorted({row["department"] for row in rows}) or ["-"]
        if selected_faculty:
            departments = [selected_faculty["department"]]
        courses = sorted({row["course"] for row in rows}) or ["-"]
        students = {row["student_id"] for row in rows}
        faculty_meta_row = ""
        if selected_faculty:
            faculty_meta_row = f"<tr><th>Faculty Name</th><td>{esc(selected_faculty['name'])} ({esc(selected_faculty['employee_id'])})</td></tr>"

        reasons = []
        for row in part_a_rows:
            reasons.extend(
                reason.strip()
                for reason in (row["reason"] or "").split(",")
                if reason.strip()
            )
        reason_rows = ""
        for idx, reason in enumerate(COURSE_REASONS, 1):
            count = sum(1 for value in reasons if value == reason)
            pct = "-" if part_a_total == 0 else f"{(count / part_a_total) * 100:.2f}"
            reason_rows += f"<tr><td>Choice {idx}</td><td>{esc(reason)}</td><td>{pct}</td></tr>"

        facility_scores = []
        academic_scores = []
        programme_values = []
        support_values = []
        teacher_ratings = {}
        for row in part_a_rows:
            facilities = json.loads(row["facilities_json"] or "{}")
            facility_scores.extend(int(v) for v in facilities.values() if str(v).isdigit())

            course_answers = json.loads(row["course_answers_json"] or "{}")
            for key, question, options in FORM_A_CHOICES:
                answer = course_answers.get(question)
                if key in ("programme_rating", "admin_support"):
                    continue
                if answer in options:
                    academic_scores.append(len(options) - options.index(answer))
            programme_values.append(course_answers.get("On the whole, how would you rate the programme/course?"))
            support_values.append(course_answers.get("University administrative support related to your studies is"))

        faculty_directory = {}
        if is_faculty_review:
            if selected_faculty:
                faculty_records = [selected_faculty]
            else:
                with db() as conn:
                    faculty_records = conn.execute(
                        "SELECT id, name, employee_id FROM faculty ORDER BY department, name"
                    ).fetchall()
            faculty_directory = {
                row["id"]: {"name": row["name"], "employee_id": row["employee_id"]}
                for row in faculty_records
            }

        for row in rows:
            teacher_answers = json.loads(row["teacher_answers_json"] or "{}")
            score = sum(int(v) for v in teacher_answers.values() if str(v).isdigit())
            if score:
                teacher_ratings.setdefault(
                    row["faculty_id"],
                    {"name": row["faculty_name"], "employee_id": row["employee_id"], "scores": []},
                )
                teacher_ratings[row["faculty_id"]]["scores"].append(score)

        if is_faculty_review:
            faculty_percentages = []
            for faculty_key, data in faculty_directory.items():
                scores = teacher_ratings.get(faculty_key, {}).get("scores", [])
                average_score = sum(scores) / len(scores) if scores else None
                faculty_percentages.append((data["name"], data["employee_id"], average_score))
        else:
            faculty_percentages = [
                (data["name"], data["employee_id"], sum(data["scores"]) / len(data["scores"]))
                for data in teacher_ratings.values()
            ]
        faculty_scores = [score for _, _, score in faculty_percentages if score is not None]
        mean_score = "-" if not faculty_scores else f"{statistics.mean(faculty_scores):.2f}"
        median_score = "-" if not faculty_scores else f"{statistics.median(faculty_scores):.2f}"
        deviation = "-"
        if len(faculty_scores) > 1:
            deviation = f"{statistics.pstdev(faculty_scores):.2f}"
        elif len(faculty_scores) == 1:
            deviation = "0.00"

        faculty_rows = ""
        for index, (name, employee_id, score) in enumerate(sorted(faculty_percentages), 1):
            initials = "".join(part[0] for part in name.split()[:2]).upper() or employee_id[:2].upper()
            if score is None:
                faculty_rows += f"<tr><td>{index}</td><td>{esc(initials)}</td><td>{esc(name)}</td><td>-</td><td>No feedback submitted</td></tr>"
            else:
                remarks = "Excellent" if score >= 85 else "Very Good" if score >= 70 else "Good" if score >= 55 else "Needs Improvement"
                faculty_rows += f"<tr><td>{index}</td><td>{esc(initials)}</td><td>{esc(name)}</td><td>{score:.2f}</td><td>{remarks}</td></tr>"
        if not faculty_rows:
            faculty_rows = "<tr><td colspan='5'>No teacher assessment submitted yet.</td></tr>"

        facility_average = "-" if not facility_scores else f"{statistics.mean(facility_scores):.2f}"
        academic_average = "-" if not academic_scores else f"{statistics.mean(academic_scores):.2f}"
        report_year = academic_year_label()
        generated_at = indian_datetime_label()
        download_name = "faculty-feedback-review.html" if is_faculty_review else "overall-student-feedback-report.html"
        actions = "" if download else """
        <div class="report-actions">
            <button class="button" onclick="window.print()">Print / Save PDF</button>
        </div>
        """.format(report_path=report_path)
        title = "Faculty Feedback Review" if is_faculty_review else "Overall Feedback Report"
        if is_faculty_review and faculty_report_type == "individual" and selected_faculty:
            title = f"Faculty Feedback Review - {selected_faculty['name']}"
            download_name = f"faculty-feedback-review-{selected_faculty['employee_id']}.html"
        body = f"""
        {actions}
        <article class="report-sheet">
            <header class="report-header">
                <div class="report-brand">
                    {university_logo("report-seal")}
                    <strong>BANGALORE UNIVERSITY</strong>
                    <em>Feedback by students {report_year}</em>
                </div>
                <h1>Feedback by the students on academic & teaching infrastructure for the year {report_year}</h1>
            </header>
            <table class="report-table meta">
                <tr><th>Name of the Department</th><td>{esc(", ".join(departments))}</td></tr>
                {faculty_meta_row}
                <tr><th>Name of the Course</th><td>{esc(", ".join(courses))}</td></tr>
                <tr><th>Total Number of Students</th><td>{len(students)}</td></tr>
                <tr><th>Report Generated On</th><td>{esc(generated_at)}</td></tr>
            </table>
            <h2>Part - A</h2>
            <table class="report-table">
                <thead><tr><th>Question 1</th><th>Most Important Reason for selecting the course</th><th>In %</th></tr></thead>
                <tbody>{reason_rows}</tbody>
            </table>
            <table class="report-table">
                <tr><th>Question 2</th><td>Physical Infrastructure</td><td>Average Score out of 5</td><td>{facility_average}</td></tr>
                <tr><th>Question 3 - 13</th><td>Academic facility</td><td>Average Score out of 4</td><td>{academic_average}</td></tr>
            </table>
            {self.percent_table("Question 14 - On the whole rating of the programme/course by the students.", programme_values, ["Excellent", "Good", "Poor", "Very poor"])}
            {self.percent_table("Question 15 - University administrative support related to studies.", support_values, ["Excellent", "Good", "Satisfactory", "Not satisfactory"])}
            <h2>Part - B</h2>
            <h3>Students Assessment of Faculties (Max. Score 100)</h3>
            <table class="report-table">
                <tr><th>Mean for the Department</th><th>Median</th><th>Standard Deviation</th></tr>
                <tr><td>{mean_score}</td><td>{median_score}</td><td>{deviation}</td></tr>
            </table>
            <table class="report-table">
                <thead><tr><th>Sl. No</th><th>Faculty Initials</th><th>Faculty Name</th><th>Rating (in %)</th><th>Remarks</th></tr></thead>
                <tbody>{faculty_rows}</tbody>
            </table>
            <footer class="report-footer">
                <div>Internal Quality Assurance Cell<br>iqac@bub.ernet.in</div>
                <div>Vice Chancellor<br>Bangalore University<br>Bengaluru-560 056</div>
            </footer>
        </article>
        """
        content = page(title, body, self.current_user())
        if download:
            data = content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{download_name}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_html(content)

    def download_faculty_report(self, method):
        return self.overall_report(method)

    def download_department_report(self, method):
        rows = self.report_rows("department")
        if rows is None:
            return self.redirect("/")
        self.csv_response("department-wise-feedback.csv", rows)


if __name__ == "__main__":
    load_env_file()
    init_db()
    host = (os.environ.get("HOST") or DEFAULT_HOST).strip()
    port = int((os.environ.get("PORT") or str(DEFAULT_PORT)).strip())
    print(f"{APP_NAME}")
    print(f"Open http://{host}:{port}")
    try:
        ThreadingHTTPServer((host, port), App).serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
