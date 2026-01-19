# config.py
# set up the database connection

import os 
from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI',
        'mysql+pymysql://root:root@localhost:3306/forum_user_db'
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=3)

