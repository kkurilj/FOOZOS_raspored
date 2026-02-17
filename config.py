import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'foozos-raspored-secret-key-2025')
    DATABASE = os.path.join(BASE_DIR, 'instance', 'raspored.db')
