<<<<<<< HEAD
from app import create_app, db
from app.models import User, Announcement
from werkzeug.security import generate_password_hash
from app.utils import get_beijing_time

def setup_database():
    """初始化数据库，创建所有表"""
    app = create_app()
    with app.app_context():
        print("正在初始化数据库...")
        
        # 创建所有表
        db.create_all()
        print("✓ 数据库表创建完成")
        
        # 创建默认公告（可选）
        default_announcement = Announcement.query.first()
        if not default_announcement:
            # 需要先有一个用户才能创建公告，所以这里先不创建
            pass
        
        print("✓ 数据库初始化完成！")
        print("\n接下来请：")
        print("1. 运行网站：python run.py")
        print("2. 注册第一个账户（建议用户名：admin）")
        print("3. 运行设置管理员脚本：python set_admin.py")

if __name__ == '__main__':
=======
from app import create_app, db
from app.models import User, Announcement
from werkzeug.security import generate_password_hash
from app.utils import get_beijing_time

def setup_database():
    """初始化数据库，创建所有表"""
    app = create_app()
    with app.app_context():
        print("正在初始化数据库...")
        
        # 创建所有表
        db.create_all()
        print("✓ 数据库表创建完成")
        
        # 创建默认公告（可选）
        default_announcement = Announcement.query.first()
        if not default_announcement:
            # 需要先有一个用户才能创建公告，所以这里先不创建
            pass
        
        print("✓ 数据库初始化完成！")
        print("\n接下来请：")
        print("1. 运行网站：python run.py")
        print("2. 注册第一个账户（建议用户名：admin）")
        print("3. 运行设置管理员脚本：python set_admin.py")

if __name__ == '__main__':
>>>>>>> 81e637fcfecb61d89e503db91f19b153f055eca2
    setup_database()