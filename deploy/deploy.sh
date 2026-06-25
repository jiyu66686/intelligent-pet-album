#!/bin/bash

# 部署脚本 - 在服务器上执行

echo "开始部署智能宠物相册系统..."

# 更新代码
cd /var/www/pet-photo-album
git pull origin main

# 后端部署
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 初始化数据库（首次执行）
flask init-db

# 重启后端服务
sudo systemctl restart pet-album

# 前端构建
cd ../frontend
npm install
npm run build

# 重载Nginx
sudo nginx -t
sudo systemctl reload nginx

echo "部署完成！"