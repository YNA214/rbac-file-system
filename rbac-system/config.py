import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:root123@rbac-mysql/rbac')
FAB_API_SWAGGER_UI = True
