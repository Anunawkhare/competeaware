import os

class Config:
    SECRET_KEY = 'your-secret-key-here'
    DATABASE = 'competeaware.db'
    SCRAPING_INTERVAL = 3600  # 1 hour
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    EMAIL_USER = 'your-email@gmail.com'
    EMAIL_PASSWORD = 'your-app-password'