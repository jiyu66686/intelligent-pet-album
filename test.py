import paramiko
import json

# 服务器信息
host = '121.43.24.232'
port = 22
username = 'root'
password = 'yying050111.'  # 你的服务器密码

# 连接到服务器
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port, username, password)

# 在服务器上执行 Python 命令
cmd = '''
cd /var/www/pet-album/backend
source venv/bin/activate
python3 -c "
from app import app
from utils.pet_recognition import recognize_pet
import os

print('服务器上的图片:', os.listdir('uploads/'))

with app.app_context():
    # 用实际的图片名
    for f in os.listdir('uploads/'):
        if f.endswith(('.jpeg', '.jpg', '.png')):
            print(f'识别: {f}')
            result = recognize_pet('uploads/' + f)
            print(result)
            break
"
'''

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()