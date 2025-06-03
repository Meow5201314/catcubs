from flask import request, redirect, url_for, flash
from flask_login import current_user

def check_email_verification():
    """检查用户邮箱验证状态的中间件"""
    # 白名单路由（不需要验证邮箱的路由）
    whitelist = [
        'auth.logout',
        'auth.verify_email',
        'auth.resend_verification',
        'auth.login',
        'auth.register',
        'static',
        'main.index',
        'posts.view',
        'main.profile',
        'admin.index',
        'admin.manage_users',
        'admin.delete_user',
        'admin.manage_posts',
        'admin.manage_comments',
        'admin.manage_reports',
        'admin_actions.manage_announcements',
        'admin_actions.create_announcement',
        'admin_actions.toggle_announcement',
        'admin_actions.delete_announcement',
        'admin_actions.view_logs',
        'admin_actions.get_stats'
    ]
    
    # 如果没有 endpoint，直接返回
    if not request.endpoint:
        return
    
    # 如果在白名单中，直接返回
    if request.endpoint in whitelist:
        return
    
    # 如果用户未登录，直接返回（让 Flask-Login 处理）
    if not current_user.is_authenticated:
        return
    
    # 如果用户已登录但邮箱未验证
    if not getattr(current_user, 'email_verified', True):
        # 对于需要验证的操作，重定向到验证页面
        if request.method == 'POST' or request.endpoint in [
            'posts.create', 'posts.add_comment', 
            'main.send_message', 'posts.edit', 'posts.delete'
        ]:
            flash('请先验证您的邮箱地址才能执行此操作', 'warning')
            return redirect(url_for('auth.resend_verification'))
