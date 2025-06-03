<<<<<<< HEAD
from app import create_app, db
from app.models import User

def set_admin():
    """将指定用户设置为站长"""
    app = create_app()
    with app.app_context():
        print("当前所有用户：")
        users = User.query.all()
        if not users:
            print("没有找到任何用户，请先注册账户！")
            return
        
        for i, user in enumerate(users, 1):
            role_display = user.role if user.role else "普通用户"
            print(f"{i}. {user.username} ({user.email}) - {role_display}")
        
        try:
            choice = input(f"\n请选择要设置为站长的用户 (1-{len(users)}): ")
            user_index = int(choice) - 1
            
            if 0 <= user_index < len(users):
                selected_user = users[user_index]
                selected_user.role = 'owner'
                selected_user.email_verified = True  # 确保邮箱已验证
                db.session.commit()
                
                print(f"✓ 用户 '{selected_user.username}' 已设置为站长！")
                print("现在该用户可以访问管理后台了。")
            else:
                print("无效的选择！")
        except (ValueError, IndexError):
            print("请输入有效的数字！")
        except Exception as e:
            print(f"设置失败：{e}")

if __name__ == '__main__':
=======
from app import create_app, db
from app.models import User

def set_admin():
    """将指定用户设置为站长"""
    app = create_app()
    with app.app_context():
        print("当前所有用户：")
        users = User.query.all()
        if not users:
            print("没有找到任何用户，请先注册账户！")
            return
        
        for i, user in enumerate(users, 1):
            role_display = user.role if user.role else "普通用户"
            print(f"{i}. {user.username} ({user.email}) - {role_display}")
        
        try:
            choice = input(f"\n请选择要设置为站长的用户 (1-{len(users)}): ")
            user_index = int(choice) - 1
            
            if 0 <= user_index < len(users):
                selected_user = users[user_index]
                selected_user.role = 'owner'
                selected_user.email_verified = True  # 确保邮箱已验证
                db.session.commit()
                
                print(f"✓ 用户 '{selected_user.username}' 已设置为站长！")
                print("现在该用户可以访问管理后台了。")
            else:
                print("无效的选择！")
        except (ValueError, IndexError):
            print("请输入有效的数字！")
        except Exception as e:
            print(f"设置失败：{e}")

if __name__ == '__main__':
>>>>>>> 81e637fcfecb61d89e503db91f19b153f055eca2
    set_admin()