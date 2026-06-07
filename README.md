# RBAC 文件访问控制系统

基于 Flask-AppBuilder 的 RBAC（基于角色的访问控制）文件管理系统，支持细粒度权限控制、SSL 双向认证、审计日志和安全增强功能。

## 🚀 功能特性

- **RBAC 权限控制**：7 个角色，细粒度文件操作权限（查看/上传/编辑/下载/删除/分享）
- **文件管理**：上传、查看、编辑、下载、删除、分享链接
- **审计日志**：全操作记录（用户/IP/时间/操作类型）
- **SSL/TLS 双向认证**：自建 CA 三级证书体系，TLS 1.3 + AES-256-GCM
- **安全增强**：登录失败锁定、操作频率限制、密码复杂度校验、scrypt 加密存储
- **用户注册**：支持新用户注册，自动密码强度校验
- **Docker 部署**：双容器（Flask + MySQL），一键启动
- **云平台部署**：已适配 Render 云平台

## 📋 技术栈

| 层次 | 技术 |
|------|------|
| 后端 | Python 3.11 + Flask + Flask-AppBuilder |
| 数据库 | MySQL 8.0 / PostgreSQL |
| ORM | SQLAlchemy + PyMySQL |
| 前端 | Bootstrap 5 + 原生 JavaScript |
| 认证 | JWT（JSON Web Token） |
| 加密 | TLS 1.3 + AES-256-GCM + scrypt |
| 部署 | Docker + Render |

## 🛠️ 快速开始

### 环境要求
- Docker Desktop
- Python 3.11（可选，用于运行测试）

### 一键启动


# 1. 创建网络
docker network create rbac-net

# 2. 启动 MySQL
docker run -d --name rbac-mysql --network rbac-net \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -e MYSQL_DATABASE=rbac \
  -p 3307:3306 \
  -v ~/rbac-system/mysql-data:/var/lib/mysql \
  mysql:8.0

# 3. 等待 MySQL 就绪
sleep 20

# 4. 构建并启动应用
docker build -t myrbac .
docker run -d --name rbac-app --network rbac-net \
  -p 5000:5000 myrbac

# 5. 初始化数据库
docker exec -it rbac-app flask fab create-db
docker exec -it rbac-app flask fab create-admin
访问地址
地址	说明
https://localhost:5000	管理后台
https://localhost:5000/login	用户登录
https://localhost:5000/register	用户注册
https://localhost:5000/file-manager	文件管理器
https://localhost:5000/audit-log	审计日志
https://localhost:5000/api/v1/ssl/info	SSL 信息
默认账号
用户名	密码	角色
admin	admin	Admin（全部权限）
📁 项目结构
text
rbac-system/
├── Dockerfile                  # Docker 镜像构建
├── config.py                   # 数据库配置
├── requirements.txt            # Python 依赖
├── test_rbac.py                # 自动化测试（16个用例）
├── render.yaml                 # Render 云部署配置
├── docker-compose.yml          # 三容器编排
├── nginx.conf                  # Nginx SSL 配置
├── certs/                      # SSL 证书体系
│   ├── ca.crt / ca.key         # CA 根证书
│   ├── server.crt / server.key # 服务器证书
│   └── client.crt / client.key # 客户端证书
├── app/
│   ├── __init__.py             # 应用入口 + 路由 + 安全中间件
│   ├── models.py               # File 模型
│   ├── log_models.py           # 审计日志模型
│   ├── views.py                # FileView + FileApi
│   └── templates/
│       ├── login.html          # 登录页
│       ├── register.html       # 注册页
│       ├── file_manager.html   # 文件管理器
│       └── audit_log.html      # 审计日志页
└── mysql-data/                 # MySQL 持久化数据
🧪 运行测试
bash
pip install requests
python test_rbac.py
测试覆盖：用户认证、权限控制、SSL 通信、审计日志、数据库完整性。

🔐 角色权限矩阵
角色	查看	下载	上传	编辑	删除	分享
Admin	✅	✅	✅	✅	✅	✅
editor	✅	✅	✅	✅	❌	✅
viewer	✅	✅	❌	❌	❌	✅
contributor	✅	✅	✅	❌	❌	✅
auditor	✅	✅	❌	❌	❌	✅
guest	❌	❌	❌	❌	❌	❌
manager	✅	✅	✅	✅	✅	✅
🔒 安全功能
功能	说明
密码加密	scrypt 算法，非明文存储
密码复杂度	8位+大小写+数字
登录锁定	3次失败锁定5秒
频率限制	上传3次/30秒，删除2次/30秒
SSL/TLS	自建CA三级证书，TLS 1.3双向认证
审计日志	全操作记录（用户/IP/时间）
☁️ 云部署
已部署到 Render：https://你的Render网址

或使用 Railway / 任何支持 Docker 的平台。

📝 开源声明
Flask-AppBuilder（Apache 2.0）

Bootstrap 5（MIT）

大模型辅助开发（DeepSeek）

👤 作者
YNA - 北京科技大学 2026 年春软件安全实验
