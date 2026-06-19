import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "personality-lab-dev-key-change-in-production")
    DATA_DIR = os.path.join(BASE_DIR, "data")
    INSTRUMENTS_DIR = os.path.join(DATA_DIR, "instruments")
    NORMS_DIR = os.path.join(DATA_DIR, "norms")
    FEEDBACK_DIR = os.path.join(DATA_DIR, "feedback")
    SESSION_TYPE = "filesystem"
    BRUTAL_HONESTY = True  # 默认开启直接坦诚模式
