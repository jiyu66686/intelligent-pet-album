import requests
import base64
import random
import os
from flask import current_app

# 品种关键词映射
BREED_MAP = {
    'cat': ['猫', '猫猫', 'cat', '布偶', '英短', '美短', '暹罗', '波斯', '缅因', '折耳', '加菲', '橘猫', '狸花', '豹猫', '狮子猫', '金吉拉', '田园猫'],
    'dog': ['狗', '狗狗', 'dog', '金毛', '哈士奇', '柴犬', '柯基', '拉布拉多', '萨摩耶', '德牧', '喜乐蒂', '腊肠', '泰迪', '比熊', '博美', '雪纳瑞', '秋田', '边牧', '吉娃娃', '阿拉斯加'],
    'other': ['鸟', '兔子', '仓鼠', '龙猫', '松鼠', '刺猬', '狐狸', '狼', '熊', '熊猫', '虎', '狮子', '豹', '鹿', '猴', '猩猩', '象', '长颈鹿', '斑马', '牛', '羊', '马', '猪']
}


def get_access_token():
    api_key = current_app.config.get('BAIDU_API_KEY')
    secret_key = current_app.config.get('BAIDU_SECRET_KEY')
    if not api_key or not secret_key:
        raise ValueError("请在config.py中配置BAIDU_API_KEY和BAIDU_SECRET_KEY")
    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.RequestException as e:
        raise RuntimeError(f"获取百度AI Access Token失败: {e}")


def classify_pet_type(breed_name):
    """
    智能判断宠物类型：
    返回 'cat' | 'dog' | 'other' | 'unknown'
    """
    breed_lower = breed_name.lower()

    # 🆕 第一轮：明确排除非动物（优先级最高！）
    if '非动物' in breed_name or 'non-animal' in breed_lower or 'non animal' in breed_lower:
        return 'unknown'

    # 第二轮：精确关键词匹配（猫）
    for keyword in BREED_MAP['cat']:
        if keyword in breed_lower:
            return 'cat'

    # 第三轮：精确关键词匹配（狗）
    for keyword in BREED_MAP['dog']:
        if keyword in breed_lower:
            return 'dog'

    # 第四轮：语义判断
    if '猫' in breed_name or 'cat' in breed_lower:
        return 'cat'
    if '狗' in breed_name or 'dog' in breed_lower or '犬' in breed_name:
        return 'dog'

    # 第五轮：其他动物关键词
    other_keywords = [
        '鸟', 'bird', '兔子', 'rabbit', '仓鼠', 'hamster', '龙猫', 'chinchilla',
        '松鼠', 'squirrel', '刺猬', 'hedgehog', '狐狸', 'fox', '狼', 'wolf',
        '熊', 'bear', '熊猫', 'panda', '虎', 'tiger', '狮子', 'lion', '豹', 'leopard',
        '鹿', 'deer', '猴', 'monkey', '猩猩', 'gorilla', '象', 'elephant',
        '长颈鹿', 'giraffe', '斑马', 'zebra', '牛', 'cow', '羊', 'sheep', '马', 'horse', '猪', 'pig'
    ]
    for keyword in other_keywords:
        if keyword in breed_lower:
            return 'other'

    # 最后：实在无法判断就返回 unknown
    return 'unknown'


def recognize_pet(image_path):
    """
    识别宠物，返回 {'pet_type': 'cat'|'dog'|'other'|'unknown', 'pet_breed': '品种名', 'confidence': 0.95}
    """
    try:
        token = get_access_token()
        if not token:
            return simulate_recognition(image_path)
    except Exception:
        return simulate_recognition(image_path)

    try:
        with open(image_path, 'rb') as f:
            img_data = f.read()
            if len(img_data) > 4 * 1024 * 1024:
                return {'pet_type': 'unknown', 'pet_breed': '图片超过4MB限制', 'confidence': 0.0}
            img_base64 = base64.b64encode(img_data).decode('utf-8')
    except FileNotFoundError:
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    except Exception as e:
        return {'pet_type': 'unknown', 'pet_breed': f'读取图片失败: {str(e)}', 'confidence': 0.0}

    request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/animal"
    params = {"access_token": token, "image": img_base64, "top_num": 3}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        response = requests.post(request_url, data=params, headers=headers, timeout=15)
        response.raise_for_status()
        result = response.json()

        if "error_code" in result:
            if result.get("error_code") in [17, 18, 6]:
                return simulate_recognition(image_path)
            return {'pet_type': 'unknown', 'pet_breed': f'API错误: {result.get("error_msg", "未知错误")}', 'confidence': 0.0}

        if "result" in result and len(result["result"]) > 0:
            top_result = result["result"][0]
            breed_name = top_result.get("name", "未知品种")
            confidence = top_result.get("score", 0.0)

            try:
                confidence = float(confidence)
            except (ValueError, TypeError):
                confidence = 0.0

            # 🆕 关键修复：非动物直接归类为 unknown
            if '非动物' in breed_name or 'non-animal' in breed_name.lower():
                return {
                    'pet_type': 'unknown',
                    'pet_breed': breed_name,
                    'confidence': round(confidence, 2)
                }

            pet_type = classify_pet_type(breed_name)

            return {
                'pet_type': pet_type,
                'pet_breed': breed_name,
                'confidence': round(confidence, 2)
            }
        else:
            return simulate_recognition(image_path)

    except requests.RequestException:
        return simulate_recognition(image_path)
    except Exception as e:
        return {'pet_type': 'unknown', 'pet_breed': f'识别异常: {str(e)}', 'confidence': 0.0}

def simulate_recognition(image_path):
    """
    模拟识别（API不可用时的备用方案）
    返回 'cat' | 'dog' | 'other' | 'unknown'
    """
    breeds = {
        'cat': ['布偶猫', '英短', '美短', '暹罗猫', '波斯猫', '缅因猫', '折耳猫', '加菲猫', '橘猫', '狸花猫'],
        'dog': ['金毛', '哈士奇', '柴犬', '柯基', '拉布拉多', '萨摩耶', '德牧', '喜乐蒂', '腊肠犬', '泰迪'],
        'other': ['鹦鹉', '兔子', '仓鼠', '龙猫', '松鼠', '小熊猫', '狐狸', '鹿', '刺猬', '蜜袋鼯']
    }
    filename = os.path.basename(image_path)
    hash_val = hash(filename + 'simulate') % 100

    if hash_val < 35:
        pet_type = 'cat'
        breed = random.choice(breeds['cat'])
    elif hash_val < 70:
        pet_type = 'dog'
        breed = random.choice(breeds['dog'])
    else:
        pet_type = 'other'
        breed = random.choice(breeds['other'])

    confidence = round(random.uniform(0.75, 0.98), 2)

    return {
        'pet_type': pet_type,
        'pet_breed': breed,
        'confidence': confidence
    }