"""
RBAC 文件管理系统 - 完整测试套件（HTTPS 版本）
"""
import requests
import subprocess
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://localhost:5000/api/v1"
VERIFY = False
RESULTS = []

def log(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    symbol = "✅" if passed else "❌"
    RESULTS.append((name, status, detail))
    print(f"{symbol} {status} | {name}")
    if detail and not passed:
        print(f"    详情: {detail}")

# 使用 session 持久化连接
session = requests.Session()
session.verify = False

def login(user, pwd):
    r = session.post(f"{BASE}/security/login", json={
        "username": user, "password": pwd, "provider": "db"
    })
    return r.json().get("access_token"), r.status_code

def api(method, path, token, **kw):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    if "json" in kw: h["Content-Type"] = "application/json"
    return session.request(method, f"{BASE}{path}", headers=h, **kw)

print("=" * 50)
print("测试组1：用户认证（HTTPS）")
print("=" * 50)

token, code = login("admin", "admin")
log("管理员登录成功", code == 200 and token is not None)

_, code = login("admin", "wrong_pwd")
log("错误密码登录失败", code != 200)

_, code = login("fake_user", "x")
log("不存在用户登录失败", code != 200)

print("\n" + "=" * 50)
print("测试组2：文件权限控制")
print("=" * 50)

admin_t, _ = login("admin", "admin")
viewer_t, _ = login("viewer_user", "viewer123")

r = api("post", "/file/", admin_t, json={"filename": "ssl_test.txt"})
file_id = r.json().get("id") if r.status_code == 201 else None
log("Admin创建文件", r.status_code == 201, str(r.status_code))

r = api("get", "/file/", admin_t)
log("Admin查看文件列表", r.status_code == 200)

if file_id:
    r = api("put", f"/file/{file_id}", admin_t, json={"filename": "ssl_renamed.txt"})
    log("Admin编辑文件", r.status_code == 200)

r = api("get", "/file/", viewer_t)
log("Viewer查看文件列表", r.status_code == 200)

r = api("post", "/file/", viewer_t, json={"filename": "hack.txt"})
log("Viewer创建文件被拒绝", r.status_code in [401, 403], str(r.status_code))

if file_id:
    r = api("delete", f"/file/{file_id}", viewer_t)
    log("Viewer删除文件被拒绝", r.status_code in [401, 403], str(r.status_code))

if file_id:
    r = api("delete", f"/file/{file_id}", admin_t)
    log("Admin删除文件", r.status_code == 200)

print("\n" + "=" * 50)
print("测试组3：SSL/TLS 安全通道")
print("=" * 50)

r = session.get(f"{BASE}/file/")
log("HTTPS连接成功", r.status_code in [200, 401])

try:
    r = requests.get("http://localhost:5000/api/v1/file/", timeout=3)
    log("HTTP明文可访问", False, "应该被拒绝")
except Exception:
    log("HTTP明文被拒绝", True)

print("\n" + "=" * 50)
print("测试组4：审计日志")
print("=" * 50)

result = subprocess.run([
    "docker", "exec", "rbac-mysql", "mysql", "-uroot", "-proot123",
    "-e", "SELECT COUNT(*) AS cnt FROM file_access_log;", "rbac"
], capture_output=True, text=True)
lines = result.stdout.strip().split('\n')
cnt = lines[-1] if len(lines) > 1 else "0"
log("审计日志有记录", int(cnt) > 0 if cnt.isdigit() else False, f"日志条数={cnt}")

print("\n" + "=" * 50)
print("测试组5：数据库表完整性")
print("=" * 50)

r = subprocess.run([
    "docker", "exec", "rbac-mysql", "mysql", "-uroot", "-proot123",
    "-e", "SHOW TABLES;", "rbac"
], capture_output=True, text=True)
log("MySQL包含RBAC基础表", "ab_user" in r.stdout and "ab_role" in r.stdout)
log("MySQL包含file表", "file" in r.stdout)
log("MySQL包含file_access_log表", "file_access_log" in r.stdout)

print("\n" + "=" * 50)
print("测试汇总")
print("=" * 50)
passed = sum(1 for _, s, _ in RESULTS if s == "PASS")
failed = sum(1 for _, s, _ in RESULTS if s == "FAIL")
total = len(RESULTS)
print(f"总计: {total} | 通过: {passed} | 失败: {failed}")
print(f"通过率: {passed/total*100:.1f}%" if total else "0%")
