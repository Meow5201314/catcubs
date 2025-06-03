<<<<<<< HEAD
# CatCubs 博客系统

一个基于 Flask 的个人博客+社区网站，支持发帖、评论、私信、通知、举报等功能。

## 功能特色

- 用户注册登录（邮箱验证、人机验证）
- 发布文章（支持 Markdown）
- 评论文章及回复评论系统
- 私信功能
- 个人资料修改
- 通知系统（发布公告、被封禁、有人回复帖子或者评论等通知）
- 举报功能（举报后管理员、站长可查看管理面板处理）
- 三级权限管理（普通用户/管理员/站长）
- 管理后台

## 环境要求

- Python 3.12
- MySQL/MariaDB 5.7+
- SMTP 邮箱服务（用于邮箱验证）

## 快速开始

### 1. 安装依赖

```bash
# 建议使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

pip install -r requirements.txt

```
### 2. 创建数据库

```mysql
CREATE DATABASE catcubs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'catcubs_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON catcubs.* TO 'catcubs_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：
```base
cp .env.example .env
```
重要配置项：

- `DATABASE_URL`: 数据库连接地址
- `SECRET_KEY`: Flask 密钥（请生成新的）
- `MAIL_*`: 邮件服务配置（必需，用于邮箱验证）

### 4. 初始化数据库

```bash
# 应用数据库迁移
flask db upgrade

# 初始化数据库表
python setup_database.py
```

### 5. 启动网站

```bash
python run.py
```

访问 http://localhost:5000

### 6. 设置管理员

1. 在网站注册第一个账户
2. 运行管理员设置脚本：

```bash
python set_admin.py
```

1. 选择刚注册的用户设置为站长

现在可以访问 `/admin` 进入管理后台了！

## 权限说明

- **普通用户**: 发帖、评论、私信
- **管理员**: 普通用户权限 + 删除帖子/评论、封禁用户、处理举报
- **站长**: 管理员权限 + 设置其他管理员、系统公告

## 项目结构

```
catcubs/
├── app/                    # 主应用代码
│   ├── routes/            # 路由模块
│   ├── templates/         # HTML 模板
│   ├── static/           # 静态文件
│   └── models.py         # 数据模型
├── migrations/           # 数据库迁移文件
└── config.py            # 配置文件
```

## 注意事项

1. 首次运行需要配置邮件服务，否则用户无法完成邮箱验证
2. 生产环境请修改 `SECRET_KEY` 和数据库密码
=======
# CatCubs 博客系统

一个基于 Flask 的个人博客+社区网站，支持发帖、评论、私信、通知、举报等功能。

## 功能特色

- 用户注册登录（邮箱验证、人机验证）
- 发布文章（支持 Markdown）
- 评论文章及回复评论系统
- 私信功能
- 个人资料修改
- 通知系统（发布公告、被封禁、有人回复帖子或者评论等通知）
- 举报功能（举报后管理员、站长可查看管理面板处理）
- 三级权限管理（普通用户/管理员/站长）
- 管理后台

## 环境要求

- Python 3.12
- MySQL/MariaDB 5.7+
- SMTP 邮箱服务（用于邮箱验证）

## 快速开始

### 1. 安装依赖

```bash
# 建议使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

pip install -r requirements.txt

### 2. 创建数据库

```mysql
CREATE DATABASE catcubs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'catcubs_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON catcubs.* TO 'catcubs_user'@'localhost';
FLUSH PRIVILEGES;
```
### 3. 配置环境变量
复制 `.env.example` 为 `.env` 并修改配置：
```base
cp .env.example .env
```
重要配置项：

- `DATABASE_URL`: 数据库连接地址
- `SECRET_KEY`: Flask 密钥（请生成新的）
- `MAIL_*`: 邮件服务配置（必需，用于邮箱验证）

### 4. 初始化数据库

```bash
# 应用数据库迁移
flask db upgrade

# 初始化数据库表
python setup_database.py
```

### 5. 启动网站

```bash
python run.py
```

访问 http://localhost:5000

### 6. 设置管理员

1. 在网站注册第一个账户
2. 运行管理员设置脚本：

```bash
python set_admin.py
```

1. 选择刚注册的用户设置为站长

现在可以访问 `/admin` 进入管理后台了！

## 权限说明

- **普通用户**: 发帖、评论、私信
- **管理员**: 普通用户权限 + 删除帖子/评论、封禁用户、处理举报
- **站长**: 管理员权限 + 设置其他管理员、系统公告

## 项目结构

```
catcubs/
├── app/                    # 主应用代码
│   ├── routes/            # 路由模块
│   ├── templates/         # HTML 模板
│   ├── static/           # 静态文件
│   └── models.py         # 数据模型
├── migrations/           # 数据库迁移文件
└── config.py            # 配置文件
```

## 注意事项

1. 首次运行需要配置邮件服务，否则用户无法完成邮箱验证
2. 生产环境请修改 `SECRET_KEY` 和数据库密码
>>>>>>> 81e637fcfecb61d89e503db91f19b153f055eca2
3. 如需禁用邮箱验证，可在代码中修改相关中间件