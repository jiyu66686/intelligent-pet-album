from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from models import db, User, PetPhoto, OperationLog, Like
from utils.jwt_helper import generate_token, verify_token
from utils.pet_recognition import recognize_pet
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from sqlalchemy import or_

app = Flask(__name__)
app.config.from_object('config.Config')
CORS(app)

db.init_app(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ============ 辅助函数 ============
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def log_operation(user_id, action, target_table, target_id, detail=''):
    try:
        log = OperationLog(
            user_id=user_id,
            action=action,
            target_table=target_table,
            target_id=target_id,
            detail=detail
        )
        db.session.add(log)
        db.session.commit()
    except:
        db.session.rollback()


def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': '未提供认证令牌'}), 401

        token = token.split(' ')[1]
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': '令牌无效或已过期'}), 401

        request.user = payload
        return f(*args, **kwargs)

    return decorated_function


# ============ 用户认证接口 ============
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400

    import bcrypt
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    user = User(username=username, password=hashed.decode('utf-8'), email=email)
    db.session.add(user)
    db.session.commit()

    log_operation(user.id, 'REGISTER', 'users', user.id, f'用户注册成功')

    return jsonify({'message': '注册成功', 'user': user.to_dict()}), 201


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 401

    import bcrypt
    if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({'error': '密码错误'}), 401

    token = generate_token(user.id, user.username, user.role)
    log_operation(user.id, 'LOGIN', 'users', user.id, '用户登录')

    return jsonify({
        'message': '登录成功',
        'token': token,
        'user': user.to_dict()
    })


@app.route('/api/user/info', methods=['GET'])
@login_required
def get_user_info():
    user = User.query.get(request.user['user_id'])
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    return jsonify(user.to_dict())


# ============ 照片管理接口 ============
@app.route('/api/photos', methods=['GET'])
@login_required
def get_photos():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort = request.args.get('sort', 'time')
    order = request.args.get('order', 'desc')
    search = request.args.get('search', '')
    pet_type = request.args.get('pet_type', '')

    query = PetPhoto.query

    if search:
        query = query.filter(
            or_(
                PetPhoto.photo_name.like(f'%{search}%'),
                PetPhoto.pet_breed.like(f'%{search}%'),
                PetPhoto.description.like(f'%{search}%')
            )
        )

    if pet_type in ('cat', 'dog', 'other', 'unknown'):
        query = query.filter(PetPhoto.pet_type == pet_type)

    if sort == 'name':
        order_column = PetPhoto.photo_name
    elif sort == 'likes':
        order_column = PetPhoto.likes
    else:
        order_column = PetPhoto.upload_time

    if order == 'asc':
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 获取当前用户已点赞的照片ID列表
    user_id = request.user['user_id']
    liked_photo_ids = {like.photo_id for like in Like.query.filter_by(user_id=user_id).all()}

    items = []
    for photo in pagination.items:
        item = photo.to_dict()
        item['has_liked'] = photo.id in liked_photo_ids
        items.append(item)

    log_operation(request.user['user_id'], 'QUERY', 'pet_photos', 0, f'查询照片列表')

    return jsonify({
        'items': items,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@app.route('/api/photos/<int:photo_id>', methods=['GET'])
@login_required
def get_photo(photo_id):
    photo = PetPhoto.query.get(photo_id)
    if not photo:
        return jsonify({'error': '照片不存在'}), 404

    log_operation(request.user['user_id'], 'QUERY', 'pet_photos', photo_id, '查看照片详情')
    return jsonify(photo.to_dict())


@app.route('/api/photos', methods=['POST'])
@login_required
def upload_photo():
    if 'photo' not in request.files:
        return jsonify({'error': '未上传图片文件'}), 400

    file = request.files['photo']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件格式，请上传jpg/png/gif'}), 400

    original_filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(filepath)

    photo_name = request.form.get('photo_name', original_filename)
    description = request.form.get('description', '')

    try:
        recognition_result = recognize_pet(filepath)
        pet_type = recognition_result.get('pet_type', 'unknown')
        pet_breed = recognition_result.get('pet_breed', '未知品种')
        confidence = recognition_result.get('confidence', 0.0)

        # 如果识别结果是非动物或未知，拒绝上传
        if pet_type == 'unknown' or '非动物' in pet_breed:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({
                'error': f'❌ 检测到非动物图片（{pet_breed}），请上传猫或狗的照片'
            }), 400

    except Exception as e:
        pet_type = 'unknown'
        pet_breed = '识别失败'
        confidence = 0.0

    photo = PetPhoto(
        user_id=request.user['user_id'],
        photo_url=f"/uploads/{unique_filename}",
        photo_name=photo_name,
        description=description,
        pet_type=pet_type,
        pet_breed=pet_breed,
        confidence=confidence
    )

    db.session.add(photo)
    db.session.commit()

    log_operation(
        request.user['user_id'],
        'CREATE',
        'pet_photos',
        photo.id,
        f'上传照片：{photo_name}，识别为{pet_breed}'
    )

    return jsonify({
        'message': '上传成功',
        'photo': photo.to_dict(),
        'recognition': {'pet_type': pet_type, 'pet_breed': pet_breed, 'confidence': confidence}
    }), 201


@app.route('/api/photos/<int:photo_id>', methods=['PUT'])
@login_required
def update_photo(photo_id):
    photo = PetPhoto.query.get(photo_id)
    if not photo:
        return jsonify({'error': '照片不存在'}), 404

    if photo.user_id != request.user['user_id'] and request.user['role'] != 'admin':
        return jsonify({'error': '没有权限修改该照片'}), 403

    data = request.get_json()
    photo.photo_name = data.get('photo_name', photo.photo_name)
    photo.description = data.get('description', photo.description)

    db.session.commit()

    log_operation(
        request.user['user_id'],
        'UPDATE',
        'pet_photos',
        photo_id,
        f'更新照片信息：{photo.photo_name}'
    )

    return jsonify({'message': '更新成功', 'photo': photo.to_dict()})


@app.route('/api/photos/<int:photo_id>', methods=['DELETE'])
@login_required
def delete_photo(photo_id):
    photo = PetPhoto.query.get(photo_id)
    if not photo:
        return jsonify({'error': '照片不存在'}), 404

    if photo.user_id != request.user['user_id'] and request.user['role'] != 'admin':
        return jsonify({'error': '没有权限删除该照片'}), 403

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], photo.photo_url.split('/')[-1])
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(photo)
    db.session.commit()

    log_operation(
        request.user['user_id'],
        'DELETE',
        'pet_photos',
        photo_id,
        f'删除照片：{photo.photo_name}'
    )

    return jsonify({'message': '删除成功'})


@app.route('/api/photos/<int:photo_id>/like', methods=['POST'])
@login_required
def like_photo(photo_id):
    user_id = request.user['user_id']

    photo = PetPhoto.query.get(photo_id)
    if not photo:
        return jsonify({'error': '照片不存在'}), 404

    # 检查是否已点赞
    existing_like = Like.query.filter_by(user_id=user_id, photo_id=photo_id).first()
    if existing_like:
        return jsonify({'error': '您已经点过赞了'}), 400

    # 创建点赞记录
    like = Like(user_id=user_id, photo_id=photo_id)
    db.session.add(like)

    # 照片点赞数+1
    photo.likes += 1
    db.session.commit()

    log_operation(
        request.user['user_id'],
        'LIKE',
        'pet_photos',
        photo_id,
        f'点赞照片：{photo.photo_name}'
    )

    return jsonify({'message': '点赞成功', 'likes': photo.likes})


@app.route('/api/photos/<int:photo_id>/unlike', methods=['POST'])
@login_required
def unlike_photo(photo_id):
    user_id = request.user['user_id']

    photo = PetPhoto.query.get(photo_id)
    if not photo:
        return jsonify({'error': '照片不存在'}), 404

    like = Like.query.filter_by(user_id=user_id, photo_id=photo_id).first()
    if not like:
        return jsonify({'error': '您还没有点赞'}), 400

    db.session.delete(like)
    photo.likes -= 1
    db.session.commit()

    return jsonify({'message': '取消点赞成功', 'likes': photo.likes})


@app.route('/api/photos/batch-delete', methods=['POST'])
@login_required
def batch_delete_photos():
    """批量删除照片"""
    data = request.get_json()
    ids = data.get('ids', [])
    if not ids or not isinstance(ids, list):
        return jsonify({'error': '请选择要删除的图片'}), 400

    success_count = 0
    for photo_id in ids:
        try:
            photo = PetPhoto.query.get(photo_id)
            if not photo:
                continue
            if photo.user_id != request.user['user_id'] and request.user['role'] != 'admin':
                continue
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], photo.photo_url.split('/')[-1])
            if os.path.exists(filepath):
                os.remove(filepath)
            db.session.delete(photo)
            success_count += 1
        except Exception as e:
            print(f"批量删除失败 id={photo_id}: {e}")
            continue

    db.session.commit()

    log_operation(
        request.user['user_id'],
        'BATCH_DELETE',
        'pet_photos',
        0,
        f'批量删除 {success_count} 张照片'
    )

    return jsonify({'message': f'成功删除 {success_count} 张照片', 'success': success_count})


