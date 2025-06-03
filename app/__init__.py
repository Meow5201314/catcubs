from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from config import Config
from app.utils import format_datetime
from werkzeug.middleware.proxy_fix import ProxyFix
import markdown
from flask_mail import Mail

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()

login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录访问此页面。'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 添加代理支持
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_prefix=1
    )   
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # 初始化邮件
    mail.init_app(app)
    
    # 注册蓝图
    from app.routes.auth import auth as auth_blueprint
    from app.routes.main import main as main_blueprint
    from app.routes.posts import posts as posts_blueprint
    from app.routes.uploads import uploads as uploads_blueprint
    from app.routes.admin import admin as admin_blueprint
    from app.routes.admin_actions import admin_actions as admin_actions_blueprint
    
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)
    app.register_blueprint(posts_blueprint)
    app.register_blueprint(uploads_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(admin_actions_blueprint)
    
    # 豁免上传路由的 CSRF 保护
    csrf.exempt(uploads_blueprint)
    
    # 注册中间件
    from app.middleware import check_email_verification
    
    @app.before_request
    def before_request():
        return check_email_verification()
    
    # 注册报告蓝图
    from app.routes.reports import reports as reports_blueprint
    app.register_blueprint(reports_blueprint)
    
    # 注册上下文处理器
    @app.context_processor
    def inject_now():
        beijing_now = datetime.now(app.config['TIMEZONE'])
        return {'now': beijing_now, 'year': beijing_now.year}
    
    # 添加全局过滤器
    @app.template_filter('datetime')
    def jinja2_filter_datetime(dt):
        return format_datetime(dt)
    
    # 添加 markdown 过滤器
    @app.template_filter('markdown')
    def jinja2_filter_markdown(text):
        if text:
            # 使用与帖子相同的 Markdown 扩展
            extensions = [
                'extra',
                'codehilite',
                'toc',
                'fenced_code',
                'nl2br',
                'tables',
                'footnotes',
                'abbr',
                'attr_list',
                'def_list',
                'sane_lists'
            ]
            
            # 配置代码高亮
            extension_configs = {
                'codehilite': {
                    'css_class': 'highlight',
                    'linenums': False
                }
            }
            
            return markdown.markdown(
                text, 
                extensions=extensions,
                extension_configs=extension_configs
            )
        return ''
    
    return app
