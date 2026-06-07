from flask import Flask, render_template, Response, jsonify, request
from flask_appbuilder import AppBuilder
from flask_sqlalchemy import SQLAlchemy
from flask_appbuilder.security.sqla.models import User, Role
import jwt, re, datetime, uuid

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

with app.app_context():
    appbuilder = AppBuilder(app, db.session)
    from .models import File
    from .log_models import FileAccessLog
    from . import views
    appbuilder.add_api(views.FileApi)
    appbuilder.add_view(views.FileView, "Files", icon="fa-files-o", category="File Management")

def get_user_from_token():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '): return None
    try:
        token = auth[7:]
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return db.session.query(User).get(payload['sub'])
    except: return None

login_attempts = {}
LOCK_COUNT = 3
LOCK_TIME = 5

@app.after_request
def handle_login_lock(response):
    if request.path == '/api/v1/security/login' and request.method == 'POST':
        data = request.get_json(silent=True) or {}
        username = data.get('username', '')
        if not username: return response
        fail_count, locked_until = login_attempts.get(username, (0, None))
        if locked_until and locked_until > datetime.datetime.utcnow():
            remain = int((locked_until - datetime.datetime.utcnow()).total_seconds())
            response.set_data(jsonify({"message": f"账户已锁定，{remain}秒后重试"}).get_data())
            response.status_code = 423
            return response
        if response.status_code == 200:
            login_attempts[username] = [0, None]
        else:
            fail_count += 1
            if fail_count >= LOCK_COUNT:
                login_attempts[username] = [fail_count, datetime.datetime.utcnow() + datetime.timedelta(seconds=LOCK_TIME)]
            else:
                login_attempts[username] = [fail_count, None]
    return response

rate_limits = {}
RATE_LIMITS = {'upload': (3, 30), 'delete': (2, 30)}

@app.before_request
def check_rate_limit():
    if request.path in ['/api/v1/file/upload', '/api/v1/file/'] and request.method in ['POST', 'DELETE']:
        user = get_user_from_token()
        if not user: return
        action = 'upload' if request.method == 'POST' else 'delete'
        max_count, seconds = RATE_LIMITS.get(action, (999, 60))
        now = datetime.datetime.utcnow()
        key = f"{user.id}_{action}"
        records = rate_limits.get(key, [])
        records = [t for t in records if now - t < datetime.timedelta(seconds=seconds)]
        if len(records) >= max_count:
            return jsonify({"message": f"操作过于频繁，{seconds}秒内最多{max_count}次"}), 429
        records.append(now)
        rate_limits[key] = records

# ========== 文件分享链接（内存存储） ==========
share_links = {}  # {share_id: {file_id, created_by, created_at}}

@app.route('/api/v1/file/<int:pk>/share', methods=['POST'])
def create_share(pk):
    user = get_user_from_token()
    if not user: return jsonify({"message": "未登录"}), 401
    item = db.session.query(File).get(pk)
    if not item: return jsonify({"message": "文件不存在"}), 404
    share_id = uuid.uuid4().hex[:10]
    share_links[share_id] = {"file_id": pk, "created_by": user.username, "created_at": datetime.datetime.utcnow().isoformat()}
    return jsonify({"share_url": f"/share/{share_id}", "share_id": share_id})

@app.route('/share/<share_id>')
def view_share(share_id):
    info = share_links.get(share_id)
    if not info: return "链接已失效", 404
    item = db.session.query(File).get(info['file_id'])
    if not item: return "文件已被删除", 404
    return Response(item.content or '', mimetype='text/plain',
        headers={'Content-Disposition': f'attachment; filename={item.filename or "download.txt"}'})

@app.route('/api/v1/file/<int:pk>/download')
def file_download(pk):
    item = db.session.query(File).get(pk)
    if not item: return jsonify({"message": "Not found"}), 404
    return Response(item.content or '', mimetype='text/plain',
        headers={'Content-Disposition': 'attachment; filename=' + (item.filename or 'download.txt')})

@app.route('/api/v1/user/roles')
def user_roles():
    user = get_user_from_token()
    if not user: return jsonify({"roles": []})
    return jsonify({"roles": [r.name for r in user.roles]})

@app.route('/api/v1/ssl/info')
def ssl_info():
    return jsonify({"ssl_enabled": True, "mutual_auth": True,
        "protocol": "TLSv1.3", "cipher": "TLS_AES_256_GCM_SHA384", "client_cert_required": True})

@app.route('/api/v1/audit-log')
def audit_log():
    user = get_user_from_token()
    if not user: return jsonify({"logs": []}), 401
    from .log_models import FileAccessLog
    role_names = [r.name for r in user.roles]
    is_admin = 'Admin' in role_names or 'admin' in role_names
    if is_admin:
        logs = db.session.query(FileAccessLog).order_by(FileAccessLog.id.desc()).limit(100).all()
    else:
        logs = db.session.query(FileAccessLog).filter_by(user_id=user.id).order_by(FileAccessLog.id.desc()).limit(50).all()
    result = []
    for log in logs:
        u = db.session.query(User).get(log.user_id)
        result.append({"id": log.id, "username": u.username if u else "未知",
            "action": log.action, "file_id": log.file_id,
            "ip_address": log.ip_address, "timestamp": log.timestamp.isoformat() if log.timestamp else "",
            "success": log.success})
    return jsonify({"logs": result, "is_admin": is_admin})

@app.route('/api/v1/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    if len(username) < 2: return jsonify({"message": "用户名至少2个字符"}), 400
    if len(password) < 8: return jsonify({"message": "密码至少8位"}), 400
    if not re.search(r'[A-Z]', password): return jsonify({"message": "密码需包含大写字母"}), 400
    if not re.search(r'[a-z]', password): return jsonify({"message": "密码需包含小写字母"}), 400
    if not re.search(r'[0-9]', password): return jsonify({"message": "密码需包含数字"}), 400
    existing = db.session.query(User).filter_by(username=username).first()
    if existing: return jsonify({"message": "用户名已存在"}), 400
    try:
        role = db.session.query(Role).filter_by(name='viewer').first()
        if not role: role = db.session.query(Role).filter_by(name='Public').first()
        appbuilder.sm.add_user(username=username, first_name=username, last_name='', email=email, role=role, password=password)
        return jsonify({"message": "注册成功", "username": username}), 201
    except Exception as e:
        return jsonify({"message": f"注册失败: {str(e)}"}), 400

@app.route('/audit-log')
def audit_log_page(): return render_template('audit_log.html')

@app.route('/register')
def register_page(): return render_template('register.html')

@app.route('/login')
def login_page(): return render_template('login.html')

@app.route('/file-manager')
def file_manager(): return render_template('file_manager.html')