# ============ 统计接口 ============
@app.route('/api/statistics', methods=['GET'])
@login_required
def get_statistics():
    total_photos = PetPhoto.query.count()
    cat_count = PetPhoto.query.filter_by(pet_type='cat').count()
    dog_count = PetPhoto.query.filter_by(pet_type='dog').count()
    other_count = PetPhoto.query.filter_by(pet_type='other').count()
    unknown_count = PetPhoto.query.filter_by(pet_type='unknown').count()

    # 计算总点赞数
    total_likes = db.session.query(db.func.sum(PetPhoto.likes)).scalar() or 0

    from sqlalchemy import func
    breed_stats = db.session.query(
        PetPhoto.pet_breed,
        func.count(PetPhoto.id).label('count')
    ).filter(PetPhoto.pet_breed.isnot(None)) \
        .group_by(PetPhoto.pet_breed) \
        .order_by(func.count(PetPhoto.id).desc()) \
        .limit(10).all()

    recent_photos = PetPhoto.query.order_by(PetPhoto.upload_time.desc()).limit(5).all()

    return jsonify({
        'total_photos': total_photos,
        'cat_count': cat_count,
        'dog_count': dog_count,
        'other_count': other_count,
        'unknown_count': unknown_count,
        'total_likes': total_likes,
        'breed_stats': [{'breed': stat[0], 'count': stat[1]} for stat in breed_stats],
        'recent_photos': [photo.to_dict() for photo in recent_photos]
    })


