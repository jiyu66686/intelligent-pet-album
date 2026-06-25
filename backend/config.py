import os
from datetime import timedelta


class Config:
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost/pet_album?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT配置
    SECRET_KEY = 'pet-album-secret-key-2024'
    JWT_EXPIRATION = timedelta(days=7)

    # 文件上传配置
    UPLOAD_FOLDER = 'uploads/'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # 百度AI配置
    BAIDU_API_KEY = 'IRBimJhuOWJT7Tg40niV3JiD'
    BAIDU_SECRET_KEY = 'quInFbdU8WdsGFJTpYqHxfKeFmAjwxQv'