# ============ 操作日志接口 ============
@app.route('/api/logs', methods=['GET'])
@login_required
def get_logs():
    if request.user['role'] != 'admin':
        return jsonify({'error': '需要管理员权限'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = OperationLog.query.order_by(OperationLog.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


# ============ 点赞修复接口 ============
@app.route('/api/fix-likes', methods=['POST'])
@login_required
def fix_likes():
    """修复点赞统计（管理员专用）"""
    if request.user['role'] != 'admin':
        return jsonify({'error': '需要管理员权限'}), 403

    try:
        # 1. 重置所有照片的点赞数为0
        PetPhoto.query.update({PetPhoto.likes: 0})
        db.session.commit()

        # 2. 重新统计 Like 表
        all_likes = Like.query.all()
        for like in all_likes:
            photo = PetPhoto.query.get(like.photo_id)
            if photo:
                photo.likes += 1
        db.session.commit()

        total_likes = db.session.query(db.func.sum(PetPhoto.likes)).scalar() or 0

        return jsonify({
            'message': '点赞统计已修复',
            'total_likes': total_likes
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'修复失败: {str(e)}'}), 500


# ============ 静态文件服务 ============
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


# ============ 初始化数据库 ============
@app.cli.command('init-db')
def init_db():
    db.create_all()
    import bcrypt
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        admin = User(username='admin', password=hashed.decode('utf-8'), email='admin@example.com', role='admin')
        db.session.add(admin)
        db.session.commit()
        print('管理员账户创建成功: admin / admin123')

    print('数据库初始化完成！')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